import os
import sqlite3


class DedupStore:
    """SQLite-backed store for tracking seen transaction hashes."""

    def __init__(self, db_path: str = "data/seen_txs.db"):
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS seen_txs (tx_hash TEXT PRIMARY KEY)"
        )
        self._conn.commit()

    def is_seen(self, tx_hash: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM seen_txs WHERE tx_hash = ?", (tx_hash,)
        )
        return cur.fetchone() is not None

    def mark_seen(self, tx_hash: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO seen_txs (tx_hash) VALUES (?)", (tx_hash,)
        )
        self._conn.commit()
