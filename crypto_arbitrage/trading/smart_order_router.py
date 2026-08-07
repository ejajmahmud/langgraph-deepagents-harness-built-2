"""V34.0 智能订单路由系统

V34.0 新增功能:
1. Smart Order Router - 智能订单路由
2. TWAP/VWAP 订单执行
3. 价格影响预测
4. 最佳交易所选择

创建时间：2026-05-07 20:50
"""

import logging
import time
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    TWAP_VOLUME = "twap_volume"


class ExecutionStrategy(Enum):
    """执行策略"""
    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"
    BALANCED = "balanced"
    MINIMAL_IMPACT = "minimal_impact"


@dataclass
class OrderRoutingDecision:
    """订单路由决策"""
    exchange: str
    order_type: OrderType
    price: float
    quantity: float
    expected_slippage: float
    expected_impact: float
    confidence: float
    reasoning: str


@dataclass
class TWAPOrder:
    """TWAP订单"""
    symbol: str
    side: str
    total_quantity: float
    num_intervals: int
    interval_seconds: int
    start_time: float = field(default_factory=time.time)
    executed_quantity: float = 0.0
    remaining_quantity: float = 0.0


@dataclass
class VWAPOrder:
    """VWAP订单"""
    symbol: str
    side: str
    total_quantity: float
    interval_seconds: int
    volume_profile: Dict[int, float] = field(default_factory=dict)
    executed_quantity: float = 0.0


class PriceImpactModel:
    """价格影响模型"""

    @staticmethod
    def estimate_impact(
        order_quantity: float,
        total_volume: float,
        volatility: float = 0.02
    ) -> float:
        """估算价格影响

        Args:
            order_quantity: 订单数量
            total_volume: 总成交量
            volatility: 波动率

        Returns:
            float: 价格影响百分比
        """
        if total_volume <= 0:
            return 0.1  # 默认10%影响

        participation = order_quantity / total_volume

        # 线性影响模型 + 非线性部分
        linear_impact = participation * 0.1
        nonlinear_impact = (participation ** 1.5) * volatility * 0.5

        return min(linear_impact + nonlinear_impact, 0.5)  # 最大50%影响

    @staticmethod
    def estimate_slippage(
        order_quantity: float,
        spread: float,
        order_type: OrderType
    ) -> float:
        """估算滑点

        Args:
            order_quantity: 订单数量
            spread: 价差
            order_type: 订单类型

        Returns:
            float: 滑点百分比
        """
        base_slippage = spread / 2  # 基础滑点为价差的一半

        if order_type == OrderType.MARKET:
            multiplier = 1.5
        elif order_type == OrderType.LIMIT:
            multiplier = 0.5
        elif order_type in [OrderType.TWAP, OrderType.VWAP]:
            multiplier = 0.3
        else:
            multiplier = 1.0

        return base_slippage * multiplier


