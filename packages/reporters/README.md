# @omniaudit/reporters

Comprehensive reporting and output formats for OmniAudit with 16 different export formats.

## Installation

```bash
npm install @omniaudit/reporters
```

## Features

- **16 Output Formats**: JSON, SARIF, Markdown, HTML, PDF, JUnit, Checkstyle, GitLab, GitHub, SonarQube, Code Climate, CSV, Slack, JIRA, Linear, Notion
- **Type-Safe**: Full TypeScript support with Zod validation
- **Extensible**: Easy to add custom reporters
- **CI/CD Ready**: Formats compatible with major CI/CD platforms

## Usage

### Basic Usage

```typescript
import { generateReport, getReporter } from '@omniaudit/reporters';

const auditResult = {
  id: 'audit-123',
  project: 'my-project',
  timestamp: new Date().toISOString(),
  duration_ms: 5000,
  total_files: 100,
  total_findings: 15,
  findings_by_severity: {
    critical: 2,
    high: 5,
    medium: 6,
    low: 2,
    info: 0,
  },
  findings: [/* ... */],
};

// Generate JSON report
const jsonReport = await generateReport(auditResult, 'json', { pretty: true });

// Generate SARIF report
const sarifReport = await generateReport(auditResult, 'sarif');

// Generate HTML report
const htmlReport = await generateReport(auditResult, 'html');
```

### Using Reporter Manager

```typescript
import { ReporterManager } from '@omniaudit/reporters';

const manager = new ReporterManager();

// Generate multiple formats
const reports = await manager.generateMultiple(
  auditResult,
  ['json', 'html', 'sarif'],
  { pretty: true }
);

// Save to files
for (const [format, content] of reports) {
  await fs.writeFile(`report.${format}`, content);
}
```

### Custom Reporter

```typescript
import { Reporter, AuditResult, ReporterOptions } from '@omniaudit/reporters';

class CustomReporter implements Reporter {
  name = 'Custom Reporter';
  format = 'custom';

  async generate(result: AuditResult, options?: ReporterOptions): Promise<string> {
    // Your custom logic here
    return 'custom report content';
  }
}

const manager = new ReporterManager();
manager.register('custom', new CustomReporter());
```

## Available Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `json` | Structured JSON output | API integration, data processing |
| `sarif` | SARIF 2.1.0 format | GitHub Code Scanning, Visual Studio |
| `markdown` | GitHub-flavored Markdown | Documentation, PR comments |
| `html` | Interactive HTML report | Human-readable dashboards |
| `pdf` | PDF document | Executive reports, archiving |
| `junit` | JUnit XML format | Jenkins, CI/CD pipelines |
| `checkstyle` | Checkstyle XML format | Java tooling, IDEs |
| `gitlab` | GitLab Code Quality | GitLab CI/CD |
| `github` | GitHub Actions format | GitHub CI/CD |
| `sonarqube` | SonarQube Generic Issue | SonarQube integration |
| `codeclimate` | Code Climate format | Code Climate integration |
| `csv` | Comma-separated values | Excel, data analysis |
| `slack` | Slack Block Kit | Slack notifications |
| `jira` | JIRA issue format | JIRA integration |
| `linear` | Linear issue format | Linear integration |
| `notion` | Notion database format | Notion integration |

## License

MIT
