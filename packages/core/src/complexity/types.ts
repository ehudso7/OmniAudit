/**
 * Complexity analyzer type definitions
 * @module @omniaudit/core/complexity/types
 */

import { z } from 'zod';

/**
 * Supported programming languages
 */
export enum Language {
  TYPESCRIPT = 'typescript',
  JAVASCRIPT = 'javascript',
  PYTHON = 'python',
  JAVA = 'java',
  GO = 'go',
  RUST = 'rust',
  C = 'c',
  CPP = 'cpp',
  CSHARP = 'csharp',
  PHP = 'php',
  RUBY = 'ruby',
  UNKNOWN = 'unknown',
}

/**
 * Language-specific complexity weights
 */
export const LanguageWeightsSchema = z.object({
  loc: z.number().default(1.0),
  cyclomatic: z.number().default(1.5),
  dependencies: z.number().default(1.0),
  nesting: z.number().default(1.2),
});

export type LanguageWeights = z.infer<typeof LanguageWeightsSchema>;

/**
 * Individual scorer result
 */
export const ScorerResultSchema = z.object({
  name: z.string(),
  score: z.number(),
  weight: z.number(),
  metadata: z.record(z.unknown()).optional(),
});

export type ScorerResult = z.infer<typeof ScorerResultSchema>;

/**
 * Complexity analysis result
 */
export const ComplexityAnalysisSchema = z.object({
  filePath: z.string(),
  language: z.nativeEnum(Language),
  scores: z.array(ScorerResultSchema),
  totalScore: z.number(),
  analyzedAt: z.date(),
  fileSize: z.number(),
});

export type ComplexityAnalysis = z.infer<typeof ComplexityAnalysisSchema>;
