import ora, { Ora } from 'ora';
import chalk from 'chalk';

export class Spinner {
  private spinner: Ora | null = null;

  start(text: string): void {
    this.spinner = ora({
      text,
      spinner: 'dots',
      color: 'cyan',
    }).start();
  }

  update(text: string): void {
    if (this.spinner) {
      this.spinner.text = text;
    }
  }

  succeed(text?: string): void {
    if (this.spinner) {
      this.spinner.succeed(text || this.spinner.text);
      this.spinner = null;
    }
  }

  fail(text?: string): void {
    if (this.spinner) {
      this.spinner.fail(text || this.spinner.text);
      this.spinner = null;
    }
  }

  warn(text?: string): void {
    if (this.spinner) {
      this.spinner.warn(text || this.spinner.text);
      this.spinner = null;
    }
  }

  info(text?: string): void {
    if (this.spinner) {
      this.spinner.info(text || this.spinner.text);
      this.spinner = null;
    }
  }

  stop(): void {
    if (this.spinner) {
      this.spinner.stop();
      this.spinner = null;
    }
  }

  clear(): void {
    if (this.spinner) {
      this.spinner.clear();
    }
  }
}

export function createSpinner(text: string): Spinner {
  const spinner = new Spinner();
  spinner.start(text);
  return spinner;
}
