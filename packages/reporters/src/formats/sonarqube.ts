import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

// SonarQube Generic Issue Import Format
// https://docs.sonarqube.org/latest/analyzing-source-code/importing-external-issues/generic-issue-import-format/

interface SonarQubeIssue {
  engineId: string;
  ruleId: string;
  severity: 'BLOCKER' | 'CRITICAL' | 'MAJOR' | 'MINOR' | 'INFO';
  type: 'BUG' | 'VULNERABILITY' | 'CODE_SMELL';
  primaryLocation: {
    message: string;
    filePath: string;
    textRange?: {
      startLine: number;
      endLine?: number;
      startColumn?: number;
      endColumn?: number;
    };
  };
  secondaryLocations?: Array<{
    message: string;
    filePath: string;
    textRange?: {
      startLine: number;
      endLine?: number;
    };
  }>;
  effortMinutes?: number;
}

interface SonarQubeReport {
  issues: SonarQubeIssue[];
}

export class SonarQubeReporter implements Reporter {
  name = 'SonarQube Reporter';
  format = 'sonarqube';

  private severityToSonarQube(severity: Severity): 'BLOCKER' | 'CRITICAL' | 'MAJOR' | 'MINOR' | 'INFO' {
    const mapping: Record<Severity, 'BLOCKER' | 'CRITICAL' | 'MAJOR' | 'MINOR' | 'INFO'> = {
      critical: 'BLOCKER',
      high: 'CRITICAL',
      medium: 'MAJOR',
      low: 'MINOR',
      info: 'INFO',
    };
    return mapping[severity];
  }

  private categoryToType(category: string): 'BUG' | 'VULNERABILITY' | 'CODE_SMELL' {
    if (category === 'security') return 'VULNERABILITY';
    if (category === 'performance') return 'CODE_SMELL';
    return 'CODE_SMELL';
  }

  private findingToSonarQubeIssue(finding: Finding): SonarQubeIssue {
    const issue: SonarQubeIssue = {
      engineId: 'omniaudit',
      ruleId: finding.rule_id,
      severity: this.severityToSonarQube(finding.severity),
      type: this.categoryToType(finding.category),
      primaryLocation: {
        message: finding.message,
        filePath: finding.file,
      },
    };

    if (finding.line) {
      issue.primaryLocation.textRange = {
        startLine: finding.line,
        ...(finding.end_line && { endLine: finding.end_line }),
        ...(finding.column !== undefined && { startColumn: finding.column }),
        ...(finding.end_column !== undefined && { endColumn: finding.end_column }),
      };
    }

    // Estimate effort based on severity
    const effortMap: Record<Severity, number> = {
      critical: 120,
      high: 60,
      medium: 30,
      low: 15,
      info: 5,
    };
    issue.effortMinutes = effortMap[finding.severity];

    return issue;
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const report: SonarQubeReport = {
      issues: result.findings.map(f => this.findingToSonarQubeIssue(f)),
    };

    return options?.pretty
      ? JSON.stringify(report, null, 2)
      : JSON.stringify(report);
  }
}
