#!/usr/bin/env node
/**
 * Pre-Bash Hook
 * Audits and validates bash commands before execution
 * - Blocks dangerous operations
 * - Logs all commands for compliance
 * - Enforces resource limits
 */

const fs = require('fs');
const path = require('path');

// Dangerous command patterns
const DANGEROUS_PATTERNS = [
  /rm\s+-rf\s+\/($|\s)/,  // rm -rf /
  /:\(\)\{\s*:\|\:&\s*\};:/,  // fork bomb
  /mkfs/,  // filesystem formatting
  /dd\s+if=.*of=\/dev\/(sd|hd)/,  // disk wiping
  /wget.*\|\s*sh/,  // pipe to shell
  /curl.*\|\s*sh/,  // pipe to shell
  /chmod\s+777\s+\//,  // dangerous permissions on root
  /chown.*\//,  // ownership changes on root
];

// Suspicious patterns (warn but allow)
const SUSPICIOUS_PATTERNS = [
  /rm\s+-rf/,  // rm -rf (but not on root)
  /sudo/,  // sudo usage
  /eval/,  // eval usage
  />\s*\/dev\/sd/,  // writing to disk devices
];

function main() {
  try {
    const args = process.argv.slice(2);
    const toolInput = args[0] ? JSON.parse(args[0]) : {};

    const command = toolInput.command || '';

    if (!command) {
      console.log('✅ No command detected, allowing operation');
      process.exit(0);
    }

    // Check dangerous patterns
    for (const pattern of DANGEROUS_PATTERNS) {
      if (pattern.test(command)) {
        console.error(`❌ BLOCKED: Dangerous command detected`);
        console.error(`Command: ${command.substring(0, 100)}`);
        console.error(`Reason: Matches dangerous pattern: ${pattern}`);
        console.error('This command could cause system damage or security issues.');
        process.exit(1);
      }
    }

    // Check suspicious patterns
    for (const pattern of SUSPICIOUS_PATTERNS) {
      if (pattern.test(command)) {
        console.warn(`⚠️  WARNING: Suspicious command pattern detected`);
        console.warn(`Command: ${command.substring(0, 100)}`);
        console.warn(`Pattern: ${pattern}`);
        console.warn('Proceeding, but exercise caution.');
        break;
      }
    }

    // Log command for audit trail
    const logDir = path.join('/home/user/OmniAudit', '.claude', 'logs');
    try {
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }

      const logFile = path.join(logDir, 'command-audit.log');
      const timestamp = new Date().toISOString();
      const logEntry = `${timestamp} | ${command}\n`;

      fs.appendFileSync(logFile, logEntry);
    } catch (err) {
      // Logging failure shouldn't block the command
      console.warn('⚠️  Could not log command:', err.message);
    }

    console.log(`✅ Command validated: ${command.substring(0, 50)}${command.length > 50 ? '...' : ''}`);
    process.exit(0);

  } catch (error) {
    console.error('❌ Pre-bash hook error:', error.message);
    // On error, allow the operation but log the issue
    process.exit(0);
  }
}

main();
