"""跨链执行、收益优化与风控自动化模块 V77.0 - Phase 21

核心功能：
- CrossChainExecutor: 跨链执行引擎
- YieldOptimizer: 收益优化器
- RiskAutomation: 风控自动化引擎
- CrossChainRoute: 跨链路由
- YieldPosition: 收益持仓
- RiskRule: 风控规则

创建时间：2026-05-09 01:10
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import math
import random


# ============ 枚举定义 ============

class ExecutionMode(Enum):
    """执行模式"""
    DIRECT = "direct"  # 直接执行
    AGGREGATOR = "aggregator"  # 聚合器
    ROUTED = "routed"  # 路由
    BRIDGED = "bridged"  # 桥接


class YieldSource(Enum):
    """收益来源"""
    STAKING = "staking"  # 质押
    Lending = "lending"  # 借贷
    Farming = "farming"  # 流动性挖矿
    Vault = "vault"  # 收益vault
    BOND = "bond"  # 债券


class RiskTriggerType(Enum):
    """风险触发类型"""
    PRICE_THRESHOLD = "price_threshold"
    VOLATILITY = "volatility"
    LIQUIDATION = "liquidation"
    CONCENTRATION = "concentration"
    CORRELATION = "correlation"


class RiskActionType(Enum):
    """风控行动类型"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    REDUCE_POSITION = "reduce_position"
    HEDGE = "hedge"
    EMERGENCY_EXIT = "emergency_exit"
    NOTIFY = "notify"


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    SIGNED = "signed"
    BROADCAST = "broadcast"
    CONFIRMED = "confirmed"
    FAILED = "failed"


# ============ 数据结构 ============

@dataclass
class CrossChainRoute:
    """跨链路由"""
    route_id: str
    from_chain: str
    to_chain: str
    protocol: str  # LayerZero, Axelar, Wormhole, Stargate
    estimated_time: float  # 秒
    estimated_fee: float
    slippage: float
    success_rate: float


@dataclass
class ExecutionOrder:
    """执行订单"""
    order_id: str
    from_address: str
    to_address: str
    token: str
    amount: float
    mode: ExecutionMode
    deadline: datetime
    status: ExecutionStatus = ExecutionStatus.PENDING
    tx_hash: str = ""
    confirmed_at: Optional[datetime] = None
    error: str = ""


@dataclass
class YieldPosition:
    """收益持仓"""
    position_id: str
    pool_id: str
    source: YieldSource
    token: str
    deposited: float
    earned: float
    apy: float
    deposit_time: datetime
    lock_period: int = 0  # 天


@dataclass
class YieldStrategy:
    """收益策略"""
    strategy_id: str
    name: str
    protocol: str
    source: YieldSource
    token_pairs: List[str]
    base_apy: float
    boosted_apy: float
    min_deposit: float
    risk_level: float  # 0-1


@dataclass
class RiskRule:
    """风控规则"""
    rule_id: str
    name: str
    trigger_type: RiskTriggerType
    trigger_value: float
    action_type: RiskActionType
    action_value: float
    enabled: bool = True
    cooldown: int = 300  # 秒


@dataclass
class RiskEvent:
    """风控事件"""
    event_id: str
    rule_id: str
    trigger_type: RiskTriggerType
    action_type: RiskActionType
    details: Dict[str, Any]
    triggered_at: datetime
    executed: bool = False
    executed_at: Optional[datetime] = None


# ============ CrossChainExecutor ============

