#!/usr/bin/env python3
"""
Wintermute Transaction Monitor
================================
Polls blockchain explorers for large altcoin transactions from tracked wallets
and sends Telegram alerts.

Usage:
    1. Copy .env.example to .env and fill in your values.
    2. Edit wallets.json to add/remove wallet addresses.
    3. Run diagnostics & test: python test_bot.py --send-ping
    4. Run bot: python bot.py
"""
import sys
import logging
import schedule
import time
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from src.config import load_config
from src.wallets import load_wallets
from src.dedup import DedupStore
from src.accumulation import AccumulationStore
from src.monitor import Monitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("wintermute-bot")


def main():
    logger.info("Starting Wintermute Transaction Monitor")

    config = load_config()
    entities = load_wallets("wallets.json")
    if not entities:
        logger.warning("No entities found in wallets.json - nothing to monitor")
        return

    logger.info(
        "Monitoring %d entit(ies): %s",
        len(entities),
        ", ".join(e.label for e in entities),
    )
    logger.info("Base USD threshold: $%.0f USD (BTC/ETH: $1,000,000 USD)", config.usd_threshold)
    if config.accumulation_enabled:
        logger.info(
            "Accumulation tracking: ACTIVE (Threshold: $%.0f USD, Window: %dh, Min TXs: %d)",
            config.accumulation_usd_threshold,
            config.accumulation_window_hours,
            config.accumulation_min_tx_count,
        )
    else:
        logger.info("Accumulation tracking: DISABLED")
    logger.info("Poll interval: %ds", config.poll_interval)

    dedup = DedupStore()
    accum_store = AccumulationStore()
    monitor = Monitor(config, entities, dedup, accum_store)

    logger.info("Running initial poll...")
    monitor.run_once()

    schedule.every(config.poll_interval).seconds.do(monitor.run_once)
    logger.info("Scheduler active. Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")


if __name__ == "__main__":
    main()
