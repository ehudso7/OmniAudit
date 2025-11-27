/**
 * Core orchestration engine
 * @module @omniaudit/core/orchestrator
 */

import { randomUUID } from 'node:crypto';
import { EventEmitter } from 'node:events';
import type {
  OrchestratorConfig,
  WorkItem,
  AnalysisResult,
  Checkpoint,
  MemoryMetrics,
  ComplexityMetrics,
} from './types/index.js';
import { EventBus } from './bus/event-bus.js';
import { AgentPool, type AgentFactory } from './agent/pool.js';
import { createCheckpointEvent, createMemoryWarningEvent } from './bus/messages.js';
import { analyzeComplexity, sortByComplexity } from './complexity/analyzer.js';

/**
 * Orchestrator events
 */
export interface OrchestratorEvents {
  started: () => void;
  progress: (processed: number, total: number) => void;
  checkpoint: (checkpoint: Checkpoint) => void;
  memoryWarning: (metrics: MemoryMetrics) => void;
  completed: (results: AnalysisResult[]) => void;
  error: (error: Error) => void;
}

/**
 * Orchestrator state
 */
interface OrchestratorState {
  workItems: Map<string, WorkItem>;
  completedItems: Set<string>;
  failedItems: Set<string>;
  results: Map<string, AnalysisResult>;
  startedAt?: Date;
  lastCheckpoint?: Date;
}

/**
 * Agent Orchestrator
 *
 * Core orchestration engine that manages:
 * - Agent pool (spawn up to 20 parallel agents)
 * - Intelligent work distribution based on file complexity
 * - Circuit breaker pattern for failing agents
 * - Agent restart with exponential backoff
 * - Memory pressure monitoring
 * - Cross-agent communication bus
 * - Checkpoint/resume capability
 *
 * @example
 * ```typescript
 * const orchestrator = new AgentOrchestrator(agentFactory, config);
 *
 * // Subscribe to events
 * orchestrator.on('progress', (processed, total) => {
 *   console.log(`Progress: ${processed}/${total}`);
 * });
 *
 * // Start analysis
 * const results = await orchestrator.orchestrate(filePaths);
 * ```
 */
export class AgentOrchestrator extends EventEmitter {
  private readonly eventBus: EventBus;
  private readonly agentPool: AgentPool;
  private readonly config: OrchestratorConfig;
  private state: OrchestratorState;
  private memoryMonitorInterval?: NodeJS.Timeout;
  private checkpointInterval?: NodeJS.Timeout;
  private isRunning = false;

  constructor(agentFactory: AgentFactory, config: Partial<OrchestratorConfig> = {}) {
    super();

    this.config = {
      maxAgents: config.maxAgents ?? 20,
      memoryThresholdMb: config.memoryThresholdMb ?? 1024,
      checkpointIntervalMs: config.checkpointIntervalMs ?? 30000,
      enableCheckpointing: config.enableCheckpointing ?? true,
      agentConfig: {
        maxRetries: config.agentConfig?.maxRetries ?? 3,
        retryBackoffMs: config.agentConfig?.retryBackoffMs ?? 1000,
        maxRetryBackoffMs: config.agentConfig?.maxRetryBackoffMs ?? 30000,
        timeoutMs: config.agentConfig?.timeoutMs ?? 300000,
        circuitBreakerThreshold: config.agentConfig?.circuitBreakerThreshold ?? 5,
        circuitBreakerResetMs: config.agentConfig?.circuitBreakerResetMs ?? 60000,
      },
    };

    this.eventBus = new EventBus();
    this.agentPool = new AgentPool(agentFactory, {
      maxAgents: this.config.maxAgents,
      circuitBreakerThreshold: this.config.agentConfig.circuitBreakerThreshold,
      circuitBreakerResetMs: this.config.agentConfig.circuitBreakerResetMs,
      eventBus: this.eventBus,
    });

    this.state = {
      workItems: new Map(),
      completedItems: new Set(),
      failedItems: new Set(),
      results: new Map(),
    };
  }

