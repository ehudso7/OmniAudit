import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

// Linear issue creation format
// https://developers.linear.app/docs/graphql/working-with-the-graphql-api

interface LinearIssue {
  title: string;
  description: string;
  priority: 0 | 1 | 2 | 3 | 4;
  labelIds?: string[];
  teamId?: string;
}

export class LinearReporter implements Reporter {
  name = 'Linear Reporter';
  format = 'linear';

  private severityToPriority(severity: Severity): 0 | 1 | 2 | 3 | 4 {
    const mapping: Record<Severity, 0 | 1 | 2 | 3 | 4> = {
      critical: 0, // Urgent
      high: 1,     // High
      medium: 2,   // Medium
      low: 3,      // Low
      info: 4,     // No priority
    };
    return mapping[severity];
  }

  private findingToLinearIssue(finding: Finding): LinearIssue {
    const location = finding.line
      ? `${finding.file}:${finding.line}`
      : finding.file;

    let description = `## ${finding.message}\n\n`;
    description += `**Location:** \`${location}\`\n`;
    description += `**Category:** ${finding.category}\n`;
    description += `**Rule:** ${finding.rule_id}\n\n`;

    if (finding.description) {
      description += `### Description\n${finding.description}\n\n`;
    }

    if (finding.code_snippet) {
      description += `### Code\n\`\`\`\n${finding.code_snippet}\n\`\`\`\n\n`;
    }

    if (finding.recommendation) {
      description += `### Recommendation\n${finding.recommendation}\n\n`;
    }

    if (finding.cwe && finding.cwe.length > 0) {
      description += `**CWE:** ${finding.cwe.join(', ')}\n`;
    }

    if (finding.owasp && finding.owasp.length > 0) {
      description += `**OWASP:** ${finding.owasp.join(', ')}\n`;
    }

    return {
      title: `[${finding.severity.toUpperCase()}] ${finding.title}`,
      description,
      priority: this.severityToPriority(finding.severity),
    };
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const issues = result.findings.map(f => this.findingToLinearIssue(f));

    const output = {
      teamId: options?.template || 'TEAM_ID', // Would be replaced with actual team ID
      issues,
      metadata: {
        source: 'omniaudit',
        project: result.project,
        timestamp: result.timestamp,
        totalFindings: result.total_findings,
      },
    };

    return options?.pretty
      ? JSON.stringify(output, null, 2)
      : JSON.stringify(output);
  }
}
