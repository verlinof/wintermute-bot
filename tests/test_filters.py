import pytest
from src.filters import is_skip_token, meets_threshold, SKIP_SYMBOLS


def test_stablecoins_skipped():
    for sym in ["USDT", "USDC", "DAI", "BUSD", "TUSD", "FRAX", "LUSD",
                "USDP", "GUSD", "USDD", "FDUSD", "PYUSD", "USDE", "USDS",
                "GHO", "EURC", "EURS"]:
        assert is_skip_token(sym), f"{sym} should be skipped"


def test_eth_variants_skipped():
    for sym in ["ETH", "WETH"]:
        assert is_skip_token(sym)


def test_btc_variants_skipped():
    for sym in ["BTC", "WBTC"]:
        assert is_skip_token(sym)


def test_altcoins_not_skipped():
    for sym in ["UNI", "AAVE", "LINK", "CRV", "ARB", "OP", "DOGE"]:
        assert not is_skip_token(sym)


def test_case_insensitive_skip():
    assert is_skip_token("usdt")
    assert is_skip_token("Usdc")


def test_meets_threshold_above():
    assert meets_threshold(150000.0, 100000.0) is True


def test_meets_threshold_exact():
    assert meets_threshold(100000.0, 100000.0) is True


def test_meets_threshold_below():
    assert meets_threshold(99999.99, 100000.0) is False
