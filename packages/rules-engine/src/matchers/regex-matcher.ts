import type { Rule, Match, Matcher, FileToAnalyze } from '../types';

/**
 * RegexMatcher - Handles regex pattern matching with caching
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
   * Match content against a rule's regex pattern
   */
  match(content: string, rule: Rule, file: FileToAnalyze): Match[] {
    const matches: Match[] = [];

    // Extract regex pattern
    const patterns = rule.patterns as any;
    if (!patterns.regex) {
      return matches;
    }

    try {
      const regex = this.getRegex(patterns.regex, patterns.flags);
      let match: RegExpExecArray | null;

      // Reset regex state
      regex.lastIndex = 0;

      while ((match = regex.exec(content)) !== null) {
        const startPos = this.getPosition(content, match.index);
        const endIndex = match.index + match[0].length;
        const endPos = this.getPosition(content, endIndex);
        const snippet = this.getSnippet(content, match.index, endIndex);

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
