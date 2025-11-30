# @omniaudit/sdk

Embeddable TypeScript SDK for OmniAudit with streaming and promise-based APIs.

## Installation

```bash
npm install @omniaudit/sdk
```

## Features

- **Promise-based API**: Clean async/await interface
- **Streaming API**: Real-time progress updates with async generators
- **Event-based API**: EventEmitter for reactive programming
- **Hooks API**: React-like hooks for easy integration
- **Type-safe**: Full TypeScript support
- **Configurable**: Flexible configuration with Zod validation

## Quick Start

### Promise-based API

```typescript
import { createClient } from '@omniaudit/sdk';

const client = createClient({
  apiUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',
});

// Run audit
const result = await client.audit({
  path: './src',
  rules: ['security/*', 'performance/*'],
  severity: ['critical', 'high'],
});

console.log(`Found ${result.total_findings} issues`);
```

### Streaming API

```typescript
import { createClient } from '@omniaudit/sdk';

const client = createClient({ apiUrl: 'http://localhost:8000' });

// Stream audit progress
for await (const progress of client.auditStream({ path: './src' })) {
  console.log(`${progress.stage}: ${progress.progress}%`);
  console.log(progress.message);

  if (progress.stage === 'complete') {
    // Access final result
    const result = progress;
    console.log(`Total findings: ${result.findingsCount}`);
  }
}
```

### Event-based API

```typescript
import { StreamingAuditClient } from '@omniaudit/sdk';

const client = new StreamingAuditClient('http://localhost:8000', 'api-key');

client.on('progress', (progress) => {
  console.log(`Progress: ${progress.progress}%`);
});

client.on('finding', (finding) => {
  console.log(`New finding: ${finding.title}`);
});

client.on('complete', (result) => {
  console.log(`Audit complete: ${result.total_findings} issues found`);
});

client.on('error', (error) => {
  console.error('Audit failed:', error);
});

await client.start({ path: './src' });
```

### Hooks API

```typescript
import { runAuditWithHooks } from '@omniaudit/sdk';

const result = await runAuditWithHooks(
  { path: './src' },
  {
    onProgress: (progress) => {
      updateProgressBar(progress.progress);
    },
    onFinding: (finding) => {
      logFinding(finding);
    },
    onComplete: (result) => {
      showReport(result);
    },
    onError: (error) => {
      showError(error);
    },
  },
  'http://localhost:8000'
);
```

## API Reference

### OmniAuditClient

Main client for promise-based API.

#### Methods

- `audit(request: AuditRequest): Promise<AuditResult>`
- `auditStream(request: AuditRequest): AsyncGenerator<AuditProgress, AuditResult>`
- `getFindings(filters?): Promise<Finding[]>`
- `getFinding(id: string): Promise<Finding | null>`
- `getRules(filters?): Promise<Rule[]>`
- `getRule(id: string): Promise<Rule | null>`
- `fix(findingIds: string[]): Promise<{fixed: number, failed: number}>`
- `export(auditId: string, format: string): Promise<string>`
- `getAuditHistory(limit?: number): Promise<AuditResult[]>`
- `compareAudits(baselineId: string, currentId: string): Promise<{new, fixed, unchanged}>`
- `getStatistics(period?: number): Promise<{totalAudits, totalFindings, ...}>`
- `health(): Promise<{status, version}>`

### StreamingAuditClient

Event-based client with real-time updates.

#### Events

- `progress` - Emitted during audit execution
- `finding` - Emitted when a finding is discovered
- `complete` - Emitted when audit completes
- `error` - Emitted on errors

#### Methods

- `start(request: AuditRequest): Promise<void>`
- `cancel(): void`

### Types

```typescript
interface AuditRequest {
  path: string;
  rules?: string[];
  severity?: string[];
  options?: {
    parallel?: boolean;
    maxWorkers?: number;
    timeout?: number;
    cache?: boolean;
  };
}

interface AuditResult {
  id: string;
  project: string;
  timestamp: string;
  duration_ms: number;
  total_files: number;
  total_findings: number;
  findings_by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  findings: Finding[];
  metadata?: {
    version: string;
    rules_count: number;
    analyzers: string[];
  };
}

interface Finding {
  id: string;
  rule_id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  file: string;
  line?: number;
  column?: number;
  message: string;
  recommendation?: string;
}
```

## Integration Examples

### React Integration

```typescript
import { useEffect, useState } from 'react';
import { createClient, AuditProgress } from '@omniaudit/sdk';

function AuditComponent() {
  const [progress, setProgress] = useState<AuditProgress | null>(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    const runAudit = async () => {
      const client = createClient({ apiUrl: 'http://localhost:8000' });

      for await (const prog of client.auditStream({ path: './src' })) {
        setProgress(prog);

        if (prog.stage === 'complete') {
          setResult(prog);
        }
      }
    };

    runAudit();
  }, []);

  return (
    <div>
      {progress && <ProgressBar value={progress.progress} />}
      {result && <ResultsTable findings={result.findings} />}
    </div>
  );
}
```

### Node.js CLI Integration

```typescript
import { createClient } from '@omniaudit/sdk';
import ora from 'ora';

const spinner = ora('Running audit...').start();
const client = createClient({ apiUrl: 'http://localhost:8000' });

try {
  const result = await client.audit({ path: process.cwd() });

  spinner.succeed(`Found ${result.total_findings} issues`);

  console.table(result.findings.map(f => ({
    severity: f.severity,
    file: f.file,
    line: f.line,
    message: f.message,
  })));
} catch (error) {
  spinner.fail('Audit failed');
  console.error(error);
}
```

## Examples

See the [examples](./examples) directory for complete working examples:

- **[basic-audit.ts](./examples/basic-audit.ts)** - Simple audit with Promise API
- **[streaming-audit.ts](./examples/streaming-audit.ts)** - Real-time progress tracking with AsyncGenerator, EventEmitter, and Hooks
- **[react-integration.tsx](./examples/react-integration.tsx)** - Full React integration with custom hooks and components
- **[ci-integration.ts](./examples/ci-integration.ts)** - GitHub Actions and GitLab CI integration with quality gates
- **[batch-processing.ts](./examples/batch-processing.ts)** - Auditing multiple projects with concurrency control
- **[custom-reporters.ts](./examples/custom-reporters.ts)** - Creating custom output formats (Markdown, HTML, JUnit, Slack, GitHub)

### Running Examples

```bash
# Install dependencies
pnpm install

# Run an example
npx tsx examples/basic-audit.ts

# With environment variables
OMNIAUDIT_API_URL=https://api.omniaudit.dev \
OMNIAUDIT_API_KEY=sk-your-key \
npx tsx examples/streaming-audit.ts
```

## License

MIT
