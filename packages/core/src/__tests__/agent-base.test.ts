/**
 * Base agent tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseAgent, AgentError } from '../agent/base.js';
import { EventBus } from '../bus/event-bus.js';
import type { WorkItem, Finding, AgentContext } from '../types/index.js';
import { AgentStatus, FindingSeverity } from '../types/index.js';

class TestAgent extends BaseAgent {
  public analyzeCallCount = 0;

  protected async doAnalyze(workItem: WorkItem): Promise<Finding[]> {
    this.analyzeCallCount++;
    this.updateProgress(50, 'Analyzing...');
    return [
      {
        id: 'finding-1',
        severity: FindingSeverity.MEDIUM,
        category: 'test',
        message: 'Test finding',
        filePath: workItem.filePath,
      },
    ];
  }
}

class FailingAgent extends BaseAgent {
  protected async doAnalyze(_workItem: WorkItem): Promise<Finding[]> {
    throw new Error('Analysis failed');
  }
}

describe('BaseAgent', () => {
  let eventBus: EventBus;
  let context: AgentContext;

  beforeEach(() => {
    eventBus = new EventBus();
    context = {
      id: 'agent-1',
      eventBus,
      config: {
        maxRetries: 3,
        retryBackoffMs: 100,
        maxRetryBackoffMs: 1000,
        timeoutMs: 5000,
        circuitBreakerThreshold: 5,
        circuitBreakerResetMs: 1000,
      },
      correlationId: 'test-correlation',
    };
  });

  describe('Initialization', () => {
    it('should initialize agent', async () => {
      const agent = new TestAgent(context);
      expect(agent.id).toBe('agent-1');

      await agent.init();

      expect(agent.isAvailable()).toBe(true);
      expect(agent.getStatus()).toBe(AgentStatus.IDLE);
    });

    it('should emit state change events', async () => {
      const agent = new TestAgent(context);
      const stateChanges: any[] = [];

      eventBus.on('state_change', (event) => {
        stateChanges.push(event);
      });

      await agent.init();

      expect(stateChanges.length).toBeGreaterThan(0);
    });
  });

  describe('Analysis', () => {
    it('should analyze work item', async () => {
      const agent = new TestAgent(context);
      await agent.init();

      const workItem: WorkItem = {
        id: 'work-1',
        filePath: '/path/to/file.ts',
        complexity: {
          filePath: '/path/to/file.ts',
          linesOfCode: 100,
          cyclomaticComplexity: 5,
          dependencyCount: 3,
          totalScore: 10,
          language: 'typescript',
        },
        status: 'pending',
        retryCount: 0,
      };

      const result = await agent.analyze(workItem);

      expect(result.success).toBe(true);
      expect(result.findings).toHaveLength(1);
      expect(result.agentId).toBe('agent-1');
      expect(result.workItemId).toBe('work-1');
      expect(result.filePath).toBe('/path/to/file.ts');
    });

    it('should emit progress events', async () => {
      const agent = new TestAgent(context);
      await agent.init();

      const progressEvents: any[] = [];
      eventBus.on('progress', (event) => {
        progressEvents.push(event);
      });

      const workItem: WorkItem = {
        id: 'work-1',
        filePath: '/path/to/file.ts',
        complexity: {
          filePath: '/path/to/file.ts',
          linesOfCode: 100,
          cyclomaticComplexity: 5,
          dependencyCount: 3,
          totalScore: 10,
          language: 'typescript',
        },
        status: 'pending',
        retryCount: 0,
      };

      await agent.analyze(workItem);

      expect(progressEvents.length).toBeGreaterThan(0);
      expect(progressEvents[0].progress).toBe(50);
    });

    it('should handle analysis errors', async () => {
      const agent = new FailingAgent(context);
      await agent.init();

      const errorEvents: any[] = [];
      eventBus.on('error', (event) => {
        errorEvents.push(event);
      });

      const workItem: WorkItem = {
        id: 'work-1',
        filePath: '/path/to/file.ts',
        complexity: {
          filePath: '/path/to/file.ts',
          linesOfCode: 100,
          cyclomaticComplexity: 5,
          dependencyCount: 3,
          totalScore: 10,
          language: 'typescript',
        },
        status: 'pending',
        retryCount: 0,
      };

      const result = await agent.analyze(workItem);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Analysis failed');
      expect(errorEvents.length).toBeGreaterThan(0);
    });

    it('should retry on failure', async () => {
      let attemptCount = 0;

      class RetryAgent extends BaseAgent {
        protected async doAnalyze(_workItem: WorkItem): Promise<Finding[]> {
          attemptCount++;
          if (attemptCount < 2) {
            throw new Error('Temporary failure');
          }
          return [];
        }
      }

      const agent = new RetryAgent(context);
      await agent.init();

      const workItem: WorkItem = {
        id: 'work-1',
        filePath: '/path/to/file.ts',
        complexity: {
          filePath: '/path/to/file.ts',
          linesOfCode: 100,
          cyclomaticComplexity: 5,
          dependencyCount: 3,
          totalScore: 10,
          language: 'typescript',
        },
        status: 'pending',
        retryCount: 0,
      };

      const result = await agent.analyze(workItem);

      expect(result.success).toBe(true);
      expect(attemptCount).toBe(2);
    });
  });

  describe('Reporting', () => {
    it('should report analysis results', async () => {
      const agent = new TestAgent(context);
      await agent.init();

      const workItem: WorkItem = {
        id: 'work-1',
        filePath: '/path/to/file.ts',
        complexity: {
          filePath: '/path/to/file.ts',
          linesOfCode: 100,
          cyclomaticComplexity: 5,
          dependencyCount: 3,
          totalScore: 10,
          language: 'typescript',
        },
        status: 'pending',
        retryCount: 0,
      };

      const completeEvents: any[] = [];
      eventBus.on('complete', (event) => {
        completeEvents.push(event);
      });

      // Analyze first (which transitions to REPORTING)
      const result = await agent.analyze(workItem);

      // Then report (already in REPORTING state)
      await agent.report(result);

      expect(completeEvents).toHaveLength(1);
      expect(completeEvents[0].result).toEqual(result);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup agent', async () => {
      const agent = new TestAgent(context);
      await agent.init();

      await agent.cleanup();

      expect(agent.getStatus()).toBe(AgentStatus.IDLE);
    });
  });

  describe('State Management', () => {
    it('should track agent state', async () => {
      const agent = new TestAgent(context);

      const state1 = agent.getState();
      expect(state1.status).toBe(AgentStatus.IDLE);
      expect(state1.progress).toBe(0);

      await agent.init();

      const state2 = agent.getState();
      expect(state2.status).toBe(AgentStatus.IDLE);
    });

    it('should check availability', async () => {
      const agent = new TestAgent(context);
      expect(agent.isAvailable()).toBe(false);

      await agent.init();
      expect(agent.isAvailable()).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should create AgentError', () => {
      const error = new AgentError('Test error', 'agent-1', true);

      expect(error.message).toBe('Test error');
      expect(error.agentId).toBe('agent-1');
      expect(error.fatal).toBe(true);
      expect(error.name).toBe('AgentError');
    });

    it('should wrap cause error', () => {
      const cause = new Error('Original error');
      const error = new AgentError('Wrapped error', 'agent-1', false, cause);

      expect(error.cause).toBe(cause);
    });
  });
});
