# Token Accumulation Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement token accumulation detection (inflow tracking over a rolling time window) with milestone alerts and SQLite persistence for the Wintermute bot.

**Architecture:** Extend the bot with an `AccumulationStore` (backed by SQLite) to record all inflow transactions to monitored wallets, aggregate cumulative USD value and transaction counts within rolling time windows, evaluate milestone progressions ($500k, $1M, $1.5M, etc.), and dispatch Telegram milestone alerts.

**Tech Stack:** Python 3.11+, SQLite3, Requests, Pytest

**Spec:** `docs/superpowers/specs/2026-08-26-token-accumulation-detection-design.md`

## Global Constraints
- `ACCUMULATION_ENABLED`: boolean flag, default `True`
- `ACCUMULATION_USD_THRESHOLD`: float, default `500000.0`
- `ACCUMULATION_WINDOW_HOURS`: int, default `24`
- `ACCUMULATION_MIN_TX_COUNT`: int, default `2`
- Inflow direction only (`to_addr` is in monitored entity wallets)
- Anti-spam via milestone progression (`floor(total_usd / threshold) * threshold`)
- Auto-pruning for records older than `window_hours`

---

### Task 1: Configuration & Environment Variables

**Files:**
- Modify: `src/config.py`
- Modify: `.env.example`
- Modify: `tests/test_config.py`

**Interfaces:**
- Produces: `Config.accumulation_enabled`, `Config.accumulation_usd_threshold`, `Config.accumulation_window_hours`, `Config.accumulation_min_tx_count`

- [ ] **Step 1: Write failing test in `tests/test_config.py`**
- [ ] **Step 2: Run test to verify it fails (`pytest tests/test_config.py`)**
- [ ] **Step 3: Update `src/config.py` and `.env.example`**
- [ ] **Step 4: Run test to verify it passes (`pytest tests/test_config.py`)**
- [ ] **Step 5: Commit changes**

---

### Task 2: Accumulation SQLite Storage (`src/accumulation.py`)

**Files:**
- Create: `src/accumulation.py`
- Create: `tests/test_accumulation.py`

**Interfaces:**
- Produces: `AccumulationStore` class with `record_inflow`, `get_accumulation_stats`, `get_highest_milestone`, `set_highest_milestone`, `prune_old_transfers`

- [ ] **Step 1: Write unit tests in `tests/test_accumulation.py`**
- [ ] **Step 2: Run tests to verify failure (`pytest tests/test_accumulation.py`)**
- [ ] **Step 3: Implement `AccumulationStore` in `src/accumulation.py`**
- [ ] **Step 4: Run tests to verify pass (`pytest tests/test_accumulation.py`)**
- [ ] **Step 5: Commit changes**

---

### Task 3: Telegram Accumulation Notifier (`src/notifier.py`)

**Files:**
- Modify: `src/notifier.py`
- Modify: `tests/test_notifier.py` (or create if needed)

**Interfaces:**
- Produces: `send_accumulation_alert(telegram_token, chat_ids, chain_name, token_symbol, token_name, total_amount, total_usd, tx_count, milestone_tier, recipient_addr, entity_label, window_hours, timestamp)`

- [ ] **Step 1: Write test for `send_accumulation_alert`**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement `send_accumulation_alert` in `src/notifier.py`**
- [ ] **Step 4: Run test to verify pass**
- [ ] **Step 5: Commit changes**

---

### Task 4: Monitor Integration & Milestone Logic (`src/monitor.py`)

**Files:**
- Modify: `src/monitor.py`
- Modify: `bot.py`
- Modify: `tests/test_monitor.py`

**Interfaces:**
- Consumes: `AccumulationStore`, `send_accumulation_alert`, `Config`
- Produces: Inflow recording, milestone alert evaluation in `Monitor.poll_chain()`, and pruning in `Monitor.run_once()`

- [ ] **Step 1: Write integration tests in `tests/test_monitor.py`**
- [ ] **Step 2: Run tests to verify failure (`pytest tests/test_monitor.py`)**
- [ ] **Step 3: Implement accumulation flow in `src/monitor.py` & `bot.py`**
- [ ] **Step 4: Run full test suite (`pytest`)**
- [ ] **Step 5: Commit changes**

---

### Task 5: Diagnostics & Verification Tool (`test_bot.py`)

**Files:**
- Modify: `test_bot.py`

**Interfaces:**
- Produces: Visual diagnostics for accumulation configuration and optional `--test-accumulation` test flag.

- [ ] **Step 1: Update `test_bot.py` with accumulation diagnostics**
- [ ] **Step 2: Run `python test_bot.py` to verify output**
- [ ] **Step 3: Run full pytest suite**
- [ ] **Step 4: Commit changes**
