"""Backward-compatible entry point for the database bootstrap command."""

from management.bootstrap import main

if __name__ == "__main__":
    raise SystemExit(main())