  /**
   * Get the event bus for external listeners
   */
  getEventBus(): EventBus {
    return this.eventBus;
  }

  /**
   * Orchestrate analysis of files
   */
  async orchestrate(filePaths: string[]): Promise<AnalysisResult[]> {
    if (this.isRunning) {
      throw new Error('Orchestrator is already running');
    }

    this.isRunning = true;
    this.state.startedAt = new Date();
    this.emit('started');

    try {
      // Initialize agent pool
      await this.agentPool.init();

      // Analyze file complexity and create work items
      const workItems = await this.prepareWorkItems(filePaths);

      // Start monitoring
      this.startMemoryMonitoring();
      if (this.config.enableCheckpointing) {
        this.startCheckpointing();
      }

      // Distribute and execute work
      const results = await this.executeWork(workItems);

      this.emit('completed', results);
      return results;
    } catch (error) {
      this.emit('error', error as Error);
      throw error;
    } finally {
      // Always stop monitoring in finally to prevent leaks
      this.stopMonitoring();
      await this.agentPool.shutdown();
      this.isRunning = false;
    }
  }

  /**
   * Resume from checkpoint
   */
  async resumeFromCheckpoint(checkpoint: Checkpoint): Promise<AnalysisResult[]> {
    // Restore state from checkpoint
    this.state.workItems = new Map(
      checkpoint.workItems.map((item) => [item.id, item]),
    );
    this.state.completedItems = new Set(checkpoint.completedItems);

    // Filter to only incomplete work items
    const incompleteWorkItems = checkpoint.workItems.filter(
      (item) => !checkpoint.completedItems.includes(item.id),
    );

    // Continue orchestration
    return this.orchestrate(incompleteWorkItems.map((item) => item.filePath));
  }

  /**
   * Get current checkpoint
   */
  createCheckpoint(): Checkpoint {
    return {
      timestamp: new Date(),
      workItems: Array.from(this.state.workItems.values()),
      agentStates: [], // Would be populated from agent pool
      completedItems: Array.from(this.state.completedItems),
      totalItems: this.state.workItems.size,
      processedItems: this.state.completedItems.size + this.state.failedItems.size,
    };
  }

  /**
   * Get pool statistics
   */
  getPoolStats() {
    return this.agentPool.getStats();
  }

  /**
   * Get orchestrator progress
   */
  getProgress(): { processed: number; total: number; percentage: number } {
    const total = this.state.workItems.size;
    const processed = this.state.completedItems.size + this.state.failedItems.size;
    return {
      processed,
      total,
      percentage: total > 0 ? Math.round((processed / total) * 100) : 0,
    };
  }

  /**
   * Prepare work items from file paths
   */
  private async prepareWorkItems(filePaths: string[]): Promise<WorkItem[]> {
    // Analyze complexity of all files
    const complexityResults = await this.analyzeComplexityBatch(filePaths);

    // Sort by complexity (most complex first for better load distribution)
    const sortedResults = sortByComplexity(complexityResults);

    // Create work items
    const workItems: WorkItem[] = sortedResults.map((complexity) => ({
      id: randomUUID(),
      filePath: complexity.filePath,
      complexity,
      status: 'pending',
      retryCount: 0,
    }));

    // Store in state
    for (const item of workItems) {
      this.state.workItems.set(item.id, item);
    }

    return workItems;
  }

  /**
   * Analyze complexity of files in batches
   */
  private async analyzeComplexityBatch(
    filePaths: string[],
  ): Promise<ComplexityMetrics[]> {
    const batchSize = 50;
    const results: ComplexityMetrics[] = [];

    for (let i = 0; i < filePaths.length; i += batchSize) {
      const batch = filePaths.slice(i, i + batchSize);
      const batchResults = await Promise.allSettled(
        batch.map((filePath) => analyzeComplexity(filePath)),
      );

      for (const result of batchResults) {
        if (result.status === 'fulfilled') {
          results.push(result.value);
        } else {
          console.warn(`Failed to analyze complexity:`, result.reason);
        }
      }
    }

    return results;
  }

