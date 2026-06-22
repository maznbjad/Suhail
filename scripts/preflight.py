"""Fast local preflight for Suhail before Streamlit starts."""
from __future__ import annotations

import importlib
import json
import os
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    ROOT / "app.py",
    ROOT / "requirements.txt",
    ROOT / "data" / "questions.json",
    ROOT / "data" / "smart_summaries.json",
    ROOT / "src" / "ui" / "sprint70_boot.js",
    ROOT / "src" / "ui" / "sprint70_unified_app.css",
    ROOT / "src" / "ui" / "sprint70_unified_app.js",
]
JSON_FILES = [
    ROOT / "data" / "questions.json",
    ROOT / "data" / "smart_summaries.json",
    ROOT / "data" / "users.json",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    print("Suhail preflight")
    print(f"Python: {sys.executable}")
    print(f"Project: {ROOT}")

    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail("Missing files: " + ", ".join(missing))

    for module in ("streamlit",):
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - command-line guard
            fail(f"Cannot import {module}: {exc}")

    try:
        py_compile.compile(str(ROOT / "app.py"), doraise=True)
    except py_compile.PyCompileError as exc:
        fail(f"Python syntax error: {exc.msg}")

    for path in JSON_FILES:
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception as exc:
            fail(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")

    data_dir = ROOT / "data"
    if not os.access(data_dir, os.W_OK):
        fail("The data folder is not writable. Move the project out of a protected folder.")

    print("[OK] Files, imports, Python syntax, JSON and write access are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
