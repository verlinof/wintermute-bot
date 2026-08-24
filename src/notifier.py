import logging
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _format_number(n: float) -> str:
    """Format large numbers with commas."""
    if n >= 1_000_000:
        return f"{n:,.2f}"
    if n >= 1_000:
        return f"{n:,.4f}"
    return f"{n:.6f}"


def send_alert(
    telegram_token: str,
    chat_id: str,
    chain_name: str,
    token_symbol: str,
    token_name: str,
    amount: float,
    usd_value: float,
    from_addr: str,
    to_addr: str,
    from_label: str,
    tx_hash: str,
    tx_url: str,
    timestamp: str,
) -> None:
    """Send a Telegram alert for a detected large transfer."""
    try:
        ts = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except (ValueError, OSError):
        ts = timestamp

    short_from = from_addr[:6] + "..." + from_addr[-4:] if len(from_addr) > 10 else from_addr
    short_to = to_addr[:6] + "..." + to_addr[-4:] if len(to_addr) > 10 else to_addr

    text = (
        "\U0001F6A8 *Large Transfer Detected!*\n"
        f"\U0001F3F7\uFE0F *Entity:* {from_label}\n"
        f"\U0001F517 *Chain:* {chain_name}\n"
        f"\U0001F4B0 *Token:* {token_symbol} ({token_name})\n"
        f"\U0001F4CA *Amount:* {_format_number(amount)} {token_symbol} (~${_format_number(usd_value)} USD)\n"
        f"\U0001F4E4 *From:* `{short_from}`\n"
        f"\U0001F4E5 *To:* `{short_to}`\n"
        f"\U0001F50D *TX:* [View on Explorer]({tx_url}{tx_hash})\n"
        f"\u23F0 *Time:* {ts}"
    )

    url = TELEGRAM_API.format(token=telegram_token)
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Alert sent for tx %s on %s", tx_hash, chain_name)
    except requests.RequestException as e:
        logger.error("Failed to send Telegram alert: %s", e)
