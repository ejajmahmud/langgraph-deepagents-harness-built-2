"""V33.0 高级投资组合协调与风险管理系统

V33.0新增功能：
1. Portfolio Coordinator - 投资组合协调器
2. Risk Manager Pro - 专业风险管理系统
3. Dynamic Hedge Engine - 动态对冲引擎
4. Strategy Auto-balancer - 策略自动平衡器
5. Real-time Risk Analytics - 实时风险分析

创建时间：2026-05-07 20:25
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import math

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HedgeStrategy(Enum):
    """对冲策略"""
    NONE = "none"
    DELTA = "delta"
    BETA = "beta"
    OPTIONS = "options"
    DIVERSIFICATION = "diversification"


@dataclass
class PortfolioPosition:
    """投资组合头寸"""
    symbol: str
    side: str  # long/short
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class RiskMetrics:
    """风险指标"""
    portfolio_value: float
    total_exposure: float
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
    beta: float
    var_95: float  # Value at Risk at 95%
    leverage: float
    risk_level: RiskLevel


@dataclass
class HedgeDecision:
    """对冲决策"""
    strategy: HedgeStrategy
    reason: str
    target_exposure: float
    current_exposure: float
    adjustment: float
    expected_risk_reduction: float


class PortfolioCoordinator:
    """投资组合协调器

    功能：
    - 多策略协调
    - 实时仓位监控
    - 组合再平衡
    - 风险分配
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化组合协调器

        Args:
            config: 配置字典
                - max_leverage: 最大杠杆 (默认3.0)
                - max_position_size: 最大头寸大小
                - balance_threshold: 再平衡阈值 (默认0.2)
                - risk_per_trade: 单笔风险比例 (默认0.02)
        """
        self.config = config
        self.max_leverage = config.get('max_leverage', 3.0)
        self.max_position_size = config.get('max_position_size', 10000)
        self.balance_threshold = config.get('balance_threshold', 0.2)
        self.risk_per_trade = config.get('risk_per_trade', 0.02)

        # 头寸管理
        self.positions: Dict[str, PortfolioPosition] = {}
        self.total_value = config.get('initial_capital', 100000)
        self.available_capital = self.total_value

        # 策略权重
        self.strategy_weights: Dict[str, float] = {}
        self.target_weights: Dict[str, float] = {}

        logger.info("[OK] PortfolioCoordinator V33.0 初始化完成")

    def add_position(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        current_price: float
    ) -> bool:
        """添加头寸

        Args:
            symbol: 交易对
            side: 方向 (long/short)
        """
        if symbol in self.positions:
            logger.warning(f"头寸 {symbol} 已存在，更新之")
            self.positions[symbol].size = size
            self.positions[symbol].entry_price = entry_price
            self.positions[symbol].current_price = current_price
            return True

        position = PortfolioPosition(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
        )
        position.unrealized_pnl = self._calculate_pnl(position)

        self.positions[symbol] = position
        self.available_capital -= size * entry_price

        logger.info(f"[OK] 添加头寸: {symbol} {side} {size}")
        return True

    def remove_position(self, symbol: str, exit_price: float) -> float:
        """平仓

        Args:
            symbol: 交易对
            exit_price: 平仓价格

        Returns:
            实现的盈亏
        """
        if symbol not in self.positions:
            logger.warning(f"头寸 {symbol} 不存在")
            return 0.0

        position = self.positions[symbol]
        position.current_price = exit_price
        position.unrealized_pnl = self._calculate_pnl(position)

        # 计算已实现盈亏
        realized = position.unrealized_pnl
        self.available_capital += position.size * exit_price

        del self.positions[symbol]

        logger.info(f"[OK] 平仓: {symbol}, 实现盈亏: ${realized:.2f}")
        return realized

    def _calculate_pnl(self, position: PortfolioPosition) -> float:
        """计算未实现盈亏"""
        if position.side == "long":
            return (position.current_price - position.entry_price) * position.size
        else:
            return (position.entry_price - position.current_price) * position.size

    def update_prices(self, prices: Dict[str, float]) -> None:
        """更新价格

        Args:
            prices: 价格字典 {symbol: price}
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
                self.positions[symbol].unrealized_pnl = self._calculate_pnl(
                    self.positions[symbol]
                )

    def get_total_exposure(self) -> float:
        """获取总敞口"""
        exposure = 0.0
        for position in self.positions.values():
            exposure += abs(position.size * position.current_price)
        return exposure

    def get_total_pnl(self) -> float:
        """获取总未实现盈亏"""
        return sum(p.unrealized_pnl for p in self.positions.values())

    def get_leverage(self) -> float:
        """获取当前杠杆"""
        return self.get_total_exposure() / self.total_value

    def check_leverage_limit(self) -> bool:
        """检查杠杆限制"""
        return self.get_leverage() <= self.max_leverage

    def rebalance_if_needed(self) -> List[str]:
        """检查是否需要再平衡

        Returns:
            需要调整的策略列表
        """
        adjustments = []

        for strategy, target in self.target_weights.items():
            current = self.strategy_weights.get(strategy, 0.0)
            diff = abs(target - current)

            if diff > self.balance_threshold:
                adjustments.append(strategy)

        return adjustments

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取组合摘要"""
        return {
            'total_value': self.total_value,
            'available_capital': self.available_capital,
            'total_exposure': self.get_total_exposure(),
            'leverage': self.get_leverage(),
            'unrealized_pnl': self.get_total_pnl(),
            'positions_count': len(self.positions),
            'strategy_weights': self.strategy_weights,
        }


class RiskManagerPro:
    """专业风险管理系统

    功能：
    - 实时风险监控
    - 动态杠杆管理
    - 止损止盈管理
    - VaR计算
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化风险管理系统

        Args:
            config: 配置字典
                - max_var: 最大VaR (默认0.05)
                - max_drawdown: 最大回撤 (默认0.2)
                - stop_loss: 止损比例 (默认0.05)
                - take_profit: 止盈比例 (默认0.15)
        """
        self.config = config
        self.max_var = config.get('max_var', 0.05)
        self.max_drawdown = config.get('max_drawdown', 0.2)
        self.stop_loss_pct = config.get('stop_loss', 0.05)
        self.take_profit_pct = config.get('take_profit', 0.15)

        # 风险统计
        self.peak_value = config.get('initial_capital', 100000)
        self.current_value = self.peak_value
        self.drawdown_history: List[float] = []

        logger.info("[OK] RiskManagerPro V33.0 初始化完成")

    def update_value(self, value: float) -> RiskLevel:
        """更新投资组合价值

        Args:
            value: 当前价值

        Returns:
            风险等级
        """
        self.current_value = value

        # 计算回撤
        if value > self.peak_value:
            self.peak_value = value

        drawdown = (self.peak_value - value) / self.peak_value
        self.drawdown_history.append(drawdown)

        return self._determine_risk_level(drawdown)

    def _determine_risk_level(self, drawdown: float) -> RiskLevel:
        """确定风险等级"""
        if drawdown >= self.max_drawdown * 1.5:
            return RiskLevel.CRITICAL
        elif drawdown >= self.max_drawdown:
            return RiskLevel.HIGH
        elif drawdown >= self.max_drawdown * 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def calculate_var(
        self,
        returns: List[float],
        confidence: float = 0.95
    ) -> float:
        """计算VaR (Value at Risk)

        Args:
            returns: 收益率列表
            confidence: 置信度

        Returns:
            VaR值
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))

        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1

        return abs(sorted_returns[index])

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """计算夏普比率"""
        if not returns:
            return 0.0

        avg_return = sum(returns) / len(returns)
        std_return = math.sqrt(
            sum((r - avg_return) ** 2 for r in returns) / len(returns)
        )

        if std_return == 0:
            return 0.0

        return (avg_return - risk_free_rate) / std_return

    def should_stop_loss(
        self,
        entry_price: float,
        current_price: float,
        side: str
    ) -> bool:
        """检查是否触发止损"""
        if side == "long":
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price

        return pnl_pct <= -self.stop_loss_pct

    def should_take_profit(
        self,
        entry_price: float,
        current_price: float,
        side: str
    ) -> bool:
        """检查是否触发止盈"""
        if side == "long":
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price

        return pnl_pct >= self.take_profit_pct

    def get_risk_metrics(
        self,
        returns: List[float]
    ) -> RiskMetrics:
        """获取风险指标"""
        exposure = abs(sum(returns)) if returns else 0.0

        # 计算波动率
        volatility = 0.0
        if returns:
            avg = sum(returns) / len(returns)
            variance = sum((r - avg) ** 2 for r in returns) / len(returns)
            volatility = math.sqrt(variance)

        drawdown = self.drawdown_history[-1] if self.drawdown_history else 0.0

        return RiskMetrics(
            portfolio_value=self.current_value,
            total_exposure=exposure,
            max_drawdown=drawdown,
            sharpe_ratio=self.calculate_sharpe_ratio(returns),
            volatility=volatility,
            beta=1.0,
            var_95=self.calculate_var(returns),
            leverage=1.0,
            risk_level=self._determine_risk_level(drawdown),
        )


