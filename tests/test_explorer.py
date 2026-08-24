import pytest
from unittest.mock import patch, MagicMock
from src.explorer import fetch_token_transfers, compute_amount, TokenTransfer
from src.chains import CHAINS


def test_compute_amount_18_decimals():
    result = compute_amount("1000000000000000000", 18)
    assert result == pytest.approx(1.0)


def test_compute_amount_6_decimals():
    result = compute_amount("1000000", 6)
    assert result == pytest.approx(1.0)


def test_fetch_returns_transfers():
    chain = next(c for c in CHAINS if c.id == "ethereum")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "status": "1",
        "result": [
            {
                "hash": "0xabc",
                "from": "0xfrom",
                "to": "0xto",
                "tokenSymbol": "UNI",
                "tokenName": "Uniswap",
                "tokenDecimal": "18",
                "value": "1000000000000000000000",
                "timeStamp": "1700000000",
                "contractAddress": "0xcontract",
            }
        ],
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("src.explorer.requests.get", return_value=mock_resp):
        transfers = fetch_token_transfers(chain, "0xfrom", "apikey")

    assert len(transfers) == 1
    assert transfers[0].token_symbol == "UNI"
    assert transfers[0].tx_hash == "0xabc"


def test_fetch_handles_api_error():
    chain = next(c for c in CHAINS if c.id == "ethereum")
    import requests as req
    with patch("src.explorer.requests.get", side_effect=req.RequestException("timeout")):
        transfers = fetch_token_transfers(chain, "0xfrom", "apikey")
    assert transfers == []
