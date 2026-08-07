"""Backtesting engine for cryptocurrency trading strategies.

This module provides:
- BacktestConfig: Configuration for backtesting
- HistoricalDataLoader: Load historical market data
- BacktestExecutor: Run backtests on strategies
- PerformanceAnalyzer: Analyze strategy performance
- BacktestReport: Generate comprehensive reports
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional

import pandas as pd
import numpy as np


class BacktestMode(str, Enum):
    """Backtest execution mode."""

    STANDARD = "standard"  # Standard backtest
    WALK_FORWARD = "walk_forward"  # Walk-forward analysis
    MONTE_CARLO = "monte_carlo"  # Monte Carlo simulation


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""

    symbol: str = "BTCUSDT"
    start_date: datetime = field(default_factory=lambda: datetime.now() - timedelta(days=90))
    end_date: datetime = field(default_factory=datetime.now)
    initial_capital: float = 10000.0
    fee_pct: float = 0.001  # 0.1% per trade
    slippage_pct: float = 0.0005  # 0.05% slippage
    max_position_pct: float = 0.95  # Max 95% of capital
    mode: BacktestMode = BacktestMode.STANDARD
    # Strategy function: (df -> signals)
    strategy: Optional[Callable] = None


@dataclass
class BacktestTrade:
    """Single trade in backtest."""

    timestamp: datetime
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: float
    fee: float
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class BacktestStats:
    """Backtest statistics."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_holding_time: float = 0.0
    trade_days: int = 0


@dataclass
class BacktestResult:
    """Result of backtest run."""

    config: BacktestConfig
    stats: BacktestStats
    equity_curve: list[float] = field(default_factory=list)
    drawdown_curve: list[float] = field(default_factory=list)
    trades: list[BacktestTrade] = field(default_factory=list)
    daily_returns: list[float] = field(default_factory=list)
    positions: list[str] = field(default_factory=list)  # long/short/flat


class HistoricalDataLoader:
    """Loads historical market data for backtesting."""

    def __init__(self) -> None:
        """Initialize data loader."""
        self._cache: dict[str, pd.DataFrame] = {}

    def load_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """Load historical data.

        Args:
            symbol: Trading symbol.
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with OHLCV data.
        """
        # Check cache
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate mock data for backtesting
        df = self._generate_mock_data(symbol, start_date, end_date)
        self._cache[cache_key] = df
        return df

    def _generate_mock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """Generate mock OHLCV data.

        Args:
            symbol: Trading symbol.
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with OHLCV data.
        """
        # Base prices per symbol
        base_prices = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3200.0,
            "SOLUSDT": 140.0,
            "DOGEUSDT": 0.14,
        }
        base_price = base_prices.get(symbol, 100.0)

        # Generate dates
        dates = pd.date_range(start=start_date, end=end_date, freq="1h")

        # Generate random walk price data
        np.random.seed(42)
        returns = np.random.normal(0.0002, 0.02, len(dates))
        close_prices = base_price * (1 + returns).cumprod()

        # Generate OHLC from close
        data = []
        for i, (date, close) in enumerate(zip(dates, close_prices)):
            volatility = close * 0.01
            high = close + abs(np.random.normal(0, volatility))
            low = close - abs(np.random.normal(0, volatility))
            open_price = close + np.random.normal(0, volatility * 0.5)

            data.append({
                "timestamp": date,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": np.random.uniform(100, 1000),
            })

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def clear_cache(self) -> None:
        """Clear data cache."""
        self._cache.clear()


