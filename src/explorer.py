import logging
import requests
from dataclasses import dataclass
from src.chains import Chain

logger = logging.getLogger(__name__)

ETHERSCAN_V2_URL = "https://api.etherscan.io/v2/api"


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
    try:
        return int(raw_value) / (10 ** decimals)
    except (ValueError, ZeroDivisionError):
        return 0.0


def fetch_token_transfers(
    chain: Chain,
    address: str,
    api_key: str,
    start_block: int = 0,
    offset: int = 50,
) -> list:
    """Fetch ERC-20 token transfer events for an address from Etherscan API V2."""
    params = {
        "chainid": chain.chain_id,
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": start_block,
        "endblock": 99999999,
        "page": 1,
        "offset": offset,
        "sort": "desc",
        "apikey": api_key,
    }
    try:
        resp = requests.get(ETHERSCAN_V2_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        message = data.get("message", "")
        result = data.get("result")

        if status != "1":
            if message == "No transactions found":
                logger.debug("No token transfers found for %s on %s", address[:10], chain.name)
            else:
                result_str = str(result)
                if "Free API access is not supported" in result_str:
                    logger.debug("%s: %s", chain.name, result_str)
                else:
                    logger.warning(
                        "Explorer returned non-success for %s on %s: message=%s, result=%s",
                        address[:10], chain.name, message, result_str[:120],
                    )
            return []

        if not isinstance(result, list):
            return []

        transfers = []
        for tx in result:
            try:
                decimals = int(tx.get("tokenDecimal", "18") or "18")
            except ValueError:
                decimals = 18
            transfers.append(TokenTransfer(
                tx_hash=tx.get("hash", ""),
                from_addr=tx.get("from", "").lower(),
                to_addr=tx.get("to", "").lower(),
                token_symbol=tx.get("tokenSymbol", "").upper(),
                token_name=tx.get("tokenName", ""),
                token_decimals=decimals,
                raw_value=tx.get("value", "0"),
                block_timestamp=tx.get("timeStamp", ""),
                contract_address=tx.get("contractAddress", "").lower(),
            ))
        return transfers
    except requests.RequestException as e:
        logger.warning("Explorer fetch failed for %s on %s: %s", address[:10], chain.name, e)
        return []
