import os
from dataclasses import dataclass


@dataclass
class Config:
    telegram_token: str
    telegram_chat_id: str
    usd_threshold: float
    poll_interval: int
    explorer_keys: dict  # chain_id -> api_key
    coingecko_api_key: str = ""


def load_config() -> "Config":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID is required")

    return Config(
        telegram_token=token,
        telegram_chat_id=chat_id,
        usd_threshold=float(os.environ.get("USD_THRESHOLD", "100000")),
        poll_interval=int(os.environ.get("POLL_INTERVAL", "180")),
        coingecko_api_key=os.environ.get("COINGECKO_API_KEY", ""),
        explorer_keys={
            "ethereum":  os.environ.get("ETHERSCAN_API_KEY", ""),
            "arbitrum":  os.environ.get("ARBISCAN_API_KEY", ""),
            "bsc":       os.environ.get("BSCSCAN_API_KEY", ""),
            "optimism":  os.environ.get("OPTIMISM_API_KEY", ""),
            "polygon":   os.environ.get("POLYGONSCAN_API_KEY", ""),
            "base":      os.environ.get("BASESCAN_API_KEY", ""),
        },
    )
