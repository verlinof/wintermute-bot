STABLECOIN_SYMBOLS: frozenset = frozenset({
    "USDT", "USDC", "DAI", "BUSD", "TUSD", "FRAX", "LUSD",
    "USDP", "GUSD", "USDD", "FDUSD", "PYUSD", "USDE", "USDS",
    "CRVUSD", "GHO", "EURC", "EURS", "USDT0", "USD₮0", "USD₮", "RLUSD"
})

ETH_SYMBOLS: frozenset = frozenset({"ETH", "WETH"})
BTC_SYMBOLS: frozenset = frozenset({"BTC", "WBTC", "RENBTC", "TBTC"})
MAJOR_SYMBOLS: frozenset = ETH_SYMBOLS | BTC_SYMBOLS


def is_skip_token(symbol: str) -> bool:
    """Return True if this token should be filtered out completely (stablecoins)."""
    return symbol.upper() in STABLECOIN_SYMBOLS


def get_required_threshold(symbol: str, base_threshold: float) -> float:
    """Return the USD threshold required for this token."""
    if symbol.upper() in MAJOR_SYMBOLS:
        return 1_000_000.0
    return base_threshold


def meets_threshold(usd_value: float, threshold: float) -> bool:
    """Return True if the USD value meets or exceeds the threshold."""
    return usd_value >= threshold
