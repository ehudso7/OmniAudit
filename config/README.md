# Configuration

This directory contains configuration files for OmniAudit collectors, analyzers, and reporters.

## Structure

- `collectors/` - Collector-specific configurations
- `analyzers/` - Analyzer-specific configurations (Phase 2)
- `reporters/` - Reporter-specific configurations (Phase 2)

## Usage

1. Copy example configuration files and remove the `.example` extension
2. Customize the values for your environment
3. Reference configurations when running OmniAudit

## Example

```bash
cp collectors/git.yaml.example collectors/git.yaml
# Edit collectors/git.yaml with your settings
omniaudit collect --config collectors/git.yaml
```
