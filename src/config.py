import os
from dataclasses import dataclass


@dataclass
class Config:
    telegram_token: str
    telegram_chat_ids: list[str]
    usd_threshold: float
    poll_interval: int
    explorer_keys: dict  # chain_id -> api_key
    coingecko_api_key: str = ""
    accumulation_enabled: bool = True
    accumulation_usd_threshold: float = 500000.0
    accumulation_window_hours: int = 24
    accumulation_min_tx_count: int = 2


def load_config() -> "Config":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    chat_ids_str = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_ids_str:
        raise ValueError("TELEGRAM_CHAT_ID is required")
    
    chat_ids = [cid.strip() for cid in chat_ids_str.split(",") if cid.strip()]
    if not chat_ids:
        raise ValueError("TELEGRAM_CHAT_ID must contain at least one valid chat ID")

    etherscan_key = os.environ.get("ETHERSCAN_API_KEY", "")

    return Config(
        telegram_token=token,
        telegram_chat_ids=chat_ids,
        usd_threshold=float(os.environ.get("USD_THRESHOLD", "100000")),
        poll_interval=int(os.environ.get("POLL_INTERVAL", "180")),
        coingecko_api_key=os.environ.get("COINGECKO_API_KEY", ""),
        explorer_keys={
            "ethereum":  etherscan_key,
            "arbitrum":  etherscan_key,
            "bsc":       etherscan_key,
            "optimism":  etherscan_key,
            "base":      etherscan_key,
        },
        accumulation_enabled=os.environ.get("ACCUMULATION_ENABLED", "true").lower() in ("true", "1", "yes"),
        accumulation_usd_threshold=float(os.environ.get("ACCUMULATION_USD_THRESHOLD", "500000")),
        accumulation_window_hours=int(os.environ.get("ACCUMULATION_WINDOW_HOURS", "24")),
        accumulation_min_tx_count=int(os.environ.get("ACCUMULATION_MIN_TX_COUNT", "2")),
    )