class PerformanceAnalyzer:
    """Analyzes backtest performance."""

    def __init__(self) -> None:
        """Initialize performance analyzer."""
        pass

    def analyze(self, result: BacktestResult) -> BacktestStats:
        """Analyze backtest results.

        Args:
            result: Backtest result.

        Returns:
            Statistics.
        """
        if not result.trades:
            return BacktestStats()

        # Basic stats
        total_trades = len(result.trades)
        winning = [t for t in result.trades if t.pnl > 0]
        losing = [t for t in result.trades if t.pnl < 0]

        total_pnl = sum(t.pnl for t in result.trades)
        total_pnl_pct = sum(t.pnl_pct for t in result.trades)

        win_rate = len(winning) / total_trades if total_trades > 0 else 0.0

        # Average win/loss
        avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0.0
        avg_loss = sum(t.pnl for t in losing) / len(losing) if losing else 0.0

        # Profit factor
        gross_profit = sum(t.pnl for t in winning) if winning else 0.0
        gross_loss = abs(sum(t.pnl for t in losing)) if losing else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Equity curve analysis
        equity = result.equity_curve
        if equity:
            # Calculate max drawdown
            peak = equity[0]
            max_dd = 0.0
            max_dd_pct = 0.0

            for value in equity:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd
                    max_dd_pct = (peak - value) / peak * 100 if peak > 0 else 0.0

            # Calculate Sharpe ratio
            returns = result.daily_returns
            if returns:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe = mean_return / std_return * np.sqrt(252) if std_return > 0 else 0.0

                # Sortino ratio (downside deviation)
                downside = [r for r in returns if r < 0]
                downside_std = np.std(downside) if downside else 0.0
                sortino = mean_return / downside_std * np.sqrt(252) if downside_std > 0 else 0.0

                # Calmar ratio (annual return / max drawdown)
                annual_return = mean_return * 252
                calmar = annual_return / max_dd if max_dd > 0 else 0.0
            else:
                sharpe = 0.0
                sortino = 0.0
                calmar = 0.0
        else:
            max_dd = 0.0
            max_dd_pct = 0.0
            sharpe = 0.0
            sortino = 0.0
            calmar = 0.0

        # Average holding time
        holding_times = []
        buy_times = [t.timestamp for t in result.trades if t.side == "buy"]
        for i, trade in enumerate(result.trades):
            if trade.side == "sell" and i > 0:
                # Find nearest buy
                for buy_time in reversed(buy_times):
                    if buy_time < trade.timestamp:
                        holding = (trade.timestamp - buy_time).total_seconds() / 3600
                        holding_times.append(holding)
                        break

        avg_holding = np.mean(holding_times) if holding_times else 0.0
        trade_days = len(set(t.timestamp.date() for t in result.trades))

        return BacktestStats(
            total_trades=total_trades,
            winning_trades=len(winning),
            losing_trades=len(losing),
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_holding_time=avg_holding,
            trade_days=trade_days,
        )

    def calculate_rolling_sharpe(
        self,
        returns: list[float],
        window: int = 30,
    ) -> list[float]:
        """Calculate rolling Sharpe ratio.

        Args:
            returns: List of returns.
            window: Rolling window size.

        Returns:
            List of rolling Sharpe ratios.
        """
        if len(returns) < window:
            return []

        rolling_sharpe = []
        for i in range(window, len(returns) + 1):
            window_returns = returns[i - window:i]
            mean_return = np.mean(window_returns)
            std_return = np.std(window_returns)
            sharpe = mean_return / std_return * np.sqrt(252) if std_return > 0 else 0.0
            rolling_sharpe.append(sharpe)

        return rolling_sharpe

    def calculate_rolling_max_dd(
        self,
        equity: list[float],
        window: int = 30,
    ) -> list[float]:
        """Calculate rolling maximum drawdown.

        Args:
            equity: Equity curve.
            window: Rolling window size.

        Returns:
            List of rolling max drawdowns.
        """
        if len(equity) < window:
            return []

        rolling_dd = []
        for i in range(window, len(equity) + 1):
            window_equity = equity[i - window:i]
            peak = max(window_equity)
            dd = (peak - window_equity[-1]) / peak if peak > 0 else 0.0
            rolling_dd.append(dd * 100)

        return rolling_dd


