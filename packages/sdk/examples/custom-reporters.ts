/**
 * Custom Reporters Example
 *
 * Demonstrates how to create custom output formats for audit results.
 */

import { createClient } from '@omniaudit/sdk';
import type { AuditResult, Finding } from '@omniaudit/sdk';

// Reporter interface
interface Reporter {
  name: string;
  description: string;
  generate(result: AuditResult): string;
}

// Markdown Reporter
const markdownReporter: Reporter = {
  name: 'markdown',
  description: 'Generate a Markdown report',

  generate(result: AuditResult): string {
    const lines: string[] = [];

    lines.push(`# OmniAudit Report`);
    lines.push('');
    lines.push(`**Project:** ${result.project}`);
    lines.push(`**Date:** ${new Date(result.timestamp).toLocaleString()}`);
    lines.push(`**Duration:** ${result.duration_ms}ms`);
    lines.push(`**Files Analyzed:** ${result.total_files}`);
    lines.push('');

    // Summary table
    lines.push('## Summary');
    lines.push('');
    lines.push('| Severity | Count |');
    lines.push('|----------|-------|');
    lines.push(`| 🔴 Critical | ${result.findings_by_severity.critical} |`);
    lines.push(`| 🟠 High | ${result.findings_by_severity.high} |`);
    lines.push(`| 🟡 Medium | ${result.findings_by_severity.medium} |`);
    lines.push(`| 🔵 Low | ${result.findings_by_severity.low} |`);
    lines.push(`| ⚪ Info | ${result.findings_by_severity.info} |`);
    lines.push(`| **Total** | **${result.total_findings}** |`);
    lines.push('');

    // Findings by severity
    const severityOrder = ['critical', 'high', 'medium', 'low', 'info'] as const;

    for (const severity of severityOrder) {
      const findings = result.findings.filter((f) => f.severity === severity);
      if (findings.length === 0) continue;

      const emoji =
        severity === 'critical'
          ? '🔴'
          : severity === 'high'
            ? '🟠'
            : severity === 'medium'
              ? '🟡'
              : severity === 'low'
                ? '🔵'
                : '⚪';

      lines.push(`## ${emoji} ${severity.charAt(0).toUpperCase() + severity.slice(1)} Findings`);
      lines.push('');

      for (const finding of findings) {
        lines.push(`### ${finding.title}`);
        lines.push('');
        lines.push(`- **Rule:** \`${finding.rule_id}\``);
        lines.push(`- **File:** \`${finding.file}:${finding.line || 0}\``);
        lines.push(`- **Category:** ${finding.category}`);
        lines.push('');
        lines.push(finding.description);
        lines.push('');

        if (finding.code_snippet) {
          lines.push('```');
          lines.push(finding.code_snippet);
          lines.push('```');
          lines.push('');
        }

        if (finding.recommendation) {
          lines.push(`💡 **Recommendation:** ${finding.recommendation}`);
          lines.push('');
        }

        lines.push('---');
        lines.push('');
      }
    }

    return lines.join('\n');
  },
};

