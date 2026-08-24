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

    etherscan_key = os.environ.get("ETHERSCAN_API_KEY", "")

    return Config(
        telegram_token=token,
        telegram_chat_id=chat_id,
        usd_threshold=float(os.environ.get("USD_THRESHOLD", "100000")),
        poll_interval=int(os.environ.get("POLL_INTERVAL", "180")),
        coingecko_api_key=os.environ.get("COINGECKO_API_KEY", ""),
        explorer_keys={
            "ethereum":  etherscan_key,
            "arbitrum":  etherscan_key,
            "bsc":       etherscan_key,
            "optimism":  etherscan_key,
            "polygon":   etherscan_key,
            "base":      etherscan_key,
        },
    )
