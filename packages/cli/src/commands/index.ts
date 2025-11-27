// Export all command creators
export { createAuditCommand } from './audit.js';
export { createFindingsCommand } from './findings.js';
export { createConfigCommand } from './config.js';
export { createRulesCommand } from './rules.js';
export { createReportCommand } from './report.js';
export { createCICommand } from './ci.js';
export { createWatchCommand } from './watch.js';
export { createFixCommand } from './fix.js';
export { createStatsCommand } from './stats.js';

// Additional commands that would be implemented
// These are exports for commands that would follow similar patterns

export function createServeCommand() {
  // Serve command - start local API server
  // Implementation similar to others
}

export function createDaemonCommand() {
  // Daemon command - run as background service
  // Implementation similar to others
}

export function createCompareCommand() {
  // Compare command - compare two audit results
  // Implementation similar to others
}

export function createExportCommand() {
  // Export command - export data in various formats
  // Implementation similar to others
}

export function createImportCommand() {
  // Import command - import audit data
  // Implementation similar to others
}

export function createPluginsCommand() {
  // Plugins command - manage plugins
  // Implementation similar to others
}

export function createCacheCommand() {
  // Cache command - manage cache
  // Implementation similar to others
}

export function createLogsCommand() {
  // Logs command - view and manage logs
  // Implementation similar to others
}

export function createVersionCommand() {
  // Version command - version info and updates
  // Implementation similar to others
}

export function createDoctorCommand() {
  // Doctor command - diagnose issues
  // Implementation similar to others
}

export function createInitCommand() {
  // Init command - initialize new project
  // Implementation similar to others
}

export function createCleanCommand() {
  // Clean command - clean up artifacts
  // Implementation similar to others
}

export function createBenchmarkCommand() {
  // Benchmark command - performance benchmarks
  // Implementation similar to others
}

export function createTeamCommand() {
  // Team command - team management
  // Implementation similar to others
}

export function createProjectsCommand() {
  // Projects command - manage projects
  // Implementation similar to others
}

export function createWebhooksCommand() {
  // Webhooks command - manage webhooks
  // Implementation similar to others
}

export function createIntegrationsCommand() {
  // Integrations command - manage integrations
  // Implementation similar to others
}

export function createScheduleCommand() {
  // Schedule command - schedule audits
  // Implementation similar to others
}

export function createNotificationsCommand() {
  // Notifications command - manage notifications
  // Implementation similar to others
}

export function createHistoryCommand() {
  // History command - audit history
  // Implementation similar to others
}

export function createDiffCommand() {
  // Diff command - diff between audits
  // Implementation similar to others
}
