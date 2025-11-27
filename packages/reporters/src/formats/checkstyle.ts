import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

export class CheckstyleReporter implements Reporter {
  name = 'Checkstyle Reporter';
  format = 'checkstyle';

  private escapeXml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  private severityToCheckstyle(severity: Severity): string {
    const mapping: Record<Severity, string> = {
      critical: 'error',
      high: 'error',
      medium: 'warning',
      low: 'warning',
      info: 'info',
    };
    return mapping[severity];
  }

  async generate(result: AuditResult, _options?: ReporterOptions): Promise<string> {
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<checkstyle version="10.0">\n';

    // Group findings by file
    const findingsByFile = new Map<string, Finding[]>();
    for (const finding of result.findings) {
      const file = finding.file;
      if (!findingsByFile.has(file)) {
        findingsByFile.set(file, []);
      }
      findingsByFile.get(file)?.push(finding);
    }

    // Generate XML for each file
    for (const [file, findings] of findingsByFile) {
      xml += `  <file name="${this.escapeXml(file)}">\n`;

      for (const finding of findings) {
        const line = finding.line || 1;
        const column = finding.column || 1;
        const severity = this.severityToCheckstyle(finding.severity);
        const source = `omniaudit.${finding.category}.${finding.rule_id}`;

        xml += `    <error `;
        xml += `line="${line}" `;
        xml += `column="${column}" `;
        xml += `severity="${severity}" `;
        xml += `message="${this.escapeXml(finding.message)}" `;
        xml += `source="${this.escapeXml(source)}"`;
        xml += `/>\n`;
      }

      xml += '  </file>\n';
    }

    xml += '</checkstyle>\n';
    return xml;
  }
}
