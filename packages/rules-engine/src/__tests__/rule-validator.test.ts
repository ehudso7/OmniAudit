import { describe, it, expect } from 'vitest';
import { RuleValidator } from '../rule-validator';
import type { Rule } from '../types';

describe('RuleValidator', () => {
  const validator = new RuleValidator();

  const validRule: Rule = {
    id: 'SEC001',
    name: 'Test Rule',
    description: 'A valid test rule for validation',
    severity: 'high',
    category: 'security',
    languages: ['javascript', 'typescript'],
    patterns: { regex: 'test' },
    cwe: ['CWE-798'],
    enabled: true,
  };

  describe('Schema Validation', () => {
    it('should validate a correct rule', () => {
      const result = validator.validate(validRule);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject rule without ID', () => {
      const invalidRule = { ...validRule, id: undefined };
      const result = validator.validate(invalidRule);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should reject rule without patterns', () => {
      const invalidRule = { ...validRule, patterns: {} };
      const result = validator.validate(invalidRule);
      expect(result.valid).toBe(false);
    });

    it('should reject invalid severity', () => {
      const invalidRule = { ...validRule, severity: 'super-critical' };
      const result = validator.validate(invalidRule);
      expect(result.valid).toBe(false);
    });
  });

  describe('Pattern Validation', () => {
    it('should validate regex patterns', () => {
      const rule = { ...validRule, patterns: { regex: 'valid.*pattern' } };
      const result = validator.validate(rule);
      expect(result.valid).toBe(true);
    });

    it('should reject invalid regex', () => {
      const rule = { ...validRule, patterns: { regex: '[invalid(' } };
      const result = validator.validate(rule);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('regex'))).toBe(true);
    });

    it('should warn about overly broad patterns', () => {
      const rule = { ...validRule, patterns: { regex: '.*' } };
      const result = validator.validate(rule);
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('Metadata Validation', () => {
    it('should validate CWE format', () => {
      const rule = { ...validRule, cwe: ['CWE-123'] };
      const result = validator.validate(rule);
      expect(result.valid).toBe(true);
    });

    it('should reject invalid CWE format', () => {
      const rule = { ...validRule, cwe: ['123'] };
      const result = validator.validate(rule);
      expect(result.valid).toBe(false);
    });

    it('should validate reference URLs', () => {
      const rule = { ...validRule, references: ['https://example.com'] };
      const result = validator.validate(rule);
      expect(result.valid).toBe(true);
    });

    it('should warn about invalid URLs', () => {
      const rule = { ...validRule, references: ['not-a-url'] };
      const result = validator.validate(rule);
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('Best Practices', () => {
    it('should warn about short descriptions', () => {
      const rule = { ...validRule, description: 'Short' };
      const result = validator.validate(rule);
      expect(result.warnings.some(w => w.includes('description'))).toBe(true);
    });

    it('should warn about non-standard ID format', () => {
      const rule = { ...validRule, id: 'test-123' };
      const result = validator.validate(rule);
      expect(result.warnings.some(w => w.includes('ID'))).toBe(true);
    });

    it('should warn if critical rule lacks references', () => {
      const rule = { ...validRule, severity: 'critical', references: undefined };
      const result = validator.validate(rule);
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('Batch Validation', () => {
    it('should validate multiple rules', () => {
      const rules = [
        validRule,
        { ...validRule, id: 'SEC002' },
        { ...validRule, id: 'QUA001', category: 'quality' },
      ];

      const results = validator.validateBatch(rules);
      expect(results.size).toBe(3);
    });

    it('should detect duplicate IDs', () => {
      const rules = [validRule, validRule];
      const results = validator.validateBatch(rules);
      const sec001Result = results.get('SEC001');
      expect(sec001Result?.errors.some(e => e.includes('Duplicate'))).toBe(true);
    });

    it('should provide summary', () => {
      const rules = [
        validRule,
        { ...validRule, id: 'SEC002' },
        { ...validRule, id: 'INVALID', patterns: {} },
      ];

      const results = validator.validateBatch(rules);
      const summary = validator.getSummary(results);

      expect(summary.total).toBe(3);
      expect(summary.valid).toBe(2);
      expect(summary.invalid).toBe(1);
    });
  });
});
