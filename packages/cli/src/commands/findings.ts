import { Command } from 'commander';
import chalk from 'chalk';
import { createSpinner } from '../ui/spinner.js';
import { printFindingsTable } from '../ui/table.js';

export function createFindingsCommand(): Command {
  const cmd = new Command('findings');

  cmd
    .description('Manage and query audit findings');

  // List findings
  cmd
    .command('list')
    .description('List all findings')
    .option('-s, --severity <levels...>', 'Filter by severity')
    .option('-c, --category <categories...>', 'Filter by category')
    .option('-f, --file <pattern>', 'Filter by file pattern')
    .option('--limit <number>', 'Limit results', '50')
    .action(async (options) => {
      const spinner = createSpinner('Fetching findings...');

      try {
        // Mock data - would fetch from API
        const findings = [
          {
            id: '1',
            rule_id: 'security/no-eval',
            title: 'Dangerous use of eval()',
            severity: 'critical',
            category: 'security',
            file: 'src/utils.ts',
            line: 42,
          },
        ];

        spinner.succeed(`Found ${findings.length} findings`);
        printFindingsTable(findings);
      } catch (error) {
        spinner.fail('Failed to fetch findings');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Show finding details
  cmd
    .command('show <id>')
    .description('Show detailed information about a finding')
    .action(async (id) => {
      const spinner = createSpinner(`Fetching finding ${id}...`);

      try {
        // Mock data
        const finding = {
          id,
          rule_id: 'security/no-eval',
          title: 'Dangerous use of eval()',
          description: 'Using eval() can lead to code injection vulnerabilities',
          severity: 'critical',
          category: 'security',
          file: 'src/utils.ts',
          line: 42,
          column: 10,
          message: 'Avoid using eval() as it poses security risks',
          recommendation: 'Use safer alternatives',
          code_snippet: 'const result = eval(userInput); // Dangerous!',
        };

        spinner.succeed('Finding retrieved');

        console.log(chalk.bold.cyan('\n📋 Finding Details\n'));
        console.log(chalk.bold('ID:'), finding.id);
        console.log(chalk.bold('Rule:'), finding.rule_id);
        console.log(chalk.bold('Title:'), finding.title);
        console.log(chalk.bold('Severity:'), chalk.red(finding.severity.toUpperCase()));
        console.log(chalk.bold('Category:'), finding.category);
        console.log(chalk.bold('Location:'), `${finding.file}:${finding.line}:${finding.column}`);
        console.log(chalk.bold('\nDescription:'));
        console.log(finding.description);
        console.log(chalk.bold('\nCode:'));
        console.log(chalk.gray(finding.code_snippet));
        console.log(chalk.bold('\nRecommendation:'));
        console.log(chalk.green(finding.recommendation));
      } catch (error) {
        spinner.fail('Failed to fetch finding');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Export findings
  cmd
    .command('export')
    .description('Export findings to a file')
    .requiredOption('-f, --format <format>', 'Export format')
    .requiredOption('-o, --output <file>', 'Output file')
    .action(async (options) => {
      const spinner = createSpinner(`Exporting findings as ${options.format}...`);

      try {
        // Implementation would export findings
        spinner.succeed(`Findings exported to ${options.output}`);
      } catch (error) {
        spinner.fail('Export failed');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Mark as fixed
  cmd
    .command('fixed <id>')
    .description('Mark a finding as fixed')
    .action(async (id) => {
      const spinner = createSpinner(`Marking finding ${id} as fixed...`);

      try {
        // Implementation would update finding status
        spinner.succeed('Finding marked as fixed');
      } catch (error) {
        spinner.fail('Failed to update finding');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Ignore finding
  cmd
    .command('ignore <id>')
    .description('Ignore a finding')
    .option('-r, --reason <text>', 'Reason for ignoring')
    .action(async (id, options) => {
      const spinner = createSpinner(`Ignoring finding ${id}...`);

      try {
        // Implementation would update finding status
        spinner.succeed(`Finding ${id} ignored${options.reason ? `: ${options.reason}` : ''}`);
      } catch (error) {
        spinner.fail('Failed to ignore finding');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  return cmd;
}
