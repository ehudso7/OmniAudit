import { ASTAnalyzer } from './ast-analyzer';
import { PerformanceAnalyzer } from './performance-analyzer';
import { SecurityAnalyzer } from './security-analyzer';
import type { Analyzer } from '../types/index';

export class AnalyzerFactory {
  private static readonly ANALYZERS = new Map<string, new (config: Record<string, unknown>) => Analyzer>([
    ['ast-analyzer', ASTAnalyzer],
    ['performance-analyzer', PerformanceAnalyzer],
    ['security-analyzer', SecurityAnalyzer],
  ]);

  static createAnalyzer(name: string, config: Record<string, unknown> = {}): Analyzer {
    const AnalyzerClass = this.ANALYZERS.get(name);

    if (!AnalyzerClass) {
      throw new Error(`Unknown analyzer: ${name}`);
    }

    return new AnalyzerClass(config);
  }

  static getAvailableAnalyzers(): string[] {
    return Array.from(this.ANALYZERS.keys());
  }

  static registerAnalyzer(
    name: string,
    analyzerClass: new (config: Record<string, unknown>) => Analyzer,
  ): void {
    this.ANALYZERS.set(name, analyzerClass);
  }
}

export { ASTAnalyzer, PerformanceAnalyzer, SecurityAnalyzer };
export type { Analyzer };
