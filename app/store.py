from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS delivered (key_hash TEXT PRIMARY KEY)")

    def is_delivered(self, key: str) -> bool:
        digest = hashlib.sha256(key.encode()).hexdigest()
        return self.connection.execute("SELECT 1 FROM delivered WHERE key_hash = ?", (digest,)).fetchone() is not None

    def mark_delivered(self, key: str) -> None:
        digest = hashlib.sha256(key.encode()).hexdigest()
        self.connection.execute("INSERT OR IGNORE INTO delivered(key_hash) VALUES (?)", (digest,))
        self.connection.commit()
