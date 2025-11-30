/**
 * Batch Processing Example
 *
 * Demonstrates how to audit multiple projects efficiently using the SDK.
 */

import { createClient, OmniAuditClient } from '@omniaudit/sdk';
import type { AuditResult, Finding } from '@omniaudit/sdk';

interface Project {
  name: string;
  path: string;
  options?: {
    rules?: string[];
    severity?: string[];
  };
}

interface BatchResult {
  project: string;
  status: 'success' | 'failed';
  result?: AuditResult;
  error?: string;
  duration: number;
}

interface BatchSummary {
  total: number;
  successful: number;
  failed: number;
  totalFindings: number;
  criticalFindings: number;
  highFindings: number;
  totalDuration: number;
  results: BatchResult[];
}

// Run audits in parallel with concurrency limit
async function runWithConcurrency<T, R>(
  items: T[],
  fn: (item: T) => Promise<R>,
  concurrency: number
): Promise<R[]> {
  const results: R[] = [];
  const executing: Promise<void>[] = [];

  for (const item of items) {
    const p = fn(item).then((result) => {
      results.push(result);
    });

    executing.push(p as Promise<void>);

    if (executing.length >= concurrency) {
      await Promise.race(executing);
      // Remove settled promises
      for (let i = executing.length - 1; i >= 0; i--) {
        const p = executing[i];
        // Check if settled by racing with an immediately resolved promise
        const settled = await Promise.race([p.then(() => true), Promise.resolve(false)]);
        if (settled) {
          executing.splice(i, 1);
        }
      }
    }
  }

  await Promise.all(executing);
  return results;
}

class BatchAuditor {
  private client: OmniAuditClient;
  private concurrency: number;

  constructor(apiUrl: string, apiKey?: string, concurrency = 3) {
    this.client = createClient({ apiUrl, apiKey });
    this.concurrency = concurrency;
  }

  async auditProjects(projects: Project[]): Promise<BatchSummary> {
    const startTime = Date.now();
    console.log(`Starting batch audit of ${projects.length} projects...`);
    console.log(`Concurrency: ${this.concurrency}\n`);

    const results = await runWithConcurrency(
      projects,
      async (project): Promise<BatchResult> => {
        const projectStart = Date.now();
        console.log(`[START] ${project.name}`);

        try {
          const result = await this.client.audit({
            path: project.path,
            rules: project.options?.rules,
            severity: project.options?.severity,
          });

          const duration = Date.now() - projectStart;
          console.log(
            `[DONE]  ${project.name} - ${result.total_findings} findings in ${duration}ms`
          );

          return {
            project: project.name,
            status: 'success',
            result,
            duration,
          };
        } catch (error) {
          const duration = Date.now() - projectStart;
          const message = error instanceof Error ? error.message : 'Unknown error';
          console.log(`[FAIL]  ${project.name} - ${message}`);

          return {
            project: project.name,
            status: 'failed',
            error: message,
            duration,
          };
        }
      },
      this.concurrency
    );

    const totalDuration = Date.now() - startTime;

    // Calculate summary
    const summary: BatchSummary = {
      total: projects.length,
      successful: results.filter((r) => r.status === 'success').length,
      failed: results.filter((r) => r.status === 'failed').length,
      totalFindings: results.reduce((sum, r) => sum + (r.result?.total_findings || 0), 0),
      criticalFindings: results.reduce(
        (sum, r) => sum + (r.result?.findings_by_severity.critical || 0),
        0
      ),
      highFindings: results.reduce((sum, r) => sum + (r.result?.findings_by_severity.high || 0), 0),
      totalDuration,
      results,
    };

    return summary;
  }

