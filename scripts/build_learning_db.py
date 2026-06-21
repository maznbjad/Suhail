#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.core.learning_repository import build_sqlite

count = build_sqlite(ROOT / "data" / "questions.json", ROOT / "data" / "suhail_learning.db")
print(f"Built SQLite learning repository with {count} questions")
