# Wintermute Transaction Monitor 🤖

Monitors Wintermute (and any other entity you add) for large altcoin transactions across multiple chains. Sends Telegram alerts for transfers exceeding your configured USD threshold.

## Features

- **Multi-chain**: Ethereum, Arbitrum, BSC, Optimism, Polygon, Base
- **Smart filtering**: Skips stablecoins, ETH, BTC — only altcoins
- **Configurable**: Add any wallet via `wallets.json`, set threshold via `.env`
- **Deduplication**: Never sends the same alert twice (SQLite)
- **Telegram alerts**: Rich formatted notifications

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Add wallet addresses

Edit `wallets.json` — no code changes needed.

### 4. Run

```bash
python bot.py
```

### Tes
