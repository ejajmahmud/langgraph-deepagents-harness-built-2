"""V62.0 网格交易策略模块

V62.0 新增功能:
1. Grid Trading Strategy - 网格交易策略
2. Grid Order - 网格订单
3. GridLevel - 网格层级
4. GridState - 网格状态
5. GridConfig - 网格配置
6. GridStatistics - 网格统计
7. GridTradingEngine - 网格交易引擎

创建时间: 2026-05-08
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class GridState(Enum):
    """网格状态"""
    INACTIVE = "inactive"  # 未激活
    ACTIVE = "active"  # 活跃
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 完成
    STOPPED = "stopped"  # 停止


class GridOrderSide(Enum):
    """网格订单方向"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class GridLevel:
    """网格层级配置"""
    price: float  # 价格
    quantity: float  # 数量
    filled: bool = False  # 是否已成交
    order_id: Optional[str] = None  # 订单ID
    filled_at: Optional[datetime] = None  # 成交时间
    filled_price: Optional[float] = None  # 成交价格

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "price": self.price,
            "quantity": self.quantity,
            "filled": self.filled,
            "order_id": self.order_id,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "filled_price": self.filled_price,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridLevel":
        """从字典创建"""
        filled_at = None
        if data.get("filled_at"):
            filled_at = datetime.fromisoformat(data["filled_at"])
        return cls(
            price=data["price"],
            quantity=data["quantity"],
            filled=data.get("filled", False),
            order_id=data.get("order_id"),
            filled_at=filled_at,
            filled_price=data.get("filled_price"),
        )


@dataclass
class GridOrder:
    """网格订单"""
    order_id: str
    symbol: str
    side: GridOrderSide
    level: int  # 网格层级索引
    price: float
    quantity: float
    status: str = "pending"  # pending, filled, cancelled
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "level": self.level,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
        }


@dataclass
class GridStatistics:
    """网格交易统计"""
    total_trades: int = 0  # 总交易次数
    buy_fills: int = 0  # 买入成交次数
    sell_fills: int = 0  # 卖出成交次数
    total_profit: float = 0.0  # 总利润
    total_volume: float = 0.0  # 总交易量
    avg_fill_price: float = 0.0  # 平均成交价格
    max_profit: float = 0.0  # 最大利润
    max_loss: float = 0.0  # 最大亏损
    grid_levels_filled: int = 0  # 已填写的网格层级数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_trades": self.total_trades,
            "buy_fills": self.buy_fills,
            "sell_fills": self.sell_fills,
            "total_profit": self.total_profit,
            "total_volume": self.total_volume,
            "avg_fill_price": self.avg_fill_price,
            "max_profit": self.max_profit,
            "max_loss": self.max_loss,
            "grid_levels_filled": self.grid_levels_filled,
        }


@dataclass
class GridConfig:
    """网格交易配置"""
    symbol: str  # 交易对
    lower_bound: float  # 价格下限
    upper_bound: float  # 价格上限
    grid_count: int = 10  # 网格数量
    quantity_per_grid: float = 0.01  # 每个网格的数量
    auto_rebalance: bool = True  # 自动再平衡
    profit_target: float = 0.0  # 利润目标 (0=不设限)
    max_loss: float = 0.0  # 最大亏损 (0=不设限)
    grid_spacing: Optional[float] = None  # 网格间距 (自动计算如果为None)

    def validate(self) -> bool:
        """验证配置"""
        if self.lower_bound >= self.upper_bound:
            logger.error("Lower bound must be less than upper bound")
            return False
        if self.grid_count <= 1:
            logger.error("Grid count must be greater than 1")
            return False
        if self.quantity_per_grid <= 0:
            logger.error("Quantity per grid must be positive")
            return False
        return True

    def calculate_grid_spacing(self) -> float:
        """计算网格间距"""
        if self.grid_spacing is not None:
            return self.grid_spacing
        return (self.upper_bound - self.lower_bound) / (self.grid_count - 1)


