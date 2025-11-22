#!/usr/bin/env bun

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import * as dotenv from 'dotenv';
import { OmniAuditSkillsEngine } from '../core/skills-engine';
import { getAllBuiltinSkills, getBuiltinSkill } from '../skills/index';
import { db } from '../db/client';
import type { CodeInput, SkillExecutionResult } from '../types/index';

dotenv.config();

const program = new Command();

program
  .name('omniaudit')
  .description('Universal AI Coding Optimization Framework')
  .version('1.0.0');

// ==================== ANALYZE COMMAND ====================

program
  .command('analyze')
  .description('Analyze code using specified skills')
  .argument('<files...>', 'Files or patterns to analyze')
  .option('-s, --skills <skills...>', 'Skills to use (space-separated)')
  .option('-o, --output <file>', 'Output file for results')
  .option('--auto-fix', 'Automatically apply fixes')
  .option('--format <format>', 'Output format (json|markdown|terminal)', 'terminal')
  .option('--max-issues <number>', 'Maximum issues to report', parseInt)
  .option('--severity <levels...>', 'Filter by severity (error|warning|info)')
  .option('--no-cache', 'Disable caching')
  .action(async (files, options) => {
    const spinner = ora('Initializing OmniAudit...').start();

    try {
      // Initialize engine
      const engine = new OmniAuditSkillsEngine({
        anthropicApiKey: process.env.ANTHROPIC_API_KEY!,
        tursoUrl: process.env.TURSO_URL!,
        tursoToken: process.env.TURSO_TOKEN!,
        upstashUrl: process.env.UPSTASH_URL!,
        upstashToken: process.env.UPSTASH_TOKEN!,
        sentryDsn: process.env.SENTRY_DSN,
      });

      // Determine skills to use
      const skills = options.skills || ['performance-optimizer-pro'];
      spinner.text = 'Loading skills...';

      for (const skillId of skills) {
        try {
          await engine.activateSkill(skillId);
          spinner.succeed(`Loaded skill: ${skillId}`);
          spinner.start();
        } catch (error) {
          spinner.fail(`Failed to load skill: ${skillId}`);
          console.error(chalk.red(error instanceof Error ? error.message : String(error)));
          process.exit(1);
        }
      }

      // Analyze files
      const allResults: SkillExecutionResult[] = [];

      for (const file of files) {
        if (!existsSync(file)) {
          console.warn(chalk.yellow(`File not found: ${file}`));
          continue;
        }

        spinner.text = `Analyzing ${file}...`;
        const code = readFileSync(file, 'utf-8');
        const language = detectLanguage(file);

        const input: CodeInput = {
          code,
          language,
          file_path: file,
        };

        for (const skillId of skills) {
          try {
            const result = await engine.executeSkill(skillId, input, {
              autoFix: options.autoFix,
              skipCache: options.noCache,
              maxIssues: options.maxIssues,
              severityFilter: options.severity,
            });

            allResults.push(result);
            spinner.succeed(`${file} analyzed with ${skillId}`);
            spinner.start();
          } catch (error) {
            spinner.fail(`Failed to analyze ${file} with ${skillId}`);
            console.error(chalk.red(error instanceof Error ? error.message : String(error)));
          }
        }
      }

      spinner.stop();

      // Display results
      displayResults(allResults, options.format);

      // Save if output specified
      if (options.output) {
        const outputData =
          options.format === 'json'
            ? JSON.stringify(allResults, null, 2)
            : formatAsMarkdown(allResults);
        writeFileSync(options.output, outputData);
        console.log(chalk.green(`\n✓ Results saved to ${options.output}`));
      }

      // Exit with error code if critical issues found
      const hasCriticalIssues = allResults.some(
        (r) => r.metrics && r.metrics.issues_found > 0,
      );
      if (hasCriticalIssues) {
        process.exit(1);
      }
    } catch (error) {
      spinner.fail('Analysis failed');
      console.error(chalk.red(error instanceof Error ? error.message : String(error)));
      process.exit(1);
    }
  });

// ==================== SKILLS COMMAND ====================

