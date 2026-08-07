# DeepAgents Crypto Trading System

A low-risk cryptocurrency arbitrage trading system built on the Deep Agents framework.

## Features

- **Market Analysis Engine** - Real-time price monitoring across multiple exchanges
- **Arbitrage Detection** - Triangular, cross-exchange, and futures-spot arbitrage
- **Risk Management** - Position sizing, stop-loss, and exposure controls
- **Memo0 Integration** - Persistent storage and knowledge base management
- **Multi-Exchange Support** - Binance, Coinbase, Bybit, OKX, Kraken

## Architecture

```
crypto_trading/
├── core/                  # Core trading engine
│   ├── market_analyzer.py  # Market data analysis
│   ├── arbitrage_engine.py # Arbitrage detection
│   └── risk_manager.py   # Risk controls
├── strategies/           # Trading strategies
│   ├── triangular.py     # Triangular arbitrage
│   ├── cross_exchange.py # Cross-exchange arbitrage
│   └── futures_spot.py  # Futures-spot arbitrage
├── storage/              # Storage layer
│   └── memo_client.py   # Memo0 storage client
├── types/                # Type definitions
│   └── __init__.py
└── __init__.py
```

## Installation

```bash
cd libs/crypto_trading
uv sync
```

## Usage

```python
from deepagents_crypto_trading import CryptoTradingSystem

system = CryptoTradingSystem()
system.initialize()
```

## License

MIT