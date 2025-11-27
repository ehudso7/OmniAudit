/**
 * OmniAudit Core Orchestration Engine
 * @module @omniaudit/core
 */

// Main orchestrator
export { AgentOrchestrator } from './orchestrator.js';
export type { OrchestratorEvents } from './orchestrator.js';

// Types
export * from './types/index.js';

// Event bus
export { EventBus } from './bus/event-bus.js';
export * from './bus/types.js';
export * from './bus/messages.js';

// Agent
export { BaseAgent, AgentError } from './agent/base.js';
export { AgentLifecycle, LifecycleStage } from './agent/lifecycle.js';
export { AgentPool } from './agent/pool.js';
export type {
  IAgent,
  AgentContext,
  AgentLifecycleHooks,
} from './agent/types.js';
export type { AgentFactory, PoolStats, AgentPoolOptions } from './agent/pool.js';

// Complexity
export {
  analyzeComplexity,
  analyzeComplexityBatch,
  sortByComplexity,
  detectLanguage,
} from './complexity/analyzer.js';
export { Language } from './complexity/types.js';
export type { LanguageWeights, ScorerResult, ComplexityAnalysis } from './complexity/types.js';

// Scorers
export { calculateLocScore } from './complexity/scorers/loc.js';
export { calculateCyclomaticScore } from './complexity/scorers/cyclomatic.js';
export { calculateDependencyScore } from './complexity/scorers/dependencies.js';