class CrossChainExecutor:
    """跨链执行引擎"""

    def __init__(self):
        self._routes: Dict[str, CrossChainRoute] = {}
        self._orders: Dict[str, ExecutionOrder] = {}
        self._default_protocols = ["LayerZero", "Axelar", "Wormhole", "Stargate"]
        self._initialize_default_routes()

    def _initialize_default_routes(self):
        """初始化默认路由"""
        default_routes = [
            CrossChainRoute("eth→arb", "eth", "arb", "LayerZero", 300, 0.005, 0.001, 0.95),
            CrossChainRoute("arb→eth", "arb", "eth", "LayerZero", 300, 0.005, 0.001, 0.95),
            CrossChainRoute("eth→avax", "eth", "avax", "Axelar", 600, 0.008, 0.002, 0.90),
            CrossChainRoute("avax→eth", "avax", "eth", "Axelar", 600, 0.008, 0.002, 0.90),
            CrossChainRoute("eth→polygon", "eth", "polygon", "Stargate", 120, 0.002, 0.0005, 0.98),
            CrossChainRoute("polygon→eth", "polygon", "eth", "Stargate", 120, 0.002, 0.0005, 0.98),
        ]
        for route in default_routes:
            self._routes[route.route_id] = route

    def get_route(self, from_chain: str, to_chain: str) -> Optional[CrossChainRoute]:
        """获取最佳路由"""
        route_id = f"{from_chain}→{to_chain}"
        return self._routes.get(route_id)

    def find_best_route(self, from_chain: str, to_chain: str) -> Optional[CrossChainRoute]:
        """查找最佳路由(最低成本)"""
        candidates = [r for r in self._routes.values()
                     if r.from_chain == from_chain and r.to_chain == to_chain]
        if not candidates:
            return None
        # 按成本排序(estimated_fee + slippage)
        return min(candidates, key=lambda r: r.estimated_fee + r.slippage)

    def create_order(
        self,
        order_id: str,
        from_address: str,
        to_address: str,
        token: str,
        amount: float,
        mode: ExecutionMode,
        from_chain: str,
        to_chain: str,
        deadline_seconds: int = 3600
    ) -> ExecutionOrder:
        """创建执行订单"""
        order = ExecutionOrder(
            order_id=order_id,
            from_address=from_address,
            to_address=to_address,
            token=token,
            amount=amount,
            mode=mode,
            deadline=datetime.now() + timedelta(seconds=deadline_seconds)
        )
        self._orders[order_id] = order
        return order

    def sign_order(self, order_id: str, tx_hash: str) -> bool:
        """签名订单"""
        if order_id not in self._orders:
            return False
        self._orders[order_id].status = ExecutionStatus.SIGNED
        self._orders[order_id].tx_hash = tx_hash
        return True

    def broadcast_order(self, order_id: str) -> bool:
        """广播订单"""
        if order_id not in self._orders:
            return False
        self._orders[order_id].status = ExecutionStatus.BROADCAST
        return True

    def confirm_order(self, order_id: str) -> bool:
        """确认订单"""
        if order_id not in self._orders:
            return False
        self._orders[order_id].status = ExecutionStatus.CONFIRMED
        self._orders[order_id].confirmed_at = datetime.now()
        return True

    def fail_order(self, order_id: str, error: str) -> bool:
        """订单失败"""
        if order_id not in self._orders:
            return False
        self._orders[order_id].status = ExecutionStatus.FAILED
        self._orders[order_id].error = error
        return True

    def get_order(self, order_id: str) -> Optional[ExecutionOrder]:
        """获取订单"""
        return self._orders.get(order_id)

    def get_pending_orders(self) -> List[ExecutionOrder]:
        """获取待处理订单"""
        return [o for o in self._orders.values()
                if o.status == ExecutionStatus.PENDING]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = len(self._orders)
        confirmed = len([o for o in self._orders.values()
                        if o.status == ExecutionStatus.CONFIRMED])
        failed = len([o for o in self._orders.values()
                   if o.status == ExecutionStatus.FAILED])
        return {
            "total_orders": total,
            "confirmed": confirmed,
            "failed": failed,
            "pending": total - confirmed - failed,
            "success_rate": confirmed / total if total > 0 else 0
        }


# ============ YieldOptimizer ============

