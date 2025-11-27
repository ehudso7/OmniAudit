import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

// GitHub Code Scanning format (SARIF-like but simplified for annotations)
// https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning

interface GitHubAnnotation {
  path: string;
  start_line: number;
  end_line: number;
  annotation_level: 'notice' | 'warning' | 'failure';
  message: string;
  title: string;
  raw_details?: string;
}

export class GitHubReporter implements Reporter {
  name = 'GitHub Actions Reporter';
  format = 'github';

  private severityToGitHub(severity: Severity): 'notice' | 'warning' | 'failure' {
    const mapping: Record<Severity, 'notice' | 'warning' | 'failure'> = {
      critical: 'failure',
      high: 'failure',
      medium: 'warning',
      low: 'warning',
      info: 'notice',
    };
    return mapping[severity];
  }

  private findingToAnnotation(finding: Finding): GitHubAnnotation {
    return {
      path: finding.file,
      start_line: finding.line || 1,
      end_line: finding.end_line || finding.line || 1,
      annotation_level: this.severityToGitHub(finding.severity),
      message: finding.message,
      title: `[${finding.severity.toUpperCase()}] ${finding.title}`,
      raw_details: finding.recommendation || finding.description,
    };
  }

  /**
   * Escape special characters for GitHub Actions annotation format
   * See: https://github.com/actions/toolkit/issues/193
   */
  private escapeAnnotationValue(value: string): string {
    return value
      .replace(/%/g, '%25')
      .replace(/\r/g, '%0D')
      .replace(/\n/g, '%0A')
      .replace(/:/g, '%3A')
      .replace(/,/g, '%2C');
  }

  private formatAsGitHubCommand(finding: Finding): string {
    const level = this.severityToGitHub(finding.severity);
    const file = finding.file;
    const line = finding.line || 1;
    const col = finding.column || 1;
    const endLine = finding.end_line || line;
    const endCol = finding.end_column || col;

    // Escape title and message to prevent format issues
    const title = this.escapeAnnotationValue(finding.title);
    const message = this.escapeAnnotationValue(finding.message);

    const props = `file=${file},line=${line},col=${col},endLine=${endLine},endColumn=${endCol},title=${title}`;
    return `::${level} ${props}::${message}`;
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    if (options?.format === 'annotations') {
      // GitHub Actions annotation format
      const commands = result.findings.map(f => this.formatAsGitHubCommand(f));
      return commands.join('\n');
    }

    // JSON format for GitHub Code Scanning
    const annotations = result.findings.map(f => this.findingToAnnotation(f));

    const output = {
      title: 'OmniAudit Code Analysis',
      summary: `Found ${result.total_findings} issues across ${result.total_files} files`,
      annotations,
      text: `## Summary\n\n` +
        `- Critical: ${result.findings_by_severity.critical}\n` +
        `- High: ${result.findings_by_severity.high}\n` +
        `- Medium: ${result.findings_by_severity.medium}\n` +
        `- Low: ${result.findings_by_severity.low}\n` +
        `- Info: ${result.findings_by_severity.info}\n`,
    };

    return options?.pretty
      ? JSON.stringify(output, null, 2)
      : JSON.stringify(output);
  }
}
