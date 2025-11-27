import type { AuditResult, Reporter, ReporterOptions } from '../types.js';

// Slack Block Kit format
// https://api.slack.com/block-kit

export class SlackReporter implements Reporter {
  name = 'Slack Reporter';
  format = 'slack';

  private getSeverityEmoji(severity: string): string {
    const emojis: Record<string, string> = {
      critical: ':red_circle:',
      high: ':orange_circle:',
      medium: ':yellow_circle:',
      low: ':large_blue_circle:',
      info: ':white_circle:',
    };
    return emojis[severity] || ':white_circle:';
  }

  private getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
      critical: '#dc2626',
      high: '#ea580c',
      medium: '#f59e0b',
      low: '#3b82f6',
      info: '#6b7280',
    };
    return colors[severity] || '#6b7280';
  }

  async generate(result: AuditResult, _options?: ReporterOptions): Promise<string> {
    const totalIssues = result.total_findings;
    const criticalCount = result.findings_by_severity.critical;
    const highCount = result.findings_by_severity.high;

    const color = criticalCount > 0 ? this.getSeverityColor('critical') :
                  highCount > 0 ? this.getSeverityColor('high') :
                  this.getSeverityColor('medium');

    const attachment = {
      color,
      blocks: [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: '🔍 OmniAudit Report',
            emoji: true,
          },
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*Project:*\n${result.project}`,
            },
            {
              type: 'mrkdwn',
              text: `*Total Issues:*\n${totalIssues}`,
            },
            {
              type: 'mrkdwn',
              text: `*Files Analyzed:*\n${result.total_files}`,
            },
            {
              type: 'mrkdwn',
              text: `*Duration:*\n${(result.duration_ms / 1000).toFixed(2)}s`,
            },
          ],
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: '*Findings by Severity:*',
          },
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `${this.getSeverityEmoji('critical')} *Critical:* ${result.findings_by_severity.critical}`,
            },
            {
              type: 'mrkdwn',
              text: `${this.getSeverityEmoji('high')} *High:* ${result.findings_by_severity.high}`,
            },
            {
              type: 'mrkdwn',
              text: `${this.getSeverityEmoji('medium')} *Medium:* ${result.findings_by_severity.medium}`,
            },
            {
              type: 'mrkdwn',
              text: `${this.getSeverityEmoji('low')} *Low:* ${result.findings_by_severity.low}`,
            },
          ],
        },
        {
          type: 'divider',
        },
      ],
    };

    // Add top 5 critical/high findings
    const criticalFindings = result.findings
      .filter(f => f.severity === 'critical' || f.severity === 'high')
      .slice(0, 5);

    if (criticalFindings.length > 0) {
      attachment.blocks.push({
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: '*Top Critical/High Issues:*',
        },
      });

      for (const finding of criticalFindings) {
        attachment.blocks.push({
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `${this.getSeverityEmoji(finding.severity)} *${finding.title}*\n` +
                  `\`${finding.file}\`${finding.line ? `:${finding.line}` : ''}\n` +
                  `_${finding.message}_`,
          },
        });
      }
    }

    const message = {
      text: `OmniAudit found ${totalIssues} issues in ${result.project}`,
      attachments: [attachment],
    };

    return JSON.stringify(message, null, 2);
  }
}
