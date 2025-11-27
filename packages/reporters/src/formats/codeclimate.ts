import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

// Code Climate Issue Data Format
// https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md

interface CodeClimateIssue {
  type: 'issue';
  check_name: string;
  description: string;
  content?: {
    body: string;
  };
  categories: string[];
  location: {
    path: string;
    lines?: {
      begin: number;
      end: number;
    };
    positions?: {
      begin: {
        line: number;
        column: number;
      };
      end: {
        line: number;
        column: number;
      };
    };
  };
  severity: 'info' | 'minor' | 'major' | 'critical' | 'blocker';
  fingerprint: string;
}

export class CodeClimateReporter implements Reporter {
  name = 'Code Climate Reporter';
  format = 'codeclimate';

  private severityToCodeClimate(severity: Severity): 'info' | 'minor' | 'major' | 'critical' | 'blocker' {
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
    const data = `${finding.rule_id}:${finding.file}:${finding.line || 0}:${finding.message}`;
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(16, '0');
  }

  private categoryToCodeClimate(category: string): string[] {
    const mapping: Record<string, string[]> = {
      security: ['Security'],
      performance: ['Performance'],
      accessibility: ['Accessibility'],
      'best-practices': ['Style'],
      maintainability: ['Complexity', 'Duplication'],
      'code-quality': ['Bug Risk'],
    };
    return mapping[category] || ['Style'];
  }

  private findingToCodeClimateIssue(finding: Finding): CodeClimateIssue {
    const issue: CodeClimateIssue = {
      type: 'issue',
      check_name: finding.rule_id,
      description: finding.title,
      categories: this.categoryToCodeClimate(finding.category),
      location: {
        path: finding.file,
      },
      severity: this.severityToCodeClimate(finding.severity),
      fingerprint: this.generateFingerprint(finding),
    };

    if (finding.recommendation || finding.description) {
      issue.content = {
        body: finding.recommendation || finding.description || '',
      };
    }

    if (finding.line && finding.column !== undefined) {
      issue.location.positions = {
        begin: {
          line: finding.line,
          column: finding.column,
        },
        end: {
          line: finding.end_line || finding.line,
          column: finding.end_column || finding.column,
        },
      };
    } else if (finding.line) {
      issue.location.lines = {
        begin: finding.line,
        end: finding.end_line || finding.line,
      };
    }

    return issue;
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const issues = result.findings.map(f => this.findingToCodeClimateIssue(f));

    // Code Climate expects newline-delimited JSON
    if (options?.format === 'ndjson') {
      return issues.map(issue => JSON.stringify(issue)).join('\n');
    }

    // Return as JSON array
    return options?.pretty
      ? JSON.stringify(issues, null, 2)
      : JSON.stringify(issues);
  }
}
