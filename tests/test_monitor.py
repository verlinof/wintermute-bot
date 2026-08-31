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


def test_poll_chain_accumulation_detection(tmp_path):
    from src.accumulation import AccumulationStore
    cfg = _make_config(
        usd_threshold=500000.0,
        accumulation_enabled=True,
        accumulation_usd_threshold=500000.0,
        accumulation_window_hours=24,
        accumulation_min_tx_count=2,
    )
    chain = next(c for c in CHAINS if c.id == "ethereum")
    entity = _make_entity(["0xmonitored"])
    dedup = DedupStore(db_path=str(tmp_path / "dedup.db"))
    accum_store = AccumulationStore(db_path=str(tmp_path / "accum.db"))
    monitor = Monitor(cfg, [entity], dedup, accumulation_store=accum_store)

    import time
    now = int(time.time())

    # Inflow transfer 1: $300,000 USD (below single transfer threshold $500,000)
    tx1 = _make_transfer(
        tx_hash="0xtx1",
        from_addr="0xsender",
        to_addr="0xmonitored",
        token_symbol="ARB",
        raw_value="300000000000000000000000", # 300,000 ARB
        block_timestamp=str(now - 1800),
    )
    # Inflow transfer 2: $300,000 USD
    tx2 = _make_transfer(
        tx_hash="0xtx2",
        from_addr="0xsender",
        to_addr="0xmonitored",
        token_symbol="ARB",
        raw_value="300000000000000000000000", # 300,000 ARB
        block_timestamp=str(now - 600),
    )

    with patch("src.monitor.fetch_token_transfers", return_value=[tx1, tx2]), \
         patch("src.monitor.get_token_price", return_value=1.0), \
         patch("src.monitor.send_alert") as mock_single_alert, \
         patch("src.monitor.send_accumulation_alert") as mock_accum_alert, \
         patch("src.monitor.time.sleep"):
        alerts, txs = monitor.poll_chain(chain)

    # Single transfer alert should not trigger ($300k < $500k)
    mock_single_alert.assert_not_called()
    # Accumulation alert should trigger ($600k total >= $500k milestone tier, 2 txs)
    assert mock_accum_alert.call_count == 1
    call_args = mock_accum_alert.call_args[1]
    assert call_args["milestone_tier"] == 500000.0
    assert call_args["tx_count"] == 2
    assert call_args["token_symbol"] == "ARB"


