import pytest
from unittest.mock import patch, MagicMock
from src.notifier import send_alert, send_accumulation_alert


def test_send_accumulation_alert():
    with patch("src.notifier.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        send_accumulation_alert(
            telegram_token="test_token",
            chat_ids=["123", "456"],
            chain_name="Ethereum",
            token_symbol="ARB",
            token_name="Arbitrum",
            total_amount=600000.0,
            total_usd=540000.0,
            tx_count=4,
            milestone_tier=500000.0,
            recipient_addr="0xrecipient",
            entity_label="Wintermute 1",
            window_hours=24,
            timestamp=1700000000,
        )

        assert mock_post.call_count == 2
        call_json = mock_post.call_args_list[0][1]["json"]
        assert "ACCUMULATION DETECTED" in call_json["text"]
        assert "ARB" in call_json["text"]
        assert "$500,000.00" in call_json["text"]
        assert "Wintermute 1" in call_json["text"]
