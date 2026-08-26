import logging
import time
from src.config import Config
from src.wallets import Entity
from src.chains import Chain, CHAINS
from src.explorer import fetch_token_transfers, compute_amount
from src.filters import is_skip_token, meets_threshold, get_required_threshold
from src.price import get_token_price
from src.dedup import DedupStore
from src.notifier import send_alert

logger = logging.getLogger(__name__)


def _short_addr(addr: str) -> str:
    return addr[:6] + "..." + addr[-4:] if len(addr) > 10 else addr


def _short_hash(tx_hash: str) -> str:
    return tx_hash[:8] + "..." if len(tx_hash) > 10 else tx_hash


class Monitor:
    def __init__(self, config: Config, entities: list[Entity], dedup_store: DedupStore):
        self.config = config
        self.entities = entities
        self.dedup = dedup_store
        
        # Build custom labels map from wallets.json
        self.custom_labels: dict[str, str] = {}
        for entity in entities:
            for addr in entity.get_addresses():
                self.custom_labels[addr.lower()] = entity.label

    def poll_chain(self, chain: Chain) -> tuple[int, int]:
        """Poll one chain for all tracked entities. Returns (alerts_sent, txs_scanned)."""
        api_key = self.config.explorer_keys.get(chain.id, "")
        alerts_sent = 0
        total_txs = 0

        for entity in self.entities:
            addresses = entity.get_addresses()
            for address in addresses:
                transfers = fetch_token_transfers(chain, address, api_key)
                total_txs += len(transfers)
                time.sleep(0.25)

                if transfers:
                    logger.info(
                        "[%s] %s (%s): Found %d token transfer(s)",
                        chain.name, entity.label, _short_addr(address), len(transfers),
                    )

                for tx in transfers:
                    # 1. Dedup check
                    if self.dedup.is_seen(tx.tx_hash):
                        continue

                    # 2. Stablecoin filter
                    if is_skip_token(tx.token_symbol):
                        logger.info(
                            "  [%s] ⏭️ TX %s [%s]: Skipped (Stablecoin)",
                            chain.name, _short_hash(tx.tx_hash), tx.token_symbol,
                        )
                        self.dedup.mark_seen(tx.tx_hash)
                        continue

                    # 3. Compute amount
                    amount = compute_amount(tx.raw_value, tx.token_decimals)

                    # 4. Fetch price
                    usd_price = get_token_price(
                        symbol=tx.token_symbol,
                        chain_prefix=chain.defillama_prefix,
                        contract_address=tx.contract_address,
                        coingecko_api_key=self.config.coingecko_api_key,
                    )
                    if usd_price is None:
                        logger.info(
                            "  [%s] ❓ TX %s [%s] Amount: %s: No USD price found -> Skipped",
                            chain.name, _short_hash(tx.tx_hash), tx.token_symbol, f"{amount:,.2f}",
                        )
                        continue

                    # 5. Compute USD value & threshold
                    usd_value = amount * usd_price
                    required_threshold = get_required_threshold(tx.token_symbol, self.config.usd_threshold)

                    if not meets_threshold(usd_value, required_threshold):
                        logger.info(
                            "  [%s] ⏭️ TX %s [%s] %s @ $%s = $%s USD (< $%s threshold) -> Skipped",
                            chain.name,
                            _short_hash(tx.tx_hash),
                            tx.token_symbol,
                            f"{amount:,.2f}",
                            f"{usd_price:,.4f}" if usd_price < 10 else f"{usd_price:,.2f}",
                            f"{usd_value:,.2f}",
                            f"{required_threshold:,.0f}",
                        )
                        self.dedup.mark_seen(tx.tx_hash)
                        continue

                    # 6. ALERT TRIGGERED!
                    logger.info(
                        "  [%s] 🚨 LARGE TRANSFER DETECTED! TX %s [%s] %s ($%s USD >= $%s) -> Sending Telegram Alert!",
                        chain.name,
                        _short_hash(tx.tx_hash),
                        tx.token_symbol,
                        f"{amount:,.2f}",
                        f"{usd_value:,.2f}",
                        f"{required_threshold:,.0f}",
                    )

                    send_alert(
                        telegram_token=self.config.telegram_token,
                        chat_ids=self.config.telegram_chat_ids,
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
                        custom_labels=self.custom_labels,
                    )
                    self.dedup.mark_seen(tx.tx_hash)
                    alerts_sent += 1

        return alerts_sent, total_txs

    def run_once(self) -> None:
        """Poll all configured chains once."""
        start_t = time.time()
        total_alerts = 0
        total_scanned = 0

        for chain in CHAINS:
            try:
                alerts, scanned = self.poll_chain(chain)
                total_alerts += alerts
                total_scanned += scanned
            except Exception as e:
                logger.error("Unexpected error polling %s: %s", chain.name, e)

        elapsed = time.time() - start_t
        logger.info(
            "=== Cycle complete in %.2fs: %d tx(s) scanned, %d alert(s) sent ===",
            elapsed, total_scanned, total_alerts,
        )
