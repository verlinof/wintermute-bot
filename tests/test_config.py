import os
import importlib
import pytest
from unittest.mock import patch


def test_load_config_reads_env():
    env = {
        "TELEGRAM_BOT_TOKEN": "token123",
        "TELEGRAM_CHAT_ID": "123456",
        "USD_THRESHOLD": "50000",
        "POLL_INTERVAL": "120",
        "ETHERSCAN_API_KEY": "unified_key_123",
    }
    with patch.dict(os.environ, env, clear=True):
        import src.config
        importlib.reload(src.config)
        from src.config import load_config
        cfg = load_config()
    assert cfg.telegram_token == "token123"
    assert cfg.telegram_chat_ids == ["123456"]
    assert cfg.usd_threshold == 50000.0
    assert cfg.poll_interval == 120
    assert cfg.explorer_keys["ethereum"] == "unified_key_123"
    assert cfg.explorer_keys["bsc"] == "unified_key_123"
    assert cfg.explorer_keys["arbitrum"] == "unified_key_123"


def test_load_config_defaults():
    env = {
        "TELEGRAM_BOT_TOKEN": "t",
        "TELEGRAM_CHAT_ID": "c",
    }
    with patch.dict(os.environ, env, clear=True):
        import src.config
        importlib.reload(src.config)
        from src.config import load_config
        cfg = load_config()
    assert cfg.usd_threshold == 100000.0
    assert cfg.poll_interval == 180


def test_load_config_missing_required_raises():
    with patch.dict(os.environ, {}, clear=True):
        import src.config
        importlib.reload(src.config)
        from src.config import load_config
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            load_config()
