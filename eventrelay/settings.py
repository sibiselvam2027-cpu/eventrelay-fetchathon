"""Local settings, without printing credentials or agent seed material."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    path = ROOT / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            if key and value:
                os.environ.setdefault(key, value)


def local_path(name: str, fallback: str) -> Path:
    path = Path(os.environ.get(name, fallback))
    return path if path.is_absolute() else ROOT / path


def demo_mode() -> bool:
    return os.environ.get("EVENTRELAY_DEMO_MODE", "0") == "1"
