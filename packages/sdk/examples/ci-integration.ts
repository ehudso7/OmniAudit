/**
 * CI/CD Integration Example
 *
 * Demonstrates how to integrate OmniAudit with CI/CD pipelines.
 * Includes GitHub Actions, GitLab CI, and generic CI examples.
 */

import { createClient, audit } from '@omniaudit/sdk';
import type { AuditResult, Finding } from '@omniaudit/sdk';

// Configuration from environment variables
const config = {
  apiUrl: process.env.OMNIAUDIT_API_URL || 'https://api.omniaudit.dev',
  apiKey: process.env.OMNIAUDIT_API_KEY,
  projectPath: process.env.PROJECT_PATH || '.',
  failOnCritical: process.env.FAIL_ON_CRITICAL !== 'false',
  failOnHigh: process.env.FAIL_ON_HIGH === 'true',
  maxFindings: parseInt(process.env.MAX_FINDINGS || '0', 10),
  baselineAuditId: process.env.BASELINE_AUDIT_ID,
};

// Exit codes for CI
const EXIT_CODES = {
  SUCCESS: 0,
  CRITICAL_FINDINGS: 1,
  HIGH_FINDINGS: 2,
  MAX_FINDINGS_EXCEEDED: 3,
  NEW_ISSUES_FOUND: 4,
  AUDIT_FAILED: 5,
};

// ANSI colors for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

function printHeader(text: string) {
  console.log(`\n${colors.bold}${colors.cyan}${'='.repeat(60)}${colors.reset}`);
  console.log(`${colors.bold}${colors.cyan}  ${text}${colors.reset}`);
  console.log(`${colors.cyan}${'='.repeat(60)}${colors.reset}\n`);
}

function printSection(title: string) {
  console.log(`\n${colors.bold}${title}${colors.reset}`);
  console.log(`${colors.blue}${'-'.repeat(40)}${colors.reset}`);
}

function severityColor(severity: string): string {
  switch (severity) {
    case 'critical':
      return colors.red;
    case 'high':
      return colors.magenta;
    case 'medium':
      return colors.yellow;
    case 'low':
      return colors.blue;
    default:
      return colors.reset;
  }
}

function printFinding(finding: Finding, index: number) {
  const color = severityColor(finding.severity);
  console.log(`${color}${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}${colors.reset}`);
  console.log(`   File: ${finding.file}:${finding.line || 0}`);
  console.log(`   Rule: ${finding.rule_id}`);
  console.log(`   ${finding.message}`);
  console.log('');
}