class GridTradingEngine:
    """网格交易引擎

    网格交易是一种在预定价格区间内低买高卖的策略:
    - 在价格下限买入
    - 在价格上限卖出
    - 在每个网格层级自动挂单
    - 实现自动化高抛低吸
    """

    def __init__(self, config: GridConfig):
        """初始化网格交易引擎"""
        if not config.validate():
            raise ValueError("Invalid grid config")
        self.config = config
        self.state = GridState.INACTIVE
        self.buy_levels: List[GridLevel] = []
        self.sell_levels: List[GridLevel] = []
        self.orders: Dict[str, GridOrder] = {}
        self.statistics = GridStatistics()
        self._generate_grid_levels()

    def _generate_grid_levels(self) -> None:
        """生成网格层级"""
        spacing = self.config.calculate_grid_spacing()

        # 生成买入网格 (lower_bound到中点)
        mid_price = (self.config.lower_bound + self.config.upper_bound) / 2
        for i in range(self.config.grid_count // 2):
            price = self.config.lower_bound + (i * spacing)
            level = GridLevel(
                price=price,
                quantity=self.config.quantity_per_grid,
            )
            self.buy_levels.append(level)

        # 生成卖出网格 (中点到upper_bound)
        for i in range(self.config.grid_count // 2, self.config.grid_count):
            price = self.config.lower_bound + (i * spacing)
            level = GridLevel(
                price=price,
                quantity=self.config.quantity_per_grid,
            )
            self.sell_levels.append(level)

        logger.info(f"Generated {len(self.buy_levels)} buy levels and {len(self.sell_levels)} sell levels")

    def start(self) -> bool:
        """启动网格交易"""
        if self.state == GridState.ACTIVE:
            logger.warning("Grid trading already active")
            return False

        self.state = GridState.ACTIVE
        logger.info(f"Grid trading started for {self.config.symbol}")
        return True

    def pause(self) -> bool:
        """暂停网格交易"""
        if self.state != GridState.ACTIVE:
            logger.warning("Grid not active")
            return False

        self.state = GridState.PAUSED
        logger.info("Grid trading paused")
        return True

    def resume(self) -> bool:
        """恢复网格交易"""
        if self.state != GridState.PAUSED:
            logger.warning("Grid not paused")
            return False

        self.state = GridState.ACTIVE
        logger.info("Grid trading resumed")
        return True

    def stop(self) -> bool:
        """停止网格交易"""
        self.state = GridState.STOPPED
        logger.info("Grid trading stopped")
        return True

    def get_buy_levels(self) -> List[GridLevel]:
        """获取买入网格层级"""
        return self.buy_levels.copy()

    def get_sell_levels(self) -> List[GridLevel]:
        """获取卖出网格层级"""
        return self.sell_levels.copy()

    def get_all_levels(self) -> List[GridLevel]:
        """获取所有网格层级"""
        return self.buy_levels + self.sell_levels

    def place_buy_order(self, level_index: int, order_id: str) -> Optional[GridOrder]:
        """下单买入"""
        if level_index >= len(self.buy_levels):
            logger.error(f"Invalid buy level index: {level_index}")
            return None

        level = self.buy_levels[level_index]
        if level.filled:
            logger.warning(f"Buy level {level_index} already filled")
            return None

        order = GridOrder(
            order_id=order_id,
            symbol=self.config.symbol,
            side=GridOrderSide.BUY,
            level=level_index,
            price=level.price,
            quantity=level.quantity,
        )
        self.orders[order_id] = order
        logger.info(f"Placed buy order at level {level_index}, price {level.price}")
        return order

    def place_sell_order(self, level_index: int, order_id: str) -> Optional[GridOrder]:
        """下单卖出"""
        if level_index >= len(self.sell_levels):
            logger.error(f"Invalid sell level index: {level_index}")
            return None

        level = self.sell_levels[level_index]
        if level.filled:
            logger.warning(f"Sell level {level_index} already filled")
            return None

        order = GridOrder(
            order_id=order_id,
            symbol=self.config.symbol,
            side=GridOrderSide.SELL,
            level=level_index,
            price=level.price,
            quantity=level.quantity,
        )
        self.orders[order_id] = order
        logger.info(f"Placed sell order at level {level_index}, price {level.price}")
        return order

    def fill_order(self, order_id: str, fill_price: float) -> bool:
        """订单成交处理"""
        order = self.orders.get(order_id)
        if not order:
            logger.error(f"Order not found: {order_id}")
            return False

        if order.status == "filled":
            logger.warning(f"Order {order_id} already filled")
            return False

        # 更新订单状态
        order.status = "filled"
        order.filled_at = datetime.now()

        # 更新网格层级状态
        if order.side == GridOrderSide.BUY:
            level = self.buy_levels[order.level]
            level.filled = True
            level.filled_at = datetime.now()
            level.filled_price = fill_price
            level.order_id = order_id
            self.statistics.buy_fills += 1
            self.statistics.grid_levels_filled += 1
        else:
            level = self.sell_levels[order.level]
            level.filled = True
            level.filled_at = datetime.now()
            level.filled_price = fill_price
            level.order_id = order_id
            self.statistics.sell_fills += 1
            self.statistics.grid_levels_filled += 1

        # 更新统计
        self.statistics.total_trades += 1
        self.statistics.total_volume += order.quantity * fill_price

        # 计算利润 (卖出-买入)
        if order.side == GridOrderSide.SELL:
            # 找到对应的买入
            for buy_level in self.buy_levels:
                if buy_level.filled and buy_level.filled_price:
                    profit = (fill_price - buy_level.filled_price) * order.quantity
                    self.statistics.total_profit += profit
                    if profit > 0:
                        self.statistics.max_profit = max(self.statistics.max_profit, profit)
                    else:
                        self.statistics.max_loss = min(self.statistics.max_loss, profit)
                    break

        # 检查是否达到利润目标
        if self.config.profit_target > 0 and self.statistics.total_profit >= self.config.profit_target:
            logger.info(f"Profit target {self.config.profit_target} reached!")
            self.state = GridState.COMPLETED
            return True

        # 检查是否达到亏损限制
        if self.config.max_loss < 0 and self.statistics.total_profit <= self.config.max_loss:
            logger.warning(f"Max loss {self.config.max_loss} reached!")
            self.state = GridState.COMPLETED
            return True

        return True

    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        order = self.orders.get(order_id)
        if not order:
            logger.error(f"Order not found: {order_id}")
            return False

        if order.status == "filled":
            logger.error(f"Cannot cancel filled order: {order_id}")
            return False

        order.status = "cancelled"
        logger.info(f"Cancelled order: {order_id}")
        return True

    def get_statistics(self) -> GridStatistics:
        """获取交易统计"""
        return self.statistics

    def get_status(self) -> Dict[str, Any]:
        """获取网格状态"""
        return {
            "symbol": self.config.symbol,
            "state": self.state.value,
            "lower_bound": self.config.lower_bound,
            "upper_bound": self.config.upper_bound,
            "grid_count": self.config.grid_count,
            "buy_levels_filled": sum(1 for l in self.buy_levels if l.filled),
            "sell_levels_filled": sum(1 for l in self.sell_levels if l.filled),
            "statistics": self.statistics.to_dict(),
        }

    def rebalance(self) -> bool:
        """重新平衡网格"""
        if not self.config.auto_rebalance:
            logger.warning("Auto rebalance disabled")
            return False

        # 检查已填写的层级
        filled_count = sum(1 for l in self.get_all_levels() if l.filled)
        total_count = self.config.grid_count

        if filled_count >= total_count * 0.8:  # 80%填写完成
            logger.info("Rebalancing grid...")
            # 重置所有未成交订单
            for level in self.get_all_levels():
                if not level.filled:
                    level.filled = False
                    level.order_id = None
                    level.filled_at = None
                    level.filled_price = None
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "config": {
                "symbol": self.config.symbol,
                "lower_bound": self.config.lower_bound,
                "upper_bound": self.config.upper_bound,
                "grid_count": self.config.grid_count,
                "quantity_per_grid": self.config.quantity_per_grid,
            },
            "state": self.state.value,
            "buy_levels": [l.to_dict() for l in self.buy_levels],
            "sell_levels": [l.to_dict() for l in self.sell_levels],
            "statistics": self.statistics.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridTradingEngine":
        """从字典创建"""
        config = GridConfig(
            symbol=data["config"]["symbol"],
            lower_bound=data["config"]["lower_bound"],
            upper_bound=data["config"]["upper_bound"],
            grid_count=data["config"]["grid_count"],
            quantity_per_grid=data["config"]["quantity_per_grid"],
        )
        engine = cls(config)
        engine.state = GridState(data["state"])

        # 恢复买入层级
        for i, level_data in enumerate(data.get("buy_levels", [])):
            if i < len(engine.buy_levels):
                engine.buy_levels[i] = GridLevel.from_dict(level_data)

        # 恢复卖出层级
        for i, level_data in enumerate(data.get("sell_levels", [])):
            if i < len(engine.sell_levels):
                engine.sell_levels[i] = GridLevel.from_dict(level_data)

        return engine


def get_grid_engine(config: GridConfig) -> GridTradingEngine:
    """获取网格交易引擎实例"""
    return GridTradingEngine(config)