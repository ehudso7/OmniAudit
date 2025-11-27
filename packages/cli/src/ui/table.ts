import Table from 'cli-table3';
import chalk from 'chalk';

export interface TableColumn {
  name: string;
  align?: 'left' | 'center' | 'right';
}

export interface TableOptions {
  columns: TableColumn[];
  title?: string;
  style?: {
    head?: string[];
    border?: string[];
  };
}

export function createTable(options: TableOptions): Table.Table {
  return new Table({
    head: options.columns.map(col => chalk.bold(col.name)),
    colAligns: options.columns.map(col => col.align || 'left'),
    style: {
      head: options.style?.head || ['cyan'],
      border: options.style?.border || ['gray'],
    },
    chars: {
      'top': '─',
      'top-mid': '┬',
      'top-left': '┌',
      'top-right': '┐',
      'bottom': '─',
      'bottom-mid': '┴',
      'bottom-left': '└',
      'bottom-right': '┘',
      'left': '│',
      'left-mid': '├',
      'mid': '─',
      'mid-mid': '┼',
      'right': '│',
      'right-mid': '┤',
      'middle': '│'
    }
  });
}

export function printFindingsTable(findings: any[]): void {
  const table = createTable({
    columns: [
      { name: 'Severity' },
      { name: 'Category' },
      { name: 'Title' },
      { name: 'File' },
      { name: 'Line' },
    ],
  });

  const severityColors: Record<string, (text: string) => string> = {
    critical: chalk.bgRed.white.bold,
    high: chalk.red.bold,
    medium: chalk.yellow,
    low: chalk.blue,
    info: chalk.gray,
  };

  for (const finding of findings) {
    const colorFn = severityColors[finding.severity] || chalk.white;

    table.push([
      colorFn(finding.severity.toUpperCase()),
      finding.category,
      finding.title,
      finding.file,
      finding.line?.toString() || '-',
    ]);
  }

  console.log(table.toString());
}

export function printSummaryTable(summary: {
  total_files: number;
  total_findings: number;
  findings_by_severity: Record<string, number>;
  duration_ms: number;
}): void {
  const table = createTable({
    columns: [
      { name: 'Metric', align: 'left' },
      { name: 'Value', align: 'right' },
    ],
  });

  table.push(
    ['Total Files', chalk.cyan(summary.total_files.toString())],
    ['Total Findings', chalk.yellow(summary.total_findings.toString())],
    ['Duration', chalk.green(`${(summary.duration_ms / 1000).toFixed(2)}s`)],
    ['', ''],
    [chalk.bold('Severity Breakdown'), ''],
    ['Critical', chalk.red(summary.findings_by_severity.critical?.toString() || '0')],
    ['High', chalk.red(summary.findings_by_severity.high?.toString() || '0')],
    ['Medium', chalk.yellow(summary.findings_by_severity.medium?.toString() || '0')],
    ['Low', chalk.blue(summary.findings_by_severity.low?.toString() || '0')],
    ['Info', chalk.gray(summary.findings_by_severity.info?.toString() || '0')]
  );

  console.log(table.toString());
}
