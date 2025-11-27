import { Command } from 'commander';
import chalk from 'chalk';
import { createSpinner } from '../ui/spinner.js';
import { createTable } from '../ui/table.js';

export function createRulesCommand(): Command {
  const cmd = new Command('rules');

  cmd.description('Manage audit rules');

  // List rules
  cmd
    .command('list')
    .description('List all available rules')
    .option('-c, --category <category>', 'Filter by category')
    .option('-s, --severity <severity>', 'Filter by default severity')
    .option('--enabled-only', 'Show only enabled rules')
    .action(async (options) => {
      const spinner = createSpinner('Loading rules...');

      try {
        // Mock rules data
        const rules = [
          {
            id: 'security/no-eval',
            name: 'No eval()',
            category: 'security',
            severity: 'critical',
            enabled: true,
          },
          {
            id: 'performance/no-sync-fs',
            name: 'No synchronous file system',
            category: 'performance',
            severity: 'medium',
            enabled: true,
          },
          {
            id: 'best-practices/use-strict',
            name: 'Use strict mode',
            category: 'best-practices',
            severity: 'low',
            enabled: false,
          },
        ];

        spinner.succeed(`Found ${rules.length} rules`);

        const table = createTable({
          columns: [
            { name: 'Rule ID' },
            { name: 'Name' },
            { name: 'Category' },
            { name: 'Severity' },
            { name: 'Status' },
          ],
        });

        for (const rule of rules) {
          table.push([
            rule.id,
            rule.name,
            rule.category,
            rule.severity,
            rule.enabled ? chalk.green('✓ Enabled') : chalk.gray('✗ Disabled'),
          ]);
        }

        console.log('\n' + table.toString());
      } catch (error) {
        spinner.fail('Failed to load rules');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Show rule details
  cmd
    .command('show <rule-id>')
    .description('Show detailed information about a rule')
    .action(async (ruleId) => {
      const spinner = createSpinner(`Loading rule ${ruleId}...`);

      try {
        // Mock rule data
        const rule = {
          id: ruleId,
          name: 'No eval()',
          description: 'Disallows the use of eval() function',
          category: 'security',
          severity: 'critical',
          enabled: true,
          autoFixable: false,
          examples: {
            bad: 'const result = eval(userInput);',
            good: 'const result = JSON.parse(userInput);',
          },
        };

        spinner.succeed();

        console.log(chalk.bold.cyan('\n📜 Rule Details\n'));
        console.log(chalk.bold('ID:'), rule.id);
        console.log(chalk.bold('Name:'), rule.name);
        console.log(chalk.bold('Category:'), rule.category);
        console.log(chalk.bold('Severity:'), chalk.red(rule.severity.toUpperCase()));
        console.log(chalk.bold('Status:'), rule.enabled ? chalk.green('✓ Enabled') : chalk.gray('✗ Disabled'));
        console.log(chalk.bold('Auto-fixable:'), rule.autoFixable ? chalk.green('Yes') : chalk.gray('No'));
        console.log(chalk.bold('\nDescription:'));
        console.log(rule.description);
        console.log(chalk.bold('\nBad Example:'));
        console.log(chalk.red(rule.examples.bad));
        console.log(chalk.bold('\nGood Example:'));
        console.log(chalk.green(rule.examples.good));
      } catch (error) {
        spinner.fail('Failed to load rule');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Enable rule
  cmd
    .command('enable <rule-id>')
    .description('Enable a rule')
    .action(async (ruleId) => {
      const spinner = createSpinner(`Enabling rule ${ruleId}...`);

      try {
        // Mock - would update config
        spinner.succeed(`Rule ${ruleId} enabled`);
      } catch (error) {
        spinner.fail('Failed to enable rule');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Disable rule
  cmd
    .command('disable <rule-id>')
    .description('Disable a rule')
    .action(async (ruleId) => {
      const spinner = createSpinner(`Disabling rule ${ruleId}...`);

      try {
        // Mock - would update config
        spinner.succeed(`Rule ${ruleId} disabled`);
      } catch (error) {
        spinner.fail('Failed to disable rule');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  // Search rules
  cmd
    .command('search <query>')
    .description('Search for rules')
    .action(async (query) => {
      const spinner = createSpinner(`Searching for "${query}"...`);

      try {
        // Mock search results
        spinner.succeed(`Found 3 rules matching "${query}"`);
        console.log(chalk.cyan('\n• security/no-eval'));
        console.log(chalk.cyan('• security/no-dangerous-regex'));
        console.log(chalk.cyan('• security/detect-unsafe-regex'));
      } catch (error) {
        spinner.fail('Search failed');
        console.error(chalk.red(error instanceof Error ? error.message : 'Unknown error'));
        process.exit(1);
      }
    });

  return cmd;
}
