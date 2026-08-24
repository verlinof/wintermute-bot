import logging
import time
from src.config import Config
from src.wallets import Entity
from src.chains import Chain, CHAINS
from src.explorer import fetch_token_transfers, compute_amount
from src.filters import is_skip_token, meets_threshold
from src.price import get_usd_price
from src.dedup import DedupStore
from src.notifier import send_alert

logger = logging.getLogger(__name__)


class Monitor:
    def __init__(self, config: Config, entities: list, dedup_store: DedupStore):
        self.config = config
        self.entities = entities
        self.dedup = dedup_store

    def poll_chain(self, chain: Chain) -> int:
        """Poll one chain for all tracked entities. Returns count of alerts sent."""
        api_key = self.config.explorer_keys.get(chain.id, "")
        alerts_sent = 0

        for entity in self.entities:
            addresses = entity.get_addresses(chain.id)
            for address in addresses:
                transfers = fetch_token_transfers(chain, address, api_key)
                time.sleep(0.25)

                for tx in transfers:
                    if self.dedup.is_seen(tx.tx_hash):
                        continue
                    if is_skip_token(tx.token_symbol):
                        self.dedup.mark_seen(tx.tx_hash)
                        continue

                    amount = compute_amount(tx.raw_value, tx.token_decimals)
                    usd_price = get_usd_price(tx.token_symbol, self.config.coingecko_api_key)
                    if usd_price is None:
                        logger.debug(
                            "Skipping %s %s - no price data", tx.token_symbol, tx.tx_hash
                        )
                        continue

                    usd_value = amount * usd_price
                    if not meets_threshold(usd_value, self.config.usd_threshold):
                        self.dedup.mark_seen(tx.tx_hash)
                        continue

                    send_alert(
                        telegram_token=self.config.telegram_token,
                        chat_id=self.config.telegram_chat_id,
                        chain_name=chain.name,
                        token_symbol=tx.token_symbol,
                        token_name=tx.token_name,
                        amount=amount,
                        usd_value=usd_value,
                        from_addr=tx.from_addr,
                        to_addr=tx.to_addr,
                        from_label=entity.label,
                        tx_hash=tx.tx_hash,
                        tx_url=chain.explorer_tx_url,
                        timestamp=tx.block_timestamp,
                    )
                    self.dedup.mark_seen(tx.tx_hash)
                    alerts_sent += 1

        return alerts_sent

    def run_once(self) -> None:
        """Poll all configured chains once."""
        total = 0
        for chain in CHAINS:
            logger.info("Polling %s...", chain.name)
            try:
                count = self.poll_chain(chain)
                total += count
            except Exception as e:
                logger.error("Unexpected error polling %s: %s", chain.name, e)
        logger.info("Poll complete - %d alert(s) sent", total)
