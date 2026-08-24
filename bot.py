#!/usr/bin/env python3
"""
Wintermute Transaction Monitor
================================
Polls blockchain explorers for large altcoin transactions from tracked wallets
and sends Telegram alerts.

Usage:
    1. Copy .env.example to .env and fill in your values.
    2. Edit wallets.json to add/remove wallet addresses.
    3. Install dependencies: pip install -r requirements.txt
    4. Run: python bot.py
"""
import logging
import schedule
import time
from dotenv import load_dotenv

load_dotenv()

from src.config import load_config
from src.wallets import load_wallets
from src.dedup import DedupStore
from src.monitor import Monitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
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
    logger.info("USD threshold: $%.0f", config.usd_threshold)
    logger.info("Poll interval: %ds", config.poll_interval)

    dedup = DedupStore()
    monitor = Monitor(config, entities, dedup)

    # Run immediately on start, then on schedule
    logger.info("Running initial poll...")
    monitor.run_once()

    schedule.every(config.poll_interval).seconds.do(monitor.run_once)
    logger.info("Scheduler started. Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")


if __name__ == "__main__":
    main()
