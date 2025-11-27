import { z } from 'zod';

// Severity levels
export const SeveritySchema = z.enum(['critical', 'high', 'medium', 'low', 'info']);
export type Severity = z.infer<typeof SeveritySchema>;

// Category types
export const CategorySchema = z.enum([
  'security',
  'quality',
  'performance',
  'best-practices',
  'accessibility',
  'documentation',
  'testing',
  'architecture',
]);
export type Category = z.infer<typeof CategorySchema>;

// Pattern types
export const PatternTypeSchema = z.enum(['regex', 'ast', 'semgrep']);
export type PatternType = z.infer<typeof PatternTypeSchema>;

// Fix types
export const FixTypeSchema = z.enum(['replace', 'insert', 'delete', 'refactor']);
export type FixType = z.infer<typeof FixTypeSchema>;

// Pattern schemas
export const RegexPatternSchema = z.object({
  regex: z.string(),
  flags: z.string().optional(),
  multiline: z.boolean().optional(),
});

export const ASTPatternSchema = z.object({
  ast: z.string(),
  selector: z.string().optional(),
});

export const SemgrepPatternSchema = z.object({
  pattern: z.string(),
  patterns: z.array(z.string()).optional(),
  pattern_either: z.array(z.string()).optional(),
  pattern_not: z.string().optional(),
});

export const PatternsSchema = z.union([
  RegexPatternSchema,
  ASTPatternSchema,
  SemgrepPatternSchema,
  z.object({
    regex: z.string().optional(),
    ast: z.string().optional(),
    pattern: z.string().optional(),
  }),
]);

// Condition schemas
export const ConditionsSchema = z.object({
  fileMatch: z.array(z.string()).optional(),
  fileExclude: z.array(z.string()).optional(),
  requires: z.array(z.string()).optional(),
  unless: z.array(z.string()).optional(),
  when: z.record(z.any()).optional(),
}).optional();

// Fix schema
export const FixSchema = z.object({
  type: FixTypeSchema,
  template: z.string(),
  confidence: z.number().min(0).max(1).optional(),
  description: z.string().optional(),
}).optional();

// Metadata schemas
export const MetadataSchema = z.object({
  cwe: z.array(z.string()).optional(),
  owasp: z.array(z.string()).optional(),
  references: z.array(z.string()).optional(),
  examples: z.array(z.object({
    code: z.string(),
    vulnerable: z.boolean().optional(),
    description: z.string().optional(),
  })).optional(),
}).optional();

// Main Rule schema
export const RuleSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  severity: SeveritySchema,
  category: CategorySchema,
  tags: z.array(z.string()).optional(),
  languages: z.array(z.string()),
  patterns: PatternsSchema,
  conditions: ConditionsSchema,
  fix: FixSchema,
  metadata: MetadataSchema,
  enabled: z.boolean().optional().default(true),
  // Additional fields
  message: z.string().optional(),
  references: z.array(z.string()).optional(),
  cwe: z.array(z.string()).optional(),
  owasp: z.array(z.string()).optional(),
});

export type Rule = z.infer<typeof RuleSchema>;

// Match result
export interface Match {
  ruleId: string;
  file: string;
  line: number;
  column: number;
  endLine?: number;
  endColumn?: number;
  message: string;
  severity: Severity;
  category: Category;
  snippet: string;
  fix?: {
    type: FixType;
    replacement: string;
    confidence: number;
  };
  metadata?: {
    cwe?: string[];
    owasp?: string[];
    references?: string[];
  };
}

// Engine options
export interface EngineOptions {
  rules: Rule[];
  parallelism?: number;
  timeout?: number;
  cache?: boolean;
  cacheDir?: string;
}

// File to analyze
export interface FileToAnalyze {
  path: string;
  content: string;
  language?: string;
}

// Engine result
export interface EngineResult {
  matches: Match[];
  errors: Array<{
    rule: string;
    file: string;
    error: string;
  }>;
  stats: {
    filesAnalyzed: number;
    rulesExecuted: number;
    matchesFound: number;
    timeMs: number;
  };
}

// Matcher interface
export interface Matcher {
  match(content: string, rule: Rule, file: FileToAnalyze): Match[];
}

// Rule validation result
export interface RuleValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// Export all schemas
export const Schemas = {
  Severity: SeveritySchema,
  Category: CategorySchema,
  PatternType: PatternTypeSchema,
  FixType: FixTypeSchema,
  Rule: RuleSchema,
  Patterns: PatternsSchema,
  Conditions: ConditionsSchema,
  Fix: FixSchema,
  Metadata: MetadataSchema,
};
