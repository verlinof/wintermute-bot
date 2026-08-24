STABLECOIN_SYMBOLS: frozenset = frozenset({
    "USDT", "USDC", "DAI", "BUSD", "TUSD", "FRAX", "LUSD",
    "USDP", "GUSD", "USDD", "FDUSD", "PYUSD", "USDE", "USDS",
    "CRVUSD", "GHO", "EURC", "EURS",
})

ETH_SYMBOLS: frozenset = frozenset({"ETH", "WETH"})
BTC_SYMBOLS: frozenset = frozenset({"BTC", "WBTC", "RENBTC", "TBTC"})

SKIP_SYMBOLS: frozenset = STABLECOIN_SYMBOLS | ETH_SYMBOLS | BTC_SYMBOLS


def is_skip_token(symbol: str) -> bool:
    """Return True if this token should be filtered out (stablecoin/ETH/BTC)."""
    return symbol.upper() in SKIP_SYMBOLS


def meets_threshold(usd_value: float, threshold: float) -> bool:
    """Return True if the USD value meets or exceeds the threshold."""
    return usd_value >= threshold
