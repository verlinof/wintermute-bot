# Wintermute Transaction Monitor - System Architecture & Plan

## Overview
The Wintermute Transaction Monitor is a multi-chain bot that tracks specific wallet addresses (e.g., Wintermute) for large altcoin transactions. It identifies token transfers, filters out stablecoins and major coins (BTC, ETH), calculates the USD value using price oracles, and triggers a Telegram alert if the value exceeds a configurable threshold.

## Core Components

### 1. **Configuration (`src/config.py`, `.env`)**
- Loads environment variables (`.env`) for sensitive data and API keys (Telegram, CoinGecko, Block Explorers).
- Defines global settings like polling intervals and default USD thresholds.

### 2. **Wallet Management (`wallets.json`, `src/wallets.py`)**
- Tracks target entities.
- Stores arrays of addresses across multiple chains.
- Uses custom labeling so alerts can specify which entity made the transfer.

### 3. **Chain & Explorer Integration (`src/chains.py`, `src/explorer.py`)**
- Defines supported chains (Ethereum, Arbitrum, BSC, Optimism, Polygon, Base).
- Utilizes block explorer APIs (Etherscan-like) to fetch recent ERC-20 token transfers for the tracked addresses.
- Handles parsing of raw token decimals and standardizes transaction data.

### 4. **Filtering & Logic (`src/filters.py`)**
- Ignores high-volume stablecoins and native assets to reduce noise.
- Evaluates whether the transaction meets the minimum USD value threshold (base threshold for altcoins, elevated threshold for BTC/ETH).

### 5. **Price Fetching (`src/price.py`)**
- Connects to price oracles (CoinGecko / DefiLlama).
- Converts token amounts to current USD value in real-time.

### 6. **Deduplication Engine (`src/dedup.py`)**
- SQLite-based storage.
- Ensures the same transaction hash is never processed or alerted more than once.

### 7. **Notification Engine (`src/notifier.py`)**
- Formats rich text messages for Telegram.
- Includes contextual data: chain, token, amount, USD value, sender/receiver labels, and explorer links.

### 8. **Monitor & Scheduler (`src/monitor.py`, `bot.py`)**
- Orchestrates the components.
- Uses `schedule` to repeatedly poll chains at the configured interval.
- Emits structured logging.

## Execution Flow

1. **Initialization**: Load config, load wallets, initialize deduplication DB.
2. **Polling Loop**: Iterate through configured chains -> Iterate through entities.
3. **Fetch Data**: Retrieve recent token transfers via Explorer APIs.
4. **Processing Pipeline** (per transaction):
    - Has it been processed? (Check Dedup) -> Yes: Skip.
    - Is it a stablecoin? -> Yes: Skip.
    - Calculate Token Amount based on decimals.
    - Fetch USD Price.
    - Calculate total USD Value.
    - Does it meet the USD threshold? -> No: Skip.
5. **Alerting**: Send Telegram message & mark TX as processed in Dedup DB.
6. **Sleep/Wait**: Wait for next scheduled cycle.

## Future Plans & Enhancements
- Expand supported chains (e.g., Solana, Avalanche).
- Integrate DEX volume/liquidity checks.
- Add dynamic thresholding based on average daily volume.
- Implement more robust error handling for API rate limits.
