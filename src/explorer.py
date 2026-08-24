import logging
import requests
from dataclasses import dataclass
from src.chains import Chain

logger = logging.getLogger(__name__)


@dataclass
class TokenTransfer:
    tx_hash: str
    from_addr: str
    to_addr: str
    token_symbol: str
    token_name: str
    token_decimals: int
    raw_value: str
    block_timestamp: str
    contract_address: str


def compute_amount(raw_value: str, decimals: int) -> float:
    """Convert raw token amount string to human-readable float."""
    return int(raw_value) / (10 ** decimals)


def fetch_token_transfers(
    chain: Chain,
    address: str,
    api_key: str,
    start_block: int = 0,
) -> list:
    """Fetch ERC-20 token transfer events for an address from a chain explorer."""
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": start_block,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": api_key,
    }
    try:
        resp = requests.get(chain.explorer_base_url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            logger.debug(
                "Explorer returned non-success for %s on %s: %s",
                address, chain.name, data.get("message"),
            )
            return []
        transfers = []
        for tx in data.get("result", []):
            try:
                decimals = int(tx.get("tokenDecimal", "18") or "18")
            except ValueError:
                decimals = 18
            transfers.append(TokenTransfer(
                tx_hash=tx["hash"],
                from_addr=tx["from"].lower(),
                to_addr=tx["to"].lower(),
                token_symbol=tx.get("tokenSymbol", ""),
                token_name=tx.get("tokenName", ""),
                token_decimals=decimals,
                raw_value=tx.get("value", "0"),
                block_timestamp=tx.get("timeStamp", ""),
                contract_address=tx.get("contractAddress", "").lower(),
            ))
        return transfers
    except requests.RequestException as e:
        logger.warning("Explorer fetch failed for %s on %s: %s", address, chain.name, e)
        return []
