"""CLI module."""

from .commands import cli


def main():
    """Main CLI entry point."""
    cli()


__all__ = ['cli', 'main']
