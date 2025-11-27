import type { Rule, Match, Matcher, FileToAnalyze } from '../types';

/**
 * Maximum number of matches to collect per file (ReDoS protection)
 */
const MAX_MATCHES_PER_FILE = 1000;

/**
 * Maximum content length to process with potentially slow patterns
 * Patterns with unbounded quantifiers are limited to this size
 */
const MAX_CONTENT_LENGTH_FOR_SLOW_PATTERNS = 500000; // 500KB

/**
 * Patterns that may cause ReDoS (unbounded quantifiers with lookahead/lookbehind)
 * Detects: [^...]*  |  [\s\S]  |  [\S\s]  |  (?=  (?!  (?<
 */
const SLOW_PATTERN_INDICATORS = /\[\^[^\]]*\]\*|\[\\s\\S\]|\[\\S\\s\]|\(\?[=!<]/;

/**
 * RegexMatcher - Handles regex pattern matching with caching and ReDoS protection
 */
export class RegexMatcher implements Matcher {
  private regexCache: Map<string, RegExp> = new Map();

  /**
   * Get or compile a regex pattern
   */
  private getRegex(pattern: string, flags?: string): RegExp {
    const cacheKey = `${pattern}|${flags || ''}`;

    if (this.regexCache.has(cacheKey)) {
      return this.regexCache.get(cacheKey)!;
    }

    const regex = new RegExp(pattern, flags || 'gm');
    this.regexCache.set(cacheKey, regex);
    return regex;
  }

  /**
   * Get line and column from index
   */
  private getPosition(content: string, index: number): { line: number; column: number } {
    const lines = content.substring(0, index).split('\n');
    return {
      line: lines.length,
      column: lines[lines.length - 1]?.length ?? 0,
    };
  }

  /**
   * Extract snippet around match
   */
  private getSnippet(content: string, startIndex: number, endIndex: number): string {
    const lines = content.split('\n');
    const startPos = this.getPosition(content, startIndex);
    const endPos = this.getPosition(content, endIndex);

    const contextLines = 2;
    const startLine = Math.max(0, startPos.line - contextLines - 1);
    const endLine = Math.min(lines.length, endPos.line + contextLines);

    return lines.slice(startLine, endLine).join('\n');
  }

  /**
   * Check if a pattern may cause ReDoS
   */
  private isSlowPattern(pattern: string): boolean {
    return SLOW_PATTERN_INDICATORS.test(pattern);
  }

  /**
   * Match content against a rule's regex pattern
   */
  match(content: string, rule: Rule, file: FileToAnalyze): Match[] {
    const matches: Match[] = [];

    // Extract regex pattern
    const patterns = rule.patterns as any;
    if (!patterns.regex) {
      return matches;
    }

    // ReDoS protection: limit content size for potentially slow patterns
    let contentToMatch = content;
    if (this.isSlowPattern(patterns.regex) && content.length > MAX_CONTENT_LENGTH_FOR_SLOW_PATTERNS) {
      console.warn(`Rule ${rule.id}: Content truncated for slow pattern (${content.length} > ${MAX_CONTENT_LENGTH_FOR_SLOW_PATTERNS} bytes)`);
      contentToMatch = content.substring(0, MAX_CONTENT_LENGTH_FOR_SLOW_PATTERNS);
    }

    try {
      const regex = this.getRegex(patterns.regex, patterns.flags);
      let match: RegExpExecArray | null;

      // Reset regex state
      regex.lastIndex = 0;

      while ((match = regex.exec(contentToMatch)) !== null) {
        // ReDoS protection: limit number of matches
        if (matches.length >= MAX_MATCHES_PER_FILE) {
          console.warn(`Rule ${rule.id}: Match limit reached (${MAX_MATCHES_PER_FILE})`);
          break;
        }

        const startPos = this.getPosition(contentToMatch, match.index);
        const endIndex = match.index + match[0].length;
        const endPos = this.getPosition(contentToMatch, endIndex);
        const snippet = this.getSnippet(contentToMatch, match.index, endIndex);

        // Build message with captured groups
        let message = rule.message || rule.description;
        if (match.length > 1) {
          message += ` (found: ${match[1]})`;
        }

        matches.push({
          ruleId: rule.id,
          file: file.path,
          line: startPos.line,
          column: startPos.column,
          endLine: endPos.line,
          endColumn: endPos.column,
          message,
          severity: rule.severity,
          category: rule.category,
          snippet,
          metadata: {
            cwe: rule.cwe,
            owasp: rule.owasp,
            references: rule.references,
          },
          fix: rule.fix ? {
            type: rule.fix.type,
            replacement: this.generateFix(match, rule.fix.template),
            confidence: rule.fix.confidence || 0.5,
          } : undefined,
        });

        // Prevent infinite loops on zero-length matches
        if (match[0].length === 0) {
          regex.lastIndex++;
        }
      }
    } catch (error) {
      console.error(`Error executing regex for rule ${rule.id}:`, error);
    }

    return matches;
  }

  /**
   * Generate fix from template
   */
  private generateFix(match: RegExpExecArray, template: string): string {
    let result = template;

    // Replace $0, $1, $2, etc. with captured groups
    for (let i = 0; i < match.length; i++) {
      result = result.replace(new RegExp(`\\$${i}`, 'g'), match[i] || '');
    }

    // Replace named groups like ${MATCH_NAME}
    if (match.groups) {
      for (const [key, value] of Object.entries(match.groups)) {
        result = result.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), value || '');
      }
    }

    return result;
  }

  /**
   * Clear regex cache
   */
  clearCache(): void {
    this.regexCache.clear();
  }

  /**
   * Get cache stats
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.regexCache.size,
      keys: Array.from(this.regexCache.keys()),
    };
  }
}

export const regexMatcher = new RegexMatcher();
