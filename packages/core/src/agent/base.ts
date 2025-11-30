/**
 * Base agent implementation
 * @module @omniaudit/core/agent/base
 */

import type { WorkItem, AnalysisResult, AgentState, Finding } from '../types/index.js';
import { AgentStatus } from '../types/index.js';
import type { IAgent, AgentContext } from './types.js';
import { AgentLifecycle } from './lifecycle.js';
import {
  createProgressEvent,
  createErrorEvent,
  createCompleteEvent,
  createStateChangeEvent,
} from '../bus/messages.js';

/**
 * Custom error class for agent errors
 */
export class AgentError extends Error {
  constructor(
    message: string,
    public readonly agentId: string,
    public readonly fatal = false,
    public readonly cause?: Error,
  ) {
    super(message);
    this.name = 'AgentError';
  }
}

/**
 * Abstract base agent class
 *
 * Provides standard agent functionality:
 * - Lifecycle management
 * - Event emission
 * - Error handling with retry logic
 * - Progress reporting
 * - State tracking
 *
 * Subclasses must implement:
 * - doAnalyze(): Actual analysis logic
 *
 * @example
 * ```typescript
 * class MyAgent extends BaseAgent {
 *   protected async doAnalyze(workItem: WorkItem): Promise<Finding[]> {
 *     // Custom analysis logic
 *     return findings;
 *   }
 * }
 *
 * const agent = new MyAgent(context);
 * await agent.init();
 * const result = await agent.analyze(workItem);
 * await agent.cleanup();
 * ```
 */
export abstract class BaseAgent implements IAgent {
  readonly id: string;
  protected readonly context: AgentContext;
  protected readonly lifecycle: AgentLifecycle;
  protected state: AgentState;
  protected retryCount = 0;

  constructor(context: AgentContext) {
    this.id = context.id;
    this.context = context;
    this.lifecycle = new AgentLifecycle(this.id);
    this.state = {
      id: this.id,
      status: AgentStatus.IDLE,
      progress: 0,
      retryCount: 0,
    };

    // Setup lifecycle hooks
    this.setupLifecycleHooks();
  }

  /**
   * Initialize the agent
   */
  async init(): Promise<void> {
    await this.lifecycle.executeInit(async () => {
      this.updateState({ status: AgentStatus.INITIALIZING });
      await this.doInit();
      this.updateState({ status: AgentStatus.IDLE });
    });
  }

  /**
   * Analyze a work item
   */
  async analyze(workItem: WorkItem): Promise<AnalysisResult> {
    const startTime = Date.now();

    return await this.lifecycle.executeAnalyze(workItem, async (item) => {
      this.updateState({
        status: AgentStatus.ANALYZING,
        currentFile: item.filePath,
        startedAt: new Date(),
      });

      try {
        // Execute analysis with retry logic
        const findings = await this.executeWithRetry(() => this.doAnalyze(item));

        const result: AnalysisResult = {
          agentId: this.id,
          workItemId: item.id,
          filePath: item.filePath,
          findings,
          duration: Date.now() - startTime,
          success: true,
        };

        // Reset retry count on success
        this.retryCount = 0;
        this.updateState({ retryCount: 0 });

        return result;
      } catch (error) {
        const agentError = error instanceof AgentError ? error : new AgentError(
          error instanceof Error ? error.message : String(error),
          this.id,
          false,
          error instanceof Error ? error : undefined,
        );

        this.handleAnalysisError(agentError, item);

        const result: AnalysisResult = {
          agentId: this.id,
          workItemId: item.id,
          filePath: item.filePath,
          findings: [],
          duration: Date.now() - startTime,
          success: false,
          error: agentError.message,
        };

        return result;
      }
    });
  }

  /**
   * Report analysis results
   */
  async report(result: AnalysisResult): Promise<void> {
    await this.lifecycle.executeReport(async () => {
      this.updateState({ status: AgentStatus.REPORTING });

      // Emit complete event
      this.context.eventBus.emit(
        createCompleteEvent(this.id, result, result.duration, this.context.correlationId),
      );

      await this.doReport(result);

      this.updateState({
        status: AgentStatus.COMPLETED,
        completedAt: new Date(),
        progress: 100,
      });
    });
  }

  /**
   * Cleanup agent resources
   */
  async cleanup(): Promise<void> {
    await this.lifecycle.executeCleanup(async () => {
      await this.doCleanup();
      this.updateState({ status: AgentStatus.IDLE });
    });
  }

  /**
   * Check if agent is available
   */
  isAvailable(): boolean {
    return this.lifecycle.isReady() && this.state.status === AgentStatus.IDLE;
  }

  /**
   * Get current agent status
   */
  getStatus(): string {
    return this.state.status;
  }

  /**
   * Get current agent state
   */
  getState(): AgentState {
    return { ...this.state };
  }

  /**
   * Update agent progress
   */
  protected updateProgress(progress: number, message?: string): void {
    this.updateState({ progress });
    this.context.eventBus.emit(
      createProgressEvent(this.id, progress, {
        message,
        currentFile: this.state.currentFile,
        correlationId: this.context.correlationId,
      }),
    );
  }

  /**
   * Update agent state
   */
  protected updateState(updates: Partial<AgentState>): void {
    const previousState = { ...this.state };
    this.state = { ...this.state, ...updates };

    // Emit state change event
    this.context.eventBus.emit(
      createStateChangeEvent(this.id, previousState, this.state, this.context.correlationId),
    );
  }

  /**
   * Execute function with retry logic
   */
  protected async executeWithRetry<T>(
    fn: () => Promise<T>,
    maxRetries?: number,
  ): Promise<T> {
    const retries = maxRetries ?? this.context.config.maxRetries;
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        if (attempt < retries) {
          const backoff = this.calculateBackoff(attempt);
          await this.sleep(backoff);
          this.retryCount++;
          this.updateState({ retryCount: this.retryCount });
        }
      }
    }

    throw lastError;
  }

  /**
   * Calculate exponential backoff delay
   */
  protected calculateBackoff(attempt: number): number {
    const baseDelay = this.context.config.retryBackoffMs;
    const maxDelay = this.context.config.maxRetryBackoffMs;
    const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);

    // Add jitter (±10%)
    const jitter = delay * 0.1 * (Math.random() * 2 - 1);
    return Math.round(delay + jitter);
  }

  /**
   * Sleep utility
   */
  protected sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Handle analysis error
   */
  protected handleAnalysisError(error: AgentError, workItem: WorkItem): void {
    this.updateState({
      status: AgentStatus.ERROR,
      lastError: error.message,
    });

    this.context.eventBus.emit(
      createErrorEvent(this.id, error, {
        filePath: workItem.filePath,
        fatal: error.fatal,
        correlationId: this.context.correlationId,
      }),
    );
  }

  /**
   * Setup lifecycle hooks
   */
  protected setupLifecycleHooks(): void {
    this.lifecycle.addHook('onError', (error) => {
      this.updateState({
        status: AgentStatus.ERROR,
        lastError: error.message,
      });
    });
  }

  /**
   * Custom initialization logic (override in subclass)
   */
  protected async doInit(): Promise<void> {
    // Override in subclass
  }

  /**
   * Custom analysis logic (must override in subclass)
   */
  protected abstract doAnalyze(workItem: WorkItem): Promise<Finding[]>;

  /**
   * Custom reporting logic (override in subclass)
   */
  protected async doReport(_result: AnalysisResult): Promise<void> {
    // Override in subclass
  }

  /**
   * Custom cleanup logic (override in subclass)
   */
  protected async doCleanup(): Promise<void> {
    // Override in subclass
  }
}
