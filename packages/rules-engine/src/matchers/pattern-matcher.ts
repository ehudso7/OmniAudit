import type { Rule, Match, Matcher, FileToAnalyze } from '../types';
import { regexMatcher } from './regex-matcher';
import { astMatcher } from './ast-matcher';

/**
 * PatternMatcher - Combines regex and AST matching (Semgrep-like)
 */
export class PatternMatcher implements Matcher {
  /**
   * Match using combined patterns
   */
  match(content: string, rule: Rule, file: FileToAnalyze): Match[] {
    const patterns = rule.patterns as any;

    // If it's a simple regex pattern
    if (patterns.regex) {
      return regexMatcher.match(content, rule, file);
    }

    // If it's an AST pattern
    if (patterns.ast) {
      return astMatcher.match(content, rule, file);
    }

    // Semgrep-like pattern matching
    if (patterns.pattern || patterns.patterns || patterns.pattern_either) {
      return this.matchSemgrepPattern(content, rule, file);
    }

    return [];
  }

  /**
   * Match Semgrep-style patterns
   */
  private matchSemgrepPattern(content: string, rule: Rule, file: FileToAnalyze): Match[] {
    const patterns = rule.patterns as any;
    let matches: Match[] = [];

    // Handle single pattern
    if (patterns.pattern) {
      matches = this.matchPattern(content, patterns.pattern, rule, file);
    }

    // Handle multiple patterns (AND logic)
    if (patterns.patterns) {
      let allMatches: Match[][] = [];
      for (const pattern of patterns.patterns) {
        const patternMatches = this.matchPattern(content, pattern, rule, file);
        allMatches.push(patternMatches);
      }
      // Intersection of all matches
      matches = this.intersectMatches(allMatches);
    }

    // Handle either patterns (OR logic)
    if (patterns.pattern_either) {
      const eitherMatches: Match[] = [];
      for (const pattern of patterns.pattern_either) {
        const patternMatches = this.matchPattern(content, pattern, rule, file);
        eitherMatches.push(...patternMatches);
      }
      matches = [...matches, ...eitherMatches];
    }

    // Handle pattern_not (exclusion)
    if (patterns.pattern_not && matches.length > 0) {
      const notMatches = this.matchPattern(content, patterns.pattern_not, rule, file);
      matches = this.excludeMatches(matches, notMatches);
    }

    return matches;
  }

  /**
   * Match a single pattern string
   */
  private matchPattern(
    content: string,
    pattern: string,
    rule: Rule,
    file: FileToAnalyze
  ): Match[] {
    // Convert pattern to regex
    const regex = this.patternToRegex(pattern);
    const tempRule = {
      ...rule,
      patterns: { regex: regex.source, flags: regex.flags },
    };
    return regexMatcher.match(content, tempRule, file);
  }

  /**
   * Escape special regex characters in a string
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Convert Semgrep-like pattern to regex
   *
   * Handles metavariables like $VAR (single identifier) and $... (ellipsis for any code)
   * Order of operations: escape first, then replace metavariables
   */
  private patternToRegex(pattern: string): RegExp {
    // Tokenize the pattern, preserving metavariables
    // Match $... (ellipsis) or $WORD (identifier metavariable)
    const metavarPattern = /(\$\.\.\.|\$\w+)/g;
    const parts = pattern.split(metavarPattern);

    let regexPattern = '';
    for (const part of parts) {
      if (part === '$...') {
        // Ellipsis matches any code (non-greedy)
        regexPattern += '[\\s\\S]*?';
      } else if (part.startsWith('$') && /^\$\w+$/.test(part)) {
        // Named metavariable matches an identifier (\w already includes digits and underscore)
        regexPattern += '\\w+';
      } else {
        // Regular text - escape special regex characters
        regexPattern += this.escapeRegex(part);
      }
    }

    return new RegExp(regexPattern, 'gm');
  }

  /**
   * Intersect multiple match arrays (AND logic)
   */
  private intersectMatches(matchArrays: Match[][]): Match[] {
    if (matchArrays.length === 0) return [];
    if (matchArrays.length === 1) return matchArrays[0] || [];

    // Find matches that appear in all arrays (by line number)
    const first = matchArrays[0] || [];
    return first.filter(match =>
      matchArrays.slice(1).every(arr =>
        arr.some(m => m.file === match.file && m.line === match.line)
      )
    );
  }

  /**
   * Exclude matches (NOT logic)
   */
  private excludeMatches(matches: Match[], excludeMatches: Match[]): Match[] {
    return matches.filter(match =>
      !excludeMatches.some(ex =>
        ex.file === match.file &&
        ex.line === match.line &&
        ex.column === match.column
      )
    );
  }

  /**
   * Check if a match overlaps with another
   */
  private matchesOverlap(m1: Match, m2: Match): boolean {
    if (m1.file !== m2.file) return false;

    const m1End = m1.endLine || m1.line;
    const m2End = m2.endLine || m2.line;

    return (
      (m1.line <= m2.line && m1End >= m2.line) ||
      (m2.line <= m1.line && m2End >= m1.line)
    );
  }
}

export const patternMatcher = new PatternMatcher();
