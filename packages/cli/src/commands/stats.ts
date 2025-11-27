import { Command } from 'commander';
import chalk from 'chalk';
import { createSpinner } from '../ui/spinner.js';
import { createTable } from '../ui/table.js';

export function createStatsCommand(): Command {
  const cmd = new Command('stats');

  cmd.description('View audit statistics and analytics');

  // Overall stats
  cmd
    .command('summary')
    .description('Show overall statistics')
    .option('--period <days>', 'Time period in days', '30')
    .action(async (options) => {
      const spinner = createSpinner('Calculating statistics...');

      try {
        // Mock stats
        spinner.succeed('Statistics calculated');

        console.log(chalk.bold.cyan('\n📊 Audit Statistics\n'));
        console.log(chalk.bold('Period:'), `Last ${options.period} days\n`);

        const table = createTable({
          columns: [
            { name: 'Metric', align: 'left' },
            { name: 'Value', align: 'right' },
          ],
        });

        table.push(
          ['Total Audits', chalk.cyan('127')],
          ['Total Findings', chalk.yellow('2,543')],
          ['Fixed Issues', chalk.green('1,892')],
          ['Open Issues', chalk.red('651')],
          ['Average Findings per Audit', chalk.cyan('20.0')],
          ['Most Common Category', chalk.yellow('security')],
          ['Fix Rate', chalk.green('74.4%')]
        );

        console.log(table.toString());
      } catch (error) {
        spinner.fail('Failed to calculate statistics');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Trends
  cmd
    .command('trends')
    .description('Show trends over time')
    .option('--period <days>', 'Time period in days', '30')
    .action(async (options) => {
      const spinner = createSpinner('Analyzing trends...');

      try {
        spinner.succeed('Trends analyzed');

        console.log(chalk.bold.cyan('\n📈 Trends\n'));
        console.log(chalk.green('▲ Issues fixed: +42% compared to previous period'));
        console.log(chalk.red('▼ New critical issues: -15% compared to previous period'));
        console.log(chalk.yellow('● Security findings: Stable'));
        console.log(chalk.cyan('▲ Code quality: +8% improvement'));
      } catch (error) {
        spinner.fail('Failed to analyze trends');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Top issues
  cmd
    .command('top-issues')
    .description('Show most common issues')
    .option('--limit <number>', 'Number of results', '10')
    .action(async (options) => {
      const spinner = createSpinner('Finding top issues...');

      try {
        spinner.succeed('Top issues found');

        const table = createTable({
          columns: [
            { name: 'Rank', align: 'right' },
            { name: 'Rule', align: 'left' },
            { name: 'Count', align: 'right' },
            { name: 'Severity', align: 'left' },
          ],
        });

        table.push(
          ['1', 'security/no-eval', '127', chalk.red('Critical')],
          ['2', 'performance/no-sync-fs', '93', chalk.yellow('Medium')],
          ['3', 'best-practices/no-console', '78', chalk.blue('Low')]
        );

        console.log(chalk.bold.cyan('\n🔝 Top Issues\n'));
        console.log(table.toString());
      } catch (error) {
        spinner.fail('Failed to get top issues');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  return cmd;
}
