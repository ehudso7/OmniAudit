import { parse } from '@babel/parser';
import traverse, { type NodePath } from '@babel/traverse';
import * as t from '@babel/types';
import type { AnalysisIssue, Analyzer, CodeInput, StaticAnalysisResult } from '../types/index';

export class PerformanceAnalyzer implements Analyzer {
  name = 'performance-analyzer';
  type = 'semantic' as const;
  enabled = true;
  config: Record<string, unknown>;

  constructor(config: Record<string, unknown> = {}) {
    this.config = {
      checkReactPerformance: true,
      checkLoops: true,
      checkRegex: true,
      checkImports: true,
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
      const ast = parse(input.code, {
        sourceType: 'module',
        plugins: ['typescript', 'jsx', 'decorators-legacy', 'classProperties'],
      });

      traverse(ast, {
        // Check for inefficient loops
        ForStatement: (path: NodePath<t.ForStatement>) => {
          if (this.config.checkLoops) {
            // Check for array.length in loop condition
            if (
              t.isBinaryExpression(path.node.test) &&
              t.isMemberExpression(path.node.test.right) &&
              t.isIdentifier(path.node.test.right.property, { name: 'length' })
            ) {
              issues.push({
                type: 'inefficient-loop',
                severity: 'info',
                message: 'Loop accesses array.length on every iteration',
                description: 'Cache array.length in a variable for better performance',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.8,
                fix: this.generateLoopLengthCacheFix(path),
              });
            }

            // Check for nested loops
            let hasNestedLoop = false;
            path.traverse({
              ForStatement() {
                hasNestedLoop = true;
              },
              WhileStatement() {
                hasNestedLoop = true;
              },
            });

            if (hasNestedLoop) {
              issues.push({
                type: 'nested-loops',
                severity: 'warning',
                message: 'Nested loops detected - O(n²) or worse complexity',
                description: 'Consider using a hash map or more efficient algorithm',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.9,
              });
            }
          }
        },

        // Check for expensive regex operations
        NewExpression: (path: NodePath<t.NewExpression>) => {
          if (this.config.checkRegex && t.isIdentifier(path.node.callee, { name: 'RegExp' })) {
            // Check if RegExp is created inside a loop or function called frequently
            let inLoop = false;
            let currentPath: NodePath | null = path;

            while (currentPath) {
              if (
                currentPath.isForStatement() ||
                currentPath.isWhileStatement() ||
                currentPath.isDoWhileStatement()
              ) {
                inLoop = true;
                break;
              }
              currentPath = currentPath.parentPath;
            }

            if (inLoop) {
              issues.push({
                type: 'regex-in-loop',
                severity: 'warning',
                message: 'RegExp created inside loop',
                description: 'Move RegExp creation outside loop for better performance',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 1.0,
              });
            }
          }
        },

        // Check for React-specific performance issues
        CallExpression: (path: NodePath<t.CallExpression>) => {
          if (this.config.checkReactPerformance) {
            // Check for missing React.memo
            if (
              t.isIdentifier(path.node.callee, { name: 'useState' }) ||
              t.isIdentifier(path.node.callee, { name: 'useEffect' })
            ) {
              const functionParent = path.getFunctionParent();
              if (functionParent) {
                const componentName = this.getComponentName(functionParent);
                if (componentName && !this.hasReactMemo(functionParent)) {
                  issues.push({
                    type: 'missing-react-memo',
                    severity: 'info',
                    message: `Component '${componentName}' may benefit from React.memo`,
                    description: 'Wrap component with React.memo to prevent unnecessary re-renders',
                    line: functionParent.node.loc?.start.line || 0,
                    column: functionParent.node.loc?.start.column,
                    confidence: 0.6,
                  });
                }
              }
            }

            // Check for array operations in render
            if (
              t.isMemberExpression(path.node.callee) &&
              t.isIdentifier(path.node.callee.property)
            ) {
              const methodName = path.node.callee.property.name;

              if (['map', 'filter', 'reduce', 'sort'].includes(methodName)) {
                const inRender = this.isInRenderPath(path);
                if (inRender && !this.isWrappedInUseMemo(path)) {
                  issues.push({
                    type: 'expensive-render-computation',
                    severity: 'warning',
                    message: `Array.${methodName}() in render without useMemo`,
                    description: 'Wrap expensive computations in useMemo hook',
                    line: path.node.loc?.start.line || 0,
                    column: path.node.loc?.start.column,
                    confidence: 0.7,
                  });
                }
              }
            }
          }

          // Check for useEffect with missing dependencies
          if (
            t.isIdentifier(path.node.callee, { name: 'useEffect' }) ||
            t.isIdentifier(path.node.callee, { name: 'useCallback' }) ||
            t.isIdentifier(path.node.callee, { name: 'useMemo' })
          ) {
            const hookName = (path.node.callee as t.Identifier).name;

            if (path.node.arguments.length < 2) {
              issues.push({
                type: 'missing-dependency-array',
                severity: 'warning',
                message: `${hookName} is missing dependency array`,
                description: 'Add dependency array to prevent stale closures',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 1.0,
              });
            }
          }
        },

        // Check for large imports
        ImportDeclaration: (path: NodePath<t.ImportDeclaration>) => {
          if (this.config.checkImports) {
            const source = path.node.source.value;

            // Check for full library imports when tree-shaking possible
            const heavyLibraries = ['lodash', 'moment', 'rxjs'];
            if (
              heavyLibraries.some((lib) => source === lib) &&
              !path.node.specifiers.some((s) => t.isImportNamespaceSpecifier(s))
            ) {
              issues.push({
                type: 'large-import',
                severity: 'info',
                message: `Import from '${source}' may include unused code`,
                description: `Use named imports like 'import { specific } from "${source}"' for better tree-shaking`,
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.8,
              });
            }

            // Check for default import of barrel exports
            if (source.endsWith('/index') || source.includes('/components')) {
              issues.push({
                type: 'barrel-import',
                severity: 'info',
                message: 'Importing from barrel export',
                description: 'Import directly from component file for faster build times',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.6,
              });
            }
          }
        },

        // Check for unnecessary object/array creation
        JSXExpressionContainer: (path: NodePath<t.JSXExpressionContainer>) => {
          const { expression } = path.node;

          // Check for inline object literals
          if (t.isObjectExpression(expression)) {
            issues.push({
              type: 'jsx-inline-object',
              severity: 'info',
              message: 'Inline object literal in JSX',
              description:
                'Creates new object on every render, causing child re-renders. Move outside or use useMemo',
              line: path.node.loc?.start.line || 0,
              column: path.node.loc?.start.column,
              confidence: 0.7,
            });
          }

          // Check for inline array literals
          if (t.isArrayExpression(expression)) {
            issues.push({
              type: 'jsx-inline-array',
              severity: 'info',
              message: 'Inline array literal in JSX',
              description: 'Creates new array on every render. Move outside or use useMemo',
              line: path.node.loc?.start.line || 0,
              column: path.node.loc?.start.column,
              confidence: 0.7,
            });
          }
        },
      });

      return {
        analyzer_name: this.name,
        analyzer_type: this.type,
        execution_time_ms: Date.now() - startTime,
        issues,
        metadata: {
          react_components_found: this.countReactComponents(ast),
          import_statements: this.countImports(ast),
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
            description: 'Fix syntax errors before analysis',
            line: 0,
            confidence: 1.0,
          },
        ],
      };
    }
  }

  private getComponentName(path: NodePath<t.Function>): string | null {
    if (
      (t.isFunctionDeclaration(path.node) || t.isFunctionExpression(path.node)) &&
      path.node.id &&
      t.isIdentifier(path.node.id)
    ) {
      return path.node.id.name;
    }

    const parent = path.parent;
    if (t.isVariableDeclarator(parent) && t.isIdentifier(parent.id)) {
      return parent.id.name;
    }

    return null;
  }

  private hasReactMemo(path: NodePath<t.Function>): boolean {
    const parent = path.parent;
    if (
      t.isCallExpression(parent) &&
      t.isMemberExpression(parent.callee) &&
      t.isIdentifier(parent.callee.object, { name: 'React' }) &&
      t.isIdentifier(parent.callee.property, { name: 'memo' })
    ) {
      return true;
    }

    if (t.isCallExpression(parent) && t.isIdentifier(parent.callee, { name: 'memo' })) {
      return true;
    }

    return false;
  }

  private isInRenderPath(path: NodePath): boolean {
    let currentPath: NodePath | null = path;

    while (currentPath) {
      if (currentPath.isJSXElement() || currentPath.isJSXFragment()) {
        return true;
      }
      currentPath = currentPath.parentPath;
    }

    return false;
  }

  private isWrappedInUseMemo(path: NodePath): boolean {
    let currentPath: NodePath | null = path;

    while (currentPath && !currentPath.isFunction()) {
      if (
        t.isCallExpression(currentPath.node) &&
        t.isIdentifier(currentPath.node.callee, { name: 'useMemo' })
      ) {
        return true;
      }
      currentPath = currentPath.parentPath;
    }

    return false;
  }

  private generateLoopLengthCacheFix(_path: NodePath<t.ForStatement>): string {
    // Generate a fix suggestion for caching array length
    return 'const len = array.length; for (let i = 0; i < len; i++) { ... }';
  }

  private countReactComponents(ast: t.Node): number {
    let count = 0;
    traverse(ast, {
      Function(path: NodePath<t.Function>) {
        if (
          (t.isFunctionDeclaration(path.node) || t.isFunctionExpression(path.node)) &&
          path.node.id &&
          t.isIdentifier(path.node.id) &&
          /^[A-Z]/.test(path.node.id.name)
        ) {
          count++;
        }
      },
      VariableDeclarator(path: NodePath<t.VariableDeclarator>) {
        if (
          t.isIdentifier(path.node.id) &&
          /^[A-Z]/.test(path.node.id.name) &&
          (t.isArrowFunctionExpression(path.node.init) || t.isFunctionExpression(path.node.init))
        ) {
          count++;
        }
      },
    });
    return count;
  }

  private countImports(ast: t.Node): number {
    let count = 0;
    traverse(ast, {
      ImportDeclaration() {
        count++;
      },
    });
    return count;
  }
}
