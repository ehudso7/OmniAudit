/**
 * Agent lifecycle tests
 */

import { describe, it, expect, vi } from 'vitest';
import { AgentLifecycle, LifecycleStage } from '../agent/lifecycle.js';
import type { WorkItem, AnalysisResult } from '../types/index.js';

describe('AgentLifecycle', () => {
  describe('Initialization', () => {
    it('should start in CREATED stage', () => {
      const lifecycle = new AgentLifecycle('agent-1');
      expect(lifecycle.getStage()).toBe(LifecycleStage.CREATED);
    });

    it('should execute init lifecycle', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      const initFn = vi.fn().mockResolvedValue(undefined);

      await lifecycle.executeInit(initFn);

      expect(initFn).toHaveBeenCalled();
      expect(lifecycle.getStage()).toBe(LifecycleStage.READY);
    });

    it('should call before/after init hooks', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      const beforeHook = vi.fn();
      const afterHook = vi.fn();

      lifecycle.addHook('onBeforeInit', beforeHook);
      lifecycle.addHook('onAfterInit', afterHook);

      await lifecycle.executeInit(async () => {});

      expect(beforeHook).toHaveBeenCalled();
      expect(afterHook).toHaveBeenCalled();
    });

    it('should handle init error', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      const error = new Error('Init failed');
      const initFn = vi.fn().mockRejectedValue(error);
      const errorHook = vi.fn();

      lifecycle.addHook('onError', errorHook);

      await expect(lifecycle.executeInit(initFn)).rejects.toThrow('Init failed');
      expect(lifecycle.getStage()).toBe(LifecycleStage.ERROR);
      expect(errorHook).toHaveBeenCalledWith(error);
    });
  });

  describe('Analysis Lifecycle', () => {
    it('should execute analyze lifecycle', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      await lifecycle.executeInit(async () => {});

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

      const result: AnalysisResult = {
        agentId: 'agent-1',
        workItemId: 'work-1',
        filePath: '/path/to/file.ts',
        findings: [],
        duration: 100,
        success: true,
      };

      const analyzeFn = vi.fn().mockResolvedValue(result);

      const actualResult = await lifecycle.executeAnalyze(workItem, analyzeFn);

      expect(analyzeFn).toHaveBeenCalledWith(workItem);
      expect(actualResult).toEqual(result);
      expect(lifecycle.getStage()).toBe(LifecycleStage.REPORTING);
    });

    it('should call before/after analyze hooks', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      await lifecycle.executeInit(async () => {});

      const beforeHook = vi.fn();
      const afterHook = vi.fn();

      lifecycle.addHook('onBeforeAnalyze', beforeHook);
      lifecycle.addHook('onAfterAnalyze', afterHook);

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

      const result: AnalysisResult = {
        agentId: 'agent-1',
        workItemId: 'work-1',
        filePath: '/path/to/file.ts',
        findings: [],
        duration: 100,
        success: true,
      };

      await lifecycle.executeAnalyze(workItem, async () => result);

      expect(beforeHook).toHaveBeenCalledWith(workItem);
      expect(afterHook).toHaveBeenCalledWith(result);
    });
  });

  describe('Reporting Lifecycle', () => {
    it('should execute report lifecycle', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      await lifecycle.executeInit(async () => {});

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

      const result: AnalysisResult = {
        agentId: 'agent-1',
        workItemId: 'work-1',
        filePath: '/path/to/file.ts',
        findings: [],
        duration: 100,
        success: true,
      };

      await lifecycle.executeAnalyze(workItem, async () => result);

      const reportFn = vi.fn().mockResolvedValue(undefined);
      await lifecycle.executeReport(reportFn);

      expect(reportFn).toHaveBeenCalled();
      expect(lifecycle.getStage()).toBe(LifecycleStage.READY);
    });
  });

  describe('Cleanup Lifecycle', () => {
    it('should execute cleanup lifecycle', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      await lifecycle.executeInit(async () => {});

      const cleanupFn = vi.fn().mockResolvedValue(undefined);
      const beforeHook = vi.fn();
      const afterHook = vi.fn();

      lifecycle.addHook('onBeforeCleanup', beforeHook);
      lifecycle.addHook('onAfterCleanup', afterHook);

      await lifecycle.executeCleanup(cleanupFn);

      expect(beforeHook).toHaveBeenCalled();
      expect(cleanupFn).toHaveBeenCalled();
      expect(afterHook).toHaveBeenCalled();
      expect(lifecycle.getStage()).toBe(LifecycleStage.DISPOSED);
    });
  });

  describe('State Checks', () => {
    it('should check if ready', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      expect(lifecycle.isReady()).toBe(false);

      await lifecycle.executeInit(async () => {});
      expect(lifecycle.isReady()).toBe(true);
    });

    it('should check if disposed', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      expect(lifecycle.isDisposed()).toBe(false);

      await lifecycle.executeInit(async () => {});
      await lifecycle.executeCleanup(async () => {});

      expect(lifecycle.isDisposed()).toBe(true);
    });

    it('should check if has error', async () => {
      const lifecycle = new AgentLifecycle('agent-1');
      expect(lifecycle.hasError()).toBe(false);

      await expect(
        lifecycle.executeInit(async () => {
          throw new Error('Init failed');
        }),
      ).rejects.toThrow();

      expect(lifecycle.hasError()).toBe(true);
    });
  });

  describe('History', () => {
    it('should track lifecycle history', async () => {
      const lifecycle = new AgentLifecycle('agent-1');

      const history1 = lifecycle.getHistory();
      expect(history1).toHaveLength(1);
      expect(history1[0].stage).toBe(LifecycleStage.CREATED);

      await lifecycle.executeInit(async () => {});

      const history2 = lifecycle.getHistory();
      expect(history2.length).toBeGreaterThan(1);

      const stages = history2.map((h) => h.stage);
      expect(stages).toContain(LifecycleStage.INITIALIZING);
      expect(stages).toContain(LifecycleStage.READY);
    });
  });

  describe('Transition Validation', () => {
    it('should allow valid transitions', async () => {
      const lifecycle = new AgentLifecycle('agent-1');

      await lifecycle.executeInit(async () => {});
      expect(lifecycle.getStage()).toBe(LifecycleStage.READY);
    });

    it('should reject invalid transitions', async () => {
      const lifecycle = new AgentLifecycle('agent-1');

      // Can't cleanup before init
      await expect(lifecycle.executeCleanup(async () => {})).rejects.toThrow(
        /Invalid lifecycle transition/,
      );
    });

    it('should allow reset after error', async () => {
      const lifecycle = new AgentLifecycle('agent-1');

      await expect(
        lifecycle.executeInit(async () => {
          throw new Error('Init failed');
        }),
      ).rejects.toThrow();

      expect(lifecycle.getStage()).toBe(LifecycleStage.ERROR);

      lifecycle.reset();
      expect(lifecycle.getStage()).toBe(LifecycleStage.READY);
    });
  });
});
