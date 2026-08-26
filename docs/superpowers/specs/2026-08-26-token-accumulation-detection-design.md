# Design Specification: Token Accumulation Detection & Milestone Alerts

## 1. Overview
The Wintermute Transaction Monitor currently tracks individual large token transfers exceeding a defined USD threshold. This feature enhances the bot to detect **cumulative inflow (accumulation)** of specific tokens across multiple transactions within a rolling time window (e.g., 24 hours), even if individual transactions are below the single-transaction threshold.

## 2. Requirements & Goals
- **Direction**: Inflow only (transfers where the recipient `to_addr` is one of the monitored wallet addresses).
- **Time Window**: Configurable rolling window in hours (default: 24 hours).
- **Threshold**: Configurable cumulative USD threshold per milestone step (default: $500,000 USD).
- **Transaction Count Gate**: Minimum number of inflow transactions required within the window to trigger an alert (default: 2 txs).
- **Milestone Anti-Spam Policy**: Alerts trigger when cumulative inflow reaches a new milestone tier (e.g., $500,000, $1,000,000, $1,500,000). Subsequent transfers that do not cross into a higher milestone tier do not produce duplicate alerts.
- **Resource Efficiency**: Use the existing SQLite store with automatic pruning for records outside the active window to ensure minimal memory and storage footprint.

## 3. Configuration & Environment Variables
The following parameters will be added to `.env.example`, `.env`, and parsed into `Config` in `src/config.py`:

| Variable | Type | Default | Description |
|---|---|---|---|
| `ACCUMULATION_ENABLED` | bool | `true` | Enable or disable accumulation detection |
| `ACCUMULATION_USD_THRESHOLD` | float | `500000.0` | USD threshold per milestone tier |
| `ACCUMULATION_WINDOW_HOURS` | int | `24` | Rolling accumulation time window in hours |
| `ACCUMULATION_MIN_TX_COUNT` | int | `2` | Minimum inflow transactions required to trigger |

## 4. Architecture & Data Model

### 4.1 SQLite Storage (`DedupStore` / `AccumulationStore`)
Extending SQLite storage (`data/dedup.db`) with two tables:

1. **`inflow_transfers`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `tx_hash TEXT UNIQUE`
   - `chain TEXT`
   - `entity_label TEXT`
   - `recipient_addr TEXT`
   - `token_symbol TEXT`
   - `token_name TEXT`
   - `amount REAL`
   - `usd_value REAL`
   - `timestamp INTEGER` (Unix epoch seconds)
   - *Index*: `idx_inflow_query ON inflow_transfers(token_symbol, entity_label, timestamp)`

2. **`accumulation_milestones`**:
   - `key TEXT PRIMARY KEY` (`<chain>:<entity_label>:<token_symbol>`)
   - `highest_milestone_usd REAL`
   - `last_alert_timestamp INTEGER`

### 4.2 Auto-Pruning
During each polling cycle or insert, records in `inflow_transfers` where `timestamp < now - (window_hours * 3600)` are pruned.

## 5. Accumulation Detection Logic

1. **Inflow Filter**:
   When scanning transfers for a monitored entity:
   - If `to_addr.lower()` matches a monitored wallet, record the transfer in `inflow_transfers` (if not already recorded).
2. **Aggregation**:
   - For the token & entity:
     `total_usd = SUM(usd_value)` for `timestamp >= (now - window_seconds)`
     `tx_count = COUNT(id)` in the window.
3. **Milestone Evaluation**:
   - Calculate current milestone tier:
     `current_tier = floor(total_usd / ACCUMULATION_USD_THRESHOLD) * ACCUMULATION_USD_THRESHOLD`
   - If `tx_count >= ACCUMULATION_MIN_TX_COUNT` AND `current_tier >= ACCUMULATION_USD_THRESHOLD` AND `current_tier > highest_alerted_milestone`:
     - Send Telegram Accumulation Alert.
     - Update `highest_milestone_usd = current_tier`.

## 6. Telegram Alert Format
Dedicated accumulation message template in `src/notifier.py`:
- Header: 📈 *ACCUMULATION DETECTED!* (Milestone Alert)
- Entity, Chain, Token, Milestone Tier, Total Inflow amount & USD, TX Count, Recipient, Window, Timestamp.

## 7. Testing & Verification
- Unit tests covering:
  - Inflow recording and deduplication.
  - Aggregation within rolling window vs outside rolling window.
  - Milestone progression ($1M alert -> $1.5M no alert -> $2M alert).
  - Pruning of expired transactions.
  - Multi-recipient Telegram alert dispatching.