  // Export consolidated report
  async exportConsolidatedReport(
    summary: BatchSummary,
    format: 'json' | 'csv' | 'sarif' = 'json'
  ): Promise<string> {
    if (format === 'json') {
      return JSON.stringify(summary, null, 2);
    }

    if (format === 'csv') {
      const lines = [
        'Project,Status,Files,Total Findings,Critical,High,Medium,Low,Info,Duration (ms)',
      ];

      for (const result of summary.results) {
        if (result.result) {
          const r = result.result;
          lines.push(
            [
              result.project,
              result.status,
              r.total_files,
              r.total_findings,
              r.findings_by_severity.critical,
              r.findings_by_severity.high,
              r.findings_by_severity.medium,
              r.findings_by_severity.low,
              r.findings_by_severity.info,
              result.duration,
            ].join(',')
          );
        } else {
          lines.push([result.project, result.status, 0, 0, 0, 0, 0, 0, 0, result.duration].join(','));
        }
      }

      return lines.join('\n');
    }

    if (format === 'sarif') {
      // Consolidated SARIF report
      const allFindings: Finding[] = summary.results
        .filter((r) => r.result)
        .flatMap((r) => r.result!.findings);

      return JSON.stringify(
        {
          version: '2.1.0',
          $schema: 'https://json.schemastore.org/sarif-2.1.0.json',
          runs: [
            {
              tool: {
                driver: {
                  name: 'OmniAudit',
                  version: '2.0.0',
                  informationUri: 'https://omniaudit.dev',
                },
              },
              results: allFindings.map((f) => ({
                ruleId: f.rule_id,
                level: mapSeverityToSarif(f.severity),
                message: { text: f.message },
                locations: [
                  {
                    physicalLocation: {
                      artifactLocation: { uri: f.file },
                      region: {
                        startLine: f.line || 1,
                        startColumn: f.column || 1,
                      },
                    },
                  },
                ],
              })),
            },
          ],
        },
        null,
        2
      );
    }

    throw new Error(`Unknown format: ${format}`);
  }
}

function mapSeverityToSarif(
  severity: string
): 'error' | 'warning' | 'note' | 'none' {
  switch (severity) {
    case 'critical':
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'note';
    default:
      return 'none';
  }
}

function printSummary(summary: BatchSummary) {
  console.log('\n' + '='.repeat(60));
  console.log('BATCH AUDIT SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total projects: ${summary.total}`);
  console.log(`  Successful: ${summary.successful}`);
  console.log(`  Failed: ${summary.failed}`);
  console.log('');
  console.log(`Total findings: ${summary.totalFindings}`);
  console.log(`  Critical: ${summary.criticalFindings}`);
  console.log(`  High: ${summary.highFindings}`);
  console.log('');
  console.log(`Total duration: ${summary.totalDuration}ms`);
  console.log(
    `Average per project: ${Math.round(summary.totalDuration / summary.total)}ms`
  );
  console.log('='.repeat(60));

  // Project breakdown
  console.log('\nPROJECT BREAKDOWN:');
  console.log('-'.repeat(60));

  for (const result of summary.results) {
    const status = result.status === 'success' ? '✓' : '✗';
    const findings = result.result?.total_findings ?? 'N/A';
    const critical = result.result?.findings_by_severity.critical ?? 0;
    const high = result.result?.findings_by_severity.high ?? 0;

    console.log(
      `${status} ${result.project.padEnd(30)} ` +
        `Findings: ${String(findings).padStart(4)} ` +
        `(C:${critical} H:${high}) ` +
        `${result.duration}ms`
    );

    if (result.error) {
      console.log(`  Error: ${result.error}`);
    }
  }
}

// Example usage
async function main() {
  const projects: Project[] = [
    { name: 'frontend', path: './packages/frontend' },
    { name: 'backend', path: './packages/backend' },
    { name: 'sdk', path: './packages/sdk' },
    { name: 'cli', path: './packages/cli' },
    { name: 'core', path: './packages/core' },
    {
      name: 'security-critical',
      path: './packages/auth',
      options: {
        rules: ['security/*'],
        severity: ['critical', 'high'],
      },
    },
  ];

  const auditor = new BatchAuditor(
    process.env.OMNIAUDIT_API_URL || 'http://localhost:8000',
    process.env.OMNIAUDIT_API_KEY,
    3 // Run 3 audits in parallel
  );

  try {
    const summary = await auditor.auditProjects(projects);
    printSummary(summary);

    // Export reports
    console.log('\nExporting reports...');

    const jsonReport = await auditor.exportConsolidatedReport(summary, 'json');
    console.log('JSON report generated');

    const csvReport = await auditor.exportConsolidatedReport(summary, 'csv');
    console.log('CSV report generated');

    const sarifReport = await auditor.exportConsolidatedReport(summary, 'sarif');
    console.log('SARIF report generated');

    // In a real implementation, write these to files
    // fs.writeFileSync('audit-report.json', jsonReport);
    // fs.writeFileSync('audit-report.csv', csvReport);
    // fs.writeFileSync('audit-report.sarif', sarifReport);

    // Exit with error if there are critical findings
    if (summary.criticalFindings > 0) {
      console.log(`\n❌ Found ${summary.criticalFindings} critical issues!`);
      process.exit(1);
    }

    console.log('\n✅ Batch audit completed successfully!');
    process.exit(0);
  } catch (error) {
    console.error('Batch audit failed:', error);
    process.exit(1);
  }
}

main();

// Export for use as a module
export { BatchAuditor, runWithConcurrency };
export type { Project, BatchResult, BatchSummary };
