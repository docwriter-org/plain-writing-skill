#!/usr/bin/env python3
"""Run the checker directly from a cloned skill or plugin installation."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plain_writing.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