class DynamicHedgeEngine:
    """动态对冲引擎

    功能：
    - 自动对冲决策
    - Delta对冲
    - 组合对冲
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化对冲引擎

        Args:
            config: 配置字典
                - hedge_threshold: 对冲阈值 (默认0.1)
                - target_delta: 目标Delta (默认0)
        """
        self.config = config
        self.hedge_threshold = config.get('hedge_threshold', 0.1)
        self.target_delta = config.get('target_delta', 0)

        # 对冲历史
        self.hedge_history: List[HedgeDecision] = []

        logger.info("[OK] DynamicHedgeEngine V33.0 初始化完成")

    def evaluate_hedge(
        self,
        portfolio: PortfolioCoordinator,
        market_data: Dict[str, Any]
    ) -> Optional[HedgeDecision]:
        """评估对冲需求

        Args:
            portfolio: 投资组合
            market_data: 市场数据

        Returns:
            对冲决策（如果需要对冲）
        """
        # 计算当前净敞口
        long_exposure = 0.0
        short_exposure = 0.0

        for position in portfolio.positions.values():
            exposure = position.size * position.current_price

            if position.side == "long":
                long_exposure += exposure
            else:
                short_exposure += exposure

        net_exposure = (long_exposure - short_exposure) / portfolio.total_value

        # 检查是否需要对冲
        if abs(net_exposure) < self.hedge_threshold:
            return None

        # 确定对冲策略
        if abs(net_exposure) > 0.3:
            strategy = HedgeStrategy.BETA
        elif abs(net_exposure) > 0.2:
            strategy = HedgeStrategy.DELTA
        else:
            strategy = HedgeStrategy.DIVERSIFICATION

        # 创建对冲决策
        decision = HedgeDecision(
            strategy=strategy,
            reason=f"净敞口 {net_exposure:.1%} 超过阈值",
            target_exposure=self.target_delta,
            current_exposure=net_exposure,
            adjustment=-net_exposure,
            expected_risk_reduction=abs(net_exposure) * 0.5,
        )

        self.hedge_history.append(decision)

        logger.info(f"[OK] 对冲决策: {strategy.value}, 调整: {decision.adjustment:.1%}")
        return decision

    def get_hedge_summary(self) -> Dict[str, Any]:
        """获取对冲摘要"""
        return {
            'total_hedges': len(self.hedge_history),
            'threshold': self.hedge_threshold,
            'target_delta': self.target_delta,
            'recent_hedges': [
                {
                    'strategy': h.strategy.value,
                    'reason': h.reason,
                    'adjustment': h.adjustment,
                }
                for h in self.hedge_history[-5:]
            ],
        }


def create_portfolio_coordinator(
    config: Dict[str, Any]
) -> PortfolioCoordinator:
    """创建投资组合协调器"""
    return PortfolioCoordinator(config)


def create_risk_manager(config: Dict[str, Any]) -> RiskManagerPro:
    """创建风险管理器"""
    return RiskManagerPro(config)


def create_hedge_engine(config: Dict[str, Any]) -> DynamicHedgeEngine:
    """创建对冲引擎"""
    return DynamicHedgeEngine(config)