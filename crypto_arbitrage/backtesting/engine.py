"""回测框架 - 基于历史数据验证策略表现

支持:
- 模拟历史价格序列
- 单策略和多策略回测
- 绩效指标计算（夏普比率、最大回撤、胜率等）
- 回测报告生成
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PriceBar:
    """价格数据条"""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TradeRecord:
    """交易记录"""
    timestamp: float
    strategy: str
    symbol: str
    side: str  # buy / sell / close
    price: float
    amount: float
    profit: float = 0.0
    profit_rate: float = 0.0
    commission: float = 0.0


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    start_time: float
    end_time: float
    initial_capital: float
    final_capital: float
    total_return: float  # 总收益率 %
    annualized_return: float  # 年化收益率 %
    max_drawdown: float  # 最大回撤 %
    sharpe_ratio: float  # 夏普比率
    sortino_ratio: float  # 索提诺比率
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float  # 盈亏比
    max_consecutive_losses: int
    trades: List[TradeRecord] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)


class BacktestEngine:
    """回测引擎"""

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,  # 0.1% 手续费
        slippage: float = 0.0005,  # 0.05% 滑点
    ):
        """初始化回测引擎

        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage

    def generate_price_data(
        self,
        base_price: float,
        bars: int,
        volatility: float = 0.02,
        drift: float = 0.0001,
        start_timestamp: Optional[float] = None,
    ) -> List[PriceBar]:
        """生成模拟价格数据（几何布朗运动）

        Args:
            base_price: 基准价格
            bars: 数据条数
            volatility: 年化波动率
            drift: 年化漂移率
            start_timestamp: 起始时间戳

        Returns:
            价格数据列表
        """
        if start_timestamp is None:
            start_timestamp = datetime.now().timestamp() - bars * 3600

        prices = [base_price]
        dt = 1 / (365 * 24)  # 每小时一个数据点

        import random
        random.seed(42)  # 可重现

        for _ in range(bars - 1):
            z = random.gauss(0, 1)
            prev = prices[-1]
            change = prev * (drift * dt + volatility * math.sqrt(dt) * z)
            prices.append(max(prev + change, prev * 0.5))  # 防止负价格

        data = []
        for i, close in enumerate(prices):
            spread = close * 0.001  # 买卖价差
            data.append(PriceBar(
                timestamp=start_timestamp + i * 3600,
                open=close * (1 + random.gauss(0, 0.001)),
                high=close * (1 + abs(random.gauss(0, volatility * math.sqrt(dt)))),
                low=close * (1 - abs(random.gauss(0, volatility * math.sqrt(dt)))),
                close=close,
                volume=random.uniform(100, 10000),
            ))

        return data

    def generate_correlated_pair(
        self,
        base_prices: List[PriceBar],
        correlation: float = 0.8,
        spread_mean: float = 0.0,
        spread_std: float = 0.005,
    ) -> List[PriceBar]:
        """生成与基准价格相关的价格数据（用于统计套利回测）

        Args:
            base_prices: 基准价格序列
            correlation: 相关系数 (0-1)
            spread_mean: 价差均值
            spread_std: 价差标准差

        Returns:
            相关价格序列
        """
        import random
        random.seed(123)

        data = []
        prev_price = base_prices[0].close

        for bar in base_prices:
            # 相关部分 + 随机部分
            base_return = (
                (bar.close - (data[-1].close if data else prev_price))
                / (data[-1].close if data else prev_price)
                if data and data[-1].close > 0 else 0
            )

            correlated_return = base_return * correlation
            noise = random.gauss(0, 1 - correlation) * 0.01
            spread = random.gauss(spread_mean, spread_std)

            if data:
                new_close = data[-1].close * (1 + correlated_return + noise) * (1 + spread)
            else:
                new_close = bar.close * (1 + spread)

            new_close = max(new_close, bar.close * 0.3)

            data.append(PriceBar(
                timestamp=bar.timestamp,
                open=new_close,
                high=new_close * 1.002,
                low=new_close * 0.998,
                close=new_close,
                volume=bar.volume * random.uniform(0.5, 1.5),
            ))

        return data

    def run_cross_exchange_backtest(
        self,
        prices_a: List[PriceBar],
        prices_b: List[PriceBar],
        min_spread: float = 0.003,
        position_size: float = 1000,
    ) -> BacktestResult:
        """运行跨交易所套利回测

        Args:
            prices_a: 交易所A价格数据
            prices_b: 交易所B价格数据
            min_spread: 最小价差阈值
            position_size: 每次交易金额

        Returns:
            回测结果
        """
        capital = self.initial_capital
        trades: List[TradeRecord] = []
        equity_curve: List[float] = [capital]

        for i in range(1, min(len(prices_a), len(prices_b))):
            price_a = prices_a[i]
            price_b = prices_b[i]

            buy_price = min(price_a.close, price_b.close)
            sell_price = max(price_a.close, price_b.close)
            spread = (sell_price - buy_price) / buy_price

            if spread >= min_spread:
                amount = position_size / buy_price
                commission = (buy_price * amount + sell_price * amount) * self.commission_rate
                slippage_cost = position_size * self.slippage
                profit = (sell_price - buy_price) * amount - commission - slippage_cost

                capital += profit

                trades.append(TradeRecord(
                    timestamp=price_a.timestamp,
                    strategy="cross_exchange",
                    symbol="BTC/USDT",
                    side="buy_sell",
                    price=buy_price,
                    amount=amount,
                    profit=profit,
                    profit_rate=(profit / position_size) * 100,
                    commission=commission,
                ))

            equity_curve.append(capital)

        return self._calculate_metrics(
            "cross_exchange",
            trades,
            equity_curve,
            prices_a[0].timestamp if prices_a else 0,
            prices_a[-1].timestamp if prices_a else 0,
        )

    def run_statistical_arbitrage_backtest(
        self,
        prices_a: List[PriceBar],
        prices_b: List[PriceBar],
        lookback: int = 100,
        z_open: float = 2.0,
        z_close: float = 0.5,
        position_size: float = 500,
    ) -> BacktestResult:
        """运行统计套利回测

        Args:
            prices_a: 资产A价格数据
            prices_b: 资产B价格数据
            lookback: 回溯期
            z_open: 开仓 Z-score 阈值
            z_close: 平仓 Z-score 阈值
            position_size: 每边交易金额

        Returns:
            回测结果
        """
        capital = self.initial_capital
        trades: List[TradeRecord] = []
        equity_curve: List[float] = [capital]

        # 计算价格比率
        ratios = []
        for i in range(min(len(prices_a), len(prices_b))):
            if prices_b[i].close > 0:
                ratios.append(prices_a[i].close / prices_b[i].close)

        in_position = False
        entry_price_a = 0.0
        entry_price_b = 0.0

        for i in range(lookback, len(ratios)):
            window = ratios[i - lookback:i]
            mean_r = sum(window) / len(window)
            std_r = math.sqrt(
                sum((r - mean_r) ** 2 for r in window) / (len(window) - 1)
            )

            if std_r == 0:
                equity_curve.append(capital)
                continue

            z = (ratios[i] - mean_r) / std_r

            if not in_position and abs(z) > z_open:
                # 开仓
                in_position = True
                entry_price_a = prices_a[i].close
                entry_price_b = prices_b[i].close

                # 做多低估的，做空高估的
                if z > 0:
                    # A 被高估 → 做空A，做多B
                    direction = "short_a_long_b"
                else:
                    direction = "long_a_short_b"

                commission = position_size * 2 * self.commission_rate
                capital -= commission

            elif in_position and abs(z) < z_close:
                # 平仓
                in_position = False
                exit_price_a = prices_a[i].close
                exit_price_b = prices_b[i].close

                if entry_price_a > 0 and entry_price_b > 0:
                    # 计算利润（配对交易）
                    pnl_a = (entry_price_a - exit_price_a) / entry_price_a * position_size
                    pnl_b = (exit_price_b - entry_price_b) / entry_price_b * position_size
                    profit = pnl_a + pnl_b

                    commission = position_size * 2 * self.commission_rate
                    net_profit = profit - commission
                    capital += net_profit

                    trades.append(TradeRecord(
                        timestamp=prices_a[i].timestamp,
                        strategy="statistical_arbitrage",
                        symbol="pair",
                        side="close",
                        price=exit_price_a,
                        amount=position_size / entry_price_a,
                        profit=net_profit,
                        profit_rate=(net_profit / (position_size * 2)) * 100,
                        commission=commission,
                    ))

            equity_curve.append(capital)

        # 如果还在持仓中，按最后价格平仓
        if in_position and prices_a and prices_b:
            capital += 0  # 简化处理，不计未实现盈亏

        return self._calculate_metrics(
            "statistical_arbitrage",
            trades,
            equity_curve,
            prices_a[0].timestamp if prices_a else 0,
            prices_a[-1].timestamp if prices_a else 0,
        )

    def _calculate_metrics(
        self,
        strategy_name: str,
        trades: List[TradeRecord],
        equity_curve: List[float],
        start_time: float,
        end_time: float,
    ) -> BacktestResult:
        """计算回测绩效指标"""
        final_capital = equity_curve[-1] if equity_curve else self.initial_capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100

        # 时间跨度（小时→年）
        hours = max((end_time - start_time) / 3600, 1)
        years = hours / (365 * 24)
        annualized_return = ((final_capital / self.initial_capital) ** (1 / max(years, 0.001)) - 1) * 100

        # 最大回撤
        max_drawdown = 0.0
        peak = self.initial_capital
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100
            if dd > max_drawdown:
                max_drawdown = dd

        # 交易统计
        winning = [t for t in trades if t.profit > 0]
        losing = [t for t in trades if t.profit <= 0]
        win_rate = (len(winning) / len(trades) * 100) if trades else 0

        avg_profit = sum(t.profit for t in winning) / len(winning) if winning else 0
        avg_loss = sum(t.profit for t in losing) / len(losing) if losing else 0

        total_loss = abs(sum(t.profit for t in losing))
        profit_factor = (
            abs(sum(t.profit for t in winning) / total_loss)
            if total_loss > 0 else float('inf')
        )

        # 夏普比率（简化）
        returns = []
        for i in range(1, len(equity_curve)):
            r = (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            returns.append(r)

        sharpe_ratio = 0.0
        if returns:
            avg_r = sum(returns) / len(returns)
            std_r = math.sqrt(sum((r - avg_r) ** 2 for r in returns) / len(returns))
            if std_r > 0:
                # 年化: 每小时一个点 → 年化因子 sqrt(365*24)
                sharpe_ratio = (avg_r / std_r) * math.sqrt(365 * 24)

        # 索提诺比率（只考虑下行波动率）
        sortino_ratio = 0.0
        if returns:
            downside = [r for r in returns if r < 0]
            if downside:
                downside_std = math.sqrt(sum(r ** 2 for r in downside) / len(downside))
                avg_r = sum(returns) / len(returns)
                if downside_std > 0:
                    sortino_ratio = (avg_r / downside_std) * math.sqrt(365 * 24)

        # 最大连续亏损
        max_consecutive = 0
        current_consecutive = 0
        for t in trades:
            if t.profit <= 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return BacktestResult(
            strategy_name=strategy_name,
            start_time=start_time,
            end_time=end_time,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_consecutive_losses=max_consecutive,
            trades=trades,
            equity_curve=equity_curve,
        )

    def generate_report(self, result: BacktestResult) -> str:
        """生成回测报告（Markdown 格式）

        Args:
            result: 回测结果

        Returns:
            Markdown 格式的报告
        """
        start_dt = datetime.fromtimestamp(result.start_time).strftime('%Y-%m-%d %H:%M')
        end_dt = datetime.fromtimestamp(result.end_time).strftime('%Y-%m-%d %H:%M')

        report = f"""# 回测报告: {result.strategy_name}

## 基本信息
- **回测区间**: {start_dt} ~ {end_dt}
- **初始资金**: ${result.initial_capital:,.2f}
- **最终资金**: ${result.final_capital:,.2f}

## 绩效指标
| 指标 | 值 |
|------|-----|
| 总收益率 | {result.total_return:.2f}% |
| 年化收益率 | {result.annualized_return:.2f}% |
| 最大回撤 | {result.max_drawdown:.2f}% |
| 夏普比率 | {result.sharpe_ratio:.2f} |
| 索提诺比率 | {result.sortino_ratio:.2f} |

## 交易统计
| 指标 | 值 |
|------|-----|
| 总交易数 | {result.total_trades} |
| 盈利交易 | {result.winning_trades} |
| 亏损交易 | {result.losing_trades} |
| 胜率 | {result.win_rate:.1f}% |
| 平均盈利 | ${result.avg_profit:.2f} |
| 平均亏损 | ${result.avg_loss:.2f} |
| 盈亏比 | {result.profit_factor:.2f} |
| 最大连续亏损 | {result.max_consecutive_losses} |

## 风险评估
- **风险等级**: {'低' if result.max_drawdown < 5 else '中' if result.max_drawdown < 10 else '高'}
- **建议**: {'适合实盘' if result.sharpe_ratio > 1 and result.win_rate > 50 else '需要优化'}
"""
        return report
