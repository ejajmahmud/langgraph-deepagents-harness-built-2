"""V69.0 多策略投资组合与高级订单类型

V69.0 新增功能:
1. MultiStrategyPortfolio - 多策略投资组合
2. StrategyAllocator - 策略配置器
3. AdvancedOrderTypes - 高级订单类型
4. OrderBuilder - 订单构建器
5. ExecutionRouter - 执行路由

创建时间：2026-05-08
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# 高级订单类型
class AdvancedOrderType(Enum):
    """高级订单类型"""
    TRAILING_STOP = "trailing_stop"          # 追踪止损
    OCO = "oco"                      # 二选一订单
    OOA = "ooa"                      # 二选一订单成交任一
    ICEBERG = "iceberg"                 # 冰山订单
    TWAP = "twap"                    # 时间加权平均
    VWAP = "vwap"                   # 成交量加权平均
    GTC = "gtc"                    # 成交为止
    FOK = "fok"                    # 全部成交
    IOC = "ioc"                    # 即时成交一部


# 策略状态
class StrategyState(Enum):
    """策略状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    CLOSED = "closed"


# 分配状态
class AllocationStatus(Enum):
    """分配状态"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class StrategyConfig:
    """策略配置"""
    strategy_id: str
    strategy_type: str
    weight: float
    enabled: bool = True
    max_position_pct: float = 0.2
    risk_limit: float = 0.1
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyAllocation:
    """策略配置"""
    strategy_id: str
    strategy_type: str
    allocated_capital: float
    current_capital: float
    pnl: float = 0.0
    trades: int = 0
    status: StrategyState = StrategyState.ACTIVE
    allocation_status: AllocationStatus = AllocationStatus.PENDING
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_type": self.strategy_type,
            "allocated_capital": self.allocated_capital,
            "current_capital": self.current_capital,
            "pnl": self.pnl,
            "trades": self.trades,
            "status": self.status.value
        }


@dataclass
class TrailingStopOrder:
    """追踪止损订单"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    activation_price: float
    trail_distance: float  # 追踪距离
    highest_price: float = 0.0
    lowest_price: float = 0.0
    filled_quantity: float = 0.0
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def update(self, current_price: float) -> bool:
        """更新追踪价格"""
        if self.side == "buy":
            if current_price > self.highest_price:
                self.highest_price = current_price
        else:
            if self.lowest_price == 0 or current_price < self.lowest_price:
                self.lowest_price = current_price
        return True


