import type { Rule, RuleValidationResult } from './types';
import { RuleSchema } from './types';

/**
 * RuleValidator - Validates rules for correctness and best practices
 */
export class RuleValidator {
  /**
   * Validate a single rule
   */
  validate(rule: any): RuleValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Schema validation
    try {
      RuleSchema.parse(rule);
    } catch (error: any) {
      if (error.errors) {
        for (const err of error.errors) {
          errors.push(`${err.path.join('.')}: ${err.message}`);
        }
      } else {
        errors.push(error.message);
      }
    }

    // If schema validation failed, return early
    if (errors.length > 0) {
      return { valid: false, errors, warnings };
    }

    // Additional validation checks
    this.validatePatterns(rule, errors, warnings);
    this.validateConditions(rule, errors, warnings);
    this.validateMetadata(rule, errors, warnings);
    this.validateFix(rule, errors, warnings);
    this.validateBestPractices(rule, errors, warnings);

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Validate patterns
   */
  private validatePatterns(rule: Rule, errors: string[], warnings: string[]): void {
    const patterns = rule.patterns as any;

    // Check if at least one pattern type is defined
    if (!patterns.regex && !patterns.ast && !patterns.pattern) {
      errors.push('Rule must have at least one pattern (regex, ast, or pattern)');
    }

    // Validate regex pattern
    if (patterns.regex) {
      try {
        new RegExp(patterns.regex, patterns.flags);
      } catch (error: any) {
        errors.push(`Invalid regex pattern: ${error.message}`);
      }

      // Check for overly broad patterns
      if (patterns.regex === '.*' || patterns.regex === '.+') {
        warnings.push('Regex pattern is too broad and may cause false positives');
      }
    }

    // Validate AST pattern
    if (patterns.ast) {
      const validSelectors = [
        'CallExpression',
        'FunctionDeclaration',
        'VariableDeclaration',
        'MemberExpression',
        'JSXAttribute',
        'console.log',
        'eval',
        'dangerouslySetInnerHTML',
      ];

      if (!validSelectors.some(s => patterns.ast.includes(s))) {
        warnings.push('AST pattern may not match known selectors');
      }
    }
  }

  /**
   * Validate conditions
   */
  private validateConditions(rule: Rule, errors: string[], warnings: string[]): void {
    if (!rule.conditions) return;

    // Check for conflicting file patterns
    if (rule.conditions.fileMatch && rule.conditions.fileExclude) {
      const hasOverlap = rule.conditions.fileMatch.some(pattern =>
        rule.conditions?.fileExclude?.includes(pattern)
      );
      if (hasOverlap) {
        warnings.push('fileMatch and fileExclude have overlapping patterns');
      }
    }

    // Validate glob patterns
    const allPatterns = [
      ...(rule.conditions.fileMatch || []),
      ...(rule.conditions.fileExclude || []),
    ];

    for (const pattern of allPatterns) {
      if (!pattern.includes('*') && !pattern.includes('/')) {
        warnings.push(`Pattern "${pattern}" may be too specific`);
      }
    }
  }

  /**
   * Validate metadata
   */
  private validateMetadata(rule: Rule, errors: string[], warnings: string[]): void {
    // Check CWE format
    if (rule.cwe) {
      for (const cwe of rule.cwe) {
        if (!cwe.startsWith('CWE-')) {
          errors.push(`Invalid CWE format: ${cwe}. Should be CWE-XXX`);
        }
      }
    }

    // Check OWASP format
    if (rule.owasp) {
      for (const owasp of rule.owasp) {
        if (!owasp.match(/^A\d{2}_\d{4}/)) {
          warnings.push(`OWASP format may be incorrect: ${owasp}`);
        }
      }
    }

    // Check references
    if (rule.references) {
      for (const ref of rule.references) {
        try {
          new URL(ref);
        } catch {
          warnings.push(`Invalid reference URL: ${ref}`);
        }
      }
    }

    // Security rules should have CWE or OWASP
    if (rule.category === 'security' && !rule.cwe && !rule.owasp) {
      warnings.push('Security rules should include CWE or OWASP references');
    }
  }

  /**
   * Validate fix
   */
  private validateFix(rule: Rule, errors: string[], warnings: string[]): void {
    if (!rule.fix) return;

    // Check confidence range
    if (rule.fix.confidence !== undefined) {
      if (rule.fix.confidence < 0 || rule.fix.confidence > 1) {
        errors.push('Fix confidence must be between 0 and 1');
      }

      // Warn about low confidence auto-fixes
      if (rule.fix.confidence < 0.5) {
        warnings.push('Fix has low confidence (<0.5), consider manual review');
      }
    }

    // Check template validity
    if (!rule.fix.template) {
      errors.push('Fix must have a template');
    }
  }

  /**
   * Validate best practices
   */
  private validateBestPractices(rule: Rule, errors: string[], warnings: string[]): void {
    // Check ID format
    if (!rule.id.match(/^[A-Z]{3}\d{3,4}$/)) {
      warnings.push('Rule ID should follow format: ABC001 (3 letters + 3-4 digits)');
    }

    // Check name length
    if (rule.name.length > 80) {
      warnings.push('Rule name is too long (>80 characters)');
    }

    // Check description length
    if (rule.description.length < 20) {
      warnings.push('Rule description is too short (<20 characters)');
    }

    if (rule.description.length > 500) {
      warnings.push('Rule description is too long (>500 characters)');
    }

    // Check tags
    if (!rule.tags || rule.tags.length === 0) {
      warnings.push('Rule should have at least one tag');
    }

    // Critical rules should have references
    if (rule.severity === 'critical' && (!rule.references || rule.references.length === 0)) {
      warnings.push('Critical rules should include references');
    }

    // Check language support
    if (rule.languages.length === 0) {
      errors.push('Rule must support at least one language');
    }

    // Warn about universal language support
    if (rule.languages.includes('*') && rule.languages.length > 1) {
      warnings.push('Use "*" alone for universal language support');
    }
  }

  /**
   * Validate multiple rules
   */
  validateBatch(rules: any[]): Map<string, RuleValidationResult> {
    const results = new Map<string, RuleValidationResult>();

    for (const rule of rules) {
      const result = this.validate(rule);
      results.set(rule.id || 'unknown', result);
    }

    // Check for duplicate IDs
    const ids = new Set<string>();
    for (const rule of rules) {
      if (rule.id) {
        if (ids.has(rule.id)) {
          const existing = results.get(rule.id);
          if (existing) {
            existing.errors.push('Duplicate rule ID');
          }
        }
        ids.add(rule.id);
      }
    }

    return results;
  }

  /**
   * Get summary of validation results
   */
  getSummary(results: Map<string, RuleValidationResult>): {
    total: number;
    valid: number;
    invalid: number;
    warnings: number;
  } {
    let valid = 0;
    let invalid = 0;
    let warnings = 0;

    for (const result of results.values()) {
      if (result.valid) {
        valid++;
      } else {
        invalid++;
      }
      warnings += result.warnings.length;
    }

    return {
      total: results.size,
      valid,
      invalid,
      warnings,
    };
  }
}

export const ruleValidator = new RuleValidator();
