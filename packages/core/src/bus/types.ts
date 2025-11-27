/**
 * Event bus type definitions
 * @module @omniaudit/core/bus/types
 */

import { z } from 'zod';
import type { Finding, AgentState, AnalysisResult } from '../types/index.js';

/**
 * Base event schema with correlation ID tracking
 */
export const BaseEventSchema = z.object({
  correlationId: z.string(),
  timestamp: z.date(),
  agentId: z.string(),
});

/**
 * Finding event - emitted when an agent discovers a finding
 */
export const FindingEventSchema = BaseEventSchema.extend({
  type: z.literal('finding'),
  finding: z.any(), // Will be validated with FindingSchema
});

export type FindingEvent = z.infer<typeof FindingEventSchema> & {
  finding: Finding;
};

/**
 * Progress event - emitted to track agent progress
 */
export const ProgressEventSchema = BaseEventSchema.extend({
  type: z.literal('progress'),
  progress: z.number().min(0).max(100),
  message: z.string().optional(),
  currentFile: z.string().optional(),
});

export type ProgressEvent = z.infer<typeof ProgressEventSchema>;

/**
 * Error event - emitted when an agent encounters an error
 */
export const ErrorEventSchema = BaseEventSchema.extend({
  type: z.literal('error'),
  error: z.string(),
  filePath: z.string().optional(),
  fatal: z.boolean().default(false),
  stack: z.string().optional(),
});

export type ErrorEvent = z.infer<typeof ErrorEventSchema>;

/**
 * Complete event - emitted when an agent completes analysis
 */
export const CompleteEventSchema = BaseEventSchema.extend({
  type: z.literal('complete'),
  result: z.any(), // Will be validated with AnalysisResultSchema
  duration: z.number(),
});

export type CompleteEvent = z.infer<typeof CompleteEventSchema> & {
  result: AnalysisResult;
};

/**
 * State change event - emitted when agent state changes
 */
export const StateChangeEventSchema = BaseEventSchema.extend({
  type: z.literal('state_change'),
  previousState: z.any(), // AgentState
  newState: z.any(), // AgentState
});

export type StateChangeEvent = z.infer<typeof StateChangeEventSchema> & {
  previousState: AgentState;
  newState: AgentState;
};

/**
 * Checkpoint event - emitted when checkpoint is saved
 */
export const CheckpointEventSchema = z.object({
  type: z.literal('checkpoint'),
  timestamp: z.date(),
  itemsProcessed: z.number(),
  itemsTotal: z.number(),
  checkpointId: z.string(),
});

export type CheckpointEvent = z.infer<typeof CheckpointEventSchema>;

/**
 * Memory warning event - emitted when memory usage is high
 */
export const MemoryWarningEventSchema = z.object({
  type: z.literal('memory_warning'),
  timestamp: z.date(),
  heapUsedMb: z.number(),
  heapTotalMb: z.number(),
  thresholdMb: z.number(),
});

export type MemoryWarningEvent = z.infer<typeof MemoryWarningEventSchema>;

/**
 * Union type of all events
 */
export type BusEvent =
  | FindingEvent
  | ProgressEvent
  | ErrorEvent
  | CompleteEvent
  | StateChangeEvent
  | CheckpointEvent
  | MemoryWarningEvent;

/**
 * Event type names
 */
export type EventType = BusEvent['type'];

/**
 * Event handler function type
 */
export type EventHandler<T extends BusEvent = BusEvent> = (event: T) => void | Promise<void>;
