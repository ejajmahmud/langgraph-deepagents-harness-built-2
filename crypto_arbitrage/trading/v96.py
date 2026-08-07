"""实时交易、订单管理与仓位追踪 V96.0 - Phase 40

核心功能：
- RealTimeTradingEngine: 实时交易引擎(信号执行/风控检查/订单下单)
- OrderManagement: 订单管理(订单状态/生命周期/历史记录)
- PositionTracking: 仓位追踪(开仓/平仓/盈亏计算/风险管理)

创建时间：2026-05-09 07:44
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import random
import math


# ============ 枚举定义 ============

class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    OCO = "oco"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(Enum):
    """仓位方向"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class TradingMode(Enum):
    """交易模式"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"


class OrderRejectReason(Enum):
    """拒绝原因"""
    INSUFFICIENT_BALANCE = "insufficient_balance"
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"
    POSITION_LIMIT_EXCEEDED = "position_limit_exceeded"
    INVALID_ORDER = "invalid_order"
    MARKET_CLOSED = "market_closed"
    EXCHANGE_ERROR = "exchange_error"


# ============ 数据结构 ============

@dataclass
class Order:
    """订单"""
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    filled_at: Optional[str] = None
    reject_reason: Optional[str] = None
    client_order_id: Optional[str] = None


@dataclass
class Position:
    """仓位"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    opened_at: str = ""
    updated_at: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class TradingSignal:
    """交易信号"""
    signal_id: str
    symbol: str
    direction: str
    strength: float
    confidence: float
    timestamp: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeResult:
    """交易结果"""
    success: bool
    order_id: Optional[str]
    message: str
    executed_quantity: float = 0.0
    executed_price: float = 0.0
    commission: float = 0.0


# ============ RealTimeTradingEngine ============

class RealTimeTradingEngine:
    """实时交易引擎"""

    def __init__(self, mode: TradingMode = TradingMode.PAPER):
        self._mode = mode
        self._orders: List[Order] = []
        self._trades: List[TradeResult] = []
        self._balance: float = 1000000.0  # 100万初始模拟资金
        self._order_id_counter: int = 0
        self._max_position_size: float = 0.3  # 最大30%仓位
        self._max_single_trade: float = 0.1  # 单笔最大10%
        self._daily_loss_limit: float = 0.05  # 每日最大亏损5%

    def _generate_order_id(self) -> str:
        self._order_id_counter += 1
        return f"ORD_{datetime.now().strftime('%Y%m%d')}_{self._order_id_counter:06d}"

    def set_mode(self, mode: TradingMode) -> None:
        self._mode = mode

    def get_mode(self) -> TradingMode:
        return self._mode

    def get_balance(self) -> float:
        return self._balance

    def set_balance(self, balance: float) -> None:
        self._balance = balance

    def check_risk_limits(self, symbol: str, side: str, quantity: float, price: float) -> Tuple[bool, Optional[str]]:
        """风控检查"""
        order_value = quantity * price

        # 检查余额
        if side == OrderSide.BUY.value:
            if order_value > self._balance:
                return False, OrderRejectReason.INSUFFICIENT_BALANCE.value

        # 检查仓位限制
        current_exposure = sum(o.quantity * o.avg_fill_price for o in self._orders if o.status == OrderStatus.FILLED.value)
        new_exposure = current_exposure + order_value

        if new_exposure / self._balance > self._max_position_size:
            return False, OrderRejectReason.POSITION_LIMIT_EXCEEDED.value

        # 检查单笔限制
        if order_value / self._balance > self._max_single_trade:
            return False, OrderRejectReason.RISK_LIMIT_EXCEEDED.value

        return True, None

    def submit_order(self, symbol: str, side: str, order_type: str,
                 quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """提交订单"""
        order_id = self._generate_order_id()
        current_time = datetime.now().isoformat()

        # Market order - 立即成交
        if order_type == OrderType.MARKET.value:
            # 模拟价格
            if price is None:
                price = random.uniform(100, 110)

            # 风控检查
            allowed, reason = self.check_risk_limits(symbol, side, quantity, price)
            if not allowed:
                order = Order(
                    order_id=order_id,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    status=OrderStatus.REJECTED.value,
                    created_at=current_time,
                    updated_at=current_time,
                    reject_reason=reason
                )
                self._orders.append(order)
                return {
                    "success": False,
                    "order_id": order_id,
                    "status": OrderStatus.REJECTED.value,
                    "reason": reason
                }

            # 执行订单
            commission = quantity * price * 0.0004  # 0.04% 手续费

            if side == OrderSide.BUY.value:
                self._balance -= (quantity * price + commission)
            else:
                self._balance += (quantity * price - commission)

            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.FILLED.value,
                filled_quantity=quantity,
                avg_fill_price=price,
                created_at=current_time,
                updated_at=current_time,
                filled_at=current_time
            )
            self._orders.append(order)

            trade_result = TradeResult(
                success=True,
                order_id=order_id,
                message="Order filled",
                executed_quantity=quantity,
                executed_price=price,
                commission=commission
            )
            self._trades.append(trade_result)

            return {
                "success": True,
                "order_id": order_id,
                "status": OrderStatus.FILLED.value,
                "filled_quantity": quantity,
                "avg_fill_price": price,
                "commission": commission
            }

        # Limit order - 保存待成交
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING.value,
            created_at=current_time,
            updated_at=current_time
        )
        self._orders.append(order)

        return {
            "success": True,
            "order_id": order_id,
            "status": OrderStatus.PENDING.value
        }

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        for order in self._orders:
            if order.order_id == order_id:
                if order.status in [OrderStatus.PENDING.value, OrderStatus.SUBMITTED.value]:
                    order.status = OrderStatus.CANCELLED.value
                    order.updated_at = datetime.now().isoformat()
                    return {
                        "success": True,
                        "order_id": order_id,
                        "status": OrderStatus.CANCELLED.value
                    }
                else:
                    return {
                        "success": False,
                        "order_id": order_id,
                        "reason": f"Cannot cancel order in status: {order.status}"
                    }

        return {
            "success": False,
            "order_id": order_id,
            "reason": "Order not found"
        }

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        for order in self._orders:
            if order.order_id == order_id:
                return order
        return None

    def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """获取订单列表"""
        if status:
            return [o for o in self._orders if o.status == status]
        return self._orders

    def execute_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """执行交易信号"""
        direction = signal.direction
        side = OrderSide.BUY.value if direction in ["bullish", "buy", "long"] else OrderSide.SELL.value

        # 计算仓位
        position_size = self._balance * signal.strength * 0.1  # 使用信号的10%
        quantity = position_size / signal.metadata.get("price", 100)

        return self.submit_order(
            symbol=signal.symbol,
            side=side,
            order_type=OrderType.MARKET.value,
            quantity=quantity,
            price=signal.metadata.get("price")
        )

    def get_trading_summary(self) -> Dict[str, Any]:
        filled_orders = [o for o in self._orders if o.status == OrderStatus.FILLED.value]
        total_volume = sum(o.filled_quantity * o.avg_fill_price for o in filled_orders)
        total_commission = sum(t.commission for t in self._trades)

        return {
            "mode": self._mode.value,
            "balance": round(self._balance, 2),
            "total_orders": len(self._orders),
            "filled_orders": len(filled_orders),
            "total_volume": round(total_volume, 2),
            "total_commission": round(total_commission, 2)
        }


