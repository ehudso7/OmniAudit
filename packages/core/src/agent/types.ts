/**
 * Agent type definitions
 * @module @omniaudit/core/agent/types
 */

import type { WorkItem, AnalysisResult, AgentConfig } from '../types/index.js';
import type { EventBus } from '../bus/event-bus.js';

/**
 * Agent initialization context
 */
export interface AgentContext {
  /** Unique agent identifier */
  id: string;

  /** Event bus for communication */
  eventBus: EventBus;

  /** Agent configuration */
  config: AgentConfig;

  /** Correlation ID for tracking related events */
  correlationId: string;
}

/**
 * Agent interface
 */
export interface IAgent {
  /** Unique agent identifier */
  readonly id: string;

  /** Initialize the agent */
  init(): Promise<void>;

  /** Analyze a work item */
  analyze(workItem: WorkItem): Promise<AnalysisResult>;

  /** Report analysis results */
  report(result: AnalysisResult): Promise<void>;

  /** Cleanup resources */
  cleanup(): Promise<void>;

  /** Check if agent is available */
  isAvailable(): boolean;

  /** Get current agent status */
  getStatus(): string;
}

/**
 * Agent lifecycle hooks
 */
export interface AgentLifecycleHooks {
  /** Called before initialization */
  onBeforeInit?(): Promise<void> | void;

  /** Called after initialization */
  onAfterInit?(): Promise<void> | void;

  /** Called before analysis */
  onBeforeAnalyze?(workItem: WorkItem): Promise<void> | void;

  /** Called after analysis */
  onAfterAnalyze?(result: AnalysisResult): Promise<void> | void;

  /** Called on error */
  onError?(error: Error): Promise<void> | void;

  /** Called before cleanup */
  onBeforeCleanup?(): Promise<void> | void;

  /** Called after cleanup */
  onAfterCleanup?(): Promise<void> | void;
}
