"""
V35.0 Paper Trading Engine - 模拟交易引擎

功能：
1. 模拟交易环境 - 无真实资金风险测试策略
2. PnL 追踪 - 模拟盈亏计算
3. 订单执行模拟 - 模拟订单簿成交
4. 持仓管理 - 模拟持仓和资金
5. 性能报告 - 生成模拟交易报告

创建时间：2026-05-07 21:15
"""

import logging
import time
import random
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PaperTradingMode(Enum):
    """模拟交易模式"""
    SANDBOX = "sandbox"          # 沙盒模式（无限虚拟资金）
    BACKTEST = "backtest"        # 回测模式（历史数据）
    LIVE_SIM = "live_sim"       # 实时模拟（模拟实时价格）


class SimulatedOrderBook:
    """模拟订单簿

    模拟订单簿成交，用于 Paper Trading。
    """

    def __init__(self, spread_bps: float = 0.001):
        """初始化模拟订单簿

        Args:
            spread_bps: 价差（基点），默认 0.001 (0.01%)
        """
        self.spread_bps = spread_bps

    def execute_market_order(
        self,
        side: str,
        quantity: float,
        mid_price: float
    ) -> Dict[str, Any]:
        """执行市价单模拟

        Args:
            side: 买入/卖出
            quantity: 数量
            mid_price: 中间价格

        Returns:
            成交结果字典
        """
        # 计算买卖价差
        spread = mid_price * self.spread_bps

        if side.lower() == "buy":
            # 买入成交于 ask 价格（高于 mid）
            exec_price = mid_price + spread / 2
        else:
            # 卖出成交于 bid 价格（低于 mid）
            exec_price = mid_price - spread / 2

        # 添加随机滑点 (0-0.5个价差)
        slippage_factor = random.uniform(0, 0.5)
        exec_price += spread * slippage_factor * (1 if side.lower() == "buy" else -1)

        # 计算成交价值
        total_value = quantity * exec_price

        return {
            "success": True,
            "exec_price": exec_price,
            "quantity": quantity,
            "total_value": total_value,
            "slippage_bps": abs(exec_price - mid_price) / mid_price * 10000,
            "timestamp": datetime.now().isoformat()
        }

    def execute_limit_order(
        self,
        side: str,
        quantity: float,
        limit_price: float,
        mid_price: float
    ) -> Dict[str, Any]:
        """执行限价单模拟

        Args:
            side: 买入/卖出
            quantity: 数量
            limit_price: 限价
            mid_price: 中间价格

        Returns:
            成交结果字典
        """
        spread = mid_price * self.spread_bps

        if side.lower() == "buy":
            # 买单：只有当 ask <= limit_price 时成交
            ask_price = mid_price + spread / 2
            can_fill = ask_price <= limit_price
            exec_price = ask_price if can_fill else limit_price
        else:
            # 卖单：只有当 bid >= limit_price 时成交
            bid_price = mid_price - spread / 2
            can_fill = bid_price >= limit_price
            exec_price = bid_price if can_fill else limit_price

        if not can_fill:
            return {
                "success": False,
                "reason": "limit_not_reached",
                "exec_price": None,
                "quantity": 0,
                "timestamp": datetime.now().isoformat()
            }

        return {
            "success": True,
            "exec_price": exec_price,
            "quantity": quantity,
            "total_value": quantity * exec_price,
            "slippage_bps": abs(exec_price - mid_price) / mid_price * 10000,
            "timestamp": datetime.now().isoformat()
        }


class PaperTradingEngine:
    """模拟交易引擎

    提供完整的模拟交易功能，用于测试和验证交易策略。
    """

    def __init__(
        self,
        initial_balance: float = 100000.0,
        mode: PaperTradingMode = PaperTradingMode.SANDBOX,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化模拟交易引擎

        Args:
            initial_balance: 初始资金
            mode: 交易模式
            config: 配置字典
        """
        self.mode = mode
        self.config = config or {}

        # 资金管理
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.available_balance = initial_balance

        # 持仓管理
        self.positions: Dict[str, Dict] = {}  # symbol -> position

        # 订单管理
        self.orders: Dict[str, Dict] = {}
        self.order_history: List[Dict] = []
        self.order_id_counter = 0

        # 交易统计
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "total_volume": 0.0,
            "total_fees": 0.0,
            "max_drawdown": 0.0,
            "peak_balance": initial_balance,
        }

        # 订单簿
        self.order_book = SimulatedOrderBook(
            spread_bps=self.config.get("spread_bps", 0.001)
        )

        # 手续费率 (0.001 = 0.01%)
        self.maker_fee = self.config.get("maker_fee", 0.001)
        self.taker_fee = self.config.get("taker_fee", 0.001)

        # 配置
        self.enable_logging = self.config.get("enable_logging", True)

    def generate_order_id(self) -> str:
        """生成订单ID

        Returns:
            订单ID字符串
        """
        self.order_id_counter += 1
        return f"PAPER_{self.order_id_counter:08d}"

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """获取持仓

        Args:
            symbol: 交易品种

        Returns:
            持仓字典，如果不存在则返回空持仓
        """
        if symbol not in self.positions:
            return {
                "symbol": symbol,
                "quantity": 0.0,
                "avg_price": 0.0,
                "value": 0.0,
                "unrealized_pnl": 0.0,
            }
        return self.positions[symbol]

    def update_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        exec_price: float
    ) -> None:
        """更新持仓

        Args:
            symbol: 交易品种
            side: 买入/卖出
            quantity: 成交数量
            exec_price: 成交价格
        """
        if symbol not in self.positions:
            self.positions[symbol] = {
                "symbol": symbol,
                "quantity": 0.0,
                "avg_price": 0.0,
                "value": 0.0,
                "cost": 0.0,
            }

        pos = self.positions[symbol]

        if side.lower() == "buy":
            # 更新买入持仓
            new_quantity = pos["quantity"] + quantity
            new_cost = pos["cost"] + quantity * exec_price
            pos["quantity"] = new_quantity
            pos["cost"] = new_cost
            pos["avg_price"] = new_cost / new_quantity if new_quantity > 0 else 0
            pos["value"] = new_quantity * exec_price

            # 扣除资金
            self.available_balance -= quantity * exec_price
        else:
            # 更新卖出持仓
            new_quantity = pos["quantity"] - quantity
            pos["quantity"] = new_quantity

            if new_quantity <= 0:
                pos["avg_price"] = 0
                pos["cost"] = 0
            else:
                # 按比例调整成本
                pos["cost"] = pos["avg_price"] * new_quantity

            # 释放资金
            self.available_balance += quantity * exec_price

        # 更新持仓价值
        pos["value"] = pos["quantity"] * exec_price

    def calculate_pnl(self, symbol: str, current_price: float) -> float:
        """计算持仓未实现盈亏

        Args:
            symbol: 交易品种
            current_price: 当前价格

        Returns:
            未实现盈亏
        """
        if symbol not in self.positions:
            return 0.0

        pos = self.positions[symbol]
        if pos["quantity"] <= 0:
            return 0.0

        # 未实现盈亏 = 持仓数量 * (当前价格 - 平均价格)
        unrealized = pos["quantity"] * (current_price - pos["avg_price"])
        pos["unrealized_pnl"] = unrealized

        return unrealized

    def execute_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        limit_price: Optional[float] = None,
        mid_price: float = 0.0
    ) -> Dict[str, Any]:
        """执行订单

        Args:
            symbol: 交易品种
            side: 买入/卖出
            order_type: 市价单/限价单
            quantity: 数量
            limit_price: 限价（限价单时需要）
            mid_price: 中间价格

        Returns:
            执行结果字典
        """
        # 生成订单ID
        order_id = self.generate_order_id()

        # 检查资金
        if side.lower() == "buy" and order_type.lower() == "market":
            required = quantity * mid_price
            if required > self.available_balance:
                return {
                    "success": False,
                    "reason": "insufficient_balance",
                    "order_id": order_id,
                }

        # 执行订单
        if order_type.lower() == "market":
            result = self.order_book.execute_market_order(
                side, quantity, mid_price
            )
        elif order_type.lower() == "limit" and limit_price:
            result = self.order_book.execute_limit_order(
                side, quantity, limit_price, mid_price
            )
        else:
            return {
                "success": False,
                "reason": "invalid_order_type",
                "order_id": order_id,
            }

        if not result["success"]:
            result["order_id"] = order_id
            return result

        # 计算手续费
        fee = result["total_value"] * self.taker_fee
        result["fee"] = fee

        # 扣除手续费
        self.available_balance -= fee
        self.stats["total_fees"] += fee
        self.stats["total_volume"] += result["total_value"]

        # 更新持仓
        self.update_position(
            symbol,
            side,
            quantity,
            result["exec_price"]
        )

        # 记录订单
        order_record = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "exec_price": result["exec_price"],
            "total_value": result["total_value"],
            "fee": fee,
            "timestamp": result["timestamp"],
        }
        self.order_history.append(order_record)
        self.orders[order_id] = order_record

        # 更新统计
        self.stats["total_trades"] += 1

        # 扣除冻结资金
        if side.lower() == "buy":
            self.balance -= result["total_value"] + fee
        else:
            self.balance += result["total_value"] - fee

        # 更新峰值余额
        if self.balance > self.stats["peak_balance"]:
            self.stats["peak_balance"] = self.balance

        # 计算最大回撤
        drawdown = (
            self.stats["peak_balance"] - self.balance
        ) / self.stats["peak_balance"]
        if drawdown > self.stats["max_drawdown"]:
            self.stats["max_drawdown"] = drawdown

        result["order_id"] = order_id
        result["available_balance"] = self.available_balance

        if self.enable_logging:
            logger.info(
                f"模拟订单执行: {side} {quantity} {symbol} @ "
                f"{result['exec_price']:.2f} (滑点: {result['slippage_bps']:.2f}bps)"
            )

        return result

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告

        Returns:
            性能报告字典
        """
        total_trades = self.stats["total_trades"]
        win_rate = (
            self.stats["winning_trades"] / total_trades
            if total_trades > 0 else 0
        )

        return {
            "mode": self.mode.value,
            "initial_balance": self.initial_balance,
            "current_balance": self.balance,
            "available_balance": self.available_balance,
            "total_pnl": self.stats["total_pnl"],
            "total_trades": total_trades,
            "winning_trades": self.stats["winning_trades"],
            "losing_trades": self.stats["losing_trades"],
            "win_rate": win_rate,
            "total_volume": self.stats["total_volume"],
            "total_fees": self.stats["total_fees"],
            "max_drawdown": self.stats["max_drawdown"],
            "positions": list(self.positions.values()),
        }

    def reset(self) -> None:
        """重置模拟交易引擎"""
        self.balance = self.initial_balance
        self.available_balance = self.initial_balance
        self.positions.clear()
        self.orders.clear()
        self.order_history.clear()
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "total_volume": 0.0,
            "total_fees": 0.0,
            "max_drawdown": 0.0,
            "peak_balance": self.initial_balance,
        }
        self.order_id_counter = 0

        logger.info("模拟交易引擎已重置")