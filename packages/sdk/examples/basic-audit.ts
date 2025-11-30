/**
 * Basic Audit Example
 *
 * Demonstrates the simplest way to run an audit using the OmniAudit SDK.
 */

import { createClient, audit } from '@omniaudit/sdk';

async function main() {
  // Option 1: Quick one-liner audit
  console.log('Running quick audit...\n');
  const quickResult = await audit('./src');

  console.log('Quick Audit Results:');
  console.log(`  Project: ${quickResult.project}`);
  console.log(`  Total files: ${quickResult.total_files}`);
  console.log(`  Total findings: ${quickResult.total_findings}`);
  console.log('');

  // Option 2: Full client with configuration
  console.log('Running configured audit...\n');

  const client = createClient({
    apiUrl: process.env.OMNIAUDIT_API_URL || 'http://localhost:8000',
    apiKey: process.env.OMNIAUDIT_API_KEY,
    timeout: 60000,
    retries: 3,
  });

  // Check API health first
  const health = await client.health();
  console.log(`API Status: ${health.status} (v${health.version})`);

  // Run the audit
  const result = await client.audit({
    path: './src',
    rules: ['security/*', 'quality/*'],
    severity: ['critical', 'high', 'medium'],
    options: {
      parallel: true,
      maxWorkers: 4,
      cache: true,
    },
  });

  // Display results
  console.log('\nAudit Complete!');
  console.log('================');
  console.log(`Audit ID: ${result.id}`);
  console.log(`Duration: ${result.duration_ms}ms`);
  console.log(`Files analyzed: ${result.total_files}`);
  console.log('');

  console.log('Findings by Severity:');
  console.log(`  Critical: ${result.findings_by_severity.critical}`);
  console.log(`  High: ${result.findings_by_severity.high}`);
  console.log(`  Medium: ${result.findings_by_severity.medium}`);
  console.log(`  Low: ${result.findings_by_severity.low}`);
  console.log(`  Info: ${result.findings_by_severity.info}`);
  console.log('');

  // Display top findings
  if (result.findings.length > 0) {
    console.log('Top Findings:');
    console.log('-'.repeat(60));

    const topFindings = result.findings
      .filter((f) => f.severity === 'critical' || f.severity === 'high')
      .slice(0, 5);

    for (const finding of topFindings) {
      console.log(`[${finding.severity.toUpperCase()}] ${finding.title}`);
      console.log(`  File: ${finding.file}:${finding.line}`);
      console.log(`  Message: ${finding.message}`);
      if (finding.recommendation) {
        console.log(`  Recommendation: ${finding.recommendation}`);
      }
      console.log('');
    }
  }
}

main().catch(console.error);
