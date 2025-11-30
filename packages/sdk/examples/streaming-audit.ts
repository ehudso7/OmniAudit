/**
 * Streaming Audit Example
 *
 * Demonstrates real-time progress tracking using the streaming API.
 */

import { createClient, StreamingAuditClient, runAuditWithHooks } from '@omniaudit/sdk';
import type { AuditProgress, Finding } from '@omniaudit/sdk';

// Helper to create a progress bar
function progressBar(percent: number, width = 30): string {
  const filled = Math.round((percent / 100) * width);
  const empty = width - filled;
  return `[${'█'.repeat(filled)}${'░'.repeat(empty)}] ${percent.toFixed(0)}%`;
}

// Example 1: AsyncGenerator streaming
async function streamWithGenerator() {
  console.log('=== AsyncGenerator Streaming ===\n');

  const client = createClient({
    apiUrl: process.env.OMNIAUDIT_API_URL || 'http://localhost:8000',
    apiKey: process.env.OMNIAUDIT_API_KEY,
  });

  const stream = client.auditStream({ path: './src' });

  for await (const progress of stream) {
    // Clear line and print progress
    process.stdout.write(`\r${progressBar(progress.progress)} ${progress.message}`);

    if (progress.filesScanned !== undefined) {
      process.stdout.write(` (${progress.filesScanned}/${progress.totalFiles} files)`);
    }

    if (progress.findingsCount !== undefined) {
      process.stdout.write(` - ${progress.findingsCount} findings`);
    }

    // Clear to end of line
    process.stdout.write('\x1b[K');
  }

  console.log('\n\nAudit completed!\n');
}

// Example 2: EventEmitter streaming
async function streamWithEvents() {
  console.log('=== EventEmitter Streaming ===\n');

  const client = new StreamingAuditClient(
    process.env.OMNIAUDIT_API_URL || 'http://localhost:8000',
    process.env.OMNIAUDIT_API_KEY
  );

  const findings: Finding[] = [];

  // Set up event handlers
  client.on('progress', (progress: AuditProgress) => {
    process.stdout.write(`\r${progressBar(progress.progress)} ${progress.stage}`);
    process.stdout.write('\x1b[K');
  });

  client.on('finding', (finding: Finding) => {
    findings.push(finding);
    // Show critical findings immediately
    if (finding.severity === 'critical') {
      console.log(`\n  🚨 CRITICAL: ${finding.title} in ${finding.file}:${finding.line}`);
    }
  });

  client.on('complete', (result) => {
    console.log('\n');
    console.log('Audit Complete!');
    console.log(`Total findings: ${result.total_findings}`);
    console.log(`Duration: ${result.duration_ms}ms`);
  });

  client.on('error', (error) => {
    console.error('\nAudit failed:', error.message);
  });

  // Start the audit
  await client.start({ path: './src' });
}

// Example 3: Hooks-based streaming (great for React)
async function streamWithHooks() {
  console.log('=== Hooks-based Streaming ===\n');

  let lastProgress = 0;
  const allFindings: Finding[] = [];

  const result = await runAuditWithHooks(
    { path: './src' },
    {
      onProgress: (progress) => {
        // Only update when progress changes significantly
        if (progress.progress - lastProgress >= 5 || progress.stage === 'complete') {
          process.stdout.write(`\r${progressBar(progress.progress)} ${progress.message}\x1b[K`);
          lastProgress = progress.progress;
        }
      },
      onFinding: (finding) => {
        allFindings.push(finding);
      },
      onComplete: (result) => {
        console.log('\n');
        console.log('✅ Audit completed successfully!');
        console.log(`   Analyzed ${result.total_files} files`);
        console.log(`   Found ${result.total_findings} issues`);
      },
      onError: (error) => {
        console.error('\n❌ Audit failed:', error.message);
      },
    },
    process.env.OMNIAUDIT_API_URL || 'http://localhost:8000',
    process.env.OMNIAUDIT_API_KEY
  );

  // Group findings by severity
  const bySeverity = allFindings.reduce(
    (acc, f) => {
      acc[f.severity] = (acc[f.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  console.log('\nFindings breakdown:');
  for (const [severity, count] of Object.entries(bySeverity)) {
    console.log(`  ${severity}: ${count}`);
  }

  return result;
}

// Main execution
async function main() {
  console.log('OmniAudit Streaming Examples\n');
  console.log('This example demonstrates three different streaming approaches:\n');

  try {
    // Run all examples
    await streamWithGenerator();
    console.log('\n' + '-'.repeat(60) + '\n');

    await streamWithEvents();
    console.log('\n' + '-'.repeat(60) + '\n');

    await streamWithHooks();
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