def test_poll_chain_accumulation_milestone_progression(tmp_path):
    from src.accumulation import AccumulationStore
    cfg = _make_config(
        usd_threshold=500000.0,
        accumulation_enabled=True,
        accumulation_usd_threshold=500000.0,
        accumulation_window_hours=24,
        accumulation_min_tx_count=2,
    )
    chain = next(c for c in CHAINS if c.id == "ethereum")
    entity = _make_entity(["0xmonitored"])
    dedup = DedupStore(db_path=str(tmp_path / "dedup.db"))
    accum_store = AccumulationStore(db_path=str(tmp_path / "accum.db"))
    monitor = Monitor(cfg, [entity], dedup, accumulation_store=accum_store)

    import time
    now = int(time.time())

    # Cycle 1: Two $300k transfers -> Total $600k (Crosses $500k milestone tier)
    tx1 = _make_transfer(tx_hash="0xtx1", from_addr="0xsender", to_addr="0xmonitored", token_symbol="ARB", raw_value="300000000000000000000000", block_timestamp=str(now - 1800))
    tx2 = _make_transfer(tx_hash="0xtx2", from_addr="0xsender", to_addr="0xmonitored", token_symbol="ARB", raw_value="300000000000000000000000", block_timestamp=str(now - 1200))

    with patch("src.monitor.fetch_token_transfers", return_value=[tx1, tx2]), \
         patch("src.monitor.get_token_price", return_value=1.0), \
         patch("src.monitor.send_accumulation_alert") as mock_accum_alert, \
         patch("src.monitor.time.sleep"):
        alerts, _ = monitor.poll_chain(chain)

    assert alerts == 1
    assert mock_accum_alert.call_count == 1
    assert mock_accum_alert.call_args[1]["milestone_tier"] == 500000.0

    # Cycle 2: One $200k transfer -> Total $800k (Still in $500k tier -> NO new alert)
    tx3 = _make_transfer(tx_hash="0xtx3", from_addr="0xsender", to_addr="0xmonitored", token_symbol="ARB", raw_value="200000000000000000000000", block_timestamp=str(now - 600))

    with patch("src.monitor.fetch_token_transfers", return_value=[tx3]), \
         patch("src.monitor.get_token_price", return_value=1.0), \
         patch("src.monitor.send_accumulation_alert") as mock_accum_alert2, \
         patch("src.monitor.time.sleep"):
        alerts2, _ = monitor.poll_chain(chain)

    assert alerts2 == 0
    mock_accum_alert2.assert_not_called()

    # Cycle 3: One $300k transfer -> Total $1.1M (Crosses $1,000,000 tier -> Triggers Tier 2 Alert!)
    tx4 = _make_transfer(tx_hash="0xtx4", from_addr="0xsender", to_addr="0xmonitored", token_symbol="ARB", raw_value="300000000000000000000000", block_timestamp=str(now - 100))

    with patch("src.monitor.fetch_token_transfers", return_value=[tx4]), \
         patch("src.monitor.get_token_price", return_value=1.0), \
         patch("src.monitor.send_accumulation_alert") as mock_accum_alert3, \
         patch("src.monitor.time.sleep"):
        alerts3, _ = monitor.poll_chain(chain)

    assert alerts3 == 1
    assert mock_accum_alert3.call_count == 1
    assert mock_accum_alert3.call_args[1]["milestone_tier"] == 1000000.0


def test_poll_chain_skips_accumulation_for_seller_entity(tmp_path):
    from src.accumulation import AccumulationStore
    cfg = _make_config(
        usd_threshold=500000.0,
        accumulation_enabled=True,
        accumulation_usd_threshold=500000.0,
        accumulation_window_hours=24,
        accumulation_min_tx_count=2,
    )
    chain = next(c for c in CHAINS if c.id == "ethereum")
    # Entity with track_accumulation=False (Seller wallet)
    seller_entity = Entity(label="Binance: Hot Wallet (jualan)", addresses=["0xseller"], track_accumulation=False)
    dedup = DedupStore(db_path=str(tmp_path / "dedup.db"))
    accum_store = AccumulationStore(db_path=str(tmp_path / "accum.db"))
    monitor = Monitor(cfg, [seller_entity], dedup, accumulation_store=accum_store)

    import time
    now = int(time.time())

    tx1 = _make_transfer(tx_hash="0xtx1", from_addr="0xfrom", to_addr="0xseller", token_symbol="ARB", raw_value="300000000000000000000000", block_timestamp=str(now - 1800))
    tx2 = _make_transfer(tx_hash="0xtx2", from_addr="0xfrom", to_addr="0xseller", token_symbol="ARB", raw_value="300000000000000000000000", block_timestamp=str(now - 1200))

    with patch("src.monitor.fetch_token_transfers", return_value=[tx1, tx2]), \
         patch("src.monitor.get_token_price", return_value=1.0), \
         patch("src.monitor.send_alert") as mock_single_alert, \
         patch("src.monitor.send_accumulation_alert") as mock_accum_alert, \
         patch("src.monitor.time.sleep"):
        alerts, txs = monitor.poll_chain(chain)

    # Accumulation alert should NOT be called for seller entity
    mock_accum_alert.assert_not_called()
    # And accumulation store should NOT have recorded any inflow for this entity
    _, _, count = accum_store.get_accumulation_stats(chain.name, seller_entity.label, "ARB")
    assert count == 0
