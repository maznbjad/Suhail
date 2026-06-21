from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import streamlit as st


@st.cache_data(show_spinner=False)
def _encode_asset(path_str: str, modified_ns: int) -> str:
    del modified_ns
    path = Path(path_str)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def asset_data_uri(path: str | Path) -> str:
    file_path = Path(path)
    try:
        stat = file_path.stat()
    except OSError:
        return ""
    return _encode_asset(str(file_path.resolve()), stat.st_mtime_ns)