class YieldOptimizer:
    """收益优化器"""

    def __init__(self):
        self._strategies: Dict[str, YieldStrategy] = {}
        self._positions: Dict[str, YieldPosition] = {}
        self._initialize_default_strategies()

    def _initialize_default_strategies(self):
        """初始化默认策略"""
        default_strategies = [
            YieldStrategy(
                "eth-staking", "ETH Staking", "Lido", YieldSource.STAKING,
                ["ETH"], 0.05, 0.08, 0.01, 0.1
            ),
            YieldStrategy(
                "avax-yield", "Avalanche Yield", "Benqi", YieldSource.Lending,
                ["AVAX", "USDC"], 0.08, 0.12, 100, 0.3
            ),
            YieldStrategy(
                "uniswap-v3", "Uniswap V3 LP", "Uniswap", YieldSource.Farming,
                ["ETH/USDC", "ETH/USDT"], 0.20, 0.35, 1000, 0.6
            ),
            YieldStrategy(
                "aave-v3", "Aave V3", "Aave", YieldSource.Lending,
                ["USDC", "USDT", "ETH"], 0.06, 0.10, 100, 0.25
            ),
            YieldStrategy(
                "curve-3pool", "Curve 3Pool", "Curve", YieldSource.Vault,
                ["DAI/USDC/USDT"], 0.04, 0.06, 1000, 0.2
            ),
        ]
        for strategy in default_strategies:
            self._strategies[strategy.strategy_id] = strategy

    def get_strategy(self, strategy_id: str) -> Optional[YieldStrategy]:
        """获取策略"""
        return self._strategies.get(strategy_id)

    def get_all_strategies(self) -> List[YieldStrategy]:
        """获取所有策略"""
        return list(self._strategies.values())

    def find_best_strategy(
        self,
        token: str,
        amount: float,
        risk_tolerance: float = 0.5
    ) -> List[YieldStrategy]:
        """查找最佳策略"""
        candidates = [
            s for s in self._strategies.values()
            if token in s.token_pairs
            and amount >= s.min_deposit
            and s.risk_level <= risk_tolerance
        ]
        # 按收益率排序
        return sorted(candidates, key=lambda s: s.boosted_apy, reverse=True)

    def open_position(
        self,
        position_id: str,
        strategy_id: str,
        deposited: float
    ) -> Optional[YieldPosition]:
        """开仓"""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return None

        pos = YieldPosition(
            position_id=position_id,
            pool_id=strategy_id,
            source=strategy.source,
            token=strategy.token_pairs[0],
            deposited=deposited,
            earned=0.0,
            apy=strategy.boosted_apy,
            deposit_time=datetime.now()
        )
        self._positions[position_id] = pos
        return pos

    def claim_rewards(self, position_id: str) -> Optional[float]:
        """领取收益"""
        pos = self._positions.get(position_id)
        if not pos:
            return None
        rewards = pos.earned
        pos.earned = 0.0
        return rewards

    def close_position(self, position_id: str) -> Optional[float]:
        """平仓"""
        pos = self._positions.get(position_id)
        if not pos:
            return None
        total = pos.deposited + pos.earned
        del self._positions[position_id]
        return total

    def get_position(self, position_id: str) -> Optional[YieldPosition]:
        """获取持仓"""
        return self._positions.get(position_id)

    def get_all_positions(self) -> List[YieldPosition]:
        """获取所有持仓"""
        return list(self._positions.values())

    def get_total_earned(self) -> float:
        """获取总收益"""
        return sum(p.earned for p in self._positions.values())

    def get_total_deposited(self) -> float:
        """获取总质押"""
        return sum(p.deposited for p in self._positions.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total_apy = sum(p.apy for p in self._positions.values()) / len(self._positions) if self._positions else 0
        return {
            "total_positions": len(self._positions),
            "total_deposited": self.get_total_deposited(),
            "total_earned": self.get_total_earned(),
            "avg_apy": total_apy
        }


# ============ RiskAutomation ============

class RiskAutomation:
    """风控自动化引擎"""

    def __init__(self):
        self._rules: Dict[str, RiskRule] = {}
        self._events: Dict[str, RiskEvent] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """初始化默认规则"""
        default_rules = [
            RiskRule(
                "stop-loss-10%", "Stop Loss 10%", RiskTriggerType.PRICE_THRESHOLD,
                0.90, RiskActionType.STOP_LOSS, 0.10
            ),
            RiskRule(
                "take-profit-20%", "Take Profit 20%", RiskTriggerType.PRICE_THRESHOLD,
                1.20, RiskActionType.TAKE_PROFIT, 0.20
            ),
            RiskRule(
                "high-volatility", "High Volatility", RiskTriggerType.VOLATILITY,
                0.05, RiskActionType.REDUCE_POSITION, 0.50
            ),
            RiskRule(
                "liquidation-alert", "Liquidation Alert", RiskTriggerType.LIQUIDATION,
                0.80, RiskActionType.NOTIFY, 1.0
            ),
            RiskRule(
                "concentration-alert", "Concentration Alert", RiskTriggerType.CONCENTRATION,
                0.30, RiskActionType.REDUCE_POSITION, 0.30
            ),
        ]
        for rule in default_rules:
            self._rules[rule.rule_id] = rule

    def add_rule(self, rule: RiskRule) -> None:
        """添加规则"""
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[RiskRule]:
        """获取规则"""
        return self._rules.get(rule_id)

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False

    def check_trigger(
        self,
        trigger_type: RiskTriggerType,
        value: float
    ) -> List[RiskRule]:
        """检查触发"""
        triggered = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if rule.trigger_type == trigger_type:
                if trigger_type == RiskTriggerType.PRICE_THRESHOLD:
                    # 价格阈值: value >= trigger_value 触发
                    if value >= rule.trigger_value:
                        triggered.append(rule)
                elif trigger_type == RiskTriggerType.VOLATILITY:
                    # 波动率: value >= trigger_value 触发
                    if value >= rule.trigger_value:
                        triggered.append(rule)
                elif trigger_type == RiskTriggerType.LIQUIDATION:
                    # 清算风险: value <= trigger_value 触发
                    if value <= rule.trigger_value:
                        triggered.append(rule)
        return triggered

    def trigger_event(
        self,
        rule_id: str,
        details: Dict[str, Any]
    ) -> RiskEvent:
        """触发事件"""
        rule = self._rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        event = RiskEvent(
            event_id=f"evt_{len(self._events)}",
            rule_id=rule_id,
            trigger_type=rule.trigger_type,
            action_type=rule.action_type,
            details=details,
            triggered_at=datetime.now()
        )
        self._events[event.event_id] = event
        return event

    def execute_event(self, event_id: str) -> bool:
        """执行事件"""
        event = self._events.get(event_id)
        if not event or event.executed:
            return False
        event.executed = True
        event.executed_at = datetime.now()
        return True

    def get_pending_events(self) -> List[RiskEvent]:
        """获取待执行事件"""
        return [e for e in self._events.values() if not e.executed]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = len(self._events)
        executed = len([e for e in self._events.values() if e.executed])
        return {
            "total_rules": len(self._rules),
            "enabled_rules": len([r for r in self._rules.values() if r.enabled]),
            "total_events": total,
            "executed_events": executed,
            "pending_events": total - executed
        }


# ============ 全局实例管理 ============

_cross_chain_executor: Optional[CrossChainExecutor] = None
_yield_optimizer: Optional[YieldOptimizer] = None
_risk_automation: Optional[RiskAutomation] = None


def get_cross_chain_executor() -> CrossChainExecutor:
    """获取跨链执行器"""
    global _cross_chain_executor
    if _cross_chain_executor is None:
        _cross_chain_executor = CrossChainExecutor()
    return _cross_chain_executor


def initialize_cross_chain_executor() -> None:
    """初始化跨链执行器"""
    global _cross_chain_executor
    _cross_chain_executor = CrossChainExecutor()


def get_yield_optimizer() -> YieldOptimizer:
    """获取收益优化器"""
    global _yield_optimizer
    if _yield_optimizer is None:
        _yield_optimizer = YieldOptimizer()
    return _yield_optimizer


def initialize_yield_optimizer() -> None:
    """初始化收益优化器"""
    global _yield_optimizer
    _yield_optimizer = YieldOptimizer()


def get_risk_automation() -> RiskAutomation:
    """获取风控自动化"""
    global _risk_automation
    if _risk_automation is None:
        _risk_automation = RiskAutomation()
    return _risk_automation


def initialize_risk_automation() -> None:
    """初始化风控自动化"""
    global _risk_automation
    _risk_automation = RiskAutomation()


def create_cross_chain_route(
    route_id: str,
    from_chain: str,
    to_chain: str,
    protocol: str = "LayerZero",
    estimated_time: float = 300,
    estimated_fee: float = 0.005,
    slippage: float = 0.001,
    success_rate: float = 0.95
) -> CrossChainRoute:
    """创建跨链路由"""
    return CrossChainRoute(
        route_id=route_id,
        from_chain=from_chain,
        to_chain=to_chain,
        protocol=protocol,
        estimated_time=estimated_time,
        estimated_fee=estimated_fee,
        slippage=slippage,
        success_rate=success_rate
    )