import { Command } from 'commander';
import chalk from 'chalk';
import { createSpinner } from '../ui/spinner.js';
import { printFindingsTable, printSummaryTable } from '../ui/table.js';
import { generateReport } from '@omniaudit/reporters';
import fs from 'fs/promises';

export function createAuditCommand(): Command {
  const cmd = new Command('audit');

  cmd
    .description('Run a comprehensive code audit')
    .argument('[path]', 'Path to audit', '.')
    .option('-f, --format <format>', 'Output format', 'json')
    .option('-o, --output <file>', 'Output file path')
    .option('-r, --rules <rules...>', 'Specific rules to run')
    .option('-s, --severity <levels...>', 'Filter by severity levels')
    .option('--fix', 'Auto-fix issues where possible')
    .option('--fail-on <severity>', 'Exit with error on severity level', 'critical')
    .option('--no-cache', 'Disable caching')
    .option('--summary', 'Show summary only')
    .action(async (path, options) => {
      const spinner = createSpinner('Starting audit...');

      try {
        // Mock audit result - in real implementation, this would call the SDK
        const result = {
          id: `audit-${Date.now()}`,
          project: path,
          timestamp: new Date().toISOString(),
          duration_ms: 5432,
          total_files: 127,
          total_findings: 23,
          findings_by_severity: {
            critical: 2,
            high: 5,
            medium: 10,
            low: 4,
            info: 2,
          },
          findings: [
            {
              id: '1',
              rule_id: 'security/no-eval',
              title: 'Dangerous use of eval()',
              description: 'Using eval() can lead to code injection vulnerabilities',
              severity: 'critical' as const,
              category: 'security' as const,
              file: 'src/utils.ts',
              line: 42,
              column: 10,
              message: 'Avoid using eval() as it poses security risks',
              recommendation: 'Use safer alternatives like Function constructor or JSON.parse',
            },
          ],
          metadata: {
            version: '2.0.0',
            rules_count: 150,
            analyzers: ['eslint', 'typescript', 'security'],
          },
        };

        spinner.succeed('Audit completed');

        if (options.summary) {
          console.log(chalk.bold.cyan('\n🔍 Audit Summary\n'));
          printSummaryTable(result);
        } else {
          console.log(chalk.bold.cyan('\n🔍 Audit Results\n'));
          printSummaryTable(result);
          console.log(chalk.bold.cyan('\n📋 Findings\n'));
          printFindingsTable(result.findings);
        }

        // Generate and save report
        if (options.output || options.format !== 'json') {
          const spinner2 = createSpinner(`Generating ${options.format} report...`);
          const report = await generateReport(result, options.format, {
            pretty: true,
            includeMetadata: true,
          });

          if (options.output) {
            await fs.writeFile(options.output, report);
            spinner2.succeed(`Report saved to ${options.output}`);
          } else {
            spinner2.stop();
            console.log('\n' + report);
          }
        }

        // Exit with error if findings exceed threshold
        const severityLevels = ['info', 'low', 'medium', 'high', 'critical'];
        const failIndex = severityLevels.indexOf(options.failOn);
        const hasCriticalFindings = severityLevels
          .slice(failIndex)
          .some(level => result.findings_by_severity[level as keyof typeof result.findings_by_severity] > 0);

        if (hasCriticalFindings) {
          console.log(chalk.red(`\n❌ Audit failed: Found ${options.failOn} or higher severity issues\n`));
          process.exit(1);
        }

        console.log(chalk.green('\n✅ Audit passed\n'));
      } catch (error) {
        spinner.fail('Audit failed');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  return cmd;
}
