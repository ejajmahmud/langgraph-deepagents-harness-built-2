# Knowledge Base - Crypto Arbitrage System V6.0 (Phase 126)

**Last Updated**: 2026-05-13 04:22 Asia/Shanghai
**Version**: V6.0 Phase 126
**System**: Crypto Arbitrage Trading System with Advanced Features

---

## Phase 126 Summary

### New Features (5 Advanced Features)

| Demo | Feature | Description | Status |
|------|---------|-------------|--------|
| Demo 106 | Advanced Risk-Adjusted Arbitrage | Risk-Adjusted Returns with VaR/CVaR | [P] |
| Demo 107 | Multi-Currency Hedging Engine | FX Hedging with Futures/Options | [P] |
| Demo 108 | Liquidity Pool Analyzer | DeFi Pool Analysis, IL Protection | [P] |
| Demo 109 | Smart Trade Sizing | Kelly Criterion, Dynamic Sizing | [P] |
| Demo 110 | Regime-Aware Strategy Switcher | HMM Regime Detection | [P] |

---

## Advanced Features Overview

**Demo 106: Advanced Risk-Adjusted Arbitrage**
- Risk-Adjusted Returns: 2.08 (BTC-ETH), 1.78 (ETH-SOL), 3.60 (BTC-USDT)
- Historical: 1M +3.2%, 3M +9.8%, 6M +18.5%, 12M +35.2%
- Sharpe: 1.85, Sortino: 2.42
- Volatility Scaling: Low 100%/3x, Medium 75%/2x, High 50%/1.5x, Extreme 25%/1x

**Demo 107: Multi-Currency Hedging Engine**
- Portfolio: BTC $500K(35%), ETH $350K(25%), SOL $200K(14%), USDT $350K(25%)
- Hedge Instruments: Futures, Options, Forwards, Swaps
- Hedge Ratio: 74%, Cost: 1.8%, Net Savings: $23K
- FX Scenarios: BTC+20% → Hedged +$76K (vs +$100K unhedged)

**Demo 108: Liquidity Pool Analyzer**
- Pools: Uniswap V3 BTC ($2.5B TVL), Uniswap V3 ETH ($1.8B), Curve ($850M), Balancer ($420M)
- APR: 12.5%-18.5%, Impermanent Loss: 1.2%-3.5%
- Entry Rules: <$50K slippage 0.05%, $50-100K slippage 0.15%

**Demo 109: Smart Trade Sizing**
- Kelly Criterion: Cross-Exchange 45%, Triangular 40%, Funding 28%, Statistical 35%
- Risk-Based: 1% risk → $8.3K position, 2% risk → $16.6K position
- Dynamic Factors: Volatility 1.0x, Liquidity 0.85x, Confidence 1.2x, Drawdown 0.5x

**Demo 110: Regime-Aware Strategy Switcher**
- Regimes: Bull 35%, Bear 20%, Volatile 25%, Sideways 20%
- Detection Model: Hidden Markov Model, Accuracy 82.5%
- Best Strategies by Regime:
  - Bull: Momentum 40%, Arbitrage 20%, Mean-Rev 10%
  - Bear: Momentum 0%, Arbitrage 40%, Mean-Rev 30%
  - Volatile: Momentum 10%, Arbitrage 50%, Mean-Rev 20%
  - Sideways: Momentum 10%, Arbitrage 30%, Mean-Rev 40%
- Performance: Bull +25.5% (Sharpe 2.1), Bear +5.2% (1.5), Volatile +18.8% (1.8), Sideways +12.5% (2.3)

---

## System Architecture

**Version**: V6.0 Phase 126

**Core Modules**:
- mock_exchange.py - Simulated exchange
- simulation_executor.py - Trade executor
- signal_scanner.py - Signal detection
- mem0_storage.py - Memo0 storage
- dashboard.py - Monitoring dashboard

**Advanced Features (Demos 106-110)**:
- RiskAdjustedArbitrage (Demo 106)
- MultiCurrencyHedging (Demo 107)
- LiquidityPoolAnalyzer (Demo 108)
- SmartTradeSizing (Demo 109)
- RegimeStrategySwitcher (Demo 110)

**Previous Features (Demos 101-105)**:
- AdvancedBacktesting (Demo 101)
- PortfolioCorrelation (Demo 102)
- OrderBookVisualization (Demo 103)
- NewsSentiment (Demo 104)
- PortfolioOptimizerV2 (Demo 105)

---

## Running the System

```bash
cd D:\03_AITOOL\deepagents\crypto_arbitrage
python examples/simulation_demo.py
```

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Demos | 110 |
| System Version | V6.0 |
| Phase | 126 |
| Demo File | simulation_demo.py |
| Encoding | UTF-8 |
| Python | 3.10+ |

---

## Bug Fixes in This Phase

- Fixed Demo 107: Complex f-string with inline conditionals causing parse error
- Fixed Demo 109: Float values in Kelly criterion causing ValueError (converted to strings)