class SmartOrderRouter:
    """智能订单路由系统

    功能：
    - TWAP/VWAP 订单执行
    - 价格影响预测
    - 最佳交易所选择
    - 自适应订单分割
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化订单路由

        Args:
            config: 配置字典
                - default_order_type: 默认订单类型
                - max_slippage: 最大滑点
                - min_participation: 最小参与率
        """
        self.config = config

        # 支持字符串格式（小写）
        order_type_str = config.get('default_order_type', 'twap').lower()
        self.default_order_type = OrderType(order_type_str)

        self.max_slippage = config.get('max_slippage', 0.005)  # 0.5%
        self.min_participation = config.get('min_participation', 0.01)  # 1%

        # 活跃订单
        self.active_orders: Dict[str, Any] = {}

        # 历史执行数据
        self.execution_history: List[Dict[str, Any]] = []

        # 交易所评分
        self.exchange_scores: Dict[str, Dict[str, float]] = {}

        logger.info(f"[OK] SmartOrderRouter 初始化完成")
        logger.info(f"    默认订单类型: {self.default_order_type.value}")

    def route_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        exchanges: List[str],
        market_data: Dict[str, Any],
        strategy: ExecutionStrategy = ExecutionStrategy.BALANCED
    ) -> List[OrderRoutingDecision]:
        """路由订单

        Args:
            symbol: 交易对
            side: 方向 (buy/sell)
            quantity: 数量
            exchanges: 可用交易所
            market_data: 市场数据
            strategy: 执行策略

        Returns:
            List[OrderRoutingDecision]: 订单路由决策列表
        """
        decisions = []

        for exchange in exchanges:
            data = market_data.get(exchange, {})
            if not data:
                continue

            # 估算滑点和影响
            impact = PriceImpactModel.estimate_impact(
                quantity,
                data.get('volume_24h', 10000)
            )
            slippage = PriceImpactModel.estimate_slippage(
                quantity,
                data.get('spread', 0.001),
                self.default_order_type
            )

            # 根据策略评分
            if strategy == ExecutionStrategy.AGGRESSIVE:
                confidence = 0.9 - impact * 0.5
                reasoning = "优先快速执行"
            elif strategy == ExecutionStrategy.PASSIVE:
                confidence = 0.7 - impact * 0.3
                reasoning = "优先最低成本"
            elif strategy == ExecutionStrategy.MINIMAL_IMPACT:
                confidence = 0.8 - impact
                reasoning = "优先最小影响"
            else:
                confidence = 0.85 - impact * 0.7
                reasoning = "平衡执行"

            # 检查滑点限制
            if slippage > self.max_slippage:
                logger.warning(f"滑点超限: {exchange} {slippage:.2%} > {self.max_slippage:.2%}")
                continue

            bid_price = data.get('bid_price', 0)
            ask_price = data.get('ask_price', 0)

            if side == "buy":
                price = ask_price
            else:
                price = bid_price

            decision = OrderRoutingDecision(
                exchange=exchange,
                order_type=self.default_order_type,
                price=price,
                quantity=quantity,
                expected_slippage=slippage,
                expected_impact=impact,
                confidence=confidence,
                reasoning=reasoning
            )
            decisions.append(decision)

        # 按置信度排序
        decisions.sort(key=lambda x: x.confidence, reverse=True)

        return decisions

    def create_twap_order(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        duration_minutes: int = 10,
        num_intervals: int = 20
    ) -> TWAPOrder:
        """创建TWAP订单

        Args:
            symbol: 交易对
            side: 方向
            total_quantity: 总数量
            duration_minutes: 持续时间(分钟)
            num_intervals: 间隔数

        Returns:
            TWAPOrder: TWAP订单
        """
        interval_seconds = (duration_minutes * 60) // num_intervals
        quantity_per_interval = total_quantity / num_intervals

        order = TWAPOrder(
            symbol=symbol,
            side=side,
            total_quantity=total_quantity,
            num_intervals=num_intervals,
            interval_seconds=interval_seconds
        )

        order.remaining_quantity = total_quantity - quantity_per_interval
        order.executed_quantity = quantity_per_interval

        logger.info(f"[OK] TWAP订单创建: {symbol} {side} {total_quantity}")
        logger.info(f"    间隔: {num_intervals} x {interval_seconds}秒")

        return order

    def create_vwap_order(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        interval_seconds: int = 60,
        volume_profile: Dict[int, float] = None
    ) -> VWAPOrder:
        """创建VWAP订单

        Args:
            symbol: 交易对
            side: 方向
            total_quantity: 总数量
            interval_seconds: 间隔秒数
            volume_profile: 成交量分布

        Returns:
            VWAPOrder: VWAP订单
        """
        # 默认使用均匀分布
        if volume_profile is None:
            volume_profile = {i: 1.0 for i in range(24)}

        order = VWAPOrder(
            symbol=symbol,
            side=side,
            total_quantity=total_quantity,
            interval_seconds=interval_seconds,
            volume_profile=volume_profile
        )

        execution = total_quantity * 0.1  # 初始执行10%
        order.executed_quantity = execution

        logger.info(f"[OK] VWAP订单创建: {symbol} {side} {total_quantity}")

        return order

    def optimize_order_distribution(
        self,
        symbol: str,
        side: str,
        quantity: float,
        exchanges: List[str],
        market_data: Dict[str, Any],
        max_per_exchange: float = 0.3
    ) -> Dict[str, float]:
        """优化订单分布

        Args:
            symbol: 交易对
            side: 方向
            quantity: 总数量
            exchanges: 交易所列表
            market_data: 市场数据
            max_per_exchange: 单个交易所最大比例

        Returns:
            Dict[str, float]: 交易所 -> 数量映射
        """
        distribution = {}

        # 按流动性排序
        rankings = []
        for ex in exchanges:
            data = market_data.get(ex, {})
            volume = data.get('volume_24h', 0)
            bid = data.get('bid_volume', 0)
            ask = data.get('ask_volume', 0)

            if side == "buy":
                liquidity = ask
            else:
                liquidity = bid

            rankings.append((ex, liquidity, volume))

        rankings.sort(key=lambda x: x[1], reverse=True)

        # 分配订单
        remaining = quantity
        for i, (ex, liq, vol) in enumerate(rankings):
            if remaining <= 0:
                break

            # 第一个交易所获得更多
            if i == 0:
                allocated = min(remaining * 0.5, quantity * max_per_exchange)
            else:
                allocated = min(remaining * 0.3, quantity * max_per_exchange)

            # 不能超过可用流动性
            max_available = liq * 0.1  # 最大使用10%流动性
            allocated = min(allocated, max_available)

            if allocated > 0:
                distribution[ex] = allocated
                remaining -= allocated

        # 确保分配完
        if remaining > 0 and distribution:
            first_ex = list(distribution.keys())[0]
            distribution[first_ex] += remaining

        logger.info(f"[OK] 订单分布优化: {distribution}")
        return distribution

    def calculate_execution_cost(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        slippage: float,
        fee_rate: float = 0.001
    ) -> Dict[str, float]:
        """计算执行成本

        Args:
            symbol: 交易对
            side: 方向
            quantity: 数量
            price: 价格
            slippage: 滑点
            fee_rate: 手续费率

        Returns:
            Dict[str, float]: 成本明细
        """
        base_cost = quantity * price
        slippage_cost = base_cost * slippage
        fee_cost = base_cost * fee_rate
        total_cost = base_cost + slippage_cost + fee_cost

        return {
            'base_cost': base_cost,
            'slippage_cost': slippage_cost,
            'fee_cost': fee_cost,
            'total_cost': total_cost,
            'effective_price': price * (1 + slippage)
        }

    def record_execution(
        self,
        exchange: str,
        order_type: OrderType,
        quantity: float,
        price: float,
        actual_slippage: float
    ) -> None:
        """记录执行结果

        Args:
            exchange: 交易所
            order_type: 订单类型
            quantity: 数量
            price: 价格
            actual_slippage: 实际滑点
        """
        record = {
            'exchange': exchange,
            'order_type': order_type.value,
            'quantity': quantity,
            'price': price,
            'slippage': actual_slippage,
            'timestamp': time.time()
        }

        self.execution_history.append(record)

        # 更新评分
        if exchange not in self.exchange_scores:
            self.exchange_scores[exchange] = {
                'total_slippage': 0,
                'count': 0,
                'avg_slippage': 0
            }

        scores = self.exchange_scores[exchange]
        scores['total_slippage'] += actual_slippage
        scores['count'] += 1
        scores['avg_slippage'] = scores['total_slippage'] / scores['count']

        logger.info(f"[OK] 执行记录: {exchange} {quantity} @ {price}")
        logger.info(f"    滑点: {actual_slippage:.4%}")