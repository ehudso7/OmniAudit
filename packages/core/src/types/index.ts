/**
 * Core type definitions for OmniAudit orchestration engine
 * @module @omniaudit/core/types
 */

import { z } from 'zod';

/**
 * Agent status enumeration
 */
export enum AgentStatus {
  IDLE = 'idle',
  INITIALIZING = 'initializing',
  ANALYZING = 'analyzing',
  REPORTING = 'reporting',
  COMPLETED = 'completed',
  ERROR = 'error',
  CIRCUIT_OPEN = 'circuit_open',
}

/**
 * Agent lifecycle state
 */
export const AgentStateSchema = z.object({
  id: z.string(),
  status: z.nativeEnum(AgentStatus),
  currentFile: z.string().optional(),
  progress: z.number().min(0).max(100),
  retryCount: z.number().default(0),
  lastError: z.string().optional(),
  startedAt: z.date().optional(),
  completedAt: z.date().optional(),
});

export type AgentState = z.infer<typeof AgentStateSchema>;

/**
 * File complexity metrics
 */
export const ComplexityMetricsSchema = z.object({
  filePath: z.string(),
  linesOfCode: z.number(),
  cyclomaticComplexity: z.number(),
  dependencyCount: z.number(),
  nestingDepth: z.number().optional(),
  totalScore: z.number(),
  language: z.string(),
});

export type ComplexityMetrics = z.infer<typeof ComplexityMetricsSchema>;

/**
 * Finding severity levels
 */
export enum FindingSeverity {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  INFO = 'info',
}

/**
 * Audit finding
 */
export const FindingSchema = z.object({
  id: z.string(),
  severity: z.nativeEnum(FindingSeverity),
  category: z.string(),
  message: z.string(),
  filePath: z.string(),
  line: z.number().optional(),
  column: z.number().optional(),
  code: z.string().optional(),
  suggestion: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type Finding = z.infer<typeof FindingSchema>;

/**
 * Agent configuration
 */
export const AgentConfigSchema = z.object({
  maxRetries: z.number().default(3),
  retryBackoffMs: z.number().default(1000),
  maxRetryBackoffMs: z.number().default(30000),
  timeoutMs: z.number().default(300000), // 5 minutes
  circuitBreakerThreshold: z.number().default(5),
  circuitBreakerResetMs: z.number().default(60000), // 1 minute
});

export type AgentConfig = z.infer<typeof AgentConfigSchema>;

/**
 * Orchestrator configuration
 */
export const OrchestratorConfigSchema = z.object({
  maxAgents: z.number().min(1).max(20).default(20),
  memoryThresholdMb: z.number().default(1024), // 1GB
  checkpointIntervalMs: z.number().default(30000), // 30 seconds
  enableCheckpointing: z.boolean().default(true),
  agentConfig: AgentConfigSchema.default({}),
});

export type OrchestratorConfig = z.infer<typeof OrchestratorConfigSchema>;

/**
 * Work item for distribution
 */
export const WorkItemSchema = z.object({
  id: z.string(),
  filePath: z.string(),
  complexity: ComplexityMetricsSchema,
  assignedAgent: z.string().optional(),
  status: z.enum(['pending', 'assigned', 'processing', 'completed', 'failed']).default('pending'),
  retryCount: z.number().default(0),
  startedAt: z.date().optional(),
  completedAt: z.date().optional(),
});

export type WorkItem = z.infer<typeof WorkItemSchema>;

/**
 * Agent analysis result
 */
export const AnalysisResultSchema = z.object({
  agentId: z.string(),
  workItemId: z.string(),
  filePath: z.string(),
  findings: z.array(FindingSchema),
  duration: z.number(),
  success: z.boolean(),
  error: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type AnalysisResult = z.infer<typeof AnalysisResultSchema>;

/**
 * Checkpoint data for resume capability
 */
export const CheckpointSchema = z.object({
  timestamp: z.date(),
  workItems: z.array(WorkItemSchema),
  agentStates: z.array(AgentStateSchema),
  completedItems: z.array(z.string()),
  totalItems: z.number(),
  processedItems: z.number(),
});

export type Checkpoint = z.infer<typeof CheckpointSchema>;

/**
 * Circuit breaker state
 */
export const CircuitBreakerStateSchema = z.object({
  agentId: z.string(),
  failureCount: z.number().default(0),
  lastFailureAt: z.date().optional(),
  state: z.enum(['closed', 'open', 'half_open']).default('closed'),
  nextAttemptAt: z.date().optional(),
});

export type CircuitBreakerState = z.infer<typeof CircuitBreakerStateSchema>;

/**
 * Memory metrics
 */
export const MemoryMetricsSchema = z.object({
  heapUsedMb: z.number(),
  heapTotalMb: z.number(),
  externalMb: z.number(),
  rss: z.number(),
  timestamp: z.date(),
});

export type MemoryMetrics = z.infer<typeof MemoryMetricsSchema>;
