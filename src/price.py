import logging
import time
import requests

logger = logging.getLogger(__name__)

# In-memory price cache: key -> (price, timestamp)
_price_cache: dict[str, tuple[float, float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes cache

_COIN_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"
_COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
_DEFILLAMA_PRICE_URL = "https://coins.llama.fi/prices/current/"

# CoinGecko symbol cache
_symbol_cache: dict[str, str] = {}
_cache_loaded = False


def _get_cached_price(key: str) -> float | None:
    if key in _price_cache:
        price, ts = _price_cache[key]
        if time.time() - ts < _CACHE_TTL_SECONDS:
            return price
    return None


def _set_cached_price(key: str, price: float) -> None:
    _price_cache[key] = (price, time.time())


def get_token_price(
    symbol: str,
    chain_prefix: str = "ethereum",
    contract_address: str = "",
    coingecko_api_key: str = "",
) -> float | None:
    """Fetch USD price using DeFiLlama by contract address first, then fallback to symbol lookup."""
    symbol = symbol.upper()
    cache_key = f"{chain_prefix}:{contract_address.lower()}" if contract_address else symbol
    
    cached = _get_cached_price(cache_key)
    if cached is not None:
        return cached

    # 1. Primary Method: DeFiLlama with contract address
    if contract_address and chain_prefix:
        llama_key = f"{chain_prefix}:{contract_address.lower()}"
        try:
            url = f"{_DEFILLAMA_PRICE_URL}{llama_key}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                coin_info = data.get("coins", {}).get(llama_key)
                if coin_info and "price" in coin_info:
                    price = float(coin_info["price"])
                    _set_cached_price(cache_key, price)
                    return price
        except Exception as e:
            logger.debug("DeFiLlama contract lookup failed for %s: %s", llama_key, e)

    # 2. Secondary Method: DeFiLlama with CoinGecko symbol ID
    coin_id = _get_coingecko_id(symbol, coingecko_api_key)
    if coin_id:
        try:
            llama_key = f"coingecko:{coin_id}"
            url = f"{_DEFILLAMA_PRICE_URL}{llama_key}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                coin_info = data.get("coins", {}).get(llama_key)
                if coin_info and "price" in coin_info:
                    price = float(coin_info["price"])
                    _set_cached_price(cache_key, price)
                    return price
        except Exception as e:
            logger.debug("DeFiLlama coingecko ID lookup failed for %s: %s", coin_id, e)

    # 3. Tertiary Method: CoinGecko Direct API
    if coin_id:
        headers = {}
        if coingecko_api_key:
            headers["x-cg-pro-api-key"] = coingecko_api_key
        try:
            resp = requests.get(
                _COINGECKO_PRICE_URL,
                params={"ids": coin_id, "vs_currencies": "usd"},
                headers=headers,
                timeout=8,
            )
            if resp.status_code == 200:
                data = resp.json()
                price = data.get(coin_id, {}).get("usd")
                if price is not None:
                    p = float(price)
                    _set_cached_price(cache_key, p)
                    return p
        except Exception as e:
            logger.debug("CoinGecko direct price failed for %s: %s", symbol, e)

    return None


def get_usd_price(symbol: str, api_key: str = "") -> float | None:
    """Backward-compatible helper for symbol-only price lookup."""
    return get_token_price(symbol=symbol, coingecko_api_key=api_key)


def _load_coin_list(api_key: str = "") -> None:
    global _cache_loaded
    # Pre-populate common major tokens so we don't even need network call for most
    common = {
        "ETH": "ethereum", "WETH": "weth", "BTC": "bitcoin", "WBTC": "wrapped-bitcoin",
        "UNI": "uniswap", "LINK": "chainlink", "AAVE": "aave", "ARB": "arbitrum",
        "OP": "optimism", "MATIC": "matic-network", "POL": "polygon-ecosystem-token",
        "SOL": "solana", "DOGE": "dogecoin", "AVAX": "avalanche-2", "SHIB": "shiba-inu",
        "PEPE": "pepe", "NEAR": "near", "FET": "fetch-ai", "RENDER": "render-token",
        "INJ": "injective-protocol", "SUI": "sui", "APT": "aptos", "TIA": "celestia",
    }
    _symbol_cache.update(common)
    _cache_loaded = True


def _get_coingecko_id(symbol: str, api_key: str = "") -> str | None:
    if not _cache_loaded:
        _load_coin_list(api_key)
    return _symbol_cache.get(symbol.upper())
