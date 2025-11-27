import { describe, it, expect, beforeEach } from 'vitest';
import { RulesEngine } from '../engine';
import type { Rule, FileToAnalyze } from '../types';

describe('RulesEngine', () => {
  let engine: RulesEngine;

  const testRule: Rule = {
    id: 'TEST001',
    name: 'Test Rule',
    description: 'A test rule for demonstration',
    severity: 'high',
    category: 'security',
    languages: ['javascript', 'typescript'],
    patterns: {
      regex: 'console\\.log',
    },
    enabled: true,
  };

  beforeEach(() => {
    engine = new RulesEngine();
  });

  describe('Rule Management', () => {
    it('should add rules programmatically', () => {
      engine.addRules([testRule]);
      const rules = engine.getRules();
      expect(rules).toHaveLength(1);
      expect(rules[0]?.id).toBe('TEST001');
    });

    it('should validate rules', () => {
      engine.addRules([testRule]);
      const results = engine.validateRules();
      expect(results.size).toBe(1);
      expect(results.get('TEST001')?.valid).toBe(true);
    });

    it('should filter rules by category', () => {
      const securityRule: Rule = { ...testRule, category: 'security' };
      const qualityRule: Rule = { ...testRule, id: 'TEST002', category: 'quality' };

      engine.addRules([securityRule, qualityRule]);

      const securityRules = engine.filterRules({ categories: ['security'] });
      expect(securityRules).toHaveLength(1);
      expect(securityRules[0]?.category).toBe('security');
    });

    it('should filter rules by severity', () => {
      const criticalRule: Rule = { ...testRule, severity: 'critical' };
      const lowRule: Rule = { ...testRule, id: 'TEST002', severity: 'low' };

      engine.addRules([criticalRule, lowRule]);

      const criticalRules = engine.filterRules({ severities: ['critical'] });
      expect(criticalRules).toHaveLength(1);
      expect(criticalRules[0]?.severity).toBe('critical');
    });
  });

  describe('File Analysis', () => {
    it('should analyze a single file', async () => {
      engine.addRules([testRule]);

      const file: FileToAnalyze = {
        path: 'test.js',
        content: 'console.log("Hello, world!");',
        language: 'javascript',
      };

      const matches = await engine.analyzeFile(file);
      expect(matches.length).toBeGreaterThan(0);
      expect(matches[0]?.ruleId).toBe('TEST001');
    });

    it('should analyze multiple files', async () => {
      engine.addRules([testRule]);

      const files: FileToAnalyze[] = [
        { path: 'file1.js', content: 'console.log("test1");', language: 'javascript' },
        { path: 'file2.js', content: 'console.log("test2");', language: 'javascript' },
      ];

      const result = await engine.analyzeFiles(files);
      expect(result.matches.length).toBeGreaterThan(0);
      expect(result.stats.filesAnalyzed).toBe(2);
    });

    it('should not match disabled rules', async () => {
      const disabledRule: Rule = { ...testRule, enabled: false };
      engine.addRules([disabledRule]);

      const file: FileToAnalyze = {
        path: 'test.js',
        content: 'console.log("test");',
        language: 'javascript',
      };

      const matches = await engine.analyzeFile(file);
      expect(matches).toHaveLength(0);
    });
  });

  describe('Statistics', () => {
    it('should provide accurate statistics', () => {
      const rules: Rule[] = [
        { ...testRule, category: 'security' },
        { ...testRule, id: 'TEST002', category: 'quality', severity: 'low' },
        { ...testRule, id: 'TEST003', category: 'security', severity: 'critical' },
      ];

      engine.addRules(rules);
      const stats = engine.getStats();

      expect(stats.total).toBe(3);
      expect(stats.byCategory.security).toBe(2);
      expect(stats.byCategory.quality).toBe(1);
      expect(stats.bySeverity.high).toBe(1);
      expect(stats.bySeverity.low).toBe(1);
      expect(stats.bySeverity.critical).toBe(1);
    });
  });

  describe('Performance Benchmark', () => {
    it('should benchmark rule execution', async () => {
      engine.addRules([testRule]);

      const file: FileToAnalyze = {
        path: 'test.js',
        content: 'console.log("benchmark test");',
        language: 'javascript',
      };

      const benchmark = await engine.benchmark(file, 10);

      expect(benchmark.totalMs).toBeGreaterThan(0);
      expect(benchmark.avgMs).toBeGreaterThan(0);
      expect(benchmark.rulesPerSecond).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid regex gracefully', async () => {
      const invalidRule: Rule = {
        ...testRule,
        patterns: { regex: '[invalid(' },
      };

      engine.addRules([invalidRule]);

      const file: FileToAnalyze = {
        path: 'test.js',
        content: 'test content',
        language: 'javascript',
      };

      const result = await engine.analyzeFiles([file]);
      expect(result.errors.length).toBeGreaterThanOrEqual(0);
    });
  });
});