@dataclass
class OCOOrder:
    """二选一订单 (One Cancels the Other)"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    limit_price: float
    stop_price: float
    legs: List[Dict[str, Any]] = field(default_factory=list)
    executed_leg: Optional[str] = None
    status: str = "pending"
    created_at: float = field(default_factory=time.time)


@dataclass
class TWAPOrder:
    """时间加权平均订单"""
    order_id: str
    symbol: str
    side: str
    total_quantity: float
    num_slices: int
    slice_duration: int  # 每 slice 持续时间(秒)
    start_time: float
    end_time: float
    filled_quantity: float = 0.0
    slices_completed: int = 0
    status: str = "pending"


@dataclass
class MultiStrategyPortfolio:
    """多策略投资组合

    功能：
    - 多策略管理
    - 资本配置
    - 策略再平衡
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化投资组合"""
        self.config = config or {}

        # 总资本
        self.total_capital: float = self.config.get("initial_capital", 100000.0)

        # 策略配置
        self.strategy_configs: Dict[str, StrategyConfig] = {}

        # 策略分配
        self.allocations: Dict[str, StrategyAllocation] = {}

        # 目标配置
        self.target_weights: Dict[str, float] = {}

        # 再平衡阈值
        self.rebalance_threshold = self.config.get("rebalance_threshold", 0.05)

        logger.info("多策略投资组合 V69.0 初始化完成")

    def add_strategy(
        self,
        strategy_id: str,
        strategy_type: str,
        weight: float,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加策略"""
        config = StrategyConfig(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            weight=weight,
            parameters=parameters or {}
        )

        self.strategy_configs[strategy_id] = config
        self.target_weights[strategy_id] = weight

        # 初始化分配
        allocation = StrategyAllocation(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            allocated_capital=self.total_capital * weight,
            current_capital=self.total_capital * weight
        )

        self.allocations[strategy_id] = allocation

        logger.info(f" Added strategy: {strategy_id} (weight: {weight:.1%})")

    def update_capital(self, new_capital: float) -> None:
        """更新总资本"""
        old_capital = self.total_capital
        self.total_capital = new_capital

        # 重新计算各策略资本
        for alloc in self.allocations.values():
            weight = self.target_weights.get(alloc.strategy_id, 0)
            new_allocated = new_capital * weight
            drift = (alloc.current_capital - new_allocated) / old_capital

            if abs(drift) > 0.01:  # 超过1%差异
                alloc.allocation_status = AllocationStatus.PENDING
            else:
                alloc.allocation_status = AllocationStatus.FILLED

        logger.info(f"Updated capital: {old_capital:.0f} -> {new_capital:.0f}")

    def get_strategy_weights(self) -> Dict[str, float]:
        """获取策略权重"""
        weights = {}
        for sid, alloc in self.allocations.items():
            if self.total_capital > 0:
                weights[sid] = alloc.current_capital / self.total_capital
        return weights

    def needs_rebalance(self) -> bool:
        """检查是否需要再平衡"""
        for sid, target_weight in self.target_weights.items():
            if sid in self.allocations:
                current = self.allocations[sid]
                if self.total_capital > 0:
                    current_weight = current.current_capital / self.total_capital
                    if abs(current_weight - target_weight) > self.rebalance_threshold:
                        return True
        return False

    def get_rebalance_orders(self) -> List[Dict[str, Any]]:
        """获取再平衡订单"""
        if not self.needs_rebalance():
            return []

        orders = []
        for sid, target_weight in self.target_weights.items():
            current = self.allocations.get(sid)
            if current:
                target_value = self.total_capital * target_weight
                drift = target_value - current.current_capital

                if abs(drift) > 100:  # 最小交易量
                    orders.append({
                        "strategy_id": sid,
                        "action": "BUY" if drift > 0 else "SELL",
                        "amount": abs(drift),
                        "current_weight": current.current_capital / self.total_capital,
                        "target_weight": target_weight
                    })

        return orders

    def update_pnl(self, strategy_id: str, pnl: float) -> None:
        """更新策略盈亏"""
        if strategy_id in self.allocations:
            self.allocations[strategy_id].pnl = pnl

    def get_total_pnl(self) -> float:
        """获取总盈亏"""
        return sum(a.pnl for a in self.allocations.values())

    def get_performance(self) -> Dict[str, Any]:
        """获取性能"""
        total_return = (self.get_total_pnl() / self.total_capital * 100) if self.total_capital > 0 else 0
        num_active = sum(1 for a in self.allocations.values() if a.status == StrategyState.ACTIVE)

        return {
            "total_capital": self.total_capital,
            "total_pnl": self.get_total_pnl(),
            "total_return_pct": total_return,
            "strategies": len(self.allocations),
            "active_strategies": num_active,
            "needs_rebalance": self.needs_rebalance()
        }


class AdvancedOrderBuilder:
    """高级订单构建器

    功能：
    - 构建追踪止损单
    - 构建OCO单
    - 构建TWAP单
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化订单构建器"""
        self.config = config or {}

        # 活跃订单
        self.active_orders: Dict[str, Any] = {}

        # 历史订单
        self.order_history: List[Any] = []

        logger.info("高级订单构建器 V69.0 初始化完成")

    def build_trailing_stop(
        self,
        symbol: str,
        side: str,
        quantity: float,
        activation_price: float,
        trail_distance: float
    ) -> TrailingStopOrder:
        """构建追踪止损单

        Args:
            symbol: 交易对
            side: BUY/SELL
            quantity: 数量
            activation_price: 激活价格
            trail_distance: 追踪距离

        Returns:
            追踪止损订单
        """
        order = TrailingStopOrder(
            order_id=f"ts_{symbol}_{int(time.time() * 1000)}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            activation_price=activation_price,
            trail_distance=trail_distance,
            highest_price=activation_price if side == "buy" else 0
        )

        self.active_orders[order.order_id] = order

        return order

    def build_oco(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        stop_price: float
    ) -> OCOOrder:
        """构建OCO订单

        Args:
            symbol: 交易对
            side: BUY/SELL
            quantity: 数量
            limit_price: 限价
            stop_price: 止损价

        Returns:
            OCO订单
        """
        legs = [
            {"type": "limit", "price": limit_price},
            {"type": "stop", "price": stop_price}
        ]

        order = OCOOrder(
            order_id=f"oco_{symbol}_{int(time.time() * 1000)}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            legs=legs
        )

        self.active_orders[order.order_id] = order

        return order

    def build_twap(
        self,
        symbol: str,
        side: str,
        quantity: float,
        duration_minutes: int = 60,
        slices: int = 60
    ) -> TWAPOrder:
        """构建TWAP订单

        Args:
            symbol: 交易对
            side: BUY/SELL
            quantity: 总数量
            duration_minutes: 持续时间(分钟)
            slices: 分片数

        Returns:
            TWAP订单
        """
        slice_quantity = quantity / slices
        slice_duration = duration_minutes * 60 / slices

        order = TWAPOrder(
            order_id=f"twap_{symbol}_{int(time.time() * 1000)}",
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            num_slices=slices,
            slice_duration=slice_duration,
            start_time=time.time(),
            end_time=time.time() + duration_minutes * 60
        )

        self.active_orders[order.order_id] = order

        return order

    def update_trailing_stop(
        self,
        order: TrailingStopOrder,
        current_price: float
    ) -> bool:
        """更新追踪止损

        Args:
            order: 追踪止损单
            current_price: 当前价格

        Returns:
            是否触发
        """
        order.update(current_price)

        # 检查是否触发
        triggered = False

        if order.side == "buy":
            stop_price = order.highest_price * (1 - order.trail_distance)
            if current_price <= stop_price:
                triggered = True
        else:
            stop_price = order.lowest_price * (1 + order.trail_distance)
            if current_price >= stop_price:
                triggered = True

        if triggered:
            order.status = "triggered"
            order.filled_quantity = order.quantity
            self.order_history.append(order)
            if order.order_id in self.active_orders:
                del self.active_orders[order.order_id]

        return triggered

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "active_orders": len(self.active_orders),
            "order_history": len(self.order_history)
        }


