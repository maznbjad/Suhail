from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ADMIN_SETTINGS_PATH = ROOT / "data" / "admin" / "admin_settings.json"
FEATURE_FLAGS_PATH = ROOT / "data" / "admin" / "feature_flags.json"
AVATARS_PATH = ROOT / "data" / "avatars" / "avatars.json"
CHALLENGE_TEMPLATES_PATH = ROOT / "data" / "challenges" / "challenge_templates.json"
SCORE_MODELS_PATH = ROOT / "data" / "scoring" / "score_models.json"


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


@lru_cache(maxsize=16)
def load_admin_settings() -> dict[str, Any]:
    return _read_json(ADMIN_SETTINGS_PATH, {})


@lru_cache(maxsize=16)
def load_feature_flags() -> dict[str, Any]:
    return _read_json(FEATURE_FLAGS_PATH, {"flags": {}})


@lru_cache(maxsize=16)
def load_avatars() -> dict[str, Any]:
    return _read_json(AVATARS_PATH, {"items": []})


@lru_cache(maxsize=16)
def load_challenge_templates() -> dict[str, Any]:
    return _read_json(CHALLENGE_TEMPLATES_PATH, {"templates": []})


@lru_cache(maxsize=16)
def load_score_models() -> dict[str, Any]:
    return _read_json(SCORE_MODELS_PATH, {"models": {}})


def invalidate_config_cache() -> None:
    load_admin_settings.cache_clear()
    load_feature_flags.cache_clear()
    load_avatars.cache_clear()
    load_challenge_templates.cache_clear()
    load_score_models.cache_clear()