# ============ OrderManagement ============

class OrderManagement:
    """订单管理系统"""

    def __init__(self):
        self._order_registry: Dict[str, Order] = {}
        self._order_history: List[Order] = []
        self._counter: int = 0

    def register_order(self, order: Order) -> None:
        self._order_registry[order.order_id] = order
        self._order_history.append(order)

    def update_order_status(self, order_id: str, status: str, fill_info: Dict[str, Any] = None) -> bool:
        """更新订单状态"""
        if order_id in self._order_registry:
            order = self._order_registry[order_id]
            order.status = status
            order.updated_at = datetime.now().isoformat()

            if fill_info:
                order.filled_quantity = fill_info.get("filled_quantity", order.filled_quantity)
                order.avg_fill_price = fill_info.get("avg_fill_price", order.avg_fill_price)
                if status == OrderStatus.FILLED.value:
                    order.filled_at = datetime.now().isoformat()

            return True
        return False

    def get_order_status(self, order_id: str) -> Optional[str]:
        """获取订单状态"""
        if order_id in self._order_registry:
            return self._order_registry[order_id].status
        return None

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取待处理订单"""
        pending = [o for o in self._order_registry.values()
                  if o.status in [OrderStatus.PENDING.value, OrderStatus.SUBMITTED.value]]
        if symbol:
            pending = [o for o in pending if o.symbol == symbol]
        return pending

    def get_order_history(self, symbol: Optional[str] = None,
                      start_time: Optional[str] = None,
                      end_time: Optional[str] = None) -> List[Order]:
        """获取订单历史"""
        history = self._order_history

        if symbol:
            history = [o for o in history if o.symbol == symbol]

        if start_time:
            history = [o for o in history if o.created_at >= start_time]

        if end_time:
            history = [o for o in history if o.created_at <= end_time]

        return history

    def get_filled_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取已成交订单"""
        filled = [o for o in self._order_registry.values()
                 if o.status == OrderStatus.FILLED.value]
        if symbol:
            filled = [o for o in filled if o.symbol == symbol]
        return filled

    def calculate_fill_rate(self, symbol: Optional[str] = None) -> float:
        """计算成交率"""
        all_orders = self._order_history
        if symbol:
            all_orders = [o for o in all_orders if o.symbol == symbol]

        if not all_orders:
            return 0.0

        filled = len([o for o in all_orders if o.status == OrderStatus.FILLED.value])
        return filled / len(all_orders)

    def get_order_statistics(self) -> Dict[str, Any]:
        """获取订单统计"""
        status_counts = {}
        for order in self._order_history:
            status = order.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_orders": len(self._order_history),
            "status_distribution": status_counts,
            "fill_rate": round(self.calculate_fill_rate(), 4)
        }