async function runCIAudit(): Promise<number> {
  printHeader('OmniAudit CI/CD Pipeline');

  console.log('Configuration:');
  console.log(`  API URL: ${config.apiUrl}`);
  console.log(`  Project: ${config.projectPath}`);
  console.log(`  Fail on critical: ${config.failOnCritical}`);
  console.log(`  Fail on high: ${config.failOnHigh}`);
  console.log(`  Max findings: ${config.maxFindings || 'unlimited'}`);

  const client = createClient({
    apiUrl: config.apiUrl,
    apiKey: config.apiKey,
    timeout: 300000, // 5 minutes for CI
  });

  try {
    // Run the audit
    printSection('Running Audit');
    console.log(`Analyzing ${config.projectPath}...`);

    const result = await client.audit({
      path: config.projectPath,
      options: {
        parallel: true,
        cache: false, // Don't cache in CI
      },
    });

    // Print summary
    printSection('Audit Summary');
    console.log(`Audit ID: ${result.id}`);
    console.log(`Duration: ${result.duration_ms}ms`);
    console.log(`Files analyzed: ${result.total_files}`);
    console.log(`Total findings: ${result.total_findings}`);
    console.log('');
    console.log('By severity:');
    console.log(`  ${colors.red}Critical: ${result.findings_by_severity.critical}${colors.reset}`);
    console.log(`  ${colors.magenta}High: ${result.findings_by_severity.high}${colors.reset}`);
    console.log(`  ${colors.yellow}Medium: ${result.findings_by_severity.medium}${colors.reset}`);
    console.log(`  ${colors.blue}Low: ${result.findings_by_severity.low}${colors.reset}`);
    console.log(`  Info: ${result.findings_by_severity.info}`);

    // Compare with baseline if provided
    if (config.baselineAuditId) {
      printSection('Baseline Comparison');
      const comparison = await client.compareAudits(config.baselineAuditId, result.id);

      console.log(`New issues: ${comparison.new.length}`);
      console.log(`Fixed issues: ${comparison.fixed.length}`);
      console.log(`Unchanged: ${comparison.unchanged.length}`);

      if (comparison.new.length > 0) {
        console.log(`\n${colors.red}New issues introduced:${colors.reset}`);
        comparison.new.slice(0, 10).forEach((f, i) => printFinding(f, i));

        // Fail if new critical/high issues
        const newCritical = comparison.new.filter((f) => f.severity === 'critical');
        const newHigh = comparison.new.filter((f) => f.severity === 'high');

        if (newCritical.length > 0 && config.failOnCritical) {
          console.log(`\n${colors.red}${colors.bold}❌ FAILED: ${newCritical.length} new critical issues found${colors.reset}`);
          return EXIT_CODES.NEW_ISSUES_FOUND;
        }

        if (newHigh.length > 0 && config.failOnHigh) {
          console.log(`\n${colors.red}${colors.bold}❌ FAILED: ${newHigh.length} new high severity issues found${colors.reset}`);
          return EXIT_CODES.NEW_ISSUES_FOUND;
        }
      }
    }

    // Print findings
    if (result.findings.length > 0) {
      printSection('Findings');
      const criticalAndHigh = result.findings.filter(
        (f) => f.severity === 'critical' || f.severity === 'high'
      );
      criticalAndHigh.slice(0, 20).forEach((f, i) => printFinding(f, i));

      if (criticalAndHigh.length > 20) {
        console.log(`... and ${criticalAndHigh.length - 20} more critical/high findings`);
      }
    }

    // Generate SARIF report for GitHub Code Scanning
    if (process.env.GITHUB_ACTIONS) {
      printSection('Generating SARIF Report');
      const sarif = await client.export(result.id, 'sarif');
      const sarifPath = process.env.SARIF_OUTPUT || 'omniaudit-results.sarif';

      // In a real implementation, write to file
      console.log(`SARIF report would be written to: ${sarifPath}`);
      console.log('Upload to GitHub Code Scanning with:');
      console.log('  - uses: github/codeql-action/upload-sarif@v2');
      console.log(`    with: { sarif_file: '${sarifPath}' }`);
    }

    // Check failure conditions
    printSection('Quality Gates');

    // Check for critical findings
    if (config.failOnCritical && result.findings_by_severity.critical > 0) {
      console.log(`${colors.red}${colors.bold}❌ FAILED: ${result.findings_by_severity.critical} critical findings${colors.reset}`);
      return EXIT_CODES.CRITICAL_FINDINGS;
    }
    console.log(`${colors.green}✓ No critical findings${colors.reset}`);

    // Check for high findings
    if (config.failOnHigh && result.findings_by_severity.high > 0) {
      console.log(`${colors.red}${colors.bold}❌ FAILED: ${result.findings_by_severity.high} high severity findings${colors.reset}`);
      return EXIT_CODES.HIGH_FINDINGS;
    }
    console.log(`${colors.green}✓ High severity check passed${colors.reset}`);

    // Check max findings
    if (config.maxFindings > 0 && result.total_findings > config.maxFindings) {
      console.log(`${colors.red}${colors.bold}❌ FAILED: ${result.total_findings} findings exceed limit of ${config.maxFindings}${colors.reset}`);
      return EXIT_CODES.MAX_FINDINGS_EXCEEDED;
    }
    console.log(`${colors.green}✓ Finding count within limits${colors.reset}`);

    // Success!
    printHeader('✅ All Quality Gates Passed');
    return EXIT_CODES.SUCCESS;
  } catch (error) {
    console.error(`\n${colors.red}${colors.bold}❌ Audit failed:${colors.reset}`, error);
    return EXIT_CODES.AUDIT_FAILED;
  }
}

// GitHub Actions annotations
function annotateFindings(findings: Finding[]) {
  if (!process.env.GITHUB_ACTIONS) return;

  for (const finding of findings) {
    const level =
      finding.severity === 'critical' || finding.severity === 'high' ? 'error' : 'warning';
    // GitHub Actions annotation format
    console.log(`::${level} file=${finding.file},line=${finding.line || 1}::${finding.message}`);
  }
}

// GitLab CI Report format
function generateGitLabReport(result: AuditResult) {
  return {
    version: '2.0',
    vulnerabilities: result.findings.map((f) => ({
      id: f.id,
      category: 'sast',
      name: f.title,
      message: f.message,
      description: f.description,
      cve: f.rule_id,
      severity: mapSeverityToGitLab(f.severity),
      solution: f.recommendation,
      scanner: {
        id: 'omniaudit',
        name: 'OmniAudit',
      },
      location: {
        file: f.file,
        start_line: f.line,
        end_line: f.end_line || f.line,
      },
      identifiers: [
        {
          type: 'omniaudit_rule',
          name: f.rule_id,
          value: f.rule_id,
        },
      ],
    })),
  };
}

function mapSeverityToGitLab(severity: string): string {
  switch (severity) {
    case 'critical':
      return 'Critical';
    case 'high':
      return 'High';
    case 'medium':
      return 'Medium';
    case 'low':
      return 'Low';
    default:
      return 'Info';
  }
}

// Run and exit with appropriate code
runCIAudit()
  .then((exitCode) => {
    process.exit(exitCode);
  })
  .catch((error) => {
    console.error('Unexpected error:', error);
    process.exit(EXIT_CODES.AUDIT_FAILED);
  });

// Export for testing
export { runCIAudit, generateGitLabReport, annotateFindings, EXIT_CODES };
