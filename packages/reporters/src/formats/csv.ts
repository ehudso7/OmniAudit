import type { AuditResult, Reporter, ReporterOptions } from '../types.js';

export class CSVReporter implements Reporter {
  name = 'CSV Reporter';
  format = 'csv';

  private escapeCSV(text: string): string {
    if (!text) return '';
    const escaped = text.replace(/"/g, '""');
    return `"${escaped}"`;
  }

  async generate(result: AuditResult, _options?: ReporterOptions): Promise<string> {
    const headers = [
      'ID',
      'Rule ID',
      'Title',
      'Severity',
      'Category',
      'File',
      'Line',
      'Column',
      'Message',
      'Recommendation',
      'CWE',
      'OWASP',
    ];

    let csv = headers.join(',') + '\n';

    for (const finding of result.findings) {
      const row = [
        this.escapeCSV(finding.id),
        this.escapeCSV(finding.rule_id),
        this.escapeCSV(finding.title),
        this.escapeCSV(finding.severity),
        this.escapeCSV(finding.category),
        this.escapeCSV(finding.file),
        finding.line?.toString() || '',
        finding.column?.toString() || '',
        this.escapeCSV(finding.message),
        this.escapeCSV(finding.recommendation || ''),
        this.escapeCSV(finding.cwe?.join('; ') || ''),
        this.escapeCSV(finding.owasp?.join('; ') || ''),
      ];

      csv += row.join(',') + '\n';
    }

    return csv;
  }
}
