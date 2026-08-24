import logging
import requests

logger = logging.getLogger(__name__)

_COIN_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"
_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"

# In-memory cache: symbol (uppercase) -> coingecko id
_symbol_cache: dict = {}
_cache_loaded = False


def _load_coin_list(api_key: str = "") -> None:
    """Populate _symbol_cache from CoinGecko coins list. Called once."""
    global _cache_loaded
    headers = {}
    if api_key:
        headers["x-cg-pro-api-key"] = api_key
    try:
        resp = requests.get(_COIN_LIST_URL, headers=headers, timeout=20)
        resp.raise_for_status()
        coins = resp.json()
        for coin in coins:
            sym = coin["symbol"].upper()
            # First match wins (avoids overwriting popular tokens with obscure ones)
            if sym not in _symbol_cache:
                _symbol_cache[sym] = coin["id"]
        _cache_loaded = True
        logger.info("CoinGecko coin list loaded: %d entries", len(_symbol_cache))
    except requests.RequestException as e:
        logger.warning("Failed to load CoinGecko coin list: %s", e)


def _get_coin_id(symbol: str, api_key: str = "") -> str:
    """Return the CoinGecko id for a token symbol, or None if unknown."""
    if not _cache_loaded:
        _load_coin_list(api_key)
    return _symbol_cache.get(symbol.upper())


def get_usd_price(symbol: str, api_key: str = "") -> float:
    """Return USD price for a token symbol via CoinGecko, or None on failure."""
    coin_id = _get_coin_id(symbol, api_key)
    if coin_id is None:
        logger.debug("No CoinGecko id found for symbol: %s", symbol)
        return None
    headers = {}
    if api_key:
        headers["x-cg-pro-api-key"] = api_key
    try:
        resp = requests.get(
            _PRICE_URL,
            params={"ids": coin_id, "vs_currencies": "usd"},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        price = data.get(coin_id, {}).get("usd")
        if price is None:
            logger.debug("No USD price in response for %s (%s)", symbol, coin_id)
            return None
        return float(price)
    except requests.RequestException as e:
        logger.warning("CoinGecko price fetch failed for %s: %s", symbol, e)
        return None
