"""Vercel entrypoint for the FastAPI application.

Vercel's Python runtime discovers root-level api.py reliably. The application
itself remains under src/forex_robot so local Docker/CLI imports are unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from forex_robot.api import app  # noqa: E402

__all__ = ["app"]
