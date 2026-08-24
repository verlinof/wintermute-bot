import os
import pytest
from src.dedup import DedupStore


def test_new_tx_not_seen(tmp_path):
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    assert store.is_seen("0xabc123") is False


def test_after_mark_seen(tmp_path):
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    store.mark_seen("0xabc123")
    assert store.is_seen("0xabc123") is True


def test_different_hashes_independent(tmp_path):
    store = DedupStore(db_path=str(tmp_path / "test.db"))
    store.mark_seen("0xaaa")
    assert store.is_seen("0xbbb") is False


def test_persists_across_instances(tmp_path):
    db = str(tmp_path / "test.db")
    store1 = DedupStore(db_path=db)
    store1.mark_seen("0xpersist")
    store2 = DedupStore(db_path=db)
    assert store2.is_seen("0xpersist") is True


def test_creates_parent_directory(tmp_path):
    nested = str(tmp_path / "subdir" / "nested.db")
    store = DedupStore(db_path=nested)
    assert os.path.exists(nested)