// HTML Reporter
const htmlReporter: Reporter = {
  name: 'html',
  description: 'Generate an HTML report',

  generate(result: AuditResult): string {
    const severityColor = (severity: string): string => {
      switch (severity) {
        case 'critical':
          return '#dc2626';
        case 'high':
          return '#ea580c';
        case 'medium':
          return '#eab308';
        case 'low':
          return '#3b82f6';
        default:
          return '#6b7280';
      }
    };

    const findingsHtml = result.findings
      .map(
        (f) => `
      <div class="finding" style="border-left: 4px solid ${severityColor(f.severity)}">
        <div class="finding-header">
          <span class="severity" style="background: ${severityColor(f.severity)}">${f.severity.toUpperCase()}</span>
          <span class="title">${escapeHtml(f.title)}</span>
        </div>
        <div class="finding-meta">
          <span class="rule">${escapeHtml(f.rule_id)}</span>
          <span class="location">${escapeHtml(f.file)}:${f.line || 0}</span>
        </div>
        <div class="finding-body">
          <p>${escapeHtml(f.description)}</p>
          ${f.code_snippet ? `<pre><code>${escapeHtml(f.code_snippet)}</code></pre>` : ''}
          ${f.recommendation ? `<div class="recommendation"><strong>Recommendation:</strong> ${escapeHtml(f.recommendation)}</div>` : ''}
        </div>
      </div>
    `
      )
      .join('\n');

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OmniAudit Report - ${escapeHtml(result.project)}</title>
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 2rem;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    header {
      background: var(--card-bg);
      border-radius: 12px;
      padding: 2rem;
      margin-bottom: 2rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    h1 { font-size: 1.875rem; margin-bottom: 1rem; }
    .meta { color: var(--text-muted); font-size: 0.875rem; }
    .stats {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 1rem;
      margin-top: 1.5rem;
    }
    .stat {
      text-align: center;
      padding: 1rem;
      border-radius: 8px;
    }
    .stat-value { font-size: 2rem; font-weight: bold; }
    .stat-label { font-size: 0.75rem; text-transform: uppercase; opacity: 0.8; }
    .finding {
      background: var(--card-bg);
      border-radius: 8px;
      padding: 1.25rem;
      margin-bottom: 1rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .finding-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
    .severity {
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      color: white;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .title { font-weight: 600; font-size: 1.125rem; }
    .finding-meta {
      display: flex;
      gap: 1rem;
      color: var(--text-muted);
      font-size: 0.875rem;
      margin-bottom: 0.75rem;
    }
    .rule { font-family: monospace; }
    .location { font-family: monospace; }
    .finding-body p { margin-bottom: 0.75rem; }
    pre {
      background: #1e293b;
      color: #e2e8f0;
      padding: 1rem;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 0.875rem;
      margin: 0.75rem 0;
    }
    .recommendation {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      padding: 0.75rem;
      border-radius: 6px;
      color: #1e40af;
    }
    footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.875rem;
      margin-top: 3rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>OmniAudit Report</h1>
      <div class="meta">
        <p><strong>Project:</strong> ${escapeHtml(result.project)}</p>
        <p><strong>Date:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
        <p><strong>Duration:</strong> ${result.duration_ms}ms | <strong>Files:</strong> ${result.total_files}</p>
      </div>
      <div class="stats">
        <div class="stat" style="background: #fee2e2; color: #dc2626;">
          <div class="stat-value">${result.findings_by_severity.critical}</div>
          <div class="stat-label">Critical</div>
        </div>
        <div class="stat" style="background: #fed7aa; color: #ea580c;">
          <div class="stat-value">${result.findings_by_severity.high}</div>
          <div class="stat-label">High</div>
        </div>
        <div class="stat" style="background: #fef08a; color: #a16207;">
          <div class="stat-value">${result.findings_by_severity.medium}</div>
          <div class="stat-label">Medium</div>
        </div>
        <div class="stat" style="background: #dbeafe; color: #3b82f6;">
          <div class="stat-value">${result.findings_by_severity.low}</div>
          <div class="stat-label">Low</div>
        </div>
        <div class="stat" style="background: #f1f5f9; color: #64748b;">
          <div class="stat-value">${result.findings_by_severity.info}</div>
          <div class="stat-label">Info</div>
        </div>
      </div>
    </header>

    <main>
      <h2 style="margin-bottom: 1rem;">Findings (${result.total_findings})</h2>
      ${findingsHtml}
    </main>

    <footer>
      <p>Generated by OmniAudit v${result.metadata?.version || '2.0.0'}</p>
    </footer>
  </div>
</body>
</html>`;
  },
};

// JUnit XML Reporter (for CI/CD)
const junitReporter: Reporter = {
  name: 'junit',
  description: 'Generate JUnit XML format for CI/CD integration',

  generate(result: AuditResult): string {
    const testCases = result.findings
      .map((f) => {
        const className = f.file.replace(/\//g, '.').replace(/\.[^.]+$/, '');
        const time = '0.001'; // Synthetic time

        if (f.severity === 'critical' || f.severity === 'high') {
          return `    <testcase classname="${escapeXml(className)}" name="${escapeXml(f.rule_id)}" time="${time}">
      <failure message="${escapeXml(f.title)}" type="${f.severity}">
${escapeXml(f.description)}

File: ${escapeXml(f.file)}:${f.line || 0}
${f.recommendation ? `\nRecommendation: ${escapeXml(f.recommendation)}` : ''}
      </failure>
    </testcase>`;
        }

        // Non-critical findings are treated as passed tests with warnings
        return `    <testcase classname="${escapeXml(className)}" name="${escapeXml(f.rule_id)}" time="${time}">
      <system-out>${escapeXml(f.message)}</system-out>
    </testcase>`;
      })
      .join('\n');

    const failures = result.findings.filter(
      (f) => f.severity === 'critical' || f.severity === 'high'
    ).length;

    return `<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="OmniAudit" tests="${result.total_findings}" failures="${failures}" time="${result.duration_ms / 1000}">
  <testsuite name="${escapeXml(result.project)}" tests="${result.total_findings}" failures="${failures}" timestamp="${result.timestamp}">
${testCases}
  </testsuite>
</testsuites>`;
  },
};

// Slack Reporter
const slackReporter: Reporter = {
  name: 'slack',
  description: 'Generate Slack Block Kit message',

  generate(result: AuditResult): string {
    const criticalHigh =
      result.findings_by_severity.critical + result.findings_by_severity.high;
    const statusEmoji = criticalHigh === 0 ? '✅' : criticalHigh > 5 ? '🚨' : '⚠️';

    const blocks = [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: `${statusEmoji} OmniAudit Report`,
          emoji: true,
        },
      },
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Project:*\n${result.project}` },
          { type: 'mrkdwn', text: `*Date:*\n${new Date(result.timestamp).toLocaleDateString()}` },
          { type: 'mrkdwn', text: `*Files:*\n${result.total_files}` },
          { type: 'mrkdwn', text: `*Duration:*\n${result.duration_ms}ms` },
        ],
      },
      { type: 'divider' },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Findings Summary*\n🔴 Critical: ${result.findings_by_severity.critical}  |  🟠 High: ${result.findings_by_severity.high}  |  🟡 Medium: ${result.findings_by_severity.medium}  |  🔵 Low: ${result.findings_by_severity.low}`,
        },
      },
    ];

    // Add top critical findings
    const criticalFindings = result.findings.filter((f) => f.severity === 'critical').slice(0, 3);

    if (criticalFindings.length > 0) {
      blocks.push({ type: 'divider' });
      blocks.push({
        type: 'section',
        text: {
          type: 'mrkdwn',
          text:
            '*🔴 Critical Issues*\n' +
            criticalFindings
              .map((f) => `• *${f.title}*\n  \`${f.file}:${f.line || 0}\``)
              .join('\n'),
        },
      });
    }

    return JSON.stringify({ blocks }, null, 2);
  },
};

