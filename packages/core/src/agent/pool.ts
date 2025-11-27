/**
 * Agent pool management
 * @module @omniaudit/core/agent/pool
 */

import { randomUUID } from 'node:crypto';
import pLimit from 'p-limit';
import type { IAgent, AgentContext } from './types.js';
import type { WorkItem, AnalysisResult, CircuitBreakerState } from '../types/index.js';
import type { EventBus } from '../bus/event-bus.js';

/**
 * Agent factory function
 */
export type AgentFactory = (context: AgentContext) => IAgent;

/**
 * Pool statistics
 */
export interface PoolStats {
  totalAgents: number;
  availableAgents: number;
  busyAgents: number;
  circuitOpenAgents: number;
  totalTasksProcessed: number;
  totalFailures: number;
}

/**
 * Agent pool options
 */
export interface AgentPoolOptions {
  /** Maximum number of agents */
  maxAgents: number;

  /** Circuit breaker failure threshold */
  circuitBreakerThreshold: number;

  /** Circuit breaker reset time in milliseconds */
  circuitBreakerResetMs: number;

  /** Event bus for communication */
  eventBus: EventBus;
}

/**
 * Agent pool for managing parallel agents
 *
 * Features:
 * - Dynamic agent spawning up to max limit
 * - Circuit breaker pattern for failing agents
 * - Agent restart with exponential backoff
 * - Work distribution across available agents
 * - Pool statistics and monitoring
 *
 * @example
 * ```typescript
 * const pool = new AgentPool(agentFactory, {
 *   maxAgents: 20,
 *   circuitBreakerThreshold: 5,
 *   circuitBreakerResetMs: 60000,
 *   eventBus,
 * });
 *
 * await pool.init();
 *
 * const result = await pool.executeWork(workItem);
 *
 * await pool.shutdown();
 * ```
 */
export class AgentPool {
  private agents: Map<string, IAgent> = new Map();
  private circuitBreakers: Map<string, CircuitBreakerState> = new Map();
  private pendingRestarts: Map<string, ReturnType<typeof setTimeout>> = new Map();
  private limiter: ReturnType<typeof pLimit>;
  private tasksProcessed = 0;
  private totalFailures = 0;
  private isInitialized = false;

  constructor(
    private readonly agentFactory: AgentFactory,
    private readonly options: AgentPoolOptions,
  ) {
    this.limiter = pLimit(options.maxAgents);
  }

  /**
   * Initialize the agent pool
   */
  async init(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    // Start with minimum number of agents (25% of max or at least 1)
    const initialAgents = Math.max(1, Math.floor(this.options.maxAgents * 0.25));

    const initPromises = Array.from({ length: initialAgents }, () =>
      this.createAgent(),
    );

    await Promise.all(initPromises);
    this.isInitialized = true;
  }

  /**
   * Execute work item using an available agent
   */
  async executeWork(workItem: WorkItem): Promise<AnalysisResult> {
    return this.limiter(async () => {
      const agent = await this.getOrCreateAgent();

      try {
        const result = await agent.analyze(workItem);
        await agent.report(result);

        this.tasksProcessed++;

        if (!result.success) {
          this.totalFailures++;
          this.handleAgentFailure(agent.id);
        } else {
          this.handleAgentSuccess(agent.id);
        }

        return result;
      } catch (error) {
        this.totalFailures++;
        this.handleAgentFailure(agent.id);

        return {
          agentId: agent.id,
          workItemId: workItem.id,
          filePath: workItem.filePath,
          findings: [],
          duration: 0,
          success: false,
          error: error instanceof Error ? error.message : String(error),
        };
      }
    });
  }

  /**
   * Execute multiple work items in parallel
   */
  async executeWorkBatch(workItems: WorkItem[]): Promise<AnalysisResult[]> {
    return Promise.all(workItems.map((item) => this.executeWork(item)));
  }

  /**
   * Get pool statistics
   */
  getStats(): PoolStats {
    const circuitOpenCount = Array.from(this.circuitBreakers.values()).filter(
      (cb) => cb.state === 'open',
    ).length;

    const busyAgents = this.agents.size - this.getAvailableAgents().length;

    return {
      totalAgents: this.agents.size,
      availableAgents: this.getAvailableAgents().length,
      busyAgents,
      circuitOpenAgents: circuitOpenCount,
      totalTasksProcessed: this.tasksProcessed,
      totalFailures: this.totalFailures,
    };
  }

  /**
   * Shutdown the pool and cleanup all agents
   */
  async shutdown(): Promise<void> {
    // Cancel all pending restart timers first
    for (const timerId of this.pendingRestarts.values()) {
      clearTimeout(timerId);
    }
    this.pendingRestarts.clear();

    const cleanupPromises = Array.from(this.agents.values()).map((agent) =>
      agent.cleanup().catch((error) => {
        console.error(`Error cleaning up agent ${agent.id}:`, error);
      }),
    );

    await Promise.all(cleanupPromises);

    this.agents.clear();
    this.circuitBreakers.clear();
    this.isInitialized = false;
  }