program
  .command('skills')
  .description('Manage skills')
  .option('-l, --list', 'List installed skills')
  .option('-s, --search <query>', 'Search marketplace')
  .option('-i, --install <skill-id>', 'Install skill')
  .option('-r, --remove <skill-id>', 'Remove skill')
  .option('-v, --view <skill-id>', 'View skill details')
  .action(async (options) => {
    try {
      if (options.list) {
        // List all available skills
        console.log(chalk.bold.cyan('\n📦 Available Skills:\n'));

        const builtinSkills = getAllBuiltinSkills();
        console.log(chalk.bold('Built-in Skills:'));
        for (const skill of builtinSkills) {
          console.log(
            `  ${chalk.green('●')} ${chalk.bold(skill.metadata.name)} (${skill.skill_id}@${skill.version})`,
          );
          console.log(`    ${chalk.gray(skill.metadata.description)}`);
          console.log(`    ${chalk.gray(`Category: ${skill.metadata.category}`)}`);
          console.log();
        }

        // List custom skills from database
        const customSkills = await db.listSkills({ is_public: true, limit: 100 });
        if (customSkills.length > 0) {
          console.log(chalk.bold('\nCustom Skills:'));
          for (const skillRow of customSkills) {
            const skill = JSON.parse(skillRow.definition as string);
            console.log(
              `  ${chalk.blue('●')} ${chalk.bold(skill.metadata.name)} (${skill.skill_id}@${skill.version})`,
            );
            console.log(`    ${chalk.gray(skill.metadata.description)}`);
          }
        }
      } else if (options.view) {
        // View skill details
        const skill = getBuiltinSkill(options.view);
        if (skill) {
          displaySkillDetails(skill);
        } else {
          console.error(chalk.red(`Skill not found: ${options.view}`));
          process.exit(1);
        }
      } else if (options.search) {
        // Search marketplace
        console.log(chalk.yellow('Marketplace search not yet implemented'));
      } else if (options.install) {
        // Install skill
        console.log(chalk.yellow('Skill installation not yet implemented'));
      } else if (options.remove) {
        // Remove skill
        console.log(chalk.yellow('Skill removal not yet implemented'));
      } else {
        program.commands.find((cmd) => cmd.name() === 'skills')?.help();
      }
    } catch (error) {
      console.error(chalk.red('Skills command failed:'), error);
      process.exit(1);
    }
  });

// ==================== INIT COMMAND ====================

program
  .command('init')
  .description('Initialize OmniAudit in project')
  .option('-t, --template <template>', 'Template to use (default|react|nextjs|node)')
  .option('--with-hooks', 'Setup pre-commit hooks')
  .option('--with-ci', 'Generate CI configuration')
  .action(async (options) => {
    const spinner = ora('Initializing OmniAudit project...').start();

    try {
      const template = options.template || 'default';

      // Create config file
      const configContent = generateConfigFile(template);
      writeFileSync('omniaudit.config.ts', configContent);
      spinner.succeed('Created omniaudit.config.ts');

      // Setup pre-commit hooks
      if (options.withHooks) {
        spinner.start('Setting up pre-commit hooks...');
        const hookContent = generatePreCommitHook();
        writeFileSync('.git/hooks/pre-commit', hookContent, { mode: 0o755 });
        spinner.succeed('Pre-commit hook installed');
      }

      // Generate CI configuration
      if (options.withCi) {
        spinner.start('Generating CI configuration...');
        const ciConfig = generateCIConfig();
        writeFileSync('.github/workflows/omniaudit.yml', ciConfig);
        spinner.succeed('Created .github/workflows/omniaudit.yml');
      }

      spinner.stop();
      console.log(chalk.green('\n✅ OmniAudit initialized successfully!\n'));
      console.log(chalk.gray('Next steps:'));
      console.log(chalk.gray('  1. Edit omniaudit.config.ts to customize settings'));
      console.log(chalk.gray('  2. Run: omniaudit analyze <files>'));
      console.log(chalk.gray('  3. View available skills: omniaudit skills --list\n'));
    } catch (error) {
      spinner.fail('Initialization failed');
      console.error(chalk.red(error instanceof Error ? error.message : String(error)));
      process.exit(1);
    }
  });

// ==================== CONFIG COMMAND ====================

program
  .command('config')
  .description('Manage OmniAudit configuration')
  .option('--show', 'Show current configuration')
  .option('--set <key=value>', 'Set configuration value')
  .option('--get <key>', 'Get configuration value')
  .action(async (options) => {
    if (options.show) {
      const configPath = 'omniaudit.config.ts';
      if (existsSync(configPath)) {
        const config = readFileSync(configPath, 'utf-8');
        console.log(chalk.bold('\nCurrent Configuration:\n'));
        console.log(config);
      } else {
        console.error(chalk.red('Configuration file not found. Run: omniaudit init'));
        process.exit(1);
      }
    } else {
      console.log(chalk.yellow('Config management not yet implemented'));
    }
  });

