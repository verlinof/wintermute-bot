import logging
from datetime import datetime, timezone
import requests
from src.labels import get_address_label

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
    chat_ids: list[str],
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
    custom_labels: dict[str, str] | None = None,
) -> None:
    """Send a Telegram alert for a detected large transfer with full address & label resolution."""
    try:
        ts = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except (ValueError, OSError):
        ts = timestamp

    from_clean = from_addr.lower()
    to_clean = to_addr.lower()

    label_from = get_address_label(from_clean, custom_labels)
    label_to = get_address_label(to_clean, custom_labels)

    # Determine transfer flow direction
    if from_label and from_clean in (custom_labels or {}):
        transfer_type = "📤 *OUTFLOW / SENT*"
    elif from_label and to_clean in (custom_labels or {}):
        transfer_type = "📥 *INFLOW / RECEIVED*"
    else:
        transfer_type = "⚡ *LARGE TRANSFER*"

    text = (
        f"🚨 *Large Transfer Detected!*\n"
        f"🏷️ *Monitored Entity:* {from_label}\n"
        f"🔄 *Flow Type:* {transfer_type}\n"
        f"🔗 *Chain:* {chain_name}\n"
        f"💰 *Token:* {token_symbol} ({token_name})\n"
        f"📊 *Amount:* {_format_number(amount)} {token_symbol} (~${_format_number(usd_value)} USD)\n\n"
        f"📤 *From:* {label_from}\n"
        f"`{from_addr}`\n\n"
        f"📥 *To:* {label_to}\n"
        f"`{to_addr}`\n\n"
        f"🔍 *TX:* [View on Explorer]({tx_url}{tx_hash})\n"
        f"⏰ *Time:* {ts}"
    )

    url = TELEGRAM_API.format(token=telegram_token)
    for chat_id in chat_ids:
        try:
            resp = requests.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Alert sent for tx %s on %s to chat_id %s", tx_hash, chain_name, chat_id)
        except requests.RequestException as e:
            logger.error("Failed to send Telegram alert to chat_id %s: %s", chat_id, e)
