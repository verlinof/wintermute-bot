import json
import pytest
import src.labels as labels_module
from src.labels import get_address_label, load_file_labels


def setup_function():
    labels_module._file_labels_cache = None


def test_get_address_label_known():
    lbl = get_address_label("0x28c6c06298d514db089934071355e5743bf21d60")
    assert lbl == "Binance: Hot Wallet 20"

    lbl_arb = get_address_label("0xb38e8c17e38363af6ebdcb3dae12e0243582891d")
    assert lbl_arb == "Binance: Hot Wallet (Arbitrum)"


def test_get_address_label_custom_arg():
    custom = {"0x1111111111111111111111111111111111111111": "My Test Wallet"}
    lbl = get_address_label("0x1111111111111111111111111111111111111111", custom_labels=custom)
    assert lbl == "My Test Wallet"


def test_get_address_label_from_labels_json(tmp_path, monkeypatch):
    labels_file = tmp_path / "labels.json"
    data = {
        "0x9999999999999999999999999999999999999999": "Binance: Deposit Special"
    }
    labels_file.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(labels_module, "load_file_labels", lambda: load_file_labels(str(labels_file)))
    lbl = get_address_label("0x9999999999999999999999999999999999999999")
    assert lbl == "Binance: Deposit Special"


def test_get_address_label_unknown():
    lbl = get_address_label("0x000000000000000000000000000000000000dead")
    assert lbl == "Unknown / External Wallet"