// ==================== REPORT COMMAND ====================

program
  .command('report')
  .description('Generate analysis reports')
  .argument('<execution-id>', 'Execution ID to generate report for')
  .option('-f, --format <format>', 'Report format (html|pdf|markdown)', 'markdown')
  .option('-o, --output <file>', 'Output file')
  .action(async (_executionId, _options) => {
    console.log(chalk.yellow('Report generation not yet implemented'));
  });

program.parse();

// ==================== HELPER FUNCTIONS ====================

function detectLanguage(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase();
  const languageMap: Record<string, string> = {
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    py: 'python',
    rs: 'rust',
    go: 'go',
    java: 'java',
  };
  return languageMap[ext || ''] || 'javascript';
}

function displayResults(results: SkillExecutionResult[], format: string): void {
  if (format === 'json') {
    console.log(JSON.stringify(results, null, 2));
    return;
  }

  // Terminal output
  for (const result of results) {
    console.log(chalk.bold(`\n${'='.repeat(70)}`));
    console.log(chalk.bold.cyan(`Skill: ${result.skill_id}`));
    console.log(chalk.bold(`${'='.repeat(70)}\n`));

    if (!result.success) {
      console.log(chalk.red(`✗ Failed: ${result.error?.message}`));
      continue;
    }

    console.log(chalk.gray(`Execution time: ${result.execution_time_ms}ms`));
    console.log(chalk.gray(`Files analyzed: ${result.metrics?.files_analyzed || 0}`));

    if (result.metrics) {
      console.log(chalk.bold('\n📊 Summary:'));
      console.log(chalk.red(`  Errors:      ${result.metrics.issues_found}`));
      console.log(chalk.yellow(`  Warnings:    ${result.metrics.warnings_found}`));
      console.log(chalk.blue(`  Suggestions: ${result.metrics.suggestions_found}`));
    }

    if (result.optimizations && result.optimizations.length > 0) {
      console.log(chalk.bold('\n🔍 Issues Found:\n'));

      for (const opt of result.optimizations.slice(0, 10)) {
        const icon = opt.severity === 'error' ? '❌' : opt.severity === 'warning' ? '⚠️' : 'ℹ️';
        const color =
          opt.severity === 'error'
            ? chalk.red
            : opt.severity === 'warning'
              ? chalk.yellow
              : chalk.blue;

        console.log(color(`${icon} ${opt.title}`));
        console.log(chalk.gray(`   ${opt.location.file}:${opt.location.line}`));
        console.log(chalk.gray(`   ${opt.description.slice(0, 100)}...`));

        if (opt.auto_fixable) {
          console.log(chalk.green(`   ✓ Auto-fixable`));
        }
        console.log();
      }

      if (result.optimizations.length > 10) {
        console.log(
          chalk.gray(`   ... and ${result.optimizations.length - 10} more issues\n`),
        );
      }
    }

    if (result.transformed_code) {
      console.log(chalk.bold('✨ Code Transformations Applied\n'));
    }
  }

  // Summary
  const totalIssues = results.reduce((sum, r) => sum + (r.metrics?.issues_found || 0), 0);
  const totalWarnings = results.reduce((sum, r) => sum + (r.metrics?.warnings_found || 0), 0);
  const totalSuggestions = results.reduce(
    (sum, r) => sum + (r.metrics?.suggestions_found || 0),
    0,
  );

  console.log(chalk.bold('\n' + '='.repeat(70)));
  console.log(chalk.bold('TOTAL SUMMARY'));
  console.log(chalk.bold('='.repeat(70)));
  console.log(chalk.red(`Errors:      ${totalIssues}`));
  console.log(chalk.yellow(`Warnings:    ${totalWarnings}`));
  console.log(chalk.blue(`Suggestions: ${totalSuggestions}\n`));
}

