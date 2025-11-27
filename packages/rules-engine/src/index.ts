// Main exports
export { RulesEngine, createEngine } from './engine';
export { RuleLoader, ruleLoader } from './rule-loader';
export { RuleValidator, ruleValidator } from './rule-validator';

// Matchers
export { RegexMatcher, regexMatcher } from './matchers/regex-matcher';
export { ASTMatcher, astMatcher } from './matchers/ast-matcher';
export { PatternMatcher, patternMatcher } from './matchers/pattern-matcher';

// Types and schemas
export * from './types';
export type {
  Rule,
  Match,
  EngineOptions,
  EngineResult,
  FileToAnalyze,
  Matcher,
  RuleValidationResult,
  Severity,
  Category,
  PatternType,
  FixType,
} from './types';

// Re-export schemas for runtime validation
export {
  RuleSchema,
  SeveritySchema,
  CategorySchema,
  PatternTypeSchema,
  FixTypeSchema,
  Schemas,
} from './types';
