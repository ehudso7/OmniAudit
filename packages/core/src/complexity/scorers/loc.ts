/**
 * Lines of Code (LOC) complexity scorer
 * @module @omniaudit/core/complexity/scorers/loc
 */

import type { ScorerResult } from '../types.js';

/**
 * Calculate complexity based on lines of code
 *
 * Scoring logic:
 * - 0-100 lines: 1 point
 * - 101-300 lines: 2 points
 * - 301-500 lines: 3 points
 * - 501-1000 lines: 5 points
 * - 1001+ lines: 8 points
 *
 * @param content File content
 * @param weight Weight multiplier for this scorer
 * @returns Scorer result with LOC metrics
 */
export function calculateLocScore(content: string, weight = 1.0): ScorerResult {
  // Count non-empty, non-comment lines
  const lines = content.split('\n');
  const codeLines = lines.filter((line) => {
    const trimmed = line.trim();
    // Skip empty lines and simple comment lines
    return (
      trimmed.length > 0 &&
      !trimmed.startsWith('//') &&
      !trimmed.startsWith('#') &&
      !trimmed.startsWith('*') &&
      trimmed !== '/*' &&
      trimmed !== '*/'
    );
  });

  const loc = codeLines.length;

  // Calculate base score based on LOC
  let baseScore: number;
  if (loc <= 100) {
    baseScore = 1;
  } else if (loc <= 300) {
    baseScore = 2;
  } else if (loc <= 500) {
    baseScore = 3;
  } else if (loc <= 1000) {
    baseScore = 5;
  } else {
    baseScore = 8;
  }

  return {
    name: 'loc',
    score: baseScore,
    weight,
    metadata: {
      totalLines: lines.length,
      codeLines: loc,
      emptyLines: lines.length - loc,
    },
  };
}
