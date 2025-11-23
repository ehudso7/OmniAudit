import { parse } from '@babel/parser';
import traverse, { type NodePath } from '@babel/traverse';
import * as t from '@babel/types';
import type { AnalysisIssue, Analyzer, CodeInput, StaticAnalysisResult } from '../types/index';

export class SecurityAnalyzer implements Analyzer {
  name = 'security-analyzer';
  type = 'semantic' as const;
  enabled = true;
  config: Record<string, unknown>;

  private readonly DANGEROUS_FUNCTIONS = [
    'eval',
    'Function',
    'setTimeout',
    'setInterval',
    'execScript',
  ];

  // Properties that could be dangerous if misused
  // private readonly DANGEROUS_PROPERTIES = [
  //   'innerHTML',
  //   'outerHTML',
  //   'insertAdjacentHTML',
  //   'document.write',
  //   'document.writeln',
  // ];

  private readonly SECRET_PATTERNS = [
    /api[_-]?key/i,
    /secret[_-]?key/i,
    /password/i,
    /private[_-]?key/i,
    /aws[_-]?access/i,
    /bearer\s+[a-zA-Z0-9\-._~+/]+=*/i,
    /sk_live_[a-zA-Z0-9]+/,
    /ghp_[a-zA-Z0-9]{36}/,
  ];

