import type { Transformer, Optimization } from '../types/index';

export abstract class BaseTransformer implements Transformer {
  abstract name: string;
  abstract type: 'refactor' | 'optimize' | 'modernize' | 'convert';
  abstract patterns: string[];
  abstract ai_assisted: boolean;

  abstract canHandle(optimization: Optimization): boolean;
  abstract apply(code: string, optimization: Optimization): Promise<string>;

  protected matchesPattern(optimization: Optimization): boolean {
    return this.patterns.some((pattern) => {
      const regex = new RegExp(pattern);
      return regex.test(optimization.type) || regex.test(optimization.title);
    });
  }
}

export class ReactMemoTransformer extends BaseTransformer {
  name = 'react-memo-transformer';
  type = 'optimize' as const;
  patterns = ['missing-react-memo', 'React.memo'];
  ai_assisted = true;

  canHandle(optimization: Optimization): boolean {
    return (
      optimization.type === 'performance' &&
      (optimization.title.includes('React.memo') ||
        optimization.title.includes('unnecessary re-render'))
    );
  }

  async apply(code: string, optimization: Optimization): Promise<string> {
    // Extract component name from the code
    const componentMatch = code.match(/(?:function|const)\s+(\w+)/);
    if (!componentMatch) return code;

    const componentName = componentMatch[1];

    // Check if already wrapped
    if (code.includes('React.memo') || code.includes('memo(')) {
      return code;
    }

    // Wrap component with React.memo
    const lines = code.split('\n');
    const componentLine = optimization.location.line - 1;

    // Add import if not present
    let hasImport = false;

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('import') && lines[i].includes('react')) {
        hasImport = true;

        // Add memo to existing import
        if (!lines[i].includes('memo')) {
          lines[i] = lines[i].replace(/from\s+['"]react['"]/, "{ memo } from 'react'");
          if (lines[i].includes('import React')) {
            lines[i] = lines[i].replace('import React', 'import React, { memo }');
          }
        }
        break;
      }
    }

    if (!hasImport) {
      lines.unshift("import { memo } from 'react';");
    }

    // Find export statement
    const exportLineIndex = lines.findIndex(
      (line) =>
        line.includes(`export default ${componentName}`) ||
        line.includes(`export { ${componentName} }`),
    );

    if (exportLineIndex !== -1) {
      lines[exportLineIndex] = lines[exportLineIndex].replace(
        componentName,
        `memo(${componentName})`,
      );
    } else {
      // Add memo wrapper at component definition
      lines[componentLine] = `const ${componentName} = memo(${lines[componentLine]});`;
    }

    return lines.join('\n');
  }
}

export class UseMemoTransformer extends BaseTransformer {
  name = 'usememo-transformer';
  type = 'optimize' as const;
  patterns = ['expensive-render-computation', 'useMemo'];
  ai_assisted = true;

  canHandle(optimization: Optimization): boolean {
    return (
      optimization.type === 'performance' &&
      (optimization.title.includes('useMemo') ||
        optimization.title.includes('expensive computation'))
    );
  }

  async apply(code: string, optimization: Optimization): Promise<string> {
    // This is a simplified implementation
    // In production, use proper AST transformation

    const lines = code.split('\n');
    const targetLine = optimization.location.line - 1;

    if (targetLine < 0 || targetLine >= lines.length) {
      return code;
    }

    const line = lines[targetLine];
    const indentation = line.match(/^\s*/)?.[0] || '';

    // Check if already wrapped
    if (line.includes('useMemo')) {
      return code;
    }

    // Extract the expensive computation
    const computation = line.trim();

    // Wrap in useMemo
    lines[targetLine] = `${indentation}const memoizedValue = useMemo(() => ${computation}, [/* dependencies */]);`;

    // Add import if not present
    if (!code.includes('useMemo')) {
      const importIndex = lines.findIndex((l) => l.includes('import') && l.includes('react'));

      if (importIndex !== -1) {
        if (!lines[importIndex].includes('useMemo')) {
          lines[importIndex] = lines[importIndex].replace(
            /from\s+['"]react['"]/,
            "{ useMemo } from 'react'",
          );
        }
      } else {
        lines.unshift("import { useMemo } from 'react';");
      }
    }

    return lines.join('\n');
  }
}

export class RemoveConsoleTransformer extends BaseTransformer {
  name = 'remove-console-transformer';
  type = 'refactor' as const;
  patterns = ['console-statement', 'console\\.log'];
  ai_assisted = false;

  canHandle(optimization: Optimization): boolean {
    return optimization.type === 'quality' && optimization.title.includes('console');
  }

  async apply(code: string, optimization: Optimization): Promise<string> {
    const lines = code.split('\n');
    const targetLine = optimization.location.line - 1;

    if (targetLine >= 0 && targetLine < lines.length) {
      // Remove or comment out the console statement
      lines[targetLine] = lines[targetLine].replace(/console\.\w+\([^)]*\);?/, '// Removed console statement');
    }

    return lines.join('\n');
  }
}
