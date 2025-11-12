"""
OmniAudit CLI Entry Point

Command-line interface for running audits and collectors.
"""

from .cli.commands import cli


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
