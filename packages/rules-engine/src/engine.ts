import type { Rule, Match, EngineOptions, EngineResult, FileToAnalyze } from './types';
import { regexMatcher } from './matchers/regex-matcher';
import { astMatcher } from './matchers/ast-matcher';
import { patternMatcher } from './matchers/pattern-matcher';
import { RuleLoader } from './rule-loader';
import { RuleValidator } from './rule-validator';

/**
 * RulesEngine - Main engine for executing rules against code
 */
export class RulesEngine {
  private loader: RuleLoader;
  private validator: RuleValidator;
  private rules: Rule[];
  private options: EngineOptions;

  constructor(options?: Partial<EngineOptions>) {
    this.loader = new RuleLoader();
    this.validator = new RuleValidator();
    this.rules = options?.rules || [];
    this.options = {
      rules: this.rules,
      parallelism: options?.parallelism || 4,
      timeout: options?.timeout || 30000,
      cache: options?.cache !== false,
      cacheDir: options?.cacheDir || '.omniaudit-cache',
    };
  }

  /**
   * Load rules from paths
   */
  async loadRules(paths: string[]): Promise<void> {
    const loadedRules = await this.loader.loadPaths(paths);
    this.rules = [...this.rules, ...loadedRules];
    this.options.rules = this.rules;
  }

  /**
   * Add rules programmatically
   */
  addRules(rules: Rule[]): void {
    this.rules = [...this.rules, ...rules];
    this.options.rules = this.rules;
  }

  /**
   * Get all loaded rules
   */
  getRules(): Rule[] {
    return this.rules;
  }

  /**
   * Validate all rules
   */
  validateRules(): Map<string, any> {
    return this.validator.validateBatch(this.rules);
  }

  /**
   * Analyze a single file
   */
  async analyzeFile(file: FileToAnalyze): Promise<Match[]> {
    const applicableRules = this.loader.getRulesForFile(file.path, file.language);
    const allMatches: Match[] = [];

    for (const rule of applicableRules) {
      try {
        const matches = this.executeRule(file, rule);
        allMatches.push(...matches);
      } catch (error) {
        console.error(`Error executing rule ${rule.id} on ${file.path}:`, error);
      }
    }

    return allMatches;
  }

  /**
   * Analyze multiple files
   */
  async analyzeFiles(files: FileToAnalyze[]): Promise<EngineResult> {
    const startTime = Date.now();
    const allMatches: Match[] = [];
    const errors: Array<{ rule: string; file: string; error: string }> = [];

    // Process files in batches for parallelism
    const batchSize = this.options.parallelism || 4;
    for (let i = 0; i < files.length; i += batchSize) {
      const batch = files.slice(i, i + batchSize);
      const batchPromises = batch.map(file => this.analyzeFile(file));

      try {
        const batchResults = await Promise.all(batchPromises);
        for (const matches of batchResults) {
          allMatches.push(...matches);
        }
      } catch (error: any) {
        errors.push({
          rule: 'unknown',
          file: 'batch',
          error: error.message,
        });
      }
    }

    const endTime = Date.now();

    return {
      matches: allMatches,
      errors,
      stats: {
        filesAnalyzed: files.length,
        rulesExecuted: this.rules.length,
        matchesFound: allMatches.length,
        timeMs: endTime - startTime,
      },
    };
  }

  /**
   * Execute a single rule against a file
   */
  private executeRule(file: FileToAnalyze, rule: Rule): Match[] {
    const patterns = rule.patterns as any;

    // Determine which matcher to use
    if (patterns.regex) {
      return regexMatcher.match(file.content, rule, file);
    }

    if (patterns.ast) {
      // Only use AST matcher for supported languages
      const astLanguages = ['javascript', 'typescript', 'jsx', 'tsx'];
      if (file.language && astLanguages.includes(file.language)) {
        return astMatcher.match(file.content, rule, file);
      }
      return [];
    }

    if (patterns.pattern || patterns.patterns || patterns.pattern_either) {
      return patternMatcher.match(file.content, rule, file);
    }

    return [];
  }

  /**
   * Get rule statistics
   */
  getStats(): {
    total: number;
    byCategory: Record<string, number>;
    bySeverity: Record<string, number>;
    byLanguage: Record<string, number>;
  } {
    return this.loader.getStats();
  }

  /**
   * Filter rules
   */
  filterRules(criteria: {
    categories?: string[];
    severities?: string[];
    languages?: string[];
    tags?: string[];
    ids?: string[];
    enabled?: boolean;
  }): Rule[] {
    return this.loader.filterRules(criteria);
  }

  /**
   * Clear all rules and cache
   */
  clear(): void {
    this.rules = [];
    this.loader.clear();
    regexMatcher.clearCache();
  }

  /**
   * Benchmark rule execution
   */
  async benchmark(file: FileToAnalyze, iterations = 100): Promise<{
    totalMs: number;
    avgMs: number;
    rulesPerSecond: number;
    matchesFound: number;
  }> {
    const startTime = Date.now();
    let totalMatches = 0;

    for (let i = 0; i < iterations; i++) {
      const matches = await this.analyzeFile(file);
      totalMatches += matches.length;
    }

    const endTime = Date.now();
    const totalMs = endTime - startTime;
    const avgMs = totalMs / iterations;
    const rulesPerSecond = (this.rules.length * iterations) / (totalMs / 1000);

    return {
      totalMs,
      avgMs,
      rulesPerSecond: Math.round(rulesPerSecond),
      matchesFound: totalMatches / iterations,
    };
  }
}

export const createEngine = (options?: Partial<EngineOptions>): RulesEngine => {
  return new RulesEngine(options);
};
