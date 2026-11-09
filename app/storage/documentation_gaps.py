import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def record_gap(query: str, alarm_id: str | None) -> None:
    path = Path(os.getenv('CK23_GAP_DB') or '.state/documentation_gaps.sqlite')
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=30)) as database, database:
        database.execute("""
            CREATE TABLE IF NOT EXISTS documentation_gaps (
                id INTEGER PRIMARY KEY,
                recorded_at TEXT NOT NULL,
                alarm_id TEXT,
                query TEXT NOT NULL
            )
        """)
        database.execute(
            'INSERT INTO documentation_gaps (recorded_at, alarm_id, query) VALUES (?, ?, ?)',
            (datetime.now(timezone.utc).isoformat(), alarm_id, query),
        )
