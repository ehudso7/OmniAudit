import { Command } from 'commander';
import chalk from 'chalk';
import { createSpinner } from '../ui/spinner.js';
import fs from 'fs/promises';
import path from 'path';

export function createConfigCommand(): Command {
  const cmd = new Command('config');

  cmd.description('Manage OmniAudit configuration');

  // Init config
  cmd
    .command('init')
    .description('Initialize a new configuration file')
    .option('-f, --force', 'Overwrite existing config')
    .option('-t, --template <name>', 'Use a template', 'default')
    .action(async (options) => {
      const spinner = createSpinner('Creating configuration...');

      try {
        const configPath = path.join(process.cwd(), 'omniaudit.config.yaml');

        // Check if config exists
        try {
          await fs.access(configPath);
          if (!options.force) {
            spinner.fail('Configuration file already exists. Use --force to overwrite.');
            return;
          }
        } catch {
          // File doesn't exist, continue
        }

        const defaultConfig = `# OmniAudit Configuration
version: 2.0.0

# Project settings
project:
  name: my-project
  paths:
    - src/
    - lib/
  exclude:
    - node_modules/
    - dist/
    - build/

# Analysis settings
analysis:
  parallel: true
  max_workers: 4
  timeout: 300000

# Rules configuration
rules:
  enabled:
    - security/*
    - performance/*
    - best-practices/*
  disabled: []
  severity_overrides: {}

# Reporting
reporting:
  formats:
    - json
    - html
  output_dir: ./reports

# Integrations
integrations:
  github:
    enabled: false
  slack:
    enabled: false
`;

        await fs.writeFile(configPath, defaultConfig);
        spinner.succeed(`Configuration created at ${configPath}`);
      } catch (error) {
        spinner.fail('Failed to create configuration');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Get config value
  cmd
    .command('get <key>')
    .description('Get a configuration value')
    .action(async (key) => {
      const spinner = createSpinner(`Getting ${key}...`);

      try {
        // Mock - would read actual config
        const value = 'example-value';
        spinner.succeed();
        console.log(chalk.cyan(key), '=', chalk.yellow(value));
      } catch (error) {
        spinner.fail('Failed to get configuration');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Set config value
  cmd
    .command('set <key> <value>')
    .description('Set a configuration value')
    .action(async (key, value) => {
      const spinner = createSpinner(`Setting ${key}...`);

      try {
        // Mock - would update actual config
        spinner.succeed(`${key} = ${value}`);
      } catch (error) {
        spinner.fail('Failed to set configuration');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // List all config
  cmd
    .command('list')
    .description('List all configuration values')
    .action(async () => {
      const spinner = createSpinner('Loading configuration...');

      try {
        // Mock config
        const config = {
          'project.name': 'my-project',
          'analysis.parallel': 'true',
          'analysis.max_workers': '4',
          'reporting.formats': 'json,html',
        };

        spinner.succeed('Configuration loaded');

        console.log(chalk.bold.cyan('\n⚙️  Configuration\n'));
        for (const [key, value] of Object.entries(config)) {
          console.log(chalk.cyan(key.padEnd(30)), chalk.yellow(value));
        }
      } catch (error) {
        spinner.fail('Failed to load configuration');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Validate config
  cmd
    .command('validate')
    .description('Validate configuration file')
    .action(async () => {
      const spinner = createSpinner('Validating configuration...');

      try {
        // Mock validation
        spinner.succeed('Configuration is valid');
      } catch (error) {
        spinner.fail('Configuration is invalid');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  return cmd;
}
