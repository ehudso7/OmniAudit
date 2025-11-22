import { parse } from '@babel/parser';
import traverse, { type NodePath } from '@babel/traverse';
import * as t from '@babel/types';
import type {
  Analyzer,
  CodeInput,
  StaticAnalysisResult,
  AnalysisIssue,
} from '../types/index';

export class ASTAnalyzer implements Analyzer {
  name = 'ast-analyzer';
  type = 'ast' as const;
  enabled = true;
  config: Record<string, unknown>;

  constructor(config: Record<string, unknown> = {}) {
    this.config = {
      checkComplexity: true,
      checkNesting: true,
      checkFunctionLength: true,
      maxComplexity: 15,
      maxNesting: 4,
      maxFunctionLength: 50,
      ...config,
    };
  }

  canHandle(language: string): boolean {
    return ['javascript', 'typescript', 'jsx', 'tsx'].includes(language.toLowerCase());
  }

  async analyze(input: CodeInput): Promise<StaticAnalysisResult> {
    const startTime = Date.now();
    const issues: AnalysisIssue[] = [];

    try {
      // Parse code into AST
      const ast = parse(input.code, {
        sourceType: 'module',
        plugins: [
          'typescript',
          'jsx',
          'decorators-legacy',
          'classProperties',
          'dynamicImport',
          'optionalChaining',
          'nullishCoalescingOperator',
        ],
      });

      // Traverse AST and collect issues
      traverse(ast, {
        Function: (path: NodePath<t.Function>) => {
          // Check cyclomatic complexity
          if (this.config.checkComplexity) {
            const complexity = this.calculateComplexity(path);
            if (complexity > (this.config.maxComplexity as number)) {
              issues.push({
                type: 'high-complexity',
                severity: 'warning',
                message: `Function has cyclomatic complexity of ${complexity}`,
                description: `Consider refactoring to reduce complexity below ${this.config.maxComplexity}`,
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 1.0,
              });
            }
          }

          // Check function length
          if (this.config.checkFunctionLength && path.node.loc) {
            const length = path.node.loc.end.line - path.node.loc.start.line;
            if (length > (this.config.maxFunctionLength as number)) {
              issues.push({
                type: 'long-function',
                severity: 'info',
                message: `Function is ${length} lines long`,
                description: `Consider breaking down into smaller functions`,
                line: path.node.loc.start.line,
                column: path.node.loc.start.column,
                confidence: 1.0,
              });
            }
          }

          // Check for missing error handling
          if (path.node.async && !this.hasTryCatch(path)) {
            issues.push({
              type: 'missing-error-handling',
              severity: 'warning',
              message: 'Async function lacks error handling',
              description: 'Wrap await calls in try-catch or use .catch()',
              line: path.node.loc?.start.line || 0,
              column: path.node.loc?.start.column,
              confidence: 0.8,
            });
          }
        },

        // Check for console.log in production code
        CallExpression: (path: NodePath<t.CallExpression>) => {
          if (
            t.isMemberExpression(path.node.callee) &&
            t.isIdentifier(path.node.callee.object, { name: 'console' })
          ) {
            const methodName = t.isIdentifier(path.node.callee.property)
              ? path.node.callee.property.name
              : '';

            if (['log', 'debug', 'info'].includes(methodName)) {
              issues.push({
                type: 'console-statement',
                severity: 'info',
                message: `console.${methodName}() should be removed before production`,
                description: 'Use a proper logging library or remove debugging statements',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 1.0,
              });
            }
          }

          // Check for eval usage
          if (t.isIdentifier(path.node.callee, { name: 'eval' })) {
            issues.push({
              type: 'unsafe-eval',
              severity: 'error',
              message: 'Usage of eval() is dangerous',
              description:
                'eval() can execute arbitrary code and poses security risks. Consider alternatives.',
              line: path.node.loc?.start.line || 0,
              column: path.node.loc?.start.column,
              confidence: 1.0,
            });
          }
        },

        // Check for unused variables
        Identifier: (path: NodePath<t.Identifier>) => {
          if (path.isReferencedIdentifier()) {
            const binding = path.scope.getBinding(path.node.name);
            if (binding && !binding.referenced) {
              issues.push({
                type: 'unused-variable',
                severity: 'warning',
                message: `Variable '${path.node.name}' is declared but never used`,
                description: 'Remove unused variable or use it',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 1.0,
              });
            }
          }
        },

        // Check for deep nesting
        IfStatement: (path: NodePath<t.IfStatement>) => {
          if (this.config.checkNesting) {
            const depth = this.getNestingDepth(path);
            if (depth > (this.config.maxNesting as number)) {
              issues.push({
                type: 'deep-nesting',
                severity: 'warning',
                message: `Code has nesting depth of ${depth}`,
                description: 'Consider early returns or extracting to separate functions',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.9,
              });
            }
          }
        },

        // Check for React-specific issues
        JSXElement: (path: NodePath<t.JSXElement>) => {
          // Check for missing key prop in array map
          const parent = path.parent;
          if (
            t.isCallExpression(parent) &&
            t.isMemberExpression(parent.callee) &&
            t.isIdentifier(parent.callee.property, { name: 'map' })
          ) {
            const hasKey = path.node.openingElement.attributes.some(
              (attr) => t.isJSXAttribute(attr) && t.isJSXIdentifier(attr.name, { name: 'key' }),
            );

            if (!hasKey) {
              issues.push({
                type: 'missing-key-prop',
                severity: 'warning',
                message: 'Missing key prop in array map',
                description: 'Each child in a list should have a unique "key" prop',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 1.0,
              });
            }
          }

          // Check for inline functions in JSX props
          path.node.openingElement.attributes.forEach((attr) => {
            if (
              t.isJSXAttribute(attr) &&
              attr.value &&
              t.isJSXExpressionContainer(attr.value) &&
              (t.isArrowFunctionExpression(attr.value.expression) ||
                t.isFunctionExpression(attr.value.expression))
            ) {
              issues.push({
                type: 'jsx-inline-function',
                severity: 'info',
                message: 'Inline function in JSX prop',
                description:
                  'Can cause unnecessary re-renders. Consider using useCallback or define outside render',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.7,
              });
            }
          });
        },
      });

      return {
        analyzer_name: this.name,
        analyzer_type: this.type,
        execution_time_ms: Date.now() - startTime,
        issues,
        metadata: {
          ast_nodes: this.countNodes(ast),
          lines_of_code: input.code.split('\n').length,
        },
      };
    } catch (error) {
      return {
        analyzer_name: this.name,
        analyzer_type: this.type,
        execution_time_ms: Date.now() - startTime,
        issues: [
          {
            type: 'parse-error',
            severity: 'error',
            message: `Failed to parse code: ${error instanceof Error ? error.message : String(error)}`,
            description: 'Fix syntax errors before analysis can proceed',
            line: 0,
            confidence: 1.0,
          },
        ],
      };
    }
  }

