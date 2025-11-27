import type { AuditResult, Reporter, ReporterOptions, Finding } from '../types.js';

export class HTMLReporter implements Reporter {
  name = 'HTML Reporter';
  format = 'html';

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
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

  private formatFinding(finding: Finding, index: number): string {
    const color = this.getSeverityColor(finding.severity);
    const location = finding.line
      ? `${this.escapeHtml(finding.file)}:${finding.line}${finding.column ? `:${finding.column}` : ''}`
      : this.escapeHtml(finding.file);

    let html = `
      <div class="finding" id="finding-${index}">
        <div class="finding-header">
          <h3>
            <span class="severity-badge" style="background: ${color}">
              ${finding.severity.toUpperCase()}
            </span>
            ${this.escapeHtml(finding.title)}
          </h3>
          <span class="category">${finding.category}</span>
        </div>
        <div class="finding-body">
          <p class="location"><strong>Location:</strong> <code>${location}</code></p>
          <p class="message">${this.escapeHtml(finding.message)}</p>
    `;

    if (finding.description) {
      html += `<p class="description">${this.escapeHtml(finding.description)}</p>`;
    }

    if (finding.code_snippet) {
      html += `<pre class="code-snippet"><code>${this.escapeHtml(finding.code_snippet)}</code></pre>`;
    }

    if (finding.recommendation) {
      html += `<div class="recommendation">
        <strong>💡 Recommendation:</strong>
        <p>${this.escapeHtml(finding.recommendation)}</p>
      </div>`;
    }

    if (finding.cwe && finding.cwe.length > 0) {
      html += `<p class="cwe"><strong>CWE:</strong> ${finding.cwe.map(c => this.escapeHtml(c)).join(', ')}</p>`;
    }

    html += `
        </div>
      </div>
    `;

    return html;
  }

  private getStyles(): string {
    return `
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          line-height: 1.6;
          color: #1f2937;
          background: #f3f4f6;
          padding: 2rem;
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          background: white;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          overflow: hidden;
        }
        .header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 2rem;
        }
        .header h1 { margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; }
        .summary {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          padding: 2rem;
          background: #f9fafb;
          border-bottom: 1px solid #e5e7eb;
        }
        .summary-card {
          background: white;
          padding: 1rem;
          border-radius: 6px;
          box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .summary-card h3 {
          font-size: 0.875rem;
          color: #6b7280;
          margin-bottom: 0.5rem;
          text-transform: uppercase;
        }
        .summary-card .value {
          font-size: 2rem;
          font-weight: bold;
          color: #1f2937;
        }
        .severity-table {
          padding: 2rem;
        }
        .severity-table table {
          width: 100%;
          border-collapse: collapse;
        }
        .severity-table th,
        .severity-table td {
          padding: 0.75rem;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }
        .severity-table th {
          background: #f9fafb;
          font-weight: 600;
          color: #374151;
        }
        .findings {
          padding: 2rem;
        }
        .finding {
          margin-bottom: 2rem;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          overflow: hidden;
        }
        .finding-header {
          background: #f9fafb;
          padding: 1rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .finding-header h3 {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .severity-badge {
          display: inline-block;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          color: white;
          font-size: 0.75rem;
          font-weight: bold;
        }
        .category {
          background: #dbeafe;
          color: #1e40af;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.875rem;
        }
        .finding-body {
          padding: 1rem;
        }
        .finding-body p {
          margin-bottom: 1rem;
        }
        .location code {
          background: #f3f4f6;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-family: 'Monaco', 'Courier New', monospace;
          font-size: 0.875rem;
        }
        .code-snippet {
          background: #1f2937;
          color: #f9fafb;
          padding: 1rem;
          border-radius: 6px;
          overflow-x: auto;
          margin: 1rem 0;
        }
        .code-snippet code {
          font-family: 'Monaco', 'Courier New', monospace;
          font-size: 0.875rem;
        }
        .recommendation {
          background: #dbeafe;
          border-left: 4px solid #3b82f6;
          padding: 1rem;
          margin: 1rem 0;
          border-radius: 4px;
        }
        .footer {
          background: #f9fafb;
          padding: 1rem 2rem;
          text-align: center;
          color: #6b7280;
          font-size: 0.875rem;
        }
      </style>
    `;
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    let html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OmniAudit Report - ${this.escapeHtml(result.project)}</title>
  ${this.getStyles()}
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔍 OmniAudit Report</h1>
      <p>Project: ${this.escapeHtml(result.project)}</p>
      <p>Generated: ${new Date(result.timestamp).toLocaleString()}</p>
    </div>

    <div class="summary">
      <div class="summary-card">
        <h3>Total Files</h3>
        <div class="value">${result.total_files}</div>
      </div>
      <div class="summary-card">
        <h3>Total Findings</h3>
        <div class="value">${result.total_findings}</div>
      </div>
      <div class="summary-card">
        <h3>Duration</h3>
        <div class="value">${(result.duration_ms / 1000).toFixed(2)}s</div>
      </div>
    </div>

    <div class="severity-table">
      <h2>Findings by Severity</h2>
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="severity-badge" style="background: #dc2626">CRITICAL</span></td>
            <td>${result.findings_by_severity.critical}</td>
          </tr>
          <tr>
            <td><span class="severity-badge" style="background: #ea580c">HIGH</span></td>
            <td>${result.findings_by_severity.high}</td>
          </tr>
          <tr>
            <td><span class="severity-badge" style="background: #f59e0b">MEDIUM</span></td>
            <td>${result.findings_by_severity.medium}</td>
          </tr>
          <tr>
            <td><span class="severity-badge" style="background: #3b82f6">LOW</span></td>
            <td>${result.findings_by_severity.low}</td>
          </tr>
          <tr>
            <td><span class="severity-badge" style="background: #6b7280">INFO</span></td>
            <td>${result.findings_by_severity.info}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="findings">
      <h2>Detailed Findings</h2>
      ${result.findings.map((f, i) => this.formatFinding(f, i)).join('')}
    </div>

    <div class="footer">
      <p>Generated by OmniAudit ${result.metadata?.version || 'v2.0.0'}</p>
    </div>
  </div>
</body>
</html>`;

    return html;
  }
}
