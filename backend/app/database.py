from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Iterable

from .config import settings
from .models import Problem

_SCHEMA = """
CREATE TABLE IF NOT EXISTS problems (
    id              TEXT PRIMARY KEY,
    platform        TEXT NOT NULL,
    title           TEXT NOT NULL,
    url             TEXT NOT NULL,
    tags            TEXT NOT NULL,        -- JSON array
    difficulty      TEXT,
    rating_raw      REAL,
    rating_unified  REAL,
    text            TEXT,
    contest_id      TEXT,
    idx             TEXT,
    frontend_id     TEXT
);

CREATE INDEX IF NOT EXISTS idx_platform ON problems(platform);
CREATE INDEX IF NOT EXISTS idx_rating   ON problems(rating_unified);
"""


def get_connection(db_path=None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or settings.db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


@contextmanager
def db_cursor(db_path=None):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_problems(problems: Iterable[Problem], db_path=None) -> int:
    rows = [(
        p.id, p.platform, p.title, p.url, json.dumps(p.tags), p.difficulty,
        p.rating_raw, p.rating_unified, p.text, p.contest_id, p.index, p.frontend_id,
    ) for p in problems]
    if not rows:
        return 0
    with db_cursor(db_path) as conn:
        conn.executemany(
            """INSERT INTO problems (id, platform, title, url, tags, difficulty,
                                     rating_raw, rating_unified, text, contest_id,
                                     idx, frontend_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 platform=excluded.platform, title=excluded.title, url=excluded.url,
                 tags=excluded.tags, difficulty=excluded.difficulty,
                 rating_raw=excluded.rating_raw, rating_unified=excluded.rating_unified,
                 text=excluded.text, contest_id=excluded.contest_id,
                 idx=excluded.idx, frontend_id=excluded.frontend_id""",
            rows,
        )
    return len(rows)


def _row_to_problem(row: sqlite3.Row) -> Problem:
    return Problem(
        id=row["id"],
        platform=row["platform"],
        title=row["title"],
        url=row["url"],
        tags=json.loads(row["tags"] or "[]"),
        difficulty=row["difficulty"] or "",
        rating_raw=row["rating_raw"],
        rating_unified=row["rating_unified"],
        text=row["text"] or "",
        contest_id=row["contest_id"],
        index=row["idx"],
        frontend_id=row["frontend_id"],
    )


def load_all_problems(db_path=None) -> list[Problem]:
    with db_cursor(db_path) as conn:
        cur = conn.execute("SELECT * FROM problems ORDER BY id")
        return [_row_to_problem(r) for r in cur.fetchall()]


def count_problems(db_path=None) -> int:
    with db_cursor(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
