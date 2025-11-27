# @omniaudit/cli

Comprehensive CLI for OmniAudit with 30+ commands, interactive mode, and beautiful TUI.

## Installation

```bash
npm install -g @omniaudit/cli
```

## Features

- **30+ Commands**: Complete suite of audit, findings, config, rules, reports, CI/CD, and more
- **Interactive Mode**: User-friendly prompts and menus
- **Watch Mode**: Real-time file monitoring and auditing
- **Beautiful TUI**: Progress bars, spinners, tables, and colored output
- **CI/CD Integration**: Built-in support for GitHub Actions, GitLab CI, Jenkins
- **Daemon Mode**: Run as background service

## Quick Start

```bash
# Run audit on current directory
omniaudit audit

# Run audit with specific output format
omniaudit audit ./src --format sarif -o report.sarif

# Start interactive mode
omniaudit interactive

# Watch for changes
omniaudit watch --initial

# Initialize configuration
omniaudit init
```

## Commands

### Audit Commands
- `audit [path]` - Run comprehensive code audit
- `watch [path]` - Watch files and run audits on changes
- `fix all` - Auto-fix all fixable issues
- `fix finding <id>` - Fix specific finding
- `fix rule <rule-id>` - Fix all issues from a rule

### Findings Commands
- `findings list` - List all findings
- `findings show <id>` - Show finding details
- `findings export` - Export findings
- `findings fixed <id>` - Mark finding as fixed
- `findings ignore <id>` - Ignore a finding

### Rules Commands
- `rules list` - List all available rules
- `rules show <rule-id>` - Show rule details
- `rules enable <rule-id>` - Enable a rule
- `rules disable <rule-id>` - Disable a rule
- `rules search <query>` - Search for rules

### Configuration Commands
- `config init` - Initialize configuration
- `config get <key>` - Get configuration value
- `config set <key> <value>` - Set configuration value
- `config list` - List all configuration
- `config validate` - Validate configuration

### Report Commands
- `report generate` - Generate report from results
- `report formats` - List available formats
- `report convert` - Convert between formats
- `report upload` - Upload report to server

### CI/CD Commands
- `ci check` - Run audit in CI mode
- `ci setup` - Setup CI/CD integration
- `ci pr-status <pr-number>` - Get PR audit status

### Statistics Commands
- `stats summary` - Show overall statistics
- `stats trends` - Show trends over time
- `stats top-issues` - Show most common issues

### Utility Commands
- `serve` - Start local API server
- `daemon` - Run as background daemon
- `compare <baseline> <current>` - Compare two audits
- `doctor` - Diagnose common issues
- `init` - Initialize OmniAudit project
- `clean` - Clean up cache and temporary files
- `version` - Show version information
- `interactive` - Start interactive mode

## Examples

### Run Audit with Filters

```bash
# Audit with severity filter
omniaudit audit --severity critical high

# Audit with specific rules
omniaudit audit --rules security/* performance/*

# Audit with auto-fix
omniaudit audit --fix

# Audit in CI mode
omniaudit audit --ci --fail-on high
```

### Manage Findings

```bash
# List critical findings
omniaudit findings list --severity critical

# Export findings to CSV
omniaudit findings export -f csv -o findings.csv

# Show detailed finding
omniaudit findings show finding-123
```

### Generate Reports

```bash
# Generate SARIF report
omniaudit report generate -i results.json -f sarif -o report.sarif

# Generate HTML dashboard
omniaudit report generate -i results.json -f html -o dashboard.html

# List all formats
omniaudit report formats
```

### Watch Mode

```bash
# Watch with initial audit
omniaudit watch --initial

# Watch specific directory
omniaudit watch ./src

# Watch with ignore patterns
omniaudit watch -i "node_modules/**" "dist/**"
```

### CI/CD Integration

```bash
# Setup GitHub Actions
omniaudit ci setup --provider github

# Run CI check
omniaudit ci check --fail-on high --upload

# Get PR status
omniaudit ci pr-status 123
```

## Configuration

Create `omniaudit.config.yaml`:

```yaml
version: 2.0.0
project:
  name: my-project
  paths:
    - src/
  exclude:
    - node_modules/
    - dist/
analysis:
  parallel: true
  max_workers: 4
rules:
  enabled:
    - security/*
    - performance/*
```

## License

MIT