class ExecutionRouter:
    """执行路由

    功能：
    - 订单路由
    - 交易所选择
    - 费用优化
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化执行路由"""
        self.config = config or {}

        # 交易所费用
        self.exchange_fees: Dict[str, Dict[str, float]] = {
            "binance": {"maker": 0.001, "taker": 0.002},
            "okx": {"maker": 0.001, "taker": 0.002},
            "bybit": {"maker": 0.001, "taker": 0.002}
        }

        # 交易所延迟
        self.exchange_latency: Dict[str, float] = {
            "binance": 0.1,
            "okx": 0.15,
            "bybit": 0.12
        }

        logger.info("执行路由 V69.0 初始化完成")

    def select_best_exchange(
        self,
        order_type: str = "market"
    ) -> str:
        """选择最佳交易所

        Args:
            order_type: 订单类型

        Returns:
            交易所
        """
        best = None
        best_score = float("inf")

        for exchange, latency in self.exchange_latency.items():
            fee = self.exchange_fees[exchange][
                "maker" if order_type == "limit" else "taker"
            ]

            # 综合评分: 延迟 + 费用
            score = latency * 0.5 + fee * 10

            if best is None or score < best_score:
                best = exchange
                best_score = score

        return best

    def calculate_total_fees(
        self,
        exchanges: List[str],
        volume: float,
        order_type: str = "market"
    ) -> float:
        """计算总费用

        Args:
            exchanges: 交易所列表
            volume: 交易量
            order_type: 订单类型

        Returns:
            总费用
        """
        total_fee = 0.0

        for exchange in exchanges:
            if exchange in self.exchange_fees:
                fee_rate = self.exchange_fees[exchange][
                    "maker" if order_type == "limit" else "taker"
                ]
                total_fee += volume * fee_rate

        return total_fee


# 全局单例
_portfolio: Optional[MultiStrategyPortfolio] = None
_order_builder: Optional[AdvancedOrderBuilder] = None
_execution_router: Optional[ExecutionRouter] = None


def get_portfolio() -> Optional[MultiStrategyPortfolio]:
    return _portfolio


def initialize_portfolio(
    config: Optional[Dict[str, Any]] = None
) -> MultiStrategyPortfolio:
    global _portfolio
    _portfolio = MultiStrategyPortfolio(config)
    return _portfolio


def get_order_builder() -> Optional[AdvancedOrderBuilder]:
    return _order_builder


def initialize_order_builder(
    config: Optional[Dict[str, Any]] = None
) -> AdvancedOrderBuilder:
    global _order_builder
    _order_builder = AdvancedOrderBuilder(config)
    return _order_builder


def get_execution_router() -> Optional[ExecutionRouter]:
    return _execution_router


def initialize_execution_router(
    config: Optional[Dict[str, Any]] = None
) -> ExecutionRouter:
    global _execution_router
    _execution_router = ExecutionRouter(config)
    return _execution_router


__all__ = [
    # 枚举
    'AdvancedOrderType',
    'StrategyState',
    'AllocationStatus',
    # 数据类
    'StrategyConfig',
    'StrategyAllocation',
    'TrailingStopOrder',
    'OCOOrder',
    'TWAPOrder',
    # 主类
    'MultiStrategyPortfolio',
    'AdvancedOrderBuilder',
    'ExecutionRouter',
    # 工厂函数
    'get_portfolio',
    'initialize_portfolio',
    'get_order_builder',
    'initialize_order_builder',
    'get_execution_router',
    'initialize_execution_router',
]