class BacktestExecutor:
    """Executes backtests on trading strategies."""

    def __init__(self) -> None:
        """Initialize backtest executor."""
        self.data_loader = HistoricalDataLoader()
        self.performance = PerformanceAnalyzer()

    def run(
        self,
        config: BacktestConfig,
    ) -> BacktestResult:
        """Run backtest.

        Args:
            config: Backtest configuration.

        Returns:
            Backtest result.
        """
        # Load data
        df = self.data_loader.load_data(
            config.symbol,
            config.start_date,
            config.end_date,
        )

        if df.empty:
            return BacktestResult(
                config=config,
                stats=BacktestStats(),
            )

        # Generate signals if no strategy
        if config.strategy is None:
            signals = self._default_strategy(df)
        else:
            signals = config.strategy(df)

        # Execute backtest
        equity = config.initial_capital
        equity_curve = [equity]
        trades: list[BacktestTrade] = []
        positions = []  # flat/long/short
        daily_returns = []

        position = 0.0  # 0 = flat, >0 = long, <0 = short
        entry_price = 0.0
        entry_time = None

        for i, (timestamp, row) in enumerate(df.iterrows()):
            current_price = row["close"]

            if i > 0:
                prev_equity = equity_curve[-1]
                daily_return = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
                daily_returns.append(daily_return)

            signal = signals[i] if i < len(signals) else 0

            if signal > 0.5 and position <= 0:  # Buy signal
                # Enter long
                max_qty = (equity * config.max_position_pct) / current_price
                qty = max_qty * 0.95

                fee = qty * current_price * config.fee_pct
                slippage = current_price * config.slippage_pct * qty

                position = qty
                entry_price = current_price + slippage
                entry_time = timestamp

                positions.append("long")

            elif signal < -0.5 and position > 0:  # Sell signal
                # Close long
                pnl = position * (current_price - entry_price)
                pnl_pct = (current_price - entry_price) / entry_price * 100

                fee = position * current_price * config.fee_pct
                slippage = current_price * config.slippage_pct * position

                net_pnl = pnl - fee - slippage

                trade = BacktestTrade(
                    timestamp=timestamp,
                    symbol=config.symbol,
                    side="sell",
                    quantity=position,
                    price=current_price,
                    fee=fee + slippage,
                    pnl=net_pnl,
                    pnl_pct=pnl_pct,
                )
                trades.append(trade)

                equity += net_pnl
                position = 0.0

                positions.append("flat")

            else:
                positions.append("long" if position > 0 else "flat")

            equity_curve.append(equity)

        # Calculate drawdown curve
        drawdown_curve = []
        peak = equity_curve[0] if equity_curve else 0

        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0.0
            drawdown_curve.append(dd * 100)

        # Analyze performance
        stats = self.performance.analyze(
            BacktestResult(
                config=config,
                stats=BacktestStats(),  # temporary
                equity_curve=equity_curve,
                drawdown_curve=drawdown_curve,
                trades=trades,
                daily_returns=daily_returns,
                positions=positions,
            )
        )

        result = BacktestResult(
            config=config,
            stats=stats,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            trades=trades,
            daily_returns=daily_returns,
            positions=positions,
        )

        return result

    def _default_strategy(self, df: pd.DataFrame) -> list[int]:
        """Default momentum strategy.

        Args:
            df: Price data.

        Returns:
            List of signals (-1, 0, 1).
        """
        # Simple moving average crossover
        signals = []
        sma_short = df["close"].rolling(10).mean()
        sma_long = df["close"].rolling(30).mean()

        for i in range(len(df)):
            if pd.isna(sma_short.iloc[i]) or pd.isna(sma_long.iloc[i]):
                signals.append(0)
            elif sma_short.iloc[i] > sma_long.iloc[i]:
                signals.append(1)
            elif sma_short.iloc[i] < sma_long.iloc[i]:
                signals.append(-1)
            else:
                signals.append(0)

        return signals

    def run_monte_carlo(
        self,
        config: BacktestConfig,
        num_simulations: int = 100,
    ) -> list[BacktestResult]:
        """Run Monte Carlo backtest simulation.

        Args:
            config: Backtest configuration.
            num_simulations: Number of simulations.

        Returns:
            List of backtest results.
        """
        results = []

        for _ in range(num_simulations):
            # Add noise to price data
            import copy
            config_copy = copy.copy(config)
            # Reset random seed for different simulation
            np.random.seed(None)

            result = self.run(config_copy)
            results.append(result)

        return results