# ============ PositionTracking ============

class PositionTracking:
    """仓位追踪系统"""

    def __init__(self):
        self._positions: Dict[str, Position] = {}
        self._position_history: List[Position] = []
        self._total_realized_pnl: float = 0.0

    def open_position(self, symbol: str, side: str, quantity: float,
                   entry_price: float, current_price: float = 0.0,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Position:
        """开仓"""
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price if current_price > 0 else entry_price,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            opened_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self._positions[symbol] = position
        self._position_history.append(position)

        return position

    def update_position(self, symbol: str, current_price: float) -> Optional[Position]:
        """更新仓位"""
        if symbol in self._positions:
            position = self._positions[symbol]

            if position.side == PositionSide.LONG.value:
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
            else:  # SHORT
                position.unrealized_pnl = (position.entry_price - current_price) * position.quantity

            position.current_price = current_price
            position.updated_at = datetime.now().isoformat()

            # 检查止损/止盈
            if position.stop_loss:
                if (position.side == PositionSide.LONG.value and current_price <= position.stop_loss) or \
                   (position.side == PositionSide.SHORT.value and current_price >= position.stop_loss):
                    return position

            if position.take_profit:
                if (position.side == PositionSide.LONG.value and current_price >= position.take_profit) or \
                   (position.side == PositionSide.SHORT.value and current_price <= position.take_profit):
                    return position

            return position

        return None

    def close_position(self, symbol: str, exit_price: float) -> Optional[Dict[str, Any]]:
        """平仓"""
        if symbol in self._positions:
            position = self._positions[symbol]

            # 计算已实现盈亏
            if position.side == PositionSide.LONG.value:
                realized_pnl = (exit_price - position.entry_price) * position.quantity
            else:
                realized_pnl = (position.entry_price - exit_price) * position.quantity

            position.realized_pnl = realized_pnl
            position.current_price = exit_price
            self._total_realized_pnl += realized_pnl

            result = {
                "symbol": symbol,
                "side": position.side,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "exit_price": exit_price,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": position.unrealized_pnl,
                "opened_at": position.opened_at,
                "closed_at": datetime.now().isoformat()
            }

            del self._positions[symbol]

            return result

        return None

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取仓位"""
        return self._positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Position]:
        """获取所有仓位"""
        return self._positions

    def get_total_exposure(self) -> float:
        """获取总敞口"""
        return sum(p.quantity * p.current_price for p in self._positions.values())

    def get_total_unrealized_pnl(self) -> float:
        """获取总未实现盈亏"""
        return sum(p.unrealized_pnl for p in self._positions.values())

    def get_total_realized_pnl(self) -> float:
        """获取总已实现盈亏"""
        return self._total_realized_pnl

    def get_position_summary(self) -> Dict[str, Any]:
        """获取仓位摘要"""
        return {
            "open_positions": len(self._positions),
            "total_exposure": round(self.get_total_exposure(), 2),
            "unrealized_pnl": round(self.get_total_unrealized_pnl(), 2),
            "realized_pnl": round(self.get_total_realized_pnl(), 2),
            "positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "quantity": p.quantity,
                    "entry": p.entry_price,
                    "current": p.current_price,
                    "unrealized": round(p.unrealized_pnl, 2)
                }
                for p in self._positions.values()
            ]
        }

    def check_position_limits(self, max_positions: int = 5) -> Tuple[bool, str]:
        """检查仓位限制"""
        if len(self._positions) >= max_positions:
            return False, f"Max positions {max_positions} reached"
        return True, "OK"


# ============ 全局实例管理 ============

_real_time_trading_engine: Optional[RealTimeTradingEngine] = None
_order_management: Optional[OrderManagement] = None
_position_tracking: Optional[PositionTracking] = None


def get_real_time_trading_engine() -> RealTimeTradingEngine:
    global _real_time_trading_engine
    if _real_time_trading_engine is None:
        _real_time_trading_engine = RealTimeTradingEngine()
    return _real_time_trading_engine


def initialize_real_time_trading_engine(mode: TradingMode = TradingMode.PAPER) -> None:
    global _real_time_trading_engine
    _real_time_trading_engine = RealTimeTradingEngine(mode)


def get_order_management() -> OrderManagement:
    global _order_management
    if _order_management is None:
        _order_management = OrderManagement()
    return _order_management


def initialize_order_management() -> None:
    global _order_management
    _order_management = OrderManagement()


def get_position_tracking() -> PositionTracking:
    global _position_tracking
    if _position_tracking is None:
        _position_tracking = PositionTracking()
    return _position_tracking


def initialize_position_tracking() -> None:
    global _position_tracking
    _position_tracking = PositionTracking()