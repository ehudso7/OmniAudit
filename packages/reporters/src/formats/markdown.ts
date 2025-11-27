import type { AuditResult, Reporter, ReporterOptions, Finding } from '../types.js';

export class MarkdownReporter implements Reporter {
  name = 'Markdown Reporter';
  format = 'markdown';

  private formatFinding(finding: Finding, index: number): string {
    const emoji = this.getSeverityEmoji(finding.severity);
    const location = finding.line
      ? `${finding.file}:${finding.line}${finding.column ? `:${finding.column}` : ''}`
      : finding.file;

    let md = `### ${emoji} ${index + 1}. ${finding.title}\n\n`;
    md += `**Severity:** ${finding.severity.toUpperCase()} | `;
    md += `**Category:** ${finding.category}\n\n`;
    md += `**Location:** \`${location}\`\n\n`;
    md += `**Message:** ${finding.message}\n\n`;

    if (finding.description) {
      md += `**Description:**\n${finding.description}\n\n`;
    }

    if (finding.code_snippet) {
      md += `**Code:**\n\`\`\`\n${finding.code_snippet}\n\`\`\`\n\n`;
    }

    if (finding.recommendation) {
      md += `**Recommendation:**\n${finding.recommendation}\n\n`;
    }

    if (finding.cwe && finding.cwe.length > 0) {
      md += `**CWE:** ${finding.cwe.join(', ')}\n\n`;
    }

    if (finding.owasp && finding.owasp.length > 0) {
      md += `**OWASP:** ${finding.owasp.join(', ')}\n\n`;
    }

    md += '---\n\n';
    return md;
  }

  private getSeverityEmoji(severity: string): string {
    const emojis: Record<string, string> = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🔵',
      info: '⚪',
    };
    return emojis[severity] || '⚪';
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    let md = `# OmniAudit Report\n\n`;
    md += `**Project:** ${result.project}\n\n`;
    md += `**Generated:** ${new Date(result.timestamp).toLocaleString()}\n\n`;
    md += `**Duration:** ${(result.duration_ms / 1000).toFixed(2)}s\n\n`;

    // Summary
    md += `## Summary\n\n`;
    md += `- **Total Files Analyzed:** ${result.total_files}\n`;
    md += `- **Total Findings:** ${result.total_findings}\n\n`;

    // Findings by Severity
    md += `### Findings by Severity\n\n`;
    md += `| Severity | Count |\n`;
    md += `|----------|-------|\n`;
    md += `| 🔴 Critical | ${result.findings_by_severity.critical} |\n`;
    md += `| 🟠 High | ${result.findings_by_severity.high} |\n`;
    md += `| 🟡 Medium | ${result.findings_by_severity.medium} |\n`;
    md += `| 🔵 Low | ${result.findings_by_severity.low} |\n`;
    md += `| ⚪ Info | ${result.findings_by_severity.info} |\n\n`;

    // Detailed Findings
    if (result.findings.length > 0) {
      md += `## Detailed Findings\n\n`;

      // Group by severity
      const bySeverity = {
        critical: result.findings.filter(f => f.severity === 'critical'),
        high: result.findings.filter(f => f.severity === 'high'),
        medium: result.findings.filter(f => f.severity === 'medium'),
        low: result.findings.filter(f => f.severity === 'low'),
        info: result.findings.filter(f => f.severity === 'info'),
      };

      let findingIndex = 0;
      for (const [severity, findings] of Object.entries(bySeverity)) {
        if (findings.length > 0) {
          md += `## ${severity.charAt(0).toUpperCase() + severity.slice(1)} Severity\n\n`;
          for (const finding of findings) {
            md += this.formatFinding(finding, findingIndex++);
          }
        }
      }
    } else {
      md += `## No Findings\n\n✅ Great job! No issues were found.\n\n`;
    }

    if (options?.includeMetadata !== false && result.metadata) {
      md += `## Metadata\n\n`;
      md += `- **Version:** ${result.metadata.version}\n`;
      md += `- **Rules:** ${result.metadata.rules_count}\n`;
      md += `- **Analyzers:** ${result.metadata.analyzers.join(', ')}\n`;
    }

    return md;
  }
}