  /**
   * Execute work items using agent pool in parallel
   *
   * Uses Promise.allSettled to ensure all work items complete even if some fail.
   * The agent pool's internal limiter controls concurrency (up to maxAgents).
   */
  private async executeWork(workItems: WorkItem[]): Promise<AnalysisResult[]> {
    // Mark all work items as processing
    for (const workItem of workItems) {
      workItem.status = 'processing';
      workItem.startedAt = new Date();
    }

    // Execute all work items in parallel using allSettled for resilience
    const settledResults = await Promise.allSettled(
      workItems.map(async (workItem) => {
        const result = await this.agentPool.executeWork(workItem);

        // Update state for each completed item
        if (result.success) {
          this.state.completedItems.add(workItem.id);
        } else {
          this.state.failedItems.add(workItem.id);
        }

        this.state.results.set(workItem.id, result);

        // Emit progress after each completion
        this.emitProgress();

        return result;
      }),
    );

    // Extract results, creating error results for any rejected promises
    const results: AnalysisResult[] = settledResults.map((settled, index) => {
      if (settled.status === 'fulfilled') {
        return settled.value;
      }
      // Handle unexpected rejections by creating an error result
      const workItem = workItems[index];
      this.state.failedItems.add(workItem.id);
      const errorResult: AnalysisResult = {
        agentId: 'unknown',
        workItemId: workItem.id,
        filePath: workItem.filePath,
        findings: [],
        duration: 0,
        success: false,
        error: settled.reason instanceof Error ? settled.reason.message : String(settled.reason),
      };
      this.state.results.set(workItem.id, errorResult);
      return errorResult;
    });

    return results;
  }

  /**
   * Emit progress event
   */
  private emitProgress(): void {
    const { processed, total } = this.getProgress();
    this.emit('progress', processed, total);
  }

  /**
   * Start memory monitoring
   */
  private startMemoryMonitoring(): void {
    this.memoryMonitorInterval = setInterval(() => {
      const metrics = this.getMemoryMetrics();

      if (metrics.heapUsedMb > this.config.memoryThresholdMb) {
        const event = createMemoryWarningEvent(
          metrics.heapUsedMb,
          metrics.heapTotalMb,
          this.config.memoryThresholdMb,
        );

        this.eventBus.emit(event);
        this.emit('memoryWarning', metrics);

        // Trigger garbage collection if available
        if (global.gc) {
          global.gc();
        }
      }
    }, 5000); // Check every 5 seconds
  }

  /**
   * Start checkpointing
   */
  private startCheckpointing(): void {
    this.checkpointInterval = setInterval(() => {
      const checkpoint = this.createCheckpoint();
      this.state.lastCheckpoint = new Date();

      const event = createCheckpointEvent(
        checkpoint.processedItems,
        checkpoint.totalItems,
      );

      this.eventBus.emit(event);
      this.emit('checkpoint', checkpoint);
    }, this.config.checkpointIntervalMs);
  }

  /**
   * Stop all monitoring
   */
  private stopMonitoring(): void {
    if (this.memoryMonitorInterval) {
      clearInterval(this.memoryMonitorInterval);
      this.memoryMonitorInterval = undefined;
    }

    if (this.checkpointInterval) {
      clearInterval(this.checkpointInterval);
      this.checkpointInterval = undefined;
    }
  }

  /**
   * Get current memory metrics
   */
  private getMemoryMetrics(): MemoryMetrics {
    const usage = process.memoryUsage();
    return {
      heapUsedMb: Math.round(usage.heapUsed / 1024 / 1024),
      heapTotalMb: Math.round(usage.heapTotal / 1024 / 1024),
      externalMb: Math.round(usage.external / 1024 / 1024),
      rss: Math.round(usage.rss / 1024 / 1024),
      timestamp: new Date(),
    };
  }
}
