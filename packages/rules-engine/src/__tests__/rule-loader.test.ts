import { describe, it, expect, beforeEach } from 'vitest';
import { RuleLoader } from '../rule-loader';
import type { Rule } from '../types';

describe('RuleLoader', () => {
  let loader: RuleLoader;

  beforeEach(() => {
    loader = new RuleLoader();
  });

  describe('Rule Filtering', () => {
    const testRules: Rule[] = [
      {
        id: 'SEC001',
        name: 'Security Rule 1',
        description: 'Test',
        severity: 'critical',
        category: 'security',
        languages: ['javascript'],
        patterns: { regex: 'test' },
        tags: ['secrets'],
        enabled: true,
      },
      {
        id: 'QUA001',
        name: 'Quality Rule 1',
        description: 'Test',
        severity: 'low',
        category: 'quality',
        languages: ['typescript'],
        patterns: { regex: 'test' },
        tags: ['complexity'],
        enabled: true,
      },
      {
        id: 'SEC002',
        name: 'Security Rule 2',
        description: 'Test',
        severity: 'high',
        category: 'security',
        languages: ['python'],
        patterns: { regex: 'test' },
        enabled: false,
      },
    ];

    beforeEach(() => {
      for (const rule of testRules) {
        loader['loadedRules'].set(rule.id, rule);
      }
    });

    it('should filter by category', () => {
      const rules = loader.filterRules({ categories: ['security'] });
      expect(rules).toHaveLength(2);
      expect(rules.every(r => r.category === 'security')).toBe(true);
    });

    it('should filter by severity', () => {
      const rules = loader.filterRules({ severities: ['critical', 'high'] });
      expect(rules).toHaveLength(2);
    });

    it('should filter by language', () => {
      const rules = loader.filterRules({ languages: ['javascript'] });
      expect(rules).toHaveLength(1);
      expect(rules[0]?.id).toBe('SEC001');
    });

    it('should filter by tags', () => {
      const rules = loader.filterRules({ tags: ['secrets'] });
      expect(rules).toHaveLength(1);
      expect(rules[0]?.tags).toContain('secrets');
    });

    it('should filter by enabled status', () => {
      const rules = loader.filterRules({ enabled: true });
      expect(rules).toHaveLength(2);
      expect(rules.every(r => r.enabled === true)).toBe(true);
    });

    it('should combine multiple filters', () => {
      const rules = loader.filterRules({
        categories: ['security'],
        enabled: true,
      });
      expect(rules).toHaveLength(1);
      expect(rules[0]?.id).toBe('SEC001');
    });
  });

  describe('File Matching', () => {
    const rule: Rule = {
      id: 'TEST001',
      name: 'Test',
      description: 'Test',
      severity: 'medium',
      category: 'security',
      languages: ['javascript'],
      patterns: { regex: 'test' },
      conditions: {
        fileMatch: ['**/*.js'],
        fileExclude: ['**/*.test.js'],
      },
      enabled: true,
    };

    beforeEach(() => {
      loader['loadedRules'].set(rule.id, rule);
    });

    it('should match files with fileMatch pattern', () => {
      expect(loader.fileMatchesConditions('src/app.js', rule)).toBe(true);
    });

    it('should exclude files with fileExclude pattern', () => {
      expect(loader.fileMatchesConditions('src/app.test.js', rule)).toBe(false);
    });

    it('should match all files when no conditions', () => {
      const noCondRule = { ...rule, conditions: undefined };
      expect(loader.fileMatchesConditions('any-file.ts', noCondRule)).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should provide accurate statistics', () => {
      const rules: Rule[] = [
        {
          id: 'SEC001',
          name: 'Sec 1',
          description: 'Test',
          severity: 'critical',
          category: 'security',
          languages: ['javascript', 'typescript'],
          patterns: { regex: 'test' },
          enabled: true,
        },
        {
          id: 'QUA001',
          name: 'Qua 1',
          description: 'Test',
          severity: 'low',
          category: 'quality',
          languages: ['javascript'],
          patterns: { regex: 'test' },
          enabled: true,
        },
      ];

      for (const rule of rules) {
        loader['loadedRules'].set(rule.id, rule);
      }

      const stats = loader.getStats();

      expect(stats.total).toBe(2);
      expect(stats.byCategory.security).toBe(1);
      expect(stats.byCategory.quality).toBe(1);
      expect(stats.bySeverity.critical).toBe(1);
      expect(stats.bySeverity.low).toBe(1);
      expect(stats.byLanguage.javascript).toBe(2);
      expect(stats.byLanguage.typescript).toBe(1);
    });
  });
});