  private calculateComplexity(path: NodePath<t.Function>): number {
    let complexity = 1;

    path.traverse({
      IfStatement() {
        complexity++;
      },
      ConditionalExpression() {
        complexity++;
      },
      SwitchCase(casePath) {
        if (casePath.node.test) complexity++;
      },
      ForStatement() {
        complexity++;
      },
      ForInStatement() {
        complexity++;
      },
      ForOfStatement() {
        complexity++;
      },
      WhileStatement() {
        complexity++;
      },
      DoWhileStatement() {
        complexity++;
      },
      LogicalExpression(logPath) {
        if (logPath.node.operator === '&&' || logPath.node.operator === '||') {
          complexity++;
        }
      },
      CatchClause() {
        complexity++;
      },
    });

    return complexity;
  }

  private getNestingDepth(path: NodePath): number {
    let depth = 0;
    let currentPath: NodePath | null = path;

    while (currentPath) {
      if (
        currentPath.isIfStatement() ||
        currentPath.isForStatement() ||
        currentPath.isWhileStatement() ||
        currentPath.isDoWhileStatement() ||
        currentPath.isSwitchStatement() ||
        currentPath.isTryStatement()
      ) {
        depth++;
      }
      currentPath = currentPath.parentPath;
    }

    return depth;
  }

  private hasTryCatch(path: NodePath<t.Function>): boolean {
    let hasTryCatch = false;

    path.traverse({
      TryStatement() {
        hasTryCatch = true;
      },
      CallExpression(callPath) {
        // Check for .catch() on promises
        if (
          t.isMemberExpression(callPath.node.callee) &&
          t.isIdentifier(callPath.node.callee.property, { name: 'catch' })
        ) {
          hasTryCatch = true;
        }
      },
    });

    return hasTryCatch;
  }

  private countNodes(ast: t.Node): number {
    let count = 0;
    traverse(ast, {
      enter() {
        count++;
      },
    });
    return count;
  }
}
