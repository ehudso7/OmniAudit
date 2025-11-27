import type { AuditResult, Reporter, ReporterOptions, Finding } from '../types.js';

export class JUnitReporter implements Reporter {
  name = 'JUnit Reporter';
  format = 'junit';

  private escapeXml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  private findingToTestCase(finding: Finding): string {
    const name = `${finding.rule_id}: ${finding.title}`;
    const classname = finding.category;
    const time = '0';

    let testCase = `    <testcase name="${this.escapeXml(name)}" classname="${this.escapeXml(classname)}" time="${time}">\n`;

    if (finding.severity === 'critical' || finding.severity === 'high') {
      testCase += `      <failure message="${this.escapeXml(finding.message)}" type="${finding.severity}">\n`;
      testCase += `File: ${this.escapeXml(finding.file)}\n`;
      if (finding.line) {
        testCase += `Line: ${finding.line}\n`;
      }
      testCase += `\n${this.escapeXml(finding.description || finding.message)}\n`;
      if (finding.recommendation) {
        testCase += `\nRecommendation: ${this.escapeXml(finding.recommendation)}\n`;
      }
      testCase += `      </failure>\n`;
    } else if (finding.severity === 'medium') {
      testCase += `      <error message="${this.escapeXml(finding.message)}" type="${finding.severity}">\n`;
      testCase += `${this.escapeXml(finding.file)}${finding.line ? `:${finding.line}` : ''}\n`;
      testCase += `      </error>\n`;
    } else {
      // Low and info are represented as skipped tests with system-out
      testCase += `      <skipped message="${this.escapeXml(finding.message)}"/>\n`;
      testCase += `      <system-out>\n`;
      testCase += `${this.escapeXml(finding.file)}${finding.line ? `:${finding.line}` : ''}\n`;
      testCase += `${this.escapeXml(finding.description || '')}\n`;
      testCase += `      </system-out>\n`;
    }

    testCase += `    </testcase>\n`;
    return testCase;
  }

  async generate(result: AuditResult, _options?: ReporterOptions): Promise<string> {
    const failures = result.findings_by_severity.critical + result.findings_by_severity.high;
    const errors = result.findings_by_severity.medium;
    const skipped = result.findings_by_severity.low + result.findings_by_severity.info;

    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += `<testsuites name="OmniAudit" tests="${result.total_findings}" failures="${failures}" errors="${errors}" skipped="${skipped}" time="${result.duration_ms / 1000}">\n`;
    xml += `  <testsuite name="${this.escapeXml(result.project)}" tests="${result.total_findings}" failures="${failures}" errors="${errors}" skipped="${skipped}" time="${result.duration_ms / 1000}">\n`;

    for (const finding of result.findings) {
      xml += this.findingToTestCase(finding);
    }

    xml += '  </testsuite>\n';
    xml += '</testsuites>\n';

    return xml;
  }
}
