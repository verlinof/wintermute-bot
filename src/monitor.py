import logging
import time
from src.config import Config
from src.wallets import Entity
from src.chains import Chain, CHAINS
from src.explorer import fetch_token_transfers, compute_amount
from src.filters import is_skip_token, meets_threshold, get_required_threshold
from src.price import get_token_price
from src.dedup import DedupStore
from src.accumulation import AccumulationStore
from src.notifier import send_alert, send_accumulation_alert

logger = logging.getLogger(__name__)


def _short_addr(addr: str) -> str:
    return addr[:6] + "..." + addr[-4:] if len(addr) > 10 else addr


def _short_hash(tx_hash: str) -> str:
    return tx_hash[:8] + "..." if len(tx_hash) > 10 else tx_hash


class Monitor:
    def __init__(
        self,
        config: Config,
        entities: list[Entity],
        dedup_store: DedupStore,
        accumulation_store: AccumulationStore | None = None,
    ):
        self.config = config
        self.entities = entities
        self.dedup = dedup_store
        self.accumulation_store = accumulation_store or AccumulationStore()
        
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
            entity_addrs_set = {a.lower() for a in addresses}

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

                    # 5. Compute USD value
                    usd_value = amount * usd_price

                    # 6. Inflow & Accumulation Check
                    if (
                        self.config.accumulation_enabled
                        and entity.track_accumulation
                        and tx.to_addr.lower() in entity_addrs_set
                    ):
                        self.accumulation_store.record_inflow(
                            tx_hash=tx.tx_hash,
                            chain=chain.name,
                            entity_label=entity.label,
                            recipient_addr=tx.to_addr,
                            token_symbol=tx.token_symbol,
                            token_name=tx.token_name,
                            amount=amount,
                            usd_value=usd_value,
                            timestamp=int(tx.block_timestamp),
                        )
                        tot_amount, tot_usd, tx_count = self.accumulation_store.get_accumulation_stats(
                            chain=chain.name,
                            entity_label=entity.label,
                            token_symbol=tx.token_symbol,
                            window_hours=self.config.accumulation_window_hours,
                        )
                        threshold = self.config.accumulation_usd_threshold
                        current_milestone = (tot_usd // threshold) * threshold
                        highest_milestone = self.accumulation_store.get_highest_milestone(
                            chain=chain.name,
                            entity_label=entity.label,
                            token_symbol=tx.token_symbol,
                        )

                        if (
                            tx_count >= self.config.accumulation_min_tx_count
                            and current_milestone >= threshold
                            and current_milestone > highest_milestone
                        ):
                            logger.info(
                                "  [%s] 📈 ACCUMULATION DETECTED! %s (%s) reached $%s milestone tier (~$%s total across %d txs) -> Sending Alert!",
                                chain.name,
                                tx.token_symbol,
                                entity.label,
                                f"{current_milestone:,.0f}",
                                f"{tot_usd:,.2f}",
                                tx_count,
                            )
                            send_accumulation_alert(
                                telegram_token=self.config.telegram_token,
                                chat_ids=self.config.telegram_chat_ids,
                                chain_name=chain.name,
                                token_symbol=tx.token_symbol,
                                token_name=tx.token_name,
                                total_amount=tot_amount,
                                total_usd=tot_usd,
                                tx_count=tx_count,
                                milestone_tier=current_milestone,
                                recipient_addr=tx.to_addr,
                                entity_label=entity.label,
                                window_hours=self.config.accumulation_window_hours,
                                timestamp=tx.block_timestamp,
                            )
                            self.accumulation_store.set_highest_milestone(
                                chain=chain.name,
                                entity_label=entity.label,
                                token_symbol=tx.token_symbol,
                                milestone_usd=current_milestone,
                            )
                            alerts_sent += 1

                    # 7. Single Large Transfer Threshold Check
                    required_threshold = get_required_threshold(tx.token_symbol, self.config.usd_threshold)

                    if meets_threshold(usd_value, required_threshold):
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
                        alerts_sent += 1
                    else:
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

                    # Mark transaction as seen
                    self.dedup.mark_seen(tx.tx_hash)

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

        if self.config.accumulation_enabled:
            pruned = self.accumulation_store.prune_old_transfers(self.config.accumulation_window_hours)
            if pruned > 0:
                logger.debug("Pruned %d expired accumulation inflow records", pruned)

        elapsed = time.time() - start_t
        logger.info(
            "=== Cycle complete in %.2fs: %d tx(s) scanned, %d alert(s) sent ===",
            elapsed, total_scanned, total_alerts,
        )