  constructor(config: Record<string, unknown> = {}) {
    this.config = {
      checkXSS: true,
      checkInjection: true,
      checkSecrets: true,
      checkCrypto: true,
      checkAuth: true,
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
      // Check for hardcoded secrets in source code
      if (this.config.checkSecrets) {
        this.checkForSecrets(input.code, issues);
      }

      const ast = parse(input.code, {
        sourceType: 'module',
        plugins: ['typescript', 'jsx', 'decorators-legacy', 'classProperties'],
      });

      traverse(ast, {
        // Check for dangerous function usage and various security issues
        CallExpression: (path: NodePath<t.CallExpression>) => {
          // Check for eval and similar
          if (t.isIdentifier(path.node.callee)) {
            const funcName = path.node.callee.name;

            if (this.DANGEROUS_FUNCTIONS.includes(funcName)) {
              issues.push({
                type: 'dangerous-function',
                severity: 'error',
                message: `Usage of ${funcName}() is dangerous`,
                description: `${funcName}() can execute arbitrary code and poses severe security risks. Avoid using it.`,
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 1.0,
              });
            }
          }

          // Check for SQL injection vulnerabilities
          if (this.config.checkInjection) {
            if (
              t.isMemberExpression(path.node.callee) &&
              t.isIdentifier(path.node.callee.property)
            ) {
              const methodName = path.node.callee.property.name;

              if (['query', 'execute', 'raw'].includes(methodName)) {
                // Check if using string concatenation or template literals with variables
                const firstArg = path.node.arguments[0];

                if (t.isTemplateLiteral(firstArg) && firstArg.expressions.length > 0) {
                  issues.push({
                    type: 'sql-injection',
                    severity: 'error',
                    message: 'Potential SQL injection vulnerability',
                    description:
                      'Use parameterized queries or prepared statements instead of string interpolation',
                    line: path.node.loc?.start.line || 0,
                    column: path.node.loc?.start.column,
                    confidence: 0.9,
                  });
                }

                if (t.isBinaryExpression(firstArg) && firstArg.operator === '+') {
                  issues.push({
                    type: 'sql-injection',
                    severity: 'error',
                    message: 'Potential SQL injection vulnerability',
                    description: 'Use parameterized queries instead of string concatenation',
                    line: path.node.loc?.start.line || 0,
                    column: path.node.loc?.start.column,
                    confidence: 1.0,
                  });
                }
              }

              // Check for command injection
              if (['exec', 'spawn', 'execSync', 'spawnSync'].includes(methodName)) {
                const firstArg = path.node.arguments[0];

                if (
                  t.isTemplateLiteral(firstArg) ||
                  (t.isBinaryExpression(firstArg) && firstArg.operator === '+')
                ) {
                  issues.push({
                    type: 'command-injection',
                    severity: 'error',
                    message: 'Potential command injection vulnerability',
                    description: 'Sanitize user input before passing to shell commands',
                    line: path.node.loc?.start.line || 0,
                    column: path.node.loc?.start.column,
                    confidence: 0.9,
                  });
                }
              }

              // Check for POST/PUT/DELETE routes without CSRF
              if (['post', 'put', 'delete', 'patch'].includes(methodName)) {
                // Simple heuristic: check if there's no mention of csrf in the route handler
                let hasCsrfCheck = false;

                path.traverse({
                  Identifier(idPath) {
                    if (idPath.node.name.toLowerCase().includes('csrf')) {
                      hasCsrfCheck = true;
                    }
                  },
                });

                if (!hasCsrfCheck) {
                  issues.push({
                    type: 'missing-csrf',
                    severity: 'warning',
                    message: `${methodName.toUpperCase()} route may lack CSRF protection`,
                    description:
                      'Consider adding CSRF token validation for state-changing operations',
                    line: path.node.loc?.start.line || 0,
                    column: path.node.loc?.start.column,
                    confidence: 0.5,
                  });
                }
              }
            }
          }

          // Check for insecure random number generation
          if (
            this.config.checkCrypto &&
            t.isMemberExpression(path.node.callee) &&
            t.isIdentifier(path.node.callee.object, { name: 'Math' }) &&
            t.isIdentifier(path.node.callee.property, { name: 'random' })
          ) {
            issues.push({
              type: 'insecure-random',
              severity: 'warning',
              message: 'Math.random() is not cryptographically secure',
              description:
                'Use crypto.randomBytes() or crypto.getRandomValues() for security-sensitive operations',
              line: path.node.loc?.start.line || 0,
              column: path.node.loc?.start.column,
              confidence: 0.8,
            });
          }

          // Check for insecure JWT verification
          if (
            this.config.checkAuth &&
            t.isMemberExpression(path.node.callee) &&
            t.isIdentifier(path.node.callee.property, { name: 'verify' })
          ) {
            // Check if jwt.verify is called without secret
            if (path.node.arguments.length < 2) {
              issues.push({
                type: 'jwt-no-secret',
                severity: 'error',
                message: 'JWT verification without secret',
                description: 'Always verify JWT tokens with a secret or public key',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.9,
              });
            }

            // Check for algorithm 'none'
            const options = path.node.arguments[2];
            if (t.isObjectExpression(options)) {
              const algorithmProp = options.properties.find(
                (prop) =>
                  t.isObjectProperty(prop) && t.isIdentifier(prop.key, { name: 'algorithms' }),
              );

              if (
                algorithmProp &&
                t.isObjectProperty(algorithmProp) &&
                t.isArrayExpression(algorithmProp.value)
              ) {
                const hasNone = algorithmProp.value.elements.some(
                  (el) => t.isStringLiteral(el) && el.value === 'none',
                );

                if (hasNone) {
                  issues.push({
                    type: 'jwt-algorithm-none',
                    severity: 'error',
                    message: 'JWT accepting "none" algorithm',
                    description: 'Never accept "none" algorithm for JWT verification',
                    line: path.node.loc?.start.line || 0,
                    column: path.node.loc?.start.column,
                    confidence: 1.0,
                  });
                }
              }
            }
          }

          // Check for insecure deserialization
          if (
            t.isMemberExpression(path.node.callee) &&
            t.isIdentifier(path.node.callee.object, { name: 'JSON' }) &&
            t.isIdentifier(path.node.callee.property, { name: 'parse' })
          ) {
            // Check if parsing untrusted input
            const firstArg = path.node.arguments[0];

            if (
              t.isMemberExpression(firstArg) &&
              t.isIdentifier(firstArg.property, { name: 'body' })
            ) {
              issues.push({
                type: 'unsafe-deserialization',
                severity: 'info',
                message: 'Parsing JSON from request body',
                description: 'Validate and sanitize JSON input before processing',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.6,
              });
            }
          }
        },

        // Check for XSS vulnerabilities
        MemberExpression: (path: NodePath<t.MemberExpression>) => {
          if (this.config.checkXSS && t.isIdentifier(path.node.property)) {
            const propName = path.node.property.name;

            if (
              ['innerHTML', 'outerHTML'].includes(propName) &&
              path.parent &&
              t.isAssignmentExpression(path.parent)
            ) {
              const right = path.parent.right;

              // Check if assigning user input or variables
              if (!t.isStringLiteral(right)) {
                issues.push({
                  type: 'xss-vulnerability',
                  severity: 'error',
                  message: `Setting ${propName} with dynamic content`,
                  description:
                    'This can lead to XSS attacks. Use textContent or properly sanitize HTML',
                  line: path.node.loc?.start.line || 0,
                  column: path.node.loc?.start.column,
                  confidence: 0.9,
                });
              }
            }

            // Check for dangerouslySetInnerHTML in React
            if (propName === 'dangerouslySetInnerHTML') {
              issues.push({
                type: 'react-xss',
                severity: 'warning',
                message: 'Using dangerouslySetInnerHTML',
                description: 'Ensure HTML is properly sanitized to prevent XSS attacks',
                line: path.node.loc?.start.line || 0,
                column: path.node.loc?.start.column,
                confidence: 0.8,
              });
            }
          }
        },

        // Check for weak cryptography
        NewExpression: (path: NodePath<t.NewExpression>) => {
          if (this.config.checkCrypto && t.isIdentifier(path.node.callee)) {
            const className = path.node.callee.name;

            if (className === 'Buffer' && path.node.arguments.length > 0) {
              const firstArg = path.node.arguments[0];
              if (
                t.isStringLiteral(firstArg) ||
                (t.isIdentifier(firstArg) && !t.isStringLiteral(firstArg))
              ) {
                issues.push({
                  type: 'buffer-from-string',
                  severity: 'warning',
                  message: 'Using Buffer constructor with string',
                  description: 'Use Buffer.from() instead of Buffer() constructor',
                  line: path.node.loc?.start.line || 0,
                  column: path.node.loc?.start.column,
                  confidence: 1.0,
                });
              }
            }
          }
        },
      });

      return {
        analyzer_name: this.name,
        analyzer_type: this.type,
        execution_time_ms: Date.now() - startTime,
        issues,
        metadata: {
          security_critical: issues.filter((i) => i.severity === 'error').length,
          security_warnings: issues.filter((i) => i.severity === 'warning').length,
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
            description: 'Fix syntax errors before security analysis',
            line: 0,
            confidence: 1.0,
          },
        ],
      };
    }
  }

  private checkForSecrets(code: string, issues: AnalysisIssue[]): void {
    const lines = code.split('\n');

    lines.forEach((line, index) => {
      this.SECRET_PATTERNS.forEach((pattern) => {
        if (pattern.test(line)) {
          // Check if it's in a comment
          const isComment = line.trim().startsWith('//') || line.trim().startsWith('*');

          if (!isComment) {
            issues.push({
              type: 'hardcoded-secret',
              severity: 'error',
              message: 'Possible hardcoded secret detected',
              description:
                'Never commit secrets to source code. Use environment variables or secret management systems',
              line: index + 1,
              confidence: 0.7,
            });
          }
        }
      });

      // Check for common secret patterns
      if (/['"]([A-Za-z0-9+/]{40,})['"]/.test(line) || /['"]([A-Za-z0-9_-]{32,})['"]/.test(line)) {
        issues.push({
          type: 'possible-secret',
          severity: 'warning',
          message: 'Possible hardcoded token or key',
          description: 'Review this line for hardcoded secrets',
          line: index + 1,
          confidence: 0.5,
        });
      }
    });
  }
}
