import pytest
from unittest.mock import patch, MagicMock
import src.price as price_module
from src.price import get_usd_price


def setup_function():
    price_module._symbol_cache.clear()
    price_module._cache_loaded = False


def test_known_symbol_returns_price():
    mock_price_resp = MagicMock()
    mock_price_resp.json.return_value = {"uniswap": {"usd": 8.50}}
    mock_price_resp.raise_for_status = MagicMock()

    mock_id_resp = MagicMock()
    mock_id_resp.json.return_value = [
        {"id": "uniswap", "symbol": "uni", "name": "Uniswap"}
    ]
    mock_id_resp.raise_for_status = MagicMock()

    with patch("src.price.requests.get") as mock_get:
        mock_get.side_effect = [mock_id_resp, mock_price_resp]
        p = get_usd_price("UNI")

    assert p == pytest.approx(8.50)


def test_unknown_symbol_returns_none():
    mock_id_resp = MagicMock()
    mock_id_resp.json.return_value = []
    mock_id_resp.raise_for_status = MagicMock()

    with patch("src.price.requests.get", return_value=mock_id_resp):
        p = get_usd_price("FAKETOKEN123")

    assert p is None


def test_network_error_returns_none():
    import requests as req
    with patch("src.price.requests.get", side_effect=req.RequestException("timeout")):
        p = get_usd_price("UNI")
    assert p is None
