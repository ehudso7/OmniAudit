import type { AuditResult, Reporter, ReporterOptions } from '../types.js';

export class JSONReporter implements Reporter {
  name = 'JSON Reporter';
  format = 'json';

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const data = options?.includeMetadata !== false ? result : {
      findings: result.findings,
      total_findings: result.total_findings,
      findings_by_severity: result.findings_by_severity,
    };

    return options?.pretty
      ? JSON.stringify(data, null, 2)
      : JSON.stringify(data);
  }
}