class BacktestReport:
    """Generates backtest reports."""

    def __init__(self) -> None:
        """Initialize report generator."""
        self.executor = BacktestExecutor()

    def generate(self, result: BacktestResult) -> str:
        """Generate text report.

        Args:
            result: Backtest result.

        Returns:
            Report string.
        """
        stats = result.stats
        config = result.config

        report = f"""
=== Backtest Report ===
Symbol: {config.symbol}
Period: {config.start_date.date()} to {config.end_date.date()}
Initial Capital: ${config.initial_capital:,.2f}

--- Performance Metrics ---
Total Trades: {stats.total_trades}
Win Rate: {stats.win_rate * 100:.1f}%
Winning Trades: {stats.winning_trades}
Losing Trades: {stats.losing_trades}

Total P&L: ${stats.total_pnl:,.2f} ({stats.total_pnl_pct:.2f}%)
Profit Factor: {stats.profit_factor:.2f}

Avg Win: ${stats.avg_win:,.2f}
Avg Loss: ${stats.avg_loss:,.2f}

--- Risk Metrics ---
Max Drawdown: {stats.max_drawdown_pct:.2f}%
Sharpe Ratio: {stats.sharpe_ratio:.2f}
Sortino Ratio: {stats.sortino_ratio:.2f}
Calmar Ratio: {stats.calmar_ratio:.2f}

--- Trading Activity ---
Trade Days: {stats.trade_days}
Avg Holding Time: {stats.avg_holding_time:.1f} hours
"""
        return report

    def generate_html(self, result: BacktestResult) -> str:
        """Generate HTML report.

        Args:
            result: Backtest result.

        Returns:
            HTML report string.
        """
        stats = result.stats

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Backtest Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
    </style>
</head>
<body>
    <h1>Backtest Report</h1>
    <div>
        <div class="metric">Total Trades: {stats.total_trades}</div>
        <div class="metric">Win Rate: {stats.win_rate * 100:.1f}%</div>
    </div>
    <div>
        <div class="metric">Total P&L: ${stats.total_pnl:,.2f}</div>
        <div class="metric">Max Drawdown: {stats.max_drawdown_pct:.2f}%</div>
    </div>
    <div>
        <div class="metric">Sharpe Ratio: {stats.sharpe_ratio:.2f}</div>
        <div class="metric">Sortino Ratio: {stats.sortino_ratio:.2f}</div>
    </div>
</body>
</html>
"""
        return html


class BacktestEngine:
    """Main backtesting engine.

    Provides unified interface for running backtests.
    """

    def __init__(self) -> None:
        """Initialize backtest engine."""
        self.executor = BacktestExecutor()
        self.report = BacktestReport()

    def run_backtest(
        self,
        symbol: str = "BTCUSDT",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        initial_capital: float = 10000.0,
        strategy: Optional[Callable] = None,
    ) -> BacktestResult:
        """Run backtest.

        Args:
            symbol: Trading symbol.
            start_date: Start date.
            end_date: End date.
            initial_capital: Initial capital.
            strategy: Strategy function.

        Returns:
            Backtest result.
        """
        config = BacktestConfig(
            symbol=symbol,
            start_date=start_date or datetime.now() - timedelta(days=90),
            end_date=end_date or datetime.now(),
            initial_capital=initial_capital,
            strategy=strategy,
        )

        return self.executor.run(config)

    def get_performance_metrics(self, result: BacktestResult) -> dict:
        """Get performance metrics.

        Args:
            result: Backtest result.

        Returns:
            Dictionary of metrics.
        """
        stats = result.stats
        return {
            "total_trades": stats.total_trades,
            "win_rate": stats.win_rate,
            "total_pnl": stats.total_pnl,
            "total_pnl_pct": stats.total_pnl_pct,
            "max_drawdown": stats.max_drawdown,
            "max_drawdown_pct": stats.max_drawdown_pct,
            "sharpe_ratio": stats.sharpe_ratio,
            "sortino_ratio": stats.sortino_ratio,
            "calmar_ratio": stats.calmar_ratio,
            "profit_factor": stats.profit_factor,
            "avg_win": stats.avg_win,
            "avg_loss": stats.avg_loss,
            "avg_holding_time": stats.avg_holding_time,
        }

    def generate_report(self, result: BacktestResult) -> str:
        """Generate report.

        Args:
            result: Backtest result.

        Returns:
            Report string.
        """
        return self.report.generate(result)

    def generate_html_report(self, result: BacktestResult) -> str:
        """Generate HTML report.

        Args:
            result: Backtest result.

        Returns:
            HTML report string.
        """
        return self.report.generate_html(result)