function displaySkillDetails(skill: any): void {
  console.log(chalk.bold.cyan(`\n${skill.metadata.name}\n`));
  console.log(chalk.gray(skill.metadata.description));
  console.log();
  console.log(chalk.bold('Details:'));
  console.log(`  ID:         ${skill.skill_id}`);
  console.log(`  Version:    ${skill.version}`);
  console.log(`  Category:   ${skill.metadata.category}`);
  console.log(`  Author:     ${skill.metadata.author}`);
  console.log(`  License:    ${skill.metadata.license}`);
  console.log(`  Languages:  ${skill.metadata.language.join(', ')}`);
  if (skill.metadata.framework) {
    console.log(`  Frameworks: ${skill.metadata.framework.join(', ')}`);
  }
  console.log();
  console.log(chalk.bold('Analyzers:'));
  for (const analyzer of skill.capabilities.analyzers) {
    console.log(`  - ${analyzer.name} (${analyzer.type})`);
  }
  console.log();
  console.log(chalk.bold('Pricing:'));
  console.log(`  Type: ${skill.pricing?.type || 'free'}`);
  if (skill.pricing?.price_usd) {
    console.log(`  Price: $${skill.pricing.price_usd}`);
  }
  console.log();
}

function formatAsMarkdown(results: SkillExecutionResult[]): string {
  let markdown = '# OmniAudit Analysis Report\n\n';

  for (const result of results) {
    markdown += `## ${result.skill_id}\n\n`;
    markdown += `- **Execution Time**: ${result.execution_time_ms}ms\n`;
    markdown += `- **Files Analyzed**: ${result.metrics?.files_analyzed || 0}\n`;
    markdown += `- **Errors**: ${result.metrics?.issues_found || 0}\n`;
    markdown += `- **Warnings**: ${result.metrics?.warnings_found || 0}\n`;
    markdown += `- **Suggestions**: ${result.metrics?.suggestions_found || 0}\n\n`;

    if (result.optimizations && result.optimizations.length > 0) {
      markdown += '### Issues Found\n\n';
      for (const opt of result.optimizations) {
        markdown += `#### ${opt.severity.toUpperCase()}: ${opt.title}\n\n`;
        markdown += `- **Location**: ${opt.location.file}:${opt.location.line}\n`;
        markdown += `- **Description**: ${opt.description}\n`;
        markdown += `- **Auto-fixable**: ${opt.auto_fixable ? 'Yes' : 'No'}\n\n`;
      }
    }
  }

  return markdown;
}

function generateConfigFile(_template: string): string {
  return `import { OmniAuditConfig } from 'omniaudit';

export default {
  // Default skills to activate
  skills: [
    'performance-optimizer-pro',
    'security-auditor-enterprise',
  ],

  // Analysis settings
  analysis: {
    strategy: 'comprehensive',
    parallel: true,
    cache: true,
  },

  // Auto-fix settings
  autoFix: {
    enabled: false,
    on_save: false,
    require_confirmation: true,
  },

  // Integrations
  integrations: {
    vscode: true,
    github: true,
    pre_commit_hook: true,
  },

  // AI settings
  ai: {
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 8000,
    temperature: 0.3,
  },

  // Exclusions
  exclude: [
    'node_modules/**',
    'dist/**',
    '*.test.ts',
    '*.spec.ts',
  ],

  // Custom rules
  rules: {
    'max-file-size': 5000,
    'max-function-length': 100,
    'max-complexity': 15,
  },
} satisfies OmniAuditConfig;
`;
}

function generatePreCommitHook(): string {
  return `#!/bin/bash
# OmniAudit pre-commit hook

echo "Running OmniAudit..."

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(ts|tsx|js|jsx)$')

if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

# Run OmniAudit
omniaudit analyze $STAGED_FILES --format terminal

if [ $? -ne 0 ]; then
  echo "❌ OmniAudit found issues. Commit aborted."
  echo "Run 'omniaudit analyze <file> --auto-fix' to fix automatically."
  exit 1
fi

echo "✅ OmniAudit passed!"
exit 0
`;
}

function generateCIConfig(): string {
  return `name: OmniAudit Code Quality

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1

      - name: Install OmniAudit
        run: bun add -g omniaudit

      - name: Run Analysis
        run: |
          omniaudit analyze src/ \\
            --skills performance-optimizer-pro security-auditor-enterprise \\
            --format json \\
            --output results.json
        env:
          ANTHROPIC_API_KEY: \${{ secrets.ANTHROPIC_API_KEY }}

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: omniaudit-results
          path: results.json
`;
}
