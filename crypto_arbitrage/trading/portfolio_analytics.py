"""Portfolio Analytics - V21.0 高级投资组合分析模块

提供投资组合级别的性能分析、风险指标和盈利追踪。

核心功能：
1. VaR (Value at Risk) 计算 - 风险价值评估
2. 最大回撤追踪 - Drawdown tracking
3. 夏普比率计算 - Performance metrics
4. 滚动ROI计算 - Rolling returns
5. 盈利统计 - PnL tracking
6. 相关性分析 - Correlation analysis

创建时间：2026-05-06 03:55
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import math

logger = logging.getLogger(__name__)


class PerformanceMetricType(Enum):
    """性能指标类型"""
    SHARPE = "sharpe_ratio"
    SORTINO = "sortino_ratio"
    CALMAR = "calmar_ratio"
    max_drawdown = "max_drawdown"
    VAR = "var"
    CVAR = "cvar"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"


@dataclass
class PortfolioMetrics:
    """投资组合指标"""
    total_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0

    # VaR metrics
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0

    # Timing
    timestamp: float = field(default_factory=time.time)


@dataclass
class DrawdownPeriod:
    """回撤周期"""
    peak_value: float
    trough_value: float
    peak_time: float
    trough_time: float
    recovery_time: Optional[float] = None

    @property
    def max_drawdown_pct(self) -> float:
        """最大回撤百分比"""
        if self.peak_value <= 0:
            return 0.0
        return (self.peak_value - self.trough_value) / self.peak_value * 100

    @property
    def is_recovered(self) -> bool:
        """是否已恢复"""
        return self.recovery_time is not None


class PortfolioAnalytics:
    """投资组合分析器

    高级投资组合性能分析和风险评估。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化投资组合分析器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 配置
        self.risk_free_rate = self.config.get('risk_free_rate', 0.02)  # 年化无风险利率
        self.trading_periods_per_year = self.config.get('trading_periods_per_year', 252 * 24)  # 假设每小时交易

        # 数据存储
        self._pnl_history: deque = deque(maxlen=self.config.get('max_history_size', 10000))
        self._equity_curve: deque = deque(maxlen=self.config.get('max_history_size', 10000))
        self._drawdown_periods: List[DrawdownPeriod] = []

        # 统计
        self._peak_equity = 0.0
        self._peak_time = 0.0

        # 缓存
        self._cached_metrics: Optional[PortfolioMetrics] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = self.config.get('cache_ttl', 60)  # 60秒缓存

    # ---------------------- 数据输入 ----------------------

    def record_trade(self, pnl: float, timestamp: Optional[float] = None) -> None:
        """记录交易

        Args:
            pnl: 盈亏金额
            timestamp: 时间戳（默认当前时间）
        """
        ts = timestamp or time.time()
        self._pnl_history.append({'pnl': pnl, 'timestamp': ts})
        self._update_equity_curve(pnl, ts)

    def record_equity(self, equity: float, timestamp: Optional[float] = None) -> None:
        """记录权益

        Args:
            equity: 当前权益
            timestamp: 时间戳（默认当前时间）
        """
        ts = timestamp or time.time()
        self._equity_curve.append({'equity': equity, 'timestamp': ts})
        self._update_drawdown(equity, ts)

    def _update_equity_curve(self, pnl: float, timestamp: float) -> None:
        """更新权益曲线"""
        if not self._equity_curve:
            # 第一笔交易
            initial_equity = self.config.get('initial_equity', 10000.0)
            self._equity_curve.append({
                'equity': initial_equity + pnl,
                'timestamp': timestamp
            })
            self._peak_equity = initial_equity + pnl
            self._peak_time = timestamp
        else:
            # 累加权益
            last_equity = self._equity_curve[-1]['equity']
            new_equity = last_equity + pnl
            self._equity_curve.append({'equity': new_equity, 'timestamp': timestamp})

    def _update_drawdown(self, equity: float, timestamp: float) -> None:
        """更新回撤追踪"""
        # 检查是否新高
        if equity > self._peak_equity:
            # 恢复或新高
            if self._drawdown_periods and not self._drawdown_periods[-1].is_recovered:
                self._drawdown_periods[-1].recovery_time = timestamp

            self._peak_equity = equity
            self._peak_time = timestamp
        else:
            # 检查是否在新回撤中
            if not self._drawdown_periods or self._drawdown_periods[-1].is_recovered:
                # 新回撤周期
                self._drawdown_periods.append(DrawdownPeriod(
                    peak_value=self._peak_equity,
                    trough_value=equity,
                    peak_time=self._peak_time,
                    trough_time=timestamp
                ))
            else:
                # 更新当前回撤
                self._drawdown_periods[-1].trough_value = equity
                self._drawdown_periods[-1].trough_time = timestamp

    # ---------------------- 核心指标计算 ----------------------

    def calculate_sharpe_ratio(
        self,
        periods: Optional[int] = None,
        annualize: bool = True
    ) -> float:
        """计算夏普比率

        Args:
            periods: 计算期数（默认全部）
            annualize: 是否年化

        Returns:
            夏普比率
        """
        history = self._get_pnl_history(periods)
        if len(history) < 2:
            return 0.0

        returns = [h['pnl'] for h in history]
        avg_return = sum(returns) / len(returns)
        std_return = self._calculate_std(returns)

        if std_return == 0:
            return 0.0

        sharpe = avg_return / std_return

        if annualize:
            # 年化
            periods_per_year = self.trading_periods_per_year
            sharpe = sharpe * math.sqrt(periods_per_year)

        return sharpe

    def calculate_sortino_ratio(
        self,
        periods: Optional[int] = None,
        annualize: bool = True,
        target_return: float = 0.0
    ) -> float:
        """计算索提诺比率

        只考虑下行波动。

        Args:
            periods: 计算期数
            annualize: 是否年化
            target_return: 目标收益

        Returns:
            索提诺比率
        """
        history = self._get_pnl_history(periods)
        if len(history) < 2:
            return 0.0

        returns = [h['pnl'] for h in history]
        avg_return = sum(returns) / len(returns)

        # 下行偏差
        downside_returns = [r - target_return for r in returns if r < target_return]
        if not downside_returns:
            return 0.0

        downside_std = self._calculate_std(downside_returns)
        if downside_std == 0:
            return 0.0

        sortino = avg_return / downside_std

        if annualize:
            sortino = sortino * math.sqrt(self.trading_periods_per_year)

        return sortino

    def calculate_calmar_ratio(self, periods: Optional[int] = None) -> float:
        """计算卡尔玛比率

        Args:
            periods: 计算期数

        Returns:
            卡尔玛比率
        """
        history = self._get_pnl_history(periods)
        if len(history) < 2:
            return 0.0

        # 总收益
        total_return = sum(h['pnl'] for h in history)

        # 最大回撤
        max_dd = self.calculate_max_drawdown(periods)

        if max_dd == 0:
            return 0.0

        return total_return / max_dd

    def calculate_var(
        self,
        confidence: float = 0.95,
        periods: Optional[int] = None
    ) -> float:
        """计算VaR (Value at Risk)

        Args:
            confidence: 置信度（0.95 = 95%）
            periods: 计算期数

        Returns:
            VaR值
        """
        history = self._get_pnl_history(periods)
        if len(history) < 2:
            return 0.0

        returns = sorted([h['pnl'] for h in history])
        index = int((1 - confidence) * len(returns))
        index = min(index, len(returns) - 1)

        # 返回正值（损失为负）
        return abs(returns[index])

    def calculate_cvar(
        self,
        confidence: float = 0.95,
        periods: Optional[int] = None
    ) -> float:
        """计算CVaR (Conditional VaR)

        也称为Expected Shortfall。

        Args:
            confidence: 置信度
            periods: 计算期数

        Returns:
            CVaR值
        """
        history = self._get_pnl_history(periods)
        if len(history) < 2:
            return 0.0

        returns = [h['pnl'] for h in history]
        threshold = self.calculate_var(confidence, None)

        # 极端损失的平均值
        extreme_losses = [r for r in returns if r <= -threshold]
        if not extreme_losses:
            return threshold

        return abs(sum(extreme_losses) / len(extreme_losses))

    def calculate_max_drawdown(self, periods: Optional[int] = None) -> float:
        """计算最大回撤

        Args:
            periods: 计算期数

        Returns:
            最大回撤金额
        """
        curve = self._get_equity_history(periods)
        if not curve:
            return 0.0

        peak = curve[0]['equity']
        max_dd = 0.0

        for point in curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def calculate_current_drawdown(self) -> float:
        """计算当前回撤

        Returns:
            当前回撤百分比
        """
        if not self._equity_curve:
            return 0.0

        current_equity = self._equity_curve[-1]['equity']
        if self._peak_equity <= 0:
            return 0.0

        return (self._peak_equity - current_equity) / self._peak_equity * 100

    # ---------------------- 统计计算 ----------------------

    def calculate_win_rate(self, periods: Optional[int] = None) -> float:
        """计算胜率

        Args:
            periods: 计算期数

        Returns:
            胜率 (0-1)
        """
        history = self._get_pnl_history(periods)
        if not history:
            return 0.0

        wins = sum(1 for h in history if h['pnl'] > 0)
        return wins / len(history)

    def calculate_profit_factor(self, periods: Optional[int] = None) -> float:
        """计算盈利因子

        Args:
            periods: 计算期数

        Returns:
            盈利因子
        """
        history = self._get_pnl_history(periods)
        if not history:
            return 0.0

        gross_profit = sum(h['pnl'] for h in history if h['pnl'] > 0)
        gross_loss = abs(sum(h['pnl'] for h in history if h['pnl'] < 0))

        if gross_loss == 0:
            return gross_profit if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    def calculate_average_win(self, periods: Optional[int] = None) -> float:
        """计算平均盈利

        Args:
            periods: 计算期数

        Returns:
            平均盈利
        """
        history = self._get_pnl_history(periods)
        wins = [h['pnl'] for h in history if h['pnl'] > 0]

        if not wins:
            return 0.0

        return sum(wins) / len(wins)

    def calculate_average_loss(self, periods: Optional[int] = None) -> float:
        """计算平均亏损

        Args:
            periods: 计算期数

        Returns:
            平均亏损（负值）
        """
        history = self._get_pnl_history(periods)
        losses = [h['pnl'] for h in history if h['pnl'] < 0]

        if not losses:
            return 0.0

        return sum(losses) / len(losses)

    def calculate_expectancy(self, periods: Optional[int] = None) -> float:
        """计算交易期望值

        Args:
            periods: 计算期数

        Returns:
            期望盈亏
        """
        win_rate = self.calculate_win_rate(periods)
        avg_win = self.calculate_average_win(periods)
        avg_loss = abs(self.calculate_average_loss(periods))

        return win_rate * avg_win - (1 - win_rate) * avg_loss

    # ---------------------- 综合指标 ----------------------

    def get_metrics(self, force_refresh: bool = False) -> PortfolioMetrics:
        """获取完整投资组合指标

        Args:
            force_refresh: 强制刷新缓存

        Returns:
            投资组合指标
        """
        now = time.time()

        # 检查缓存
        if not force_refresh and self._cached_metrics:
            if now - self._cache_timestamp < self._cache_ttl:
                return self._cached_metrics

        # 计算所有指标
        pnl_history = self._get_pnl_history(None)
        total_pnl = sum(h['pnl'] for h in pnl_history)
        winning_trades = sum(1 for h in pnl_history if h['pnl'] > 0)
        losing_trades = sum(1 for h in pnl_history if h['pnl'] < 0)

        metrics = PortfolioMetrics(
            total_pnl=total_pnl,
            total_trades=len(pnl_history),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=self.calculate_win_rate(None),
            avg_win=self.calculate_average_win(None),
            avg_loss=self.calculate_average_loss(None),
            profit_factor=self.calculate_profit_factor(None),

            # Risk metrics
            sharpe_ratio=self.calculate_sharpe_ratio(None, True),
            sortino_ratio=self.calculate_sortino_ratio(None, True),
            calmar_ratio=self.calculate_calmar_ratio(None),
            max_drawdown=self.calculate_max_drawdown(None),
            current_drawdown=self.calculate_current_drawdown(),

            # VaR metrics
            var_95=self.calculate_var(0.95, None),
            var_99=self.calculate_var(0.99, None),
            cvar_95=self.calculate_cvar(0.95, None),

            timestamp=now
        )

        # 缓存
        self._cached_metrics = metrics
        self._cache_timestamp = now

        return metrics

    def get_drawdown_periods(self) -> List[DrawdownPeriod]:
        """获取回撤周期列表

        Returns:
            回撤周期列表
        """
        return self._drawdown_periods.copy()

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """获取权益曲线

        Returns:
            权益曲线数据
        """
        return list(self._equity_curve)

    # ---------------------- 辅助方法 ----------------------

    def _get_pnl_history(self, periods: Optional[int]) -> List[Dict[str, Any]]:
        """获取盈亏历史

        Args:
            periods: 期数限制

        Returns:
            盈亏历史
        """
        history = list(self._pnl_history)
        if periods and periods < len(history):
            history = history[-periods:]
        return history

    def _get_equity_history(self, periods: Optional[int]) -> List[Dict[str, Any]]:
        """获取权益历史

        Args:
            periods: 期数限制

        Returns:
            权益历史
        """
        history = list(self._equity_curve)
        if periods and periods < len(history):
            history = history[-periods:]
        return history

    @staticmethod
    def _calculate_std(values: List[float]) -> float:
        """计算标准差

        Args:
            values: 值列表

        Returns:
            标准差
        """
        if not values:
            return 0.0

        n = len(values)
        if n < 2:
            return 0.0

        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)

        return math.sqrt(variance)

    # ---------------------- 统计属性 ----------------------

    @property
    def total_trades(self) -> int:
        """总交易数"""
        return len(self._pnl_history)

    @property
    def peak_equity(self) -> float:
        """历史最高权益"""
        return self._peak_equity

    @property
    def current_equity(self) -> float:
        """当前权益"""
        if not self._equity_curve:
            return self.config.get('initial_equity', 10000.0)
        return self._equity_curve[-1]['equity']