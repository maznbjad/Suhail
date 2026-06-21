from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


@st.cache_data(show_spinner=False)
def load_json_cached(path_str: str, modified_ns: int) -> Any:
    """Load JSON once per file revision.

    modified_ns is part of the cache key so edits are picked up immediately while
    unchanged content is not reparsed for every Streamlit rerun.
    """
    del modified_ns
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json(path: str | Path, default: Any) -> Any:
    file_path = Path(path)
    try:
        stat = file_path.stat()
        return load_json_cached(str(file_path.resolve()), stat.st_mtime_ns)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        return default


def compact_json(value: Any) -> str:
    """Serialize JSON compactly for embedding in the client shell."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
