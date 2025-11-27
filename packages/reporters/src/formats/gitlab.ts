import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

// GitLab Code Quality Report format
// https://docs.gitlab.com/ee/ci/testing/code_quality.html

interface GitLabCodeQualityIssue {
  description: string;
  check_name: string;
  fingerprint: string;
  severity: 'info' | 'minor' | 'major' | 'critical' | 'blocker';
  location: {
    path: string;
    lines?: {
      begin: number;
      end?: number;
    };
  };
  categories?: string[];
}

export class GitLabReporter implements Reporter {
  name = 'GitLab Code Quality Reporter';
  format = 'gitlab';

  private severityToGitLab(severity: Severity): 'info' | 'minor' | 'major' | 'critical' | 'blocker' {
    const mapping: Record<Severity, 'info' | 'minor' | 'major' | 'critical' | 'blocker'> = {
      critical: 'blocker',
      high: 'critical',
      medium: 'major',
      low: 'minor',
      info: 'info',
    };
    return mapping[severity];
  }

  private generateFingerprint(finding: Finding): string {
    // Include end_line for better deduplication of multi-line findings
    const data = `${finding.rule_id}:${finding.file}:${finding.line || 0}:${finding.end_line || 0}`;
    // Use a better hash algorithm (djb2) for reduced collisions
    let hash = 5381;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) + hash) + char; // hash * 33 + char
      hash = hash & 0x7fffffff; // Keep it 31-bit positive
    }
    return hash.toString(16).padStart(8, '0');
  }

  private findingToGitLabIssue(finding: Finding): GitLabCodeQualityIssue {
    const issue: GitLabCodeQualityIssue = {
      description: finding.message,
      check_name: finding.rule_id,
      fingerprint: this.generateFingerprint(finding),
      severity: this.severityToGitLab(finding.severity),
      location: {
        path: finding.file,
      },
      categories: [finding.category],
    };

    if (finding.line) {
      issue.location.lines = {
        begin: finding.line,
        ...(finding.end_line && { end: finding.end_line }),
      };
    }

    return issue;
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const issues = result.findings.map(f => this.findingToGitLabIssue(f));

    return options?.pretty
      ? JSON.stringify(issues, null, 2)
      : JSON.stringify(issues);
  }
}
