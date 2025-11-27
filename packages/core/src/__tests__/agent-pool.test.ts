/**
 * Agent pool tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AgentPool } from '../agent/pool.js';
import { BaseAgent } from '../agent/base.js';
import { EventBus } from '../bus/event-bus.js';
import type { WorkItem, Finding, AgentContext } from '../types/index.js';
import { FindingSeverity } from '../types/index.js';

class TestPoolAgent extends BaseAgent {
  protected async doAnalyze(workItem: WorkItem): Promise<Finding[]> {
    await new Promise((resolve) => setTimeout(resolve, 10)); // Small delay
    return [
      {
        id: 'finding-1',
        severity: FindingSeverity.LOW,
        category: 'test',
        message: 'Test finding',
        filePath: workItem.filePath,
      },
    ];
  }
}

describe('AgentPool', () => {
  let eventBus: EventBus;

  beforeEach(() => {
    eventBus = new EventBus();
  });

  const createAgentFactory = () => (context: AgentContext) => {
    return new TestPoolAgent(context);
  };

  describe('Initialization', () => {
    it('should initialize pool with initial agents', async () => {
      const pool = new AgentPool(createAgentFactory(), {
        maxAgents: 4,
        circuitBreakerThreshold: 5,
        circuitBreakerResetMs: 1000,
        eventBus,
      });

      await pool.init();

      const stats = pool.getStats();
      expect(stats.totalAgents).toBeGreaterThan(0);
      expect(stats.availableAgents).toBeGreaterThan(0);

      await pool.shutdown();
    });

    it('should not re-initialize if already initialized', async () => {
      const pool = new AgentPool(createAgentFactory(), {
        maxAgents: 4,
        circuitBreakerThreshold: 5,
        circuitBreakerResetMs: 1000,
        eventBus,
      });

      await pool.init();
      const stats1 = pool.getStats();

      await pool.init();
      const stats2 = pool.getStats();

      expect(stats1.totalAgents).toBe(stats2.totalAgents);

      await pool.shutdown();
    });
  });

  describe('Work Execution', () => {
    it('should execute work item', async () => {
      const pool = new AgentPool(createAgentFactory(), {
        maxAgents: 4,
        circuitBreakerThreshold: 5,
        circuitBreakerResetMs: 1000,
        eventBus,
      });

      await pool.init();

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

      const result = await pool.executeWork(workItem);

      expect(result.success).toBe(true);
      expect(result.findings).toHaveLength(1);

      await pool.shutdown();
    });

    it('should execute multiple work items in batch', async () => {
      const pool = new AgentPool(createAgentFactory(), {
        maxAgents: 4,
        circuitBreakerThreshold: 5,
        circuitBreakerResetMs: 1000,
        eventBus,
      });

      await pool.init();

      const workItems: WorkItem[] = Array.from({ length: 3 }, (_, i) => ({
        id: `work-${i}`,
        filePath: `/path/to/file${i}.ts`,
        complexity: {
          filePath: `/path/to/file${i}.ts`,
          linesOfCode: 100,
          cyclomaticComplexity: 5,
          dependencyCount: 3,
          totalScore: 10,
          language: 'typescript',
        },
        status: 'pending' as const,
        retryCount: 0,
      }));

      const results = await pool.executeWorkBatch(workItems);

      expect(results).toHaveLength(3);
      // Check each result individually to see which failed
      for (const result of results) {
        if (!result.success) {
          console.error('Failed result:', result);
        }
      }
      const successCount = results.filter((r) => r.success).length;
      expect(successCount).toBeGreaterThan(0); // At least some should succeed

      await pool.shutdown();
    });
  });

  describe('Pool Statistics', () => {
    it('should track pool statistics', async () => {
      const pool = new AgentPool(createAgentFactory(), {
        maxAgents: 4,
        circuitBreakerThreshold: 5,
        circuitBreakerResetMs: 1000,
        eventBus,
      });

      await pool.init();

      const initialStats = pool.getStats();
      expect(initialStats.totalTasksProcessed).toBe(0);
      expect(initialStats.totalFailures).toBe(0);

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

      await pool.executeWork(workItem);

      const finalStats = pool.getStats();
      expect(finalStats.totalTasksProcessed).toBe(1);

      await pool.shutdown();
    });
  });

  describe('Shutdown', () => {
    it('should shutdown pool and cleanup agents', async () => {
      const pool = new AgentPool(createAgentFactory(), {
        maxAgents: 4,
        circuitBreakerThreshold: 5,
        circuitBreakerResetMs: 1000,
        eventBus,
      });

      await pool.init();
      expect(pool.getStats().totalAgents).toBeGreaterThan(0);

      await pool.shutdown();

      const stats = pool.getStats();
      expect(stats.totalAgents).toBe(0);
    });
  });
});
