import pytest
from unittest.mock import MagicMock, patch
from src.monitor import Monitor
from src.chains import CHAINS
from src.config import Config
from src.wallets import Entity
from src.dedup import DedupStore
from src.explorer import TokenTransfer


def _make_config(**kwargs):
    defaults = dict(
        telegram_token="tok",
        telegram_chat_ids=["cid"],
        usd_threshold=100000.0,
        poll_interval=180,
        explorer_keys={c.id: "key" for c in CHAINS},
        coingecko_api_key="",
    )
    defaults.update(kwargs)
    return Config(**defaults)


def _make_entity(addresses: list) -> Entity:
    return Entity(label="TestEntity", addresses=addresses)


def _make_transfer(**kwargs) -> TokenTransfer:
    defaults = dict(
        tx_hash="0xhash",
        from_addr="0xfrom",
        to_addr="0xto",
        token_symbol="UNI",
        token_name="Uniswap",
        token_decimals=18,
        raw_value="1000000000000000000000",  # 1000 UNI
        block_timestamp="1700000000",
        contract_address="0xcontract",
    )
    defaults.update(kwargs)
    return TokenTransfer(**defaults)


def test_poll_chain_sends_alert_for_large_altcoin(tmp_path):
    cfg = _make_config()
    chain = next(c for c in CHAINS if c.id == "ethereum")
    entity = _make_entity(["0xfrom"])
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    monitor = Monitor(cfg, [entity], store)
    transfer = _make_transfer()

    with patch("src.monitor.fetch_token_transfers", return_value=[transfer]), \
         patch("src.monitor.get_token_price", return_value=200.0), \
         patch("src.monitor.send_alert") as mock_alert, \
         patch("src.monitor.time.sleep"):
        alerts, txs = monitor.poll_chain(chain)

    assert alerts == 1
    mock_alert.assert_called_once()


def test_poll_chain_skips_stablecoin(tmp_path):
    cfg = _make_config()
    chain = next(c for c in CHAINS if c.id == "ethereum")
    entity = _make_entity(["0xfrom"])
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    monitor = Monitor(cfg, [entity], store)
    transfer = _make_transfer(token_symbol="USDC")

    with patch("src.monitor.fetch_token_transfers", return_value=[transfer]), \
         patch("src.monitor.send_alert") as mock_alert, \
         patch("src.monitor.time.sleep"):
        alerts, txs = monitor.poll_chain(chain)

    assert alerts == 0
    mock_alert.assert_not_called()


def test_poll_chain_skips_below_threshold(tmp_path):
    cfg = _make_config(usd_threshold=100000.0)
    chain = next(c for c in CHAINS if c.id == "ethereum")
    entity = _make_entity(["0xfrom"])
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    monitor = Monitor(cfg, [entity], store)
    transfer = _make_transfer()  # 1000 UNI

    with patch("src.monitor.fetch_token_transfers", return_value=[transfer]), \
         patch("src.monitor.get_token_price", return_value=50.0), \
         patch("src.monitor.send_alert") as mock_alert, \
         patch("src.monitor.time.sleep"):
        alerts, txs = monitor.poll_chain(chain)

    # 1000 UNI * $50 = $50,000 < $100,000 threshold
    assert alerts == 0
    mock_alert.assert_not_called()


def test_poll_chain_major_token_threshold(tmp_path):
    cfg = _make_config(usd_threshold=100000.0)
    chain = next(c for c in CHAINS if c.id == "ethereum")
    entity = _make_entity(["0xfrom"])
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    monitor = Monitor(cfg, [entity], store)
    
    # Below $1M threshold
    transfer1 = _make_transfer(token_symbol="ETH", tx_hash="0xhash1")
    # Above $1M threshold
    transfer2 = _make_transfer(token_symbol="ETH", tx_hash="0xhash2", raw_value="3000000000000000000000") # 3000 ETH

    with patch("src.monitor.fetch_token_transfers", return_value=[transfer1, transfer2]), \
         patch("src.monitor.get_token_price", return_value=500.0), \
         patch("src.monitor.send_alert") as mock_alert, \
         patch("src.monitor.time.sleep"):
        alerts, txs = monitor.poll_chain(chain)

    assert alerts == 1
    mock_alert.assert_called_once()
    assert mock_alert.call_args[1]["tx_hash"] == "0xhash2"


def test_poll_chain_deduplicates(tmp_path):
    cfg = _make_config()
    chain = next(c for c in CHAINS if c.id == "ethereum")
    entity = _make_entity(["0xfrom"])
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    monitor = Monitor(cfg, [entity], store)
    transfer = _make_transfer()

    with patch("src.monitor.fetch_token_transfers", return_value=[transfer]), \
         patch("src.monitor.get_token_price", return_value=200.0), \
         patch("src.monitor.send_alert") as mock_alert, \
         patch("src.monitor.time.sleep"):
        monitor.poll_chain(chain)
        alerts, txs = monitor.poll_chain(chain)

    assert alerts == 0
    assert mock_alert.call_count == 1
