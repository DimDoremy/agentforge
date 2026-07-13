"""Pytest configuration for the template skeleton tests.

These tests verify the harness itself (not any agent). They must run without a
live Postgres or an LLM provider — guard anything that needs those.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `src` importable when running `uv run pytest` from the template root
# (the package is also installed by uv, but this keeps tests robust in CI).
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Provide harmless defaults so Settings() can construct without a real .env.
os.environ.setdefault("MODEL", "openai:gpt-4o-mini")
os.environ.setdefault("DB_DSN", "postgresql://postgres:postgres@postgres:5432/agentforge?sslmode=disable")
os.environ.setdefault("DB_NAME", "agentforge")
