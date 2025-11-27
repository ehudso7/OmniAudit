// Export types
export * from './types.js';

// Export all reporter formats
export { JSONReporter } from './formats/json.js';
export { SARIFReporter } from './formats/sarif.js';
export { MarkdownReporter } from './formats/markdown.js';
export { HTMLReporter } from './formats/html.js';
export { PDFReporter } from './formats/pdf.js';
export { JUnitReporter } from './formats/junit.js';
export { CheckstyleReporter } from './formats/checkstyle.js';
export { GitLabReporter } from './formats/gitlab.js';
export { GitHubReporter } from './formats/github.js';
export { SonarQubeReporter } from './formats/sonarqube.js';
export { CodeClimateReporter } from './formats/codeclimate.js';
export { CSVReporter } from './formats/csv.js';
export { SlackReporter } from './formats/slack.js';
export { JIRAReporter } from './formats/jira.js';
export { LinearReporter } from './formats/linear.js';
export { NotionReporter } from './formats/notion.js';

import { JSONReporter } from './formats/json.js';
import { SARIFReporter } from './formats/sarif.js';
import { MarkdownReporter } from './formats/markdown.js';
import { HTMLReporter } from './formats/html.js';
import { PDFReporter } from './formats/pdf.js';
import { JUnitReporter } from './formats/junit.js';
import { CheckstyleReporter } from './formats/checkstyle.js';
import { GitLabReporter } from './formats/gitlab.js';
import { GitHubReporter } from './formats/github.js';
import { SonarQubeReporter } from './formats/sonarqube.js';
import { CodeClimateReporter } from './formats/codeclimate.js';
import { CSVReporter } from './formats/csv.js';
import { SlackReporter } from './formats/slack.js';
import { JIRAReporter } from './formats/jira.js';
import { LinearReporter } from './formats/linear.js';
import { NotionReporter } from './formats/notion.js';

import type { Reporter, AuditResult, ReporterOptions } from './types.js';

/**
 * Registry of all available reporters
 */
export const REPORTERS = {
  json: new JSONReporter(),
  sarif: new SARIFReporter(),
  markdown: new MarkdownReporter(),
  html: new HTMLReporter(),
  pdf: new PDFReporter(),
  junit: new JUnitReporter(),
  checkstyle: new CheckstyleReporter(),
  gitlab: new GitLabReporter(),
  github: new GitHubReporter(),
  sonarqube: new SonarQubeReporter(),
  codeclimate: new CodeClimateReporter(),
  csv: new CSVReporter(),
  slack: new SlackReporter(),
  jira: new JIRAReporter(),
  linear: new LinearReporter(),
  notion: new NotionReporter(),
} as const;

export type ReporterFormat = keyof typeof REPORTERS;

/**
 * Get a reporter by format
 */
export function getReporter(format: ReporterFormat): Reporter {
  const reporter = REPORTERS[format];
  if (!reporter) {
    throw new Error(`Unknown reporter format: ${format}`);
  }
  return reporter;
}

/**
 * Generate a report in the specified format
 */
export async function generateReport(
  result: AuditResult,
  format: ReporterFormat = 'json',
  options?: ReporterOptions
): Promise<string> {
  const reporter = getReporter(format);
  return reporter.generate(result, options);
}

/**
 * Get list of all available formats
 */
export function getAvailableFormats(): ReporterFormat[] {
  return Object.keys(REPORTERS) as ReporterFormat[];
}

/**
 * Main ReporterManager class for managing multiple reporters
 */
export class ReporterManager {
  private reporters: Map<string, Reporter>;

  constructor() {
    this.reporters = new Map(Object.entries(REPORTERS));
  }

  /**
   * Register a custom reporter
   */
  register(format: string, reporter: Reporter): void {
    this.reporters.set(format, reporter);
  }

  /**
   * Get a reporter by format
   */
  get(format: string): Reporter | undefined {
    return this.reporters.get(format);
  }

  /**
   * Generate report using the specified format
   */
  async generate(
    result: AuditResult,
    format: string,
    options?: ReporterOptions
  ): Promise<string> {
    const reporter = this.reporters.get(format);
    if (!reporter) {
      throw new Error(`Reporter not found: ${format}`);
    }
    return reporter.generate(result, options);
  }

  /**
   * Generate reports in multiple formats
   */
  async generateMultiple(
    result: AuditResult,
    formats: string[],
    options?: ReporterOptions
  ): Promise<Map<string, string>> {
    const reports = new Map<string, string>();

    await Promise.all(
      formats.map(async (format) => {
        try {
          const report = await this.generate(result, format, options);
          reports.set(format, report);
        } catch (error) {
          console.error(`Failed to generate ${format} report:`, error);
          throw error;
        }
      })
    );

    return reports;
  }

  /**
   * Get all available formats
   */
  getFormats(): string[] {
    return Array.from(this.reporters.keys());
  }
}

// Export singleton instance
export const reporterManager = new ReporterManager();
