"""Primary project validation entrypoint for Suhail Sprint 56."""
from __future__ import annotations
import runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts" / "validate_sprint56.py"), run_name="__main__")
