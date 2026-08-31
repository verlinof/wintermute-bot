import json
import pytest
from src.wallets import Entity, load_wallets


def test_load_wallets_auto_detects_seller_keyword(tmp_path):
    wallets_file = tmp_path / "wallets.json"
    data = {
        "entities": [
            {
                "label": "Binance Cold Wallet: Wintermute 2 (akumulasi)",
                "addresses": ["0x5a52E96BAcdaBb82fd05763E25335261B270Efcb"]
            },
            {
                "label": "Binance Hot Wallet: Wintermute (jualan)",
                "addresses": ["0x28C6c06298d514Db089934071355E5743bf21d60"]
            },
            {
                "label": "Binance Hot Wallet: Wintermute (DUMP)",
                "addresses": ["0x1111111111111111111111111111111111111111"]
            },
            {
                "label": "Whale Seller",
                "addresses": ["0x2222222222222222222222222222222222222222"]
            },
            {
                "label": "Regular Buyer",
                "addresses": ["0x3333333333333333333333333333333333333333"]
            }
        ]
    }
    wallets_file.write_text(json.dumps(data), encoding="utf-8")

    entities = load_wallets(str(wallets_file))
    assert len(entities) == 5
    assert entities[0].track_accumulation is True
    assert entities[1].track_accumulation is False
    assert entities[2].track_accumulation is False
    assert entities[3].track_accumulation is False
    assert entities[4].track_accumulation is True


def test_load_wallets_explicit_override(tmp_path):
    wallets_file = tmp_path / "wallets.json"
    data = {
        "entities": [
            {
                "label": "Explicitly Disabled",
                "addresses": ["0x123"],
                "track_accumulation": False
            },
            {
                "label": "Has Jualan in name but forced true",
                "addresses": ["0x456"],
                "track_accumulation": True
            }
        ]
    }
    wallets_file.write_text(json.dumps(data), encoding="utf-8")

    entities = load_wallets(str(wallets_file))
    assert entities[0].track_accumulation is False
    assert entities[1].track_accumulation is True
