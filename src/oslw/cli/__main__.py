"""OSLW CLI entry point.

Usage:
    python -m oslw.cli status
    python -m oslw.cli sync
    python -m oslw.cli doctor
    python -m oslw.cli graph --generate
    python -m oslw.cli digest
    python -m oslw.cli monitor
    python -m oslw.cli page --list
"""

from oslw.cli.commands import cli

if __name__ == "__main__":
    cli()
