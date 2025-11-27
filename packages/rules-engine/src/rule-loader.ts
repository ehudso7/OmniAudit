import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import type { Rule } from './types';
import { RuleSchema } from './types';
import micromatch from 'micromatch';

/**
 * RuleLoader - Loads and manages rules from YAML files
 */
export class RuleLoader {
  private loadedRules: Map<string, Rule> = new Map();
  private ruleFiles: Map<string, string> = new Map();

  /**
   * Load a single rule file
   */
  async loadFile(filePath: string): Promise<Rule[]> {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const data = yaml.load(content);

      // Handle both single rule and array of rules
      const rules = Array.isArray(data) ? data : [data];
      const validRules: Rule[] = [];

      for (const ruleData of rules) {
        try {
          const rule = RuleSchema.parse(ruleData);
          this.loadedRules.set(rule.id, rule);
          this.ruleFiles.set(rule.id, filePath);
          validRules.push(rule);
        } catch (error) {
          console.error(`Error parsing rule in ${filePath}:`, error);
        }
      }

      return validRules;
    } catch (error) {
      console.error(`Error loading rule file ${filePath}:`, error);
      return [];
    }
  }

  /**
   * Load all rules from a directory
   */
  async loadDirectory(dirPath: string, recursive = true): Promise<Rule[]> {
    const rules: Rule[] = [];

    try {
      const files = fs.readdirSync(dirPath);

      for (const file of files) {
        const filePath = path.join(dirPath, file);
        const stat = fs.statSync(filePath);

        if (stat.isDirectory() && recursive) {
          const dirRules = await this.loadDirectory(filePath, recursive);
          rules.push(...dirRules);
        } else if (stat.isFile() && (file.endsWith('.yaml') || file.endsWith('.yml'))) {
          const fileRules = await this.loadFile(filePath);
          rules.push(...fileRules);
        }
      }
    } catch (error) {
      console.error(`Error loading directory ${dirPath}:`, error);
    }

    return rules;
  }

  /**
   * Load multiple rule paths
   */
  async loadPaths(paths: string[]): Promise<Rule[]> {
    const allRules: Rule[] = [];

    for (const rulePath of paths) {
      try {
        const stat = fs.statSync(rulePath);

        if (stat.isDirectory()) {
          const rules = await this.loadDirectory(rulePath);
          allRules.push(...rules);
        } else if (stat.isFile()) {
          const rules = await this.loadFile(rulePath);
          allRules.push(...rules);
        }
      } catch (error) {
        console.error(`Error loading path ${rulePath}:`, error);
      }
    }

    return allRules;
  }

  /**
   * Get a rule by ID
   */
  getRule(id: string): Rule | undefined {
    return this.loadedRules.get(id);
  }

  /**
   * Get all loaded rules
   */
  getAllRules(): Rule[] {
    return Array.from(this.loadedRules.values());
  }

  /**
   * Filter rules by criteria
   */
  filterRules(criteria: {
    categories?: string[];
    severities?: string[];
    languages?: string[];
    tags?: string[];
    ids?: string[];
    enabled?: boolean;
  }): Rule[] {
    let rules = this.getAllRules();

    if (criteria.categories) {
      rules = rules.filter(r => criteria.categories?.includes(r.category));
    }

    if (criteria.severities) {
      rules = rules.filter(r => criteria.severities?.includes(r.severity));
    }

    if (criteria.languages) {
      rules = rules.filter(r =>
        r.languages.some(lang => criteria.languages?.includes(lang))
      );
    }

    if (criteria.tags) {
      rules = rules.filter(r =>
        r.tags?.some(tag => criteria.tags?.includes(tag))
      );
    }

    if (criteria.ids) {
      rules = rules.filter(r => criteria.ids?.includes(r.id));
    }

    if (criteria.enabled !== undefined) {
      rules = rules.filter(r => r.enabled === criteria.enabled);
    }

    return rules;
  }

  /**
   * Check if a file matches rule conditions
   */
  fileMatchesConditions(filePath: string, rule: Rule): boolean {
    if (!rule.conditions) {
      return true;
    }

    // Check fileMatch patterns
    if (rule.conditions.fileMatch) {
      const matches = micromatch.isMatch(filePath, rule.conditions.fileMatch);
      if (!matches) return false;
    }

    // Check fileExclude patterns
    if (rule.conditions.fileExclude) {
      const excluded = micromatch.isMatch(filePath, rule.conditions.fileExclude);
      if (excluded) return false;
    }

    return true;
  }

  /**
   * Get rules applicable to a file
   */
  getRulesForFile(filePath: string, language?: string): Rule[] {
    let rules = this.getAllRules();

    // Filter by language
    if (language) {
      rules = rules.filter(r => r.languages.includes(language));
    }

    // Filter by file conditions
    rules = rules.filter(r => this.fileMatchesConditions(filePath, r));

    // Filter enabled rules only
    rules = rules.filter(r => r.enabled !== false);

    return rules;
  }

  /**
   * Get statistics about loaded rules
   */
  getStats(): {
    total: number;
    byCategory: Record<string, number>;
    bySeverity: Record<string, number>;
    byLanguage: Record<string, number>;
  } {
    const rules = this.getAllRules();

    const stats = {
      total: rules.length,
      byCategory: {} as Record<string, number>,
      bySeverity: {} as Record<string, number>,
      byLanguage: {} as Record<string, number>,
    };

    for (const rule of rules) {
      // Count by category
      stats.byCategory[rule.category] = (stats.byCategory[rule.category] || 0) + 1;

      // Count by severity
      stats.bySeverity[rule.severity] = (stats.bySeverity[rule.severity] || 0) + 1;

      // Count by language
      for (const lang of rule.languages) {
        stats.byLanguage[lang] = (stats.byLanguage[lang] || 0) + 1;
      }
    }

    return stats;
  }

  /**
   * Clear all loaded rules
   */
  clear(): void {
    this.loadedRules.clear();
    this.ruleFiles.clear();
  }
}

export const ruleLoader = new RuleLoader();
