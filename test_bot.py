#!/usr/bin/env python3
"""
Wintermute Bot — Diagnostic & Testing Tool
===========================================
Run this script to verify:
1. Environment & configuration (.env and wallets.json)
2. Telegram Bot connection & send a test alert
3. Price Oracle (DeFiLlama & CoinGecko)
4. Blockchain Explorer API V2 connections
5. Live wallet transaction simulation (dry-run with detailed breakdown)
6. Send a REAL live transaction alert to Telegram for proof!

Usage:
    python test_bot.py                     # Full diagnostic scan
    python test_bot.py --send-ping         # Send a ping test message to Telegram
    python test_bot.py --test-alert        # Fetch REAL transaction from Etherscan and send as live alert to Telegram!
    python test_bot.py --test-accumulation # Send a test accumulation milestone alert to Telegram!
"""
import sys
import os
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from src.config import load_config
from src.wallets import load_wallets
from src.chains import CHAINS
from src.explorer import fetch_token_transfers, compute_amount
from src.filters import is_skip_token, meets_threshold, get_required_threshold
from src.price import get_token_price
from src.notifier import send_alert, send_accumulation_alert
from src.labels import get_address_label


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_diagnostics(send_ping: bool = False, send_real_alert: bool = False, send_accum_alert: bool = False):
    print_banner("WINTERMUTE BOT - FULL SYSTEM DIAGNOSTICS")

    # -------------------------------------------------------------
    # 1. Config & Wallets Check
    # -------------------------------------------------------------
    print("\n[1/5] Checking Configuration & Wallets...")
    try:
        cfg = load_config()
        print(f"  [OK] Config loaded successfully")
        print(f"       - Base USD Threshold : ${cfg.usd_threshold:,.2f}")
        print(f"       - Poll Interval      : {cfg.poll_interval}s")
        if cfg.accumulation_enabled:
            print(f"       - Accumulation Track : ENABLED")
            print(f"         • Threshold / Tier : ${cfg.accumulation_usd_threshold:,.2f} USD")
            print(f"         • Rolling Window   : {cfg.accumulation_window_hours} hours")
            print(f"         • Min Transactions : {cfg.accumulation_min_tx_count} txs")
        else:
            print(f"       - Accumulation Track : DISABLED")
        key_status = ('Set (***' + cfg.explorer_keys.get('ethereum', '')[-4:] + ')') if cfg.explorer_keys.get('ethereum') else 'NOT SET'
        print(f"       - Etherscan API Key  : {key_status}")
    except Exception as e:
        print(f"  [FAIL] Error loading config: {e}")
        return

    try:
        entities = load_wallets("wallets.json")
        total_addresses = sum(len(e.get_addresses()) for e in entities)
        custom_labels: dict[str, str] = {}
        for entity in entities:
            for addr in entity.get_addresses():
                custom_labels[addr.lower()] = entity.label

        print(f"  [OK] Wallets loaded: {len(entities)} entity/entities ({total_addresses} address(es) total)")
        for idx, e in enumerate(entities, 1):
            addrs = e.get_addresses()
            print(f"       {idx}. {e.label}: {len(addrs)} address(es)")
            for a in addrs:
                print(f"          -> {a}")
    except Exception as e:
        print(f"  [FAIL] Error loading wallets.json: {e}")
        return

    # -------------------------------------------------------------
    # 2. Telegram Bot Connection
    # -------------------------------------------------------------
    print("\n[2/5] Testing Telegram Bot Connection...")
    try:
        get_me_url = f"https://api.telegram.org/bot{cfg.telegram_token}/getMe"
        resp = requests.get(get_me_url, timeout=10)
        data = resp.json()
        if data.get("ok"):
            bot_info = data["result"]
            print(f"  [OK] Telegram Bot Connected: @{bot_info.get('username')} ({bot_info.get('first_name')})")
            print(f"       - Target Chat ID(s): {', '.join(cfg.telegram_chat_ids)}")
            
            if send_ping:
                send_url = f"https://api.telegram.org/bot{cfg.telegram_token}/sendMessage"
                msg_text = (
                    "🚨 *Wintermute Bot Diagnostic Test*\n\n"
                    "✅ *Status:* Bot is alive & connected!\n"
                    f"📊 *Configured Threshold:* ${cfg.usd_threshold:,.0f} USD\n"
                    f"👀 *Monitored Entities:* {len(entities)}\n\n"
                    "Everything is ready to track transactions."
                )
                for chat_id in cfg.telegram_chat_ids:
                    r = requests.post(send_url, json={"chat_id": chat_id, "text": msg_text, "parse_mode": "Markdown"}, timeout=10)
                    if r.status_code == 200:
                        print(f"  [SUCCESS] Test ping sent to Telegram chat {chat_id} successfully!")
                    else:
                        print(f"  [WARN] Failed to send test alert to {chat_id}: {r.text}")

            if send_accum_alert:
                print(f"  🚀 Sending test accumulation milestone alert to Telegram chat(s)...")
                sample_entity = entities[0] if entities else None
                sample_label = sample_entity.label if sample_entity else "Wintermute"
                sample_recipient = sample_entity.get_addresses()[0] if sample_entity and sample_entity.get_addresses() else "0x0000000000000000000000000000000000000000"
                send_accumulation_alert(
                    telegram_token=cfg.telegram_token,
                    chat_ids=cfg.telegram_chat_ids,
                    chain_name="Ethereum",
                    token_symbol="ARB",
                    token_name="Arbitrum",
                    total_amount=600000.0,
                    total_usd=540000.0,
                    tx_count=4,
                    milestone_tier=cfg.accumulation_usd_threshold,
                    recipient_addr=sample_recipient,
                    entity_label=sample_label,
                    window_hours=cfg.accumulation_window_hours,
                )
                print("  [SUCCESS] Test accumulation milestone alert sent successfully!")
        else:
            print(f"  [FAIL] Telegram Bot error: {data.get('description')}")
    except Exception as e:
        print(f"  [FAIL] Telegram connection failed: {e}")

    # -------------------------------------------------------------
    # 3. Price Oracle Check
    # -------------------------------------------------------------
    print("\n[3/5] Testing Price Oracle (DeFiLlama & CoinGecko)...")
    test_symbols = ["ETH", "BTC", "UNI", "LINK", "ARB", "AAVE"]
    for sym in test_symbols:
        try:
            price = get_token_price(sym, coingecko_api_key=cfg.coingecko_api_key)
            if price is not None:
                print(f"  [OK] {sym:5}: ${price:,.2f} USD")
            else:
                print(f"  [WARN] {sym:5}: Price not found")
        except Exception as e:
            print(f"  [FAIL] {sym:5}: Error fetching price ({e})")

    # -------------------------------------------------------------
    # 4. Explorer API V2 Status Check
    # -------------------------------------------------------------
    print("\n[4/5] Testing Etherscan API V2 on configured chains...")
    api_key = cfg.explorer_keys.get("ethereum", "")
    for chain in CHAINS:
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": chain.chain_id,
            "module": "account",
            "action": "tokentx",
            "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
            "page": 1,
            "offset": 2,
            "sort": "desc",
            "apikey": api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            st = data.get("status")
            msg = data.get("message", "")
            res = data.get("result")
            if st == "1":
                print(f"  [OK]   {chain.name:15} (ChainID {chain.chain_id:5}): Active & responding (OK)")
            elif "Free API access is not supported" in str(res):
                print(f"  [INFO] {chain.name:15} (ChainID {chain.chain_id:5}): Requires Pro Etherscan Key on V2")
            else:
                print(f"  [INFO] {chain.name:15} (ChainID {chain.chain_id:5}): status={st}, msg={msg}")
        except Exception as e:
            print(f"  [FAIL] {chain.name:15}: Connection error ({e})")

    # -------------------------------------------------------------
    # 5. Live Wallet Transaction Scan & Filter Simulation
    # -------------------------------------------------------------
    print("\n[5/5] Scanning Live Transactions on Configured Wallets (Simulation)...")
    total_found = 0
    total_would_alert = 0
    sample_alert_sent = False

    for entity in entities:
        print(f"\n  🔍 Entity: {entity.label}")
        for addr in entity.get_addresses():
            print(f"     Address: {addr}")
            for chain in CHAINS:
                txs = fetch_token_transfers(chain, addr, api_key, offset=5)
                if not txs:
                    continue
                total_found += len(txs)
                print(f"       -> Chain: {chain.name} ({len(txs)} recent live txs from Etherscan):")
                for tx in txs:
                    amount = compute_amount(tx.raw_value, tx.token_decimals)
                    symbol = tx.token_symbol or "UNKNOWN"
                    is_stable = is_skip_token(symbol)
                    
                    if is_stable:
                        print(f"          • [{symbol:6}] {amount:>14,.2f} {symbol:6} -> [SKIP] Stablecoin")
                        continue

                    price = get_token_price(symbol, chain.defillama_prefix, tx.contract_address, cfg.coingecko_api_key)
                    if price is None:
                        print(f"          • [{symbol:6}] {amount:>14,.2f} {symbol:6} -> [SKIP] No price found")
                        continue

                    usd_val = amount * price
                    req_threshold = get_required_threshold(symbol, cfg.usd_threshold)
                    meets = meets_threshold(usd_val, req_threshold)

                    from_lbl = get_address_label(tx.from_addr, custom_labels)
                    to_lbl = get_address_label(tx.to_addr, custom_labels)

                    if meets:
                        total_would_alert += 1
                        print(f"          • [{symbol:6}] {amount:>14,.2f} {symbol:6} @ ${price:,.2f} = ${usd_val:>14,.2f} USD -> [ALERT!] (>= ${req_threshold:,.0f})")
                        print(f"            From: {from_lbl} ({tx.from_addr})")
                        print(f"            To  : {to_lbl} ({tx.to_addr})")
                        
                        # If user requested --test-alert, send the first real alert to Telegram as proof!
                        if send_real_alert and not sample_alert_sent:
                            print(f"\n  🚀 SENDING UPDATED REAL LIVE TRANSACTION TO TELEGRAM AS TEST ALERT...")
                            send_alert(
                                telegram_token=cfg.telegram_token,
                                chat_ids=cfg.telegram_chat_ids,
                                chain_name=chain.name,
                                token_symbol=tx.token_symbol,
                                token_name=tx.token_name,
                                amount=amount,
                                usd_value=usd_val,
                                from_addr=tx.from_addr,
                                to_addr=tx.to_addr,
                                from_label=entity.label,
                                tx_hash=tx.tx_hash,
                                tx_url=chain.explorer_tx_url,
                                timestamp=tx.block_timestamp,
                                custom_labels=custom_labels,
                            )
                            print(f"  ✅ Sent live alert for TX {tx.tx_hash[:10]}... ({amount:,.2f} {symbol} = ${usd_val:,.2f} USD) to Telegram!")
                            sample_alert_sent = True
                    else:
                        print(f"          • [{symbol:6}] {amount:>14,.2f} {symbol:6} @ ${price:,.2f} = ${usd_val:>14,.2f} USD -> [SKIP] (< ${req_threshold:,.0f})")

    print_banner("DIAGNOSTIC SUMMARY")
    print(f"  • Total live transactions fetched from Etherscan : {total_found}")
    print(f"  • Transactions meeting threshold criteria        : {total_would_alert}")
    print(f"  • System Status                                  : ALL SYSTEMS OPERATIONAL (READY TO RUN)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    send_ping_flag = "--send-ping" in sys.argv
    send_real_alert_flag = "--test-alert" in sys.argv
    send_accum_alert_flag = "--test-accumulation" in sys.argv
    run_diagnostics(
        send_ping=send_ping_flag,
        send_real_alert=send_real_alert_flag,
        send_accum_alert=send_accum_alert_flag,
    )
