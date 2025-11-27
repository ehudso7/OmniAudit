import cliProgress from 'cli-progress';
import chalk from 'chalk';

export class ProgressBar {
  private bar: cliProgress.SingleBar;

  constructor(total: number, format?: string) {
    this.bar = new cliProgress.SingleBar({
      format: format || `${chalk.cyan('{bar}')} {percentage}% | {value}/{total} | {status}`,
      barCompleteChar: '\u2588',
      barIncompleteChar: '\u2591',
      hideCursor: true,
    });

    this.bar.start(total, 0, { status: 'Initializing...' });
  }

  update(current: number, status?: string): void {
    this.bar.update(current, { status: status || 'Processing...' });
  }

  increment(status?: string): void {
    this.bar.increment(1, { status: status || 'Processing...' });
  }

  stop(): void {
    this.bar.stop();
  }
}

export class MultiProgressBar {
  private multibar: cliProgress.MultiBar;
  private bars: Map<string, cliProgress.SingleBar>;

  constructor() {
    this.multibar = new cliProgress.MultiBar({
      clearOnComplete: false,
      hideCursor: true,
      format: `${chalk.cyan('{bar}')} | {task} | {value}/{total}`,
    });
    this.bars = new Map();
  }

  create(id: string, task: string, total: number): void {
    const bar = this.multibar.create(total, 0, { task });
    this.bars.set(id, bar);
  }

  update(id: string, value: number): void {
    const bar = this.bars.get(id);
    if (bar) {
      bar.update(value);
    }
  }

  increment(id: string, delta = 1): void {
    const bar = this.bars.get(id);
    if (bar) {
      bar.increment(delta);
    }
  }

  stop(): void {
    this.multibar.stop();
  }
}
