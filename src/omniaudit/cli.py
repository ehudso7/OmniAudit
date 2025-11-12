"""
OmniAudit CLI Entry Point

Command-line interface for running audits and collectors.
"""

import sys


def main():
    """Main CLI entry point."""
    print("OmniAudit v0.1.0")
    print("Universal Project Auditing & Monitoring Platform")
    print()
    print("Available commands:")
    print("  audit     - Run full audit")
    print("  collect   - Run specific collector")
    print("  analyze   - Run specific analyzer")
    print("  report    - Generate report")
    print()
    print("For detailed help: omniaudit <command> --help")
    return 0


if __name__ == "__main__":
    sys.exit(main())
