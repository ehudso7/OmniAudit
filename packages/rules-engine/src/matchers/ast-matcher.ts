import { parse } from '@babel/parser';
import traverse from '@babel/traverse';
import type * as t from '@babel/types';
import type { Rule, Match, Matcher, FileToAnalyze } from '../types';

/**
 * ASTMatcher - Handles AST-based pattern matching
 */
export class ASTMatcher implements Matcher {
  /**
   * Parse source code to AST
   */
  private parseToAST(content: string, _language?: string): t.File | null {
    try {
      const plugins: any[] = [
        'jsx',
        'typescript',
        'decorators-legacy',
        'classProperties',
        'classPrivateProperties',
        'classPrivateMethods',
        'exportDefaultFrom',
        'exportNamespaceFrom',
        'dynamicImport',
        'numericSeparator',
        'optionalChaining',
        'nullishCoalescingOperator',
        'bigInt',
        'optionalCatchBinding',
        'objectRestSpread',
        'asyncGenerators',
      ];

      return parse(content, {
        sourceType: 'unambiguous',
        plugins,
        errorRecovery: true,
      });
    } catch (error) {
      console.error('Error parsing AST:', error);
      return null;
    }
  }

  /**
   * Get line and column from AST node
   */
  private getPosition(node: any): { line: number; column: number } {
    return {
      line: node.loc?.start.line || 0,
      column: node.loc?.start.column || 0,
    };
  }

  /**
   * Extract snippet from source
   */
  private getSnippet(content: string, node: any): string {
    if (!node.loc) return '';

    const lines = content.split('\n');
    const startLine = Math.max(0, node.loc.start.line - 3);
    const endLine = Math.min(lines.length, node.loc.end.line + 2);

    return lines.slice(startLine, endLine).join('\n');
  }

  /**
   * Match content against a rule's AST pattern
   */
  match(content: string, rule: Rule, file: FileToAnalyze): Match[] {
    const matches: Match[] = [];
    const patterns = rule.patterns as any;

    if (!patterns.ast) {
      return matches;
    }

    const ast = this.parseToAST(content, file.language);
    if (!ast) {
      return matches;
    }

    try {
      // Parse the AST selector (e.g., "CallExpression", "FunctionDeclaration")
      const selector = patterns.selector || patterns.ast;

      traverse(ast, {
        enter: (path) => {
          // Check if node type matches selector
          if (!this.matchesSelector(path.node, selector)) {
            return;
          }

          // Additional pattern matching
          if (!this.matchesPattern(path.node, patterns.ast)) {
            return;
          }

          const startPos = this.getPosition(path.node);
          const endPos = {
            line: path.node.loc?.end.line || startPos.line,
            column: path.node.loc?.end.column || startPos.column,
          };

          matches.push({
            ruleId: rule.id,
            file: file.path,
            line: startPos.line,
            column: startPos.column,
            endLine: endPos.line,
            endColumn: endPos.column,
            message: rule.message || rule.description,
            severity: rule.severity,
            category: rule.category,
            snippet: this.getSnippet(content, path.node),
            metadata: {
              cwe: rule.cwe,
              owasp: rule.owasp,
              references: rule.references,
            },
          });
        },
      });
    } catch (error) {
      console.error(`Error traversing AST for rule ${rule.id}:`, error);
    }

    return matches;
  }

  /**
   * Check if node matches selector
   */
  private matchesSelector(node: any, selector: string): boolean {
    // Simple type matching
    if (node.type === selector) {
      return true;
    }

    // Pattern matching for common patterns
    const patterns: Record<string, (node: any) => boolean> = {
      'console.log': (n) =>
        n.type === 'CallExpression' &&
        n.callee?.type === 'MemberExpression' &&
        n.callee?.object?.name === 'console' &&
        n.callee?.property?.name === 'log',

      'eval': (n) =>
        n.type === 'CallExpression' &&
        n.callee?.name === 'eval',

      'dangerouslySetInnerHTML': (n) =>
        n.type === 'JSXAttribute' &&
        n.name?.name === 'dangerouslySetInnerHTML',

      'Function constructor': (n) =>
        n.type === 'NewExpression' &&
        n.callee?.name === 'Function',

      'setTimeout string': (n) =>
        n.type === 'CallExpression' &&
        n.callee?.name === 'setTimeout' &&
        n.arguments?.[0]?.type === 'StringLiteral',

      'setInterval string': (n) =>
        n.type === 'CallExpression' &&
        n.callee?.name === 'setInterval' &&
        n.arguments?.[0]?.type === 'StringLiteral',

      'innerHTML': (n) =>
        n.type === 'MemberExpression' &&
        n.property?.name === 'innerHTML',

      'document.write': (n) =>
        n.type === 'CallExpression' &&
        n.callee?.type === 'MemberExpression' &&
        n.callee?.object?.name === 'document' &&
        n.callee?.property?.name === 'write',
    };

    const pattern = patterns[selector];
    return pattern ? pattern(node) : false;
  }

  /**
   * Check if node matches complex pattern
   */
  private matchesPattern(_node: any, _pattern: string): boolean {
    // For now, simple implementation
    // Could be extended to support more complex pattern matching
    return true;
  }
}

export const astMatcher = new ASTMatcher();
