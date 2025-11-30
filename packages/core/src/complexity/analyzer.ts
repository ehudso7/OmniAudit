/**
 * File complexity analyzer
 * @module @omniaudit/core/complexity/analyzer
 */

import { readFile } from 'node:fs/promises';
import { extname } from 'node:path';
import type { ComplexityMetrics } from '../types/index.js';
import { Language, type LanguageWeights } from './types.js';
import { calculateLocScore } from './scorers/loc.js';
import { calculateCyclomaticScore } from './scorers/cyclomatic.js';
import { calculateDependencyScore } from './scorers/dependencies.js';

/**
 * Default language weights
 */
const DEFAULT_LANGUAGE_WEIGHTS: Record<Language, LanguageWeights> = {
  [Language.TYPESCRIPT]: { loc: 1.0, cyclomatic: 1.5, dependencies: 1.0, nesting: 1.2 },
  [Language.JAVASCRIPT]: { loc: 1.0, cyclomatic: 1.5, dependencies: 1.0, nesting: 1.2 },
  [Language.PYTHON]: { loc: 1.0, cyclomatic: 1.4, dependencies: 1.1, nesting: 1.3 },
  [Language.JAVA]: { loc: 1.1, cyclomatic: 1.3, dependencies: 1.2, nesting: 1.1 },
  [Language.GO]: { loc: 1.0, cyclomatic: 1.2, dependencies: 1.0, nesting: 1.0 },
  [Language.RUST]: { loc: 1.2, cyclomatic: 1.4, dependencies: 1.1, nesting: 1.2 },
  [Language.C]: { loc: 1.3, cyclomatic: 1.5, dependencies: 0.8, nesting: 1.4 },
  [Language.CPP]: { loc: 1.3, cyclomatic: 1.6, dependencies: 1.0, nesting: 1.4 },
  [Language.CSHARP]: { loc: 1.1, cyclomatic: 1.4, dependencies: 1.1, nesting: 1.2 },
  [Language.PHP]: { loc: 0.9, cyclomatic: 1.3, dependencies: 1.0, nesting: 1.2 },
  [Language.RUBY]: { loc: 0.9, cyclomatic: 1.3, dependencies: 1.1, nesting: 1.2 },
  [Language.UNKNOWN]: { loc: 1.0, cyclomatic: 1.0, dependencies: 1.0, nesting: 1.0 },
};

/**
 * File extension to language mapping
 */
const EXTENSION_TO_LANGUAGE: Record<string, Language> = {
  '.ts': Language.TYPESCRIPT,
  '.tsx': Language.TYPESCRIPT,
  '.js': Language.JAVASCRIPT,
  '.jsx': Language.JAVASCRIPT,
  '.mjs': Language.JAVASCRIPT,
  '.cjs': Language.JAVASCRIPT,
  '.py': Language.PYTHON,
  '.java': Language.JAVA,
  '.go': Language.GO,
  '.rs': Language.RUST,
  '.c': Language.C,
  '.h': Language.C,
  '.cpp': Language.CPP,
  '.cc': Language.CPP,
  '.cxx': Language.CPP,
  '.hpp': Language.CPP,
  '.cs': Language.CSHARP,
  '.php': Language.PHP,
  '.rb': Language.RUBY,
};

/**
 * Detect programming language from file path
 * @param filePath Path to the file
 * @returns Detected language
 */
export function detectLanguage(filePath: string): Language {
  const ext = extname(filePath).toLowerCase();
  return EXTENSION_TO_LANGUAGE[ext] ?? Language.UNKNOWN;
}

/**
 * Calculate nesting depth score
 * @param content File content
 * @returns Nesting depth
 */
function calculateNestingDepth(content: string): number {
  const lines = content.split('\n');
  let maxDepth = 0;
  let currentDepth = 0;

  for (const line of lines) {
    // Count opening braces
    const openBraces = (line.match(/\{/g) || []).length;
    const closeBraces = (line.match(/\}/g) || []).length;

    currentDepth += openBraces - closeBraces;
    maxDepth = Math.max(maxDepth, currentDepth);
  }

  return maxDepth;
}

/**
 * Analyze file complexity
 *
 * Calculates complexity metrics for a file using multiple scorers:
 * - Lines of Code (LOC)
 * - Cyclomatic Complexity
 * - Dependency Count
 * - Nesting Depth
 *
 * Results are weighted based on programming language characteristics.
 *
 * @param filePath Path to the file to analyze
 * @param customWeights Optional custom language weights
 * @returns Complexity metrics for the file
 *
 * @example
 * ```typescript
 * const metrics = await analyzeComplexity('/path/to/file.ts');
 * console.log(`Total complexity score: ${metrics.totalScore}`);
 * ```
 */
export async function analyzeComplexity(
  filePath: string,
  customWeights?: Partial<Record<Language, Partial<LanguageWeights>>>,
): Promise<ComplexityMetrics> {
  // Read file content
  const content = await readFile(filePath, 'utf-8');

  // Detect language
  const language = detectLanguage(filePath);

  // Get language weights
  const baseWeights = DEFAULT_LANGUAGE_WEIGHTS[language];
  const weights = customWeights?.[language]
    ? { ...baseWeights, ...customWeights[language] }
    : baseWeights;

  // Calculate individual scores
  const locScore = calculateLocScore(content, weights.loc);
  const cyclomaticScore = calculateCyclomaticScore(content, weights.cyclomatic);
  const dependencyScore = calculateDependencyScore(content, weights.dependencies);
  const nestingDepth = calculateNestingDepth(content);

  // Calculate weighted total score
  const totalScore =
    locScore.score * locScore.weight +
    cyclomaticScore.score * cyclomaticScore.weight +
    dependencyScore.score * dependencyScore.weight +
    nestingDepth * weights.nesting;

  return {
    filePath,
    linesOfCode: (locScore.metadata?.codeLines as number) ?? 0,
    cyclomaticComplexity: (cyclomaticScore.metadata?.decisionPoints as number) ?? 0,
    dependencyCount: (dependencyScore.metadata?.totalDependencies as number) ?? 0,
    nestingDepth,
    totalScore: Math.round(totalScore * 100) / 100, // Round to 2 decimal places
    language,
  };
}

/**
 * Batch analyze multiple files
 * @param filePaths Array of file paths to analyze
 * @param customWeights Optional custom language weights
 * @returns Array of complexity metrics
 */
export async function analyzeComplexityBatch(
  filePaths: string[],
  customWeights?: Partial<Record<Language, Partial<LanguageWeights>>>,
): Promise<ComplexityMetrics[]> {
  const results = await Promise.allSettled(
    filePaths.map((filePath) => analyzeComplexity(filePath, customWeights)),
  );

  return results
    .filter((result): result is PromiseFulfilledResult<ComplexityMetrics> => result.status === 'fulfilled')
    .map((result) => result.value);
}

/**
 * Sort files by complexity score (descending)
 * @param metrics Array of complexity metrics
 * @returns Sorted array (most complex first)
 */
export function sortByComplexity(metrics: ComplexityMetrics[]): ComplexityMetrics[] {
  return [...metrics].sort((a, b) => b.totalScore - a.totalScore);
}
