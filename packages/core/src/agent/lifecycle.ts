/**
 * Agent lifecycle management
 * @module @omniaudit/core/agent/lifecycle
 */

import type { WorkItem, AnalysisResult } from '../types/index.js';
import type { AgentLifecycleHooks } from './types.js';

/**
 * Standard agent lifecycle stages
 */
export enum LifecycleStage {
  CREATED = 'created',
  INITIALIZING = 'initializing',
  READY = 'ready',
  ANALYZING = 'analyzing',
  REPORTING = 'reporting',
  CLEANING_UP = 'cleaning_up',
  DISPOSED = 'disposed',
  ERROR = 'error',
}

/**
 * Lifecycle state
 */
export interface LifecycleState {
  stage: LifecycleStage;
  timestamp: Date;
  error?: Error;
}

/**
 * Agent lifecycle manager
 *
 * Manages the standard lifecycle of an agent:
 * 1. Created → Initializing → Ready
 * 2. Ready → Analyzing → Reporting → Ready (repeatable)
 * 3. Ready → Cleaning Up → Disposed
 *
 * @example
 * ```typescript
 * const lifecycle = new AgentLifecycle('agent-1');
 * lifecycle.addHook('onBeforeInit', async () => {
 *   console.log('Initializing...');
 * });
 *
 * await lifecycle.executeInit(async () => {
 *   // Initialization logic
 * });
 * ```
 */
export class AgentLifecycle {
  private currentStage: LifecycleStage = LifecycleStage.CREATED;
  private stateHistory: LifecycleState[] = [];
  private hooks: AgentLifecycleHooks = {};

  constructor(private readonly agentId: string) {
    this.recordState(LifecycleStage.CREATED);
  }

  /**
   * Get current lifecycle stage
   */
  getStage(): LifecycleStage {
    return this.currentStage;
  }

  /**
   * Get lifecycle history
   */
  getHistory(): LifecycleState[] {
    return [...this.stateHistory];
  }

  /**
   * Check if agent is in a specific stage
   */
  isInStage(stage: LifecycleStage): boolean {
    return this.currentStage === stage;
  }

  /**
   * Check if agent is ready
   */
  isReady(): boolean {
    return this.currentStage === LifecycleStage.READY;
  }

  /**
   * Check if agent is disposed
   */
  isDisposed(): boolean {
    return this.currentStage === LifecycleStage.DISPOSED;
  }

  /**
   * Check if agent has error
   */
  hasError(): boolean {
    return this.currentStage === LifecycleStage.ERROR;
  }

  /**
   * Add lifecycle hook
   */
  addHook<K extends keyof AgentLifecycleHooks>(
    hookName: K,
    handler: NonNullable<AgentLifecycleHooks[K]>,
  ): void {
    this.hooks[hookName] = handler;
  }

  /**
   * Execute initialization lifecycle
   */
  async executeInit(initFn: () => Promise<void>): Promise<void> {
    this.validateTransition(LifecycleStage.INITIALIZING);
    this.transitionTo(LifecycleStage.INITIALIZING);

    try {
      await this.hooks.onBeforeInit?.();
      await initFn();
      await this.hooks.onAfterInit?.();
      this.transitionTo(LifecycleStage.READY);
    } catch (error) {
      this.handleError(error as Error);
      throw error;
    }
  }

  /**
   * Execute analysis lifecycle
   */
  async executeAnalyze(
    workItem: WorkItem,
    analyzeFn: (workItem: WorkItem) => Promise<AnalysisResult>,
  ): Promise<AnalysisResult> {
    this.validateTransition(LifecycleStage.ANALYZING);
    this.transitionTo(LifecycleStage.ANALYZING);

    try {
      await this.hooks.onBeforeAnalyze?.(workItem);
      const result = await analyzeFn(workItem);
      await this.hooks.onAfterAnalyze?.(result);
      this.transitionTo(LifecycleStage.REPORTING);
      return result;
    } catch (error) {
      this.handleError(error as Error);
      throw error;
    }
  }

  /**
   * Execute reporting lifecycle
   */
  async executeReport(reportFn: () => Promise<void>): Promise<void> {
    // May already be in reporting stage from analyze
    if (this.currentStage !== LifecycleStage.REPORTING) {
      this.validateTransition(LifecycleStage.REPORTING);
      this.transitionTo(LifecycleStage.REPORTING);
    }

    try {
      await reportFn();
      this.transitionTo(LifecycleStage.READY);
    } catch (error) {
      this.handleError(error as Error);
      throw error;
    }
  }

  /**
   * Execute cleanup lifecycle
   */
  async executeCleanup(cleanupFn: () => Promise<void>): Promise<void> {
    this.validateTransition(LifecycleStage.CLEANING_UP);
    this.transitionTo(LifecycleStage.CLEANING_UP);

    try {
      await this.hooks.onBeforeCleanup?.();
      await cleanupFn();
      await this.hooks.onAfterCleanup?.();
      this.transitionTo(LifecycleStage.DISPOSED);
    } catch (error) {
      this.handleError(error as Error);
      throw error;
    }
  }

  /**
   * Reset to ready state (after error or completion)
   */
  reset(): void {
    if (this.currentStage === LifecycleStage.ERROR || this.currentStage === LifecycleStage.READY) {
      this.transitionTo(LifecycleStage.READY);
    }
  }

  /**
   * Transition to new stage
   */
  private transitionTo(stage: LifecycleStage): void {
    this.currentStage = stage;
    this.recordState(stage);
  }

  /**
   * Record state in history
   */
  private recordState(stage: LifecycleStage, error?: Error): void {
    this.stateHistory.push({
      stage,
      timestamp: new Date(),
      error,
    });
  }

  /**
   * Validate if transition is allowed
   */
  private validateTransition(targetStage: LifecycleStage): void {
    const validTransitions: Record<LifecycleStage, LifecycleStage[]> = {
      [LifecycleStage.CREATED]: [LifecycleStage.INITIALIZING],
      [LifecycleStage.INITIALIZING]: [LifecycleStage.READY, LifecycleStage.ERROR],
      [LifecycleStage.READY]: [
        LifecycleStage.ANALYZING,
        LifecycleStage.CLEANING_UP,
        LifecycleStage.ERROR,
      ],
      [LifecycleStage.ANALYZING]: [
        LifecycleStage.REPORTING,
        LifecycleStage.READY,
        LifecycleStage.ERROR,
      ],
      [LifecycleStage.REPORTING]: [LifecycleStage.READY, LifecycleStage.ERROR],
      [LifecycleStage.CLEANING_UP]: [LifecycleStage.DISPOSED, LifecycleStage.ERROR],
      [LifecycleStage.DISPOSED]: [],
      [LifecycleStage.ERROR]: [LifecycleStage.READY, LifecycleStage.CLEANING_UP],
    };

    const allowed = validTransitions[this.currentStage];
    if (!allowed.includes(targetStage)) {
      throw new Error(
        `Invalid lifecycle transition from ${this.currentStage} to ${targetStage} for agent ${this.agentId}`,
      );
    }
  }

  /**
   * Handle lifecycle error
   */
  private handleError(error: Error): void {
    this.currentStage = LifecycleStage.ERROR;
    this.recordState(LifecycleStage.ERROR, error);
    this.hooks.onError?.(error);
  }
}
