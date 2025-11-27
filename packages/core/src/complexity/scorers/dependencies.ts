/**
 * Dependency count complexity scorer
 * @module @omniaudit/core/complexity/scorers/dependencies
 */

import type { ScorerResult } from '../types.js';

/**
 * Calculate complexity based on import/dependency count
 *
 * Counts various import patterns:
 * - ES6 imports (import ... from)
 * - CommonJS requires (require(...))
 * - Python imports (import ..., from ... import)
 * - Java imports
 * - Go imports
 * - Rust use statements
 *
 * Scoring logic:
 * - 0-5 imports: 1 point
 * - 6-10 imports: 2 points
 * - 11-20 imports: 3 points
 * - 21-30 imports: 4 points
 * - 31+ imports: 6 points
 *
 * @param content File content
 * @param weight Weight multiplier for this scorer
 * @returns Scorer result with dependency metrics
 */
export function calculateDependencyScore(content: string, weight = 1.0): ScorerResult {
  let dependencyCount = 0;

  // ES6 imports
  const es6Imports = content.match(/^import\s+.*?from\s+['"][^'"]+['"]/gm);
  dependencyCount += es6Imports ? es6Imports.length : 0;

  // CommonJS requires
  const requireMatches = content.match(/require\s*\(\s*['"][^'"]+['"]\s*\)/g);
  dependencyCount += requireMatches ? requireMatches.length : 0;

  // Python imports
  const pythonImports = content.match(/^(?:import\s+\w+|from\s+\w+\s+import)/gm);
  dependencyCount += pythonImports ? pythonImports.length : 0;

  // Java imports
  const javaImports = content.match(/^import\s+[\w.]+;/gm);
  dependencyCount += javaImports ? javaImports.length : 0;

  // Go imports
  const goImports = content.match(/^import\s+\(\s*$[\s\S]*?^\)/gm);
  if (goImports) {
    // Count individual imports within import blocks
    for (const block of goImports) {
      const imports = block.match(/["'][\w./]+["']/g);
      dependencyCount += imports ? imports.length : 0;
    }
  }

  // Single Go imports
  const singleGoImports = content.match(/^import\s+["'][\w./]+["']/gm);
  dependencyCount += singleGoImports ? singleGoImports.length : 0;

  // Rust use statements
  const rustUse = content.match(/^use\s+[\w:]+/gm);
  dependencyCount += rustUse ? rustUse.length : 0;

  // Calculate base score
  let baseScore: number;
  if (dependencyCount <= 5) {
    baseScore = 1;
  } else if (dependencyCount <= 10) {
    baseScore = 2;
  } else if (dependencyCount <= 20) {
    baseScore = 3;
  } else if (dependencyCount <= 30) {
    baseScore = 4;
  } else {
    baseScore = 6;
  }

  return {
    name: 'dependencies',
    score: baseScore,
    weight,
    metadata: {
      totalDependencies: dependencyCount,
      es6Imports: es6Imports?.length ?? 0,
      commonjsRequires: requireMatches?.length ?? 0,
    },
  };
}
