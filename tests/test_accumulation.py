import time
import pytest
from src.accumulation import AccumulationStore


def test_record_inflow_and_stats(tmp_path):
    db_path = str(tmp_path / "test_accumulation.db")
    store = AccumulationStore(db_path=db_path)

    now = int(time.time())

    # Record 2 inflows for UNI
    store.record_inflow(
        tx_hash="0xtx1",
        chain="ethereum",
        entity_label="Wintermute 1",
        recipient_addr="0xrecipient",
        token_symbol="UNI",
        token_name="Uniswap",
        amount=10000.0,
        usd_value=100000.0,
        timestamp=now - 3600,  # 1 hour ago
    )
    store.record_inflow(
        tx_hash="0xtx2",
        chain="ethereum",
        entity_label="Wintermute 1",
        recipient_addr="0xrecipient",
        token_symbol="UNI",
        token_name="Uniswap",
        amount=50000.0,
        usd_value=500000.0,
        timestamp=now - 1800,  # 30 mins ago
    )

    # Inflow for different token (ARB)
    store.record_inflow(
        tx_hash="0xtx3",
        chain="ethereum",
        entity_label="Wintermute 1",
        recipient_addr="0xrecipient",
        token_symbol="ARB",
        token_name="Arbitrum",
        amount=20000.0,
        usd_value=20000.0,
        timestamp=now - 1800,
    )

    # Old inflow outside 24h window
    store.record_inflow(
        tx_hash="0xtx4",
        chain="ethereum",
        entity_label="Wintermute 1",
        recipient_addr="0xrecipient",
        token_symbol="UNI",
        token_name="Uniswap",
        amount=50000.0,
        usd_value=500000.0,
        timestamp=now - (25 * 3600),  # 25 hours ago
    )

    # Duplicate tx_hash should be ignored
    store.record_inflow(
        tx_hash="0xtx1",
        chain="ethereum",
        entity_label="Wintermute 1",
        recipient_addr="0xrecipient",
        token_symbol="UNI",
        token_name="Uniswap",
        amount=10000.0,
        usd_value=100000.0,
        timestamp=now - 3600,
    )

    # Check 24h window stats for UNI
    total_amount, total_usd, tx_count = store.get_accumulation_stats(
        chain="ethereum",
        entity_label="Wintermute 1",
        token_symbol="UNI",
        window_hours=24,
    )

    assert tx_count == 2
    assert total_amount == pytest.approx(60000.0)
    assert total_usd == pytest.approx(600000.0)


def test_milestone_tracking(tmp_path):
    db_path = str(tmp_path / "test_accumulation.db")
    store = AccumulationStore(db_path=db_path)

    # Initial milestone is 0.0
    m0 = store.get_highest_milestone("ethereum", "Wintermute 1", "UNI")
    assert m0 == 0.0

    # Set milestone to $500k
    store.set_highest_milestone("ethereum", "Wintermute 1", "UNI", 500000.0)
    m1 = store.get_highest_milestone("ethereum", "Wintermute 1", "UNI")
    assert m1 == 500000.0

    # Update milestone to $1M
    store.set_highest_milestone("ethereum", "Wintermute 1", "UNI", 1000000.0)
    m2 = store.get_highest_milestone("ethereum", "Wintermute 1", "UNI")
    assert m2 == 1000000.0


def test_pruning_old_transfers(tmp_path):
    db_path = str(tmp_path / "test_accumulation.db")
    store = AccumulationStore(db_path=db_path)

    now = int(time.time())

    # Recent tx
    store.record_inflow(
        tx_hash="0xrecent",
        chain="ethereum",
        entity_label="Wintermute 1",
        recipient_addr="0xrecipient",
        token_symbol="UNI",
        token_name="Uniswap",
        amount=1000.0,
        usd_value=10000.0,
        timestamp=now - 3600,
    )

    # Old tx
    store.record_inflow(
        tx_hash="0xold",
        chain="ethereum",
        entity_label="Wintermute 1",
        recipient_addr="0xrecipient",
        token_symbol="UNI",
        token_name="Uniswap",
        amount=1000.0,
        usd_value=10000.0,
        timestamp=now - (48 * 3600),
    )

    pruned = store.prune_old_transfers(window_hours=24)
    assert pruned == 1

    # Check total remaining
    _, _, count = store.get_accumulation_stats("ethereum", "Wintermute 1", "UNI", window_hours=72)
    assert count == 1
