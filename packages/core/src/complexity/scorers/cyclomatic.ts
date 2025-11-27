/**
 * Cyclomatic complexity scorer
 * @module @omniaudit/core/complexity/scorers/cyclomatic
 */

import type { ScorerResult } from '../types.js';

/**
 * Calculate cyclomatic complexity score
 *
 * Approximates cyclomatic complexity by counting decision points:
 * - if/else statements
 * - for/while/do loops
 * - case statements
 * - ternary operators
 * - logical operators (&&, ||)
 * - catch blocks
 *
 * Scoring logic:
 * - 1-5 decision points: 1 point
 * - 6-10 decision points: 2 points
 * - 11-20 decision points: 4 points
 * - 21-30 decision points: 6 points
 * - 31+ decision points: 10 points
 *
 * @param content File content
 * @param weight Weight multiplier for this scorer
 * @returns Scorer result with cyclomatic complexity metrics
 */
export function calculateCyclomaticScore(content: string, weight = 1.5): ScorerResult {
  let decisionPoints = 0;

  // Count if/else statements
  const ifMatches = content.match(/\bif\s*\(/g);
  decisionPoints += ifMatches ? ifMatches.length : 0;

  const elseMatches = content.match(/\belse\s+if\s*\(|\belse\b/g);
  decisionPoints += elseMatches ? elseMatches.length : 0;

  // Count loops
  const forMatches = content.match(/\bfor\s*\(/g);
  decisionPoints += forMatches ? forMatches.length : 0;

  const whileMatches = content.match(/\bwhile\s*\(/g);
  decisionPoints += whileMatches ? whileMatches.length : 0;

  const doMatches = content.match(/\bdo\s*\{/g);
  decisionPoints += doMatches ? doMatches.length : 0;

  // Count switch cases
  const caseMatches = content.match(/\bcase\s+/g);
  decisionPoints += caseMatches ? caseMatches.length : 0;

  // Count ternary operators
  const ternaryMatches = content.match(/\?[^?]*:/g);
  decisionPoints += ternaryMatches ? ternaryMatches.length : 0;

  // Count logical operators (as they create branches)
  const andMatches = content.match(/&&/g);
  decisionPoints += andMatches ? andMatches.length : 0;

  const orMatches = content.match(/\|\|/g);
  decisionPoints += orMatches ? orMatches.length : 0;

  // Count catch blocks
  const catchMatches = content.match(/\bcatch\s*\(/g);
  decisionPoints += catchMatches ? catchMatches.length : 0;

  // Calculate base score
  let baseScore: number;
  if (decisionPoints <= 5) {
    baseScore = 1;
  } else if (decisionPoints <= 10) {
    baseScore = 2;
  } else if (decisionPoints <= 20) {
    baseScore = 4;
  } else if (decisionPoints <= 30) {
    baseScore = 6;
  } else {
    baseScore = 10;
  }

  return {
    name: 'cyclomatic',
    score: baseScore,
    weight,
    metadata: {
      decisionPoints,
      ifStatements: (ifMatches?.length ?? 0) + (elseMatches?.length ?? 0),
      loops: (forMatches?.length ?? 0) + (whileMatches?.length ?? 0) + (doMatches?.length ?? 0),
      switches: caseMatches?.length ?? 0,
      ternaries: ternaryMatches?.length ?? 0,
    },
  };
}