  /**
   * Remove a specific agent from the pool
   */
  async removeAgent(agentId: string): Promise<void> {
    const agent = this.agents.get(agentId);
    if (agent) {
      await agent.cleanup();
      this.agents.delete(agentId);
      this.circuitBreakers.delete(agentId);
    }
  }

  /**
   * Restart a specific agent
   */
  async restartAgent(agentId: string): Promise<void> {
    await this.removeAgent(agentId);
    await this.createAgent();
  }

  /**
   * Get or create an available agent
   */
  private async getOrCreateAgent(): Promise<IAgent> {
    // Try to get an available agent
    const availableAgents = this.getAvailableAgents();
    if (availableAgents.length > 0) {
      return availableAgents[0];
    }

    // Create new agent if under limit
    if (this.agents.size < this.options.maxAgents) {
      return await this.createAgent();
    }

    // Wait for an agent to become available
    return await this.waitForAvailableAgent();
  }

  /**
   * Get list of available agents (not in circuit breaker open state)
   */
  private getAvailableAgents(): IAgent[] {
    return Array.from(this.agents.values()).filter((agent) => {
      const circuitBreaker = this.circuitBreakers.get(agent.id);
      if (circuitBreaker?.state === 'open') {
        // Check if we should try half-open
        if (
          circuitBreaker.nextAttemptAt &&
          circuitBreaker.nextAttemptAt <= new Date()
        ) {
          circuitBreaker.state = 'half_open';
          return agent.isAvailable();
        }
        return false;
      }
      return agent.isAvailable();
    });
  }

  /**
   * Wait for an agent to become available with timeout
   */
  private async waitForAvailableAgent(): Promise<IAgent> {
    const timeoutMs = this.options.circuitBreakerResetMs * 2;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        clearInterval(checkInterval);
        reject(new Error(`Timeout waiting for available agent after ${timeoutMs}ms`));
      }, timeoutMs);

      const checkInterval = setInterval(() => {
        const available = this.getAvailableAgents();
        if (available.length > 0) {
          clearTimeout(timeout);
          clearInterval(checkInterval);
          resolve(available[0]);
        }
      }, 100); // Check every 100ms
    });
  }

  /**
   * Create a new agent
   */
  private async createAgent(): Promise<IAgent> {
    const agentId = `agent-${randomUUID()}`;

    const context: AgentContext = {
      id: agentId,
      eventBus: this.options.eventBus,
      config: {
        maxRetries: 3,
        retryBackoffMs: 1000,
        maxRetryBackoffMs: 30000,
        timeoutMs: 300000,
        circuitBreakerThreshold: this.options.circuitBreakerThreshold,
        circuitBreakerResetMs: this.options.circuitBreakerResetMs,
      },
      correlationId: randomUUID(),
    };

    const agent = this.agentFactory(context);
    await agent.init();

    this.agents.set(agentId, agent);
    this.circuitBreakers.set(agentId, {
      agentId,
      failureCount: 0,
      state: 'closed',
    });

    return agent;
  }

  /**
   * Handle agent failure
   */
  private handleAgentFailure(agentId: string): void {
    const circuitBreaker = this.circuitBreakers.get(agentId);
    if (!circuitBreaker) {
      return;
    }

    circuitBreaker.failureCount++;
    circuitBreaker.lastFailureAt = new Date();

    if (circuitBreaker.failureCount >= this.options.circuitBreakerThreshold) {
      // Open circuit breaker
      circuitBreaker.state = 'open';
      circuitBreaker.nextAttemptAt = new Date(
        Date.now() + this.options.circuitBreakerResetMs,
      );

      // Schedule agent restart with exponential backoff
      this.scheduleAgentRestart(agentId);
    }
  }

  /**
   * Handle agent success
   */
  private handleAgentSuccess(agentId: string): void {
    const circuitBreaker = this.circuitBreakers.get(agentId);
    if (!circuitBreaker) {
      return;
    }

    // Reset failure count on success
    if (circuitBreaker.state === 'half_open') {
      circuitBreaker.state = 'closed';
      circuitBreaker.failureCount = 0;
    } else if (circuitBreaker.failureCount > 0) {
      circuitBreaker.failureCount = Math.max(0, circuitBreaker.failureCount - 1);
    }
  }

  /**
   * Schedule agent restart with exponential backoff
   */
  private scheduleAgentRestart(agentId: string): void {
    const circuitBreaker = this.circuitBreakers.get(agentId);
    if (!circuitBreaker) {
      return;
    }

    // Cancel any existing pending restart for this agent
    const existingTimer = this.pendingRestarts.get(agentId);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    const backoffMs = Math.min(
      1000 * Math.pow(2, circuitBreaker.failureCount - this.options.circuitBreakerThreshold),
      60000, // Max 60 seconds
    );

    // Add jitter (±10%) to prevent thundering herd
    const jitter = backoffMs * 0.1 * (Math.random() - 0.5) * 2;
    const finalBackoffMs = Math.max(0, backoffMs + jitter);

    const timerId = setTimeout(async () => {
      this.pendingRestarts.delete(agentId);
      try {
        await this.restartAgent(agentId);
      } catch (error) {
        console.error(`Failed to restart agent ${agentId}:`, error);
      }
    }, finalBackoffMs);

    this.pendingRestarts.set(agentId, timerId);
  }
}
