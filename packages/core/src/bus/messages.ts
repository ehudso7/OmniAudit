/**
 * Message factory functions for creating typed events
 * @module @omniaudit/core/bus/messages
 */

import { randomUUID } from 'node:crypto';
import type {
  FindingEvent,
  ProgressEvent,
  ErrorEvent,
  CompleteEvent,
  StateChangeEvent,
  CheckpointEvent,
  MemoryWarningEvent,
} from './types.js';
import type { Finding, AgentState, AnalysisResult } from '../types/index.js';

/**
 * Create a finding event
 */
export function createFindingEvent(
  agentId: string,
  finding: Finding,
  correlationId?: string,
): FindingEvent {
  return {
    type: 'finding',
    correlationId: correlationId ?? randomUUID(),
    timestamp: new Date(),
    agentId,
    finding,
  };
}

/**
 * Create a progress event
 */
export function createProgressEvent(
  agentId: string,
  progress: number,
  options?: {
    message?: string;
    currentFile?: string;
    correlationId?: string;
  },
): ProgressEvent {
  return {
    type: 'progress',
    correlationId: options?.correlationId ?? randomUUID(),
    timestamp: new Date(),
    agentId,
    progress,
    message: options?.message,
    currentFile: options?.currentFile,
  };
}

/**
 * Create an error event
 */
export function createErrorEvent(
  agentId: string,
  error: Error | string,
  options?: {
    filePath?: string;
    fatal?: boolean;
    correlationId?: string;
  },
): ErrorEvent {
  const errorMessage = typeof error === 'string' ? error : error.message;
  const stack = typeof error === 'string' ? undefined : error.stack;

  return {
    type: 'error',
    correlationId: options?.correlationId ?? randomUUID(),
    timestamp: new Date(),
    agentId,
    error: errorMessage,
    filePath: options?.filePath,
    fatal: options?.fatal ?? false,
    stack,
  };
}

/**
 * Create a complete event
 */
export function createCompleteEvent(
  agentId: string,
  result: AnalysisResult,
  duration: number,
  correlationId?: string,
): CompleteEvent {
  return {
    type: 'complete',
    correlationId: correlationId ?? randomUUID(),
    timestamp: new Date(),
    agentId,
    result,
    duration,
  };
}

/**
 * Create a state change event
 */
export function createStateChangeEvent(
  agentId: string,
  previousState: AgentState,
  newState: AgentState,
  correlationId?: string,
): StateChangeEvent {
  return {
    type: 'state_change',
    correlationId: correlationId ?? randomUUID(),
    timestamp: new Date(),
    agentId,
    previousState,
    newState,
  };
}

/**
 * Create a checkpoint event
 */
export function createCheckpointEvent(
  itemsProcessed: number,
  itemsTotal: number,
  checkpointId?: string,
): CheckpointEvent {
  return {
    type: 'checkpoint',
    timestamp: new Date(),
    itemsProcessed,
    itemsTotal,
    checkpointId: checkpointId ?? randomUUID(),
  };
}

/**
 * Create a memory warning event
 */
export function createMemoryWarningEvent(
  heapUsedMb: number,
  heapTotalMb: number,
  thresholdMb: number,
): MemoryWarningEvent {
  return {
    type: 'memory_warning',
    timestamp: new Date(),
    heapUsedMb,
    heapTotalMb,
    thresholdMb,
  };
}
