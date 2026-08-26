import os
import sqlite3
import time
import logging

logger = logging.getLogger(__name__)


class AccumulationStore:
    def __init__(self, db_path: str = "data/dedup.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS inflow_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tx_hash TEXT UNIQUE,
                    chain TEXT,
                    entity_label TEXT,
                    recipient_addr TEXT,
                    token_symbol TEXT,
                    token_name TEXT,
                    amount REAL,
                    usd_value REAL,
                    timestamp INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_inflow_query
                ON inflow_transfers (chain, entity_label, token_symbol, timestamp)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accumulation_milestones (
                    key TEXT PRIMARY KEY,
                    highest_milestone_usd REAL,
                    last_alert_timestamp INTEGER
                )
                """
            )
            conn.commit()

    def _make_key(self, chain: str, entity_label: str, token_symbol: str) -> str:
        return f"{chain.lower()}:{entity_label.lower()}:{token_symbol.upper()}"

    def record_inflow(
        self,
        tx_hash: str,
        chain: str,
        entity_label: str,
        recipient_addr: str,
        token_symbol: str,
        token_name: str,
        amount: float,
        usd_value: float,
        timestamp: int,
    ) -> bool:
        """Record an inflow transfer. Returns True if inserted, False if duplicate."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO inflow_transfers
                    (tx_hash, chain, entity_label, recipient_addr, token_symbol, token_name, amount, usd_value, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx_hash,
                        chain.lower(),
                        entity_label,
                        recipient_addr.lower(),
                        token_symbol.upper(),
                        token_name,
                        float(amount),
                        float(usd_value),
                        int(timestamp),
                    ),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error("Failed to record inflow transfer %s: %s", tx_hash, e)
            return False

    def get_accumulation_stats(
        self,
        chain: str,
        entity_label: str,
        token_symbol: str,
        window_hours: int = 24,
    ) -> tuple[float, float, int]:
        """Returns (total_amount, total_usd, tx_count) within the rolling window."""
        cutoff = int(time.time()) - (window_hours * 3600)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0.0), COALESCE(SUM(usd_value), 0.0), COUNT(id)
                    FROM inflow_transfers
                    WHERE chain = ? AND entity_label = ? AND token_symbol = ? AND timestamp >= ?
                    """,
                    (chain.lower(), entity_label, token_symbol.upper(), cutoff),
                )
                row = cursor.fetchone()
                if row:
                    return float(row[0]), float(row[1]), int(row[2])
        except sqlite3.Error as e:
            logger.error("Failed to get accumulation stats for %s: %s", token_symbol, e)
        return 0.0, 0.0, 0

    def get_highest_milestone(
        self,
        chain: str,
        entity_label: str,
        token_symbol: str,
    ) -> float:
        """Returns the highest alerted milestone USD tier recorded for this token & entity."""
        key = self._make_key(chain, entity_label, token_symbol)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT highest_milestone_usd FROM accumulation_milestones WHERE key = ?",
                    (key,),
                )
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return float(row[0])
        except sqlite3.Error as e:
            logger.error("Failed to get highest milestone for %s: %s", key, e)
        return 0.0

    def set_highest_milestone(
        self,
        chain: str,
        entity_label: str,
        token_symbol: str,
        milestone_usd: float,
    ) -> None:
        """Sets or updates the highest alerted milestone tier."""
        key = self._make_key(chain, entity_label, token_symbol)
        now = int(time.time())
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO accumulation_milestones (key, highest_milestone_usd, last_alert_timestamp)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        highest_milestone_usd = excluded.highest_milestone_usd,
                        last_alert_timestamp = excluded.last_alert_timestamp
                    """,
                    (key, float(milestone_usd), now),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error("Failed to set highest milestone for %s: %s", key, e)

    def prune_old_transfers(self, window_hours: int = 24) -> int:
        """Deletes inflow transfers older than the rolling window. Returns deleted row count."""
        cutoff = int(time.time()) - (window_hours * 3600)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM inflow_transfers WHERE timestamp < ?",
                    (cutoff,),
                )
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error("Failed to prune old inflow transfers: %s", e)
            return 0
