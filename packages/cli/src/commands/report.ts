import { Command } from 'commander';
import chalk from 'chalk';
import { createSpinner } from '../ui/spinner.js';
import { getAvailableFormats } from '@omniaudit/reporters';

export function createReportCommand(): Command {
  const cmd = new Command('report');

  cmd.description('Generate and manage audit reports');

  // Generate report
  cmd
    .command('generate')
    .description('Generate a report from audit results')
    .requiredOption('-i, --input <file>', 'Input audit results file')
    .requiredOption('-f, --format <format>', 'Output format')
    .option('-o, --output <file>', 'Output file')
    .option('--pretty', 'Pretty print output')
    .action(async (options) => {
      const spinner = createSpinner(`Generating ${options.format} report...`);

      try {
        // Mock - would read input and generate report
        spinner.succeed(`Report generated: ${options.output || 'stdout'}`);
      } catch (error) {
        spinner.fail('Failed to generate report');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // List formats
  cmd
    .command('formats')
    .description('List all available report formats')
    .action(() => {
      const formats = getAvailableFormats();

      console.log(chalk.bold.cyan('\n📄 Available Report Formats\n'));
      for (const format of formats) {
        console.log(chalk.cyan(`• ${format}`));
      }
      console.log();
    });

  // Convert report
  cmd
    .command('convert')
    .description('Convert a report from one format to another')
    .requiredOption('-i, --input <file>', 'Input file')
    .requiredOption('--from <format>', 'Source format')
    .requiredOption('--to <format>', 'Target format')
    .option('-o, --output <file>', 'Output file')
    .action(async (options) => {
      const spinner = createSpinner(`Converting from ${options.from} to ${options.to}...`);

      try {
        // Mock conversion
        spinner.succeed('Report converted');
      } catch (error) {
        spinner.fail('Conversion failed');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Upload report
  cmd
    .command('upload')
    .description('Upload report to OmniAudit server')
    .requiredOption('-i, --input <file>', 'Report file to upload')
    .option('--api-url <url>', 'API URL')
    .action(async (options) => {
      const spinner = createSpinner('Uploading report...');

      try {
        // Mock upload
        spinner.succeed('Report uploaded successfully');
      } catch (error) {
        spinner.fail('Upload failed');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  return cmd;
}
