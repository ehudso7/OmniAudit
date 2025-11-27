import type { AuditResult, Reporter, ReporterOptions, Finding, Severity } from '../types.js';

interface SarifResult {
  ruleId: string;
  message: {
    text: string;
  };
  level: 'error' | 'warning' | 'note';
  locations?: Array<{
    physicalLocation: {
      artifactLocation: {
        uri: string;
      };
      region?: {
        startLine?: number;
        startColumn?: number;
        endLine?: number;
        endColumn?: number;
      };
    };
  }>;
  properties?: Record<string, unknown>;
}

export class SARIFReporter implements Reporter {
  name = 'SARIF Reporter';
  format = 'sarif';

  private severityToLevel(severity: Severity): 'error' | 'warning' | 'note' {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
      case 'info':
        return 'note';
    }
  }

  private findingToSarifResult(finding: Finding): SarifResult {
    const result: SarifResult = {
      ruleId: finding.rule_id,
      message: {
        text: finding.message,
      },
      level: this.severityToLevel(finding.severity),
    };

    if (finding.file) {
      result.locations = [
        {
          physicalLocation: {
            artifactLocation: {
              uri: finding.file,
            },
            ...(finding.line && {
              region: {
                startLine: finding.line,
                startColumn: finding.column,
                endLine: finding.end_line,
                endColumn: finding.end_column,
              },
            }),
          },
        },
      ];
    }

    if (finding.metadata) {
      result.properties = finding.metadata;
    }

    return result;
  }

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    const sarif = {
      version: '2.1.0',
      $schema: 'https://json.schemastore.org/sarif-2.1.0.json',
      runs: [
        {
          tool: {
            driver: {
              name: 'OmniAudit',
              version: result.metadata?.version || '2.0.0',
              informationUri: 'https://github.com/omniaudit/omniaudit',
              rules: Array.from(new Set(result.findings.map(f => f.rule_id))).map(ruleId => {
                const finding = result.findings.find(f => f.rule_id === ruleId);
                return {
                  id: ruleId,
                  shortDescription: {
                    text: finding?.title || ruleId,
                  },
                  fullDescription: {
                    text: finding?.description || '',
                  },
                  help: {
                    text: finding?.recommendation || '',
                  },
                };
              }),
            },
          },
          results: result.findings.map(f => this.findingToSarifResult(f)),
          properties: {
            metrics: {
              totalFiles: result.total_files,
              totalFindings: result.total_findings,
              findingsBySeverity: result.findings_by_severity,
              durationMs: result.duration_ms,
            },
          },
        },
      ],
    };

    return options?.pretty
      ? JSON.stringify(sarif, null, 2)
      : JSON.stringify(sarif);
  }
}