// GitHub PR Comment Reporter
const githubCommentReporter: Reporter = {
  name: 'github-comment',
  description: 'Generate GitHub PR comment markdown',

  generate(result: AuditResult): string {
    const criticalHigh =
      result.findings_by_severity.critical + result.findings_by_severity.high;
    const statusIcon = criticalHigh === 0 ? '✅' : criticalHigh > 5 ? '❌' : '⚠️';

    let comment = `## ${statusIcon} OmniAudit Results\n\n`;

    comment += `| Metric | Value |\n`;
    comment += `|--------|-------|\n`;
    comment += `| Files Analyzed | ${result.total_files} |\n`;
    comment += `| Total Findings | ${result.total_findings} |\n`;
    comment += `| Critical | ${result.findings_by_severity.critical} |\n`;
    comment += `| High | ${result.findings_by_severity.high} |\n`;
    comment += `| Duration | ${result.duration_ms}ms |\n\n`;

    if (criticalHigh > 0) {
      comment += `<details>\n<summary>🔴 Critical & High Findings (${criticalHigh})</summary>\n\n`;

      const importantFindings = result.findings.filter(
        (f) => f.severity === 'critical' || f.severity === 'high'
      );

      for (const f of importantFindings.slice(0, 10)) {
        comment += `### ${f.title}\n`;
        comment += `- **Severity:** ${f.severity}\n`;
        comment += `- **Location:** \`${f.file}:${f.line || 0}\`\n`;
        comment += `- **Rule:** \`${f.rule_id}\`\n\n`;
        comment += `${f.description}\n\n`;
        if (f.recommendation) {
          comment += `💡 **Recommendation:** ${f.recommendation}\n\n`;
        }
        comment += `---\n\n`;
      }

      if (importantFindings.length > 10) {
        comment += `\n*...and ${importantFindings.length - 10} more critical/high findings*\n`;
      }

      comment += `</details>\n`;
    }

    comment += `\n---\n*Powered by [OmniAudit](https://omniaudit.dev)*`;

    return comment;
  },
};

// Helper functions
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// Reporter registry
const reporters = new Map<string, Reporter>([
  ['markdown', markdownReporter],
  ['html', htmlReporter],
  ['junit', junitReporter],
  ['slack', slackReporter],
  ['github-comment', githubCommentReporter],
]);

// Factory function
function createReporter(format: string): Reporter {
  const reporter = reporters.get(format);
  if (!reporter) {
    throw new Error(`Unknown reporter format: ${format}. Available: ${Array.from(reporters.keys()).join(', ')}`);
  }
  return reporter;
}

// Example usage
async function main() {
  const client = createClient({
    apiUrl: process.env.OMNIAUDIT_API_URL || 'http://localhost:8000',
    apiKey: process.env.OMNIAUDIT_API_KEY,
  });

  console.log('Running audit...');
  const result = await client.audit({ path: './src' });

  console.log('\nGenerating reports in different formats:\n');

  // Generate all formats
  for (const [name, reporter] of reporters) {
    console.log(`--- ${name.toUpperCase()} (${reporter.description}) ---`);
    const output = reporter.generate(result);
    console.log(output.slice(0, 500) + (output.length > 500 ? '\n...[truncated]' : ''));
    console.log('\n');
  }
}

main().catch(console.error);

// Export for use as a module
export { reporters, createReporter };
export type { Reporter };
