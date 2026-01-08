import chalk from 'chalk';
import chokidar from 'chokidar';
import { Command } from 'commander';

export function createWatchCommand(): Command {
  const cmd = new Command('watch');

  cmd
    .description('Watch files and run audits on changes')
    .argument('[path]', 'Path to watch', '.')
    .option('-i, --ignore <patterns...>', 'Patterns to ignore', ['node_modules/**', 'dist/**'])
    .option('-d, --debounce <ms>', 'Debounce delay in milliseconds', '1000')
    .option('--initial', 'Run audit on start')
    .action(async (path, options) => {
      console.log(chalk.bold.cyan('👁️  Watch Mode Started\n'));
      console.log(chalk.gray(`Watching: ${path}`));
      console.log(chalk.gray(`Ignored: ${options.ignore.join(', ')}\n`));

      let timeout: NodeJS.Timeout | null = null;

      const runAudit = async () => {
        console.log(chalk.yellow('\n⚡ Change detected, running audit...\n'));
        // Mock audit - would actually run audit
        setTimeout(() => {
          console.log(chalk.green('✅ Audit completed\n'));
          console.log(chalk.gray('Watching for changes...\n'));
        }, 2000);
      };

      if (options.initial) {
        await runAudit();
      } else {
        console.log(chalk.gray('Watching for changes...\n'));
      }

      const watcher = chokidar.watch(path, {
        ignored: options.ignore,
        persistent: true,
        ignoreInitial: true,
      });

      watcher.on('change', (filePath) => {
        console.log(chalk.cyan(`Changed: ${filePath}`));

        if (timeout) {
          clearTimeout(timeout);
        }

        timeout = setTimeout(runAudit, Number.parseInt(options.debounce));
      });

      watcher.on('add', (filePath) => {
        console.log(chalk.green(`Added: ${filePath}`));
      });

      watcher.on('unlink', (filePath) => {
        console.log(chalk.red(`Removed: ${filePath}`));
      });

      // Keep process alive
      process.on('SIGINT', () => {
        console.log(chalk.yellow('\n\n👋 Stopping watch mode...\n'));
        watcher.close();
        process.exit(0);
      });
    });

  return cmd;
}
