"""执行增强、风险监控与组合优化 V97.0 - Phase 41

核心功能：
- ExecutionEnhancement: 执行增强(智能订单路由/滑点控制/部分成交)
- RiskMonitoring: 风险监控(实时VaR/杠杆监控/异常检测/熔断)
- PortfolioOptimization: 组合优化(动态再平衡/相关性调整/风险预算)

创建时间：2026-05-09 08:02
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import random
import math


# ============ 枚举定义 ============

class ExecutionStrategy(Enum):
    """执行策略"""
    IMMEDIATE = "immediate"
    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"
    TWAP = "twap"
    VWAP = "vwap"
    ADAPTIVE = "adaptive"


class MarketCondition(Enum):
    """市场条件"""
    NORMAL = "normal"
    VOLATILE = "volatile"
    ILLIQUID = "illiquid"
    TRENDING = "trending"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """告警类型"""
    POSITION_LIMIT = "position_limit"
    LOSS_LIMIT = "loss_limit"
    LEVERAGE_LIMIT = "leverage_limit"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAK = "correlation_break"
    CIRCUIT_BREAKER = "circuit_breaker"


class RebalanceTrigger(Enum):
    """再平衡触发器"""
    TIME_BASED = "time_based"
    THRESHOLD_BASED = "threshold_based"
    VOLATILITY_BASED = "volatility_based"
    RISK_BASED = "risk_based"


# ============ 数据结构 ============

@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    order_id: str
    filled_quantity: float
    avg_price: float
    slippage: float
    fees: float
    duration: float


@dataclass
class RiskAlert:
    """风险告警"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskMetrics:
    """风险指标"""
    portfolio_var_95: float
    portfolio_var_99: float
    leverage: float
    beta: float
    correlation: float
    concentration: float


@dataclass
class PortfolioAllocation:
    """组合配置"""
    asset: str
    target_weight: float
    current_weight: float
    adjustment: float
    risk_contribution: float


# ============ ExecutionEnhancement ============

class ExecutionEnhancement:
    """执行增强引擎"""

    def __init__(self):
        self._executions: List[ExecutionResult] = []
        self._strategy: ExecutionStrategy = ExecutionStrategy.ADAPTIVE
        self._max_slippage: float = 0.001  # 0.1% 最大滑点
        self._split_orders: int = 1

    def set_strategy(self, strategy: ExecutionStrategy) -> None:
        self._strategy = strategy

    def get_strategy(self) -> ExecutionStrategy:
        return self._strategy

    def calculate_slippage(self, side: str, market_volatility: float) -> float:
        """计算滑点"""
        base_slippage = 0.0002  # 0.02% 基础滑点

        if side == "buy":
            slippage = base_slippage * (1 + market_volatility)
        else:
            slippage = base_slippage * (1 + market_volatility) * 1.1

        return min(slippage, self._max_slippage)

    def smart_order_routing(self, symbol: str, quantity: float,
                          market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """智能订单路由"""
        # 根据市场条件选择最佳交易所/价格
        venues = market_conditions.get("venues", [])

        if not venues:
            # 模拟默认路由
            best_venue = {
                "name": "simulated",
                "price": market_conditions.get("base_price", 100),
                "liquidity": 1000000,
                "fee": 0.0004
            }
        else:
            # 选择最佳流动性
            best_venue = min(venues, key=lambda x: x.get("fee", 0.001))

        return {
            "venue": best_venue.get("name", "unknown"),
            "quoted_price": best_venue.get("price", 0),
            "liquidity": best_venue.get("liquidity", 0),
            "fee": best_venue.get("fee", 0)
        }

    def execute_with_slippage_control(self, symbol: str, side: str,
                                     quantity: float, limit_price: float,
                                     market_volatility: float = 0.01) -> Dict[str, Any]:
        """带滑点控制的执行"""
        slippage = self.calculate_slippage(side, market_volatility)

        if side == "buy":
            max_price = limit_price * (1 + slippage)
            fill_price = limit_price + limit_price * slippage
        else:
            max_price = limit_price * (1 - slippage)
            fill_price = limit_price - limit_price * slippage

        # 检查是否可成交
        if fill_price > max_price:
            return {
                "success": False,
                "reason": "slippage_exceeded",
                "slippage": slippage
            }

        fees = quantity * fill_price * 0.0004

        result = ExecutionResult(
            success=True,
            order_id=f"EXEC_{random.randint(100000, 999999)}",
            filled_quantity=quantity,
            avg_price=fill_price,
            slippage=slippage,
            fees=fees,
            duration=random.uniform(0.1, 1.0)
        )
        self._executions.append(result)

        return {
            "success": True,
            "order_id": result.order_id,
            "filled_quantity": result.filled_quantity,
            "avg_price": result.avg_price,
            "slippage": f"{result.slippage:.4f}",
            "fees": result.fees,
            "duration": f"{result.duration:.2f}s"
        }

    def TWAP_execution(self, symbol: str, side: str, total_quantity: float,
                    num_slices: int = 10, duration_minutes: int = 60) -> Dict[str, Any]:
        """TWAP分时执行"""
        slice_quantity = total_quantity / num_slices
        slices = []

        for i in range(num_slices):
            price_adjustment = random.uniform(-0.002, 0.002)
            slice_price = total_quantity * (1 + price_adjustment)

            slices.append({
                "slice": i + 1,
                "quantity": slice_quantity,
                "target_price": slice_price,
                "executed": True
            })

        return {
            "strategy": "TWAP",
            "total_quantity": total_quantity,
            "num_slices": num_slices,
            "slices": slices,
            "avg_fill": sum(s["target_price"] for s in slices) / len(slices),
            "completion": "100%"
        }

    def VWAP_execution(self, symbol: str, side: str, quantity: float,
                    volume_profile: List[float]) -> Dict[str, Any]:
        """VWAP加权执行"""
        if not volume_profile:
            volume_profile = [random.uniform(0.01, 0.1) for _ in range(10)]

        total_volume = sum(volume_profile)
        weights = [v / total_volume for v in volume_profile]

        executed = []
        for i, weight in enumerate(weights):
            exec_qty = quantity * weight
            executed.append({
                "period": i + 1,
                "weight": f"{weight:.2%}",
                "executed": exec_qty
            })

        return {
            "strategy": "VWAP",
            "total_quantity": quantity,
            "periods": len(volume_profile),
            "execution": executed,
            "completion": "100%"
        }

    def partial_fill_handling(self, symbol: str, side: str,
                          requested: float, filled: float,
                          remaining: float) -> Dict[str, Any]:
        """部分成交处理"""
        fill_rate = filled / requested if requested > 0 else 0

        if remaining > 0 and fill_rate < 0.5:
            action = "cancel_remaining"
        elif remaining > 0:
            action = "submit_rest"
        else:
            action = "complete"

        return {
            "requested": requested,
            "filled": filled,
            "remaining": remaining,
            "fill_rate": f"{fill_rate:.2%}",
            "action": action
        }

    def get_execution_summary(self) -> Dict[str, Any]:
        if not self._executions:
            return {"total_executions": 0}

        total_slippage = sum(e.slippage for e in self._executions)
        total_fees = sum(e.fees for e in self._executions)

        return {
            "total_executions": len(self._executions),
            "avg_slippage": total_slippage / len(self._executions),
            "total_fees": total_fees,
            "strategy": self._strategy.value
        }


# ============ RiskMonitoring ============

class RiskMonitoring:
    """风险监控系统"""

    def __init__(self):
        self._alerts: List[RiskAlert] = []
        self._daily_pnl: float = 0.0
        self._circuit_breaker_triggered: bool = False

    def calculate_real_time_var(self, positions: Dict[str, Any],
                              confidence: float = 0.95) -> Dict[str, Any]:
        """实时VaR计算"""
        var_95 = 0.0
        var_99 = 0.0

        for symbol, pos in positions.items():
            vol = pos.get("volatility", 0.02)
            value = pos.get("value", 0)

            # 简化VaR计算
            if confidence >= 0.95:
                var_95 += value * vol * 1.645
            if confidence >= 0.99:
                var_99 += value * vol * 2.326

        return {
            "var_95": round(var_95, 2),
            "var_99": round(var_99, 2),
            "confidence": confidence,
            "positions": len(positions)
        }

    def monitor_leverage(self, total_equity: float, total_exposure: float) -> Dict[str, Any]:
        """杠杆监控"""
        leverage = total_exposure / total_equity if total_equity > 0 else 0

        if leverage > 3.0:
            level = RiskLevel.CRITICAL.value
            action = "reduce_exposure"
        elif leverage > 2.0:
            level = RiskLevel.HIGH.value
            action = "warning"
        elif leverage > 1.0:
            level = RiskLevel.MEDIUM.value
            action = "monitor"
        else:
            level = RiskLevel.LOW.value
            action = "normal"

        return {
            "leverage": round(leverage, 2),
            "level": level,
            "action": action
        }

    def detect_anomaly(self, prices: List[float], threshold: float = 3.0) -> Dict[str, Any]:
        """异常检测"""
        if len(prices) < 20:
            return {"anomaly": False}

        mean = sum(prices) / len(prices)
        std = math.sqrt(sum((p - mean) ** 2 for p in prices) / len(prices))

        recent_price = prices[-1]
        z_score = abs(recent_price - mean) / std if std > 0 else 0

        if z_score > threshold:
            return {
                "anomaly": True,
                "z_score": round(z_score, 2),
                "severity": "high" if z_score > 4 else "medium",
                "direction": "up" if recent_price > mean else "down"
            }

        return {"anomaly": False, "z_score": round(z_score, 2)}

    def check_circuit_breaker(self, daily_pnl: float, limit: float = -0.05) -> Dict[str, Any]:
        """熔断检查"""
        self._daily_pnl = daily_pnl

        if daily_pnl < limit * 100000:  # 假设100k基准
            self._circuit_breaker_triggered = True
            return {
                "triggered": True,
                "daily_pnl": daily_pnl,
                "limit": limit,
                "action": "halt_trading"
            }

        return {
            "triggered": False,
            "daily_pnl": daily_pnl,
            "status": "active"
        }

    def track_daily_loss(self, pnl: float, max_loss: float = 50000) -> Dict[str, Any]:
        """每日亏损追踪"""
        self._daily_pnl += pnl

        remaining = max_loss + self._daily_pnl
        used_pct = abs(self._daily_pnl) / max_loss if self._daily_pnl < 0 else 0

        return {
            "daily_pnl": round(self._daily_pnl, 2),
            "remaining": round(remaining, 2),
            "utilization": f"{used_pct:.1%}",
            "status": "halt" if self._daily_pnl < -max_loss else "active"
        }

    def create_alert(self, alert_type: str, severity: str,
                    message: str, metadata: Dict[str, Any] = None) -> RiskAlert:
        """创建告警"""
        alert = RiskAlert(
            alert_id=f"ALERT_{random.randint(10000, 99999)}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self._alerts.append(alert)
        return alert

    def get_active_alerts(self) -> List[RiskAlert]:
        """获取活跃告警"""
        return [a for a in self._alerts if a.severity in ["high", "critical"]]

    def get_risk_summary(self) -> Dict[str, Any]:
        return {
            "active_alerts": len(self.get_active_alerts()),
            "total_alerts": len(self._alerts),
            "daily_pnl": round(self._daily_pnl, 2),
            "circuit_breaker": self._circuit_breaker_triggered
        }


# ============ PortfolioOptimization ============

class PortfolioOptimization:
    """组合优化器"""

    def __init__(self):
        self._allocations: Dict[str, PortfolioAllocation] = {}
        self._rebalance_count: int = 0

    def calculate_optimal_weights(self, expected_returns: Dict[str, float],
                              volatilities: Dict[str, float],
                              correlations: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """计算最优权重"""
        assets = list(expected_returns.keys())
        n = len(assets)

        if n == 0:
            return {}

        # 简化均值-方差优化
        total = 0
        weights = {}

        for asset in assets:
            ret = expected_returns[asset]
            vol = volatilities.get(asset, 0.01)

            # 简化的夏普比率权重
            if vol > 0:
                weight = ret / vol
            else:
                weight = 0

            weights[asset] = weight
            total += weight

        # 归一化
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def dynamic_rebalance(self, current_weights: Dict[str, float],
                        target_weights: Dict[str, float],
                        threshold: float = 0.05) -> Dict[str, Any]:
        """动态再平衡"""
        adjustments = {}
        total_adjustment = 0

        for asset in target_weights:
            diff = target_weights[asset] - current_weights.get(asset, 0)
            if abs(diff) > threshold:
                adjustments[asset] = diff
                total_adjustment += abs(diff)

        needs_rebalance = total_adjustment > threshold

        return {
            "needs_rebalance": needs_rebalance,
            "adjustments": adjustments,
            "total_adjustment": round(total_adjustment, 4),
            "trigger": "threshold" if needs_rebalance else "none"
        }

    def risk_budget_allocation(self, portfolio_value: float,
                            risk_contributions: Dict[str, float],
                            max_risk: float = 0.02) -> Dict[str, Any]:
        """风险预算配置"""
        total_risk = sum(risk_contributions.values())
        budget = portfolio_value * max_risk

        allocations = {}
        for asset, risk in risk_contributions.items():
            allocation = budget * (risk / total_risk) if total_risk > 0 else 0
            allocations[asset] = allocation

        return {
            "total_budget": budget,
            "allocations": allocations,
            "utilization": f"{(total_risk / max_risk):.1%}" if max_risk > 0 else "N/A",
            "status": "within_limit" if total_risk <= max_risk else "exceeded"
        }

    def correlate_adjustment(self, weights: Dict[str, float],
                         correlations: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """相关性调整"""
        adjusted = weights.copy()

        # 降低高相关性资产权重
        for asset1 in weights:
            for asset2 in weights:
                if asset1 != asset2:
                    corr = correlations.get(asset1, {}).get(asset2, 0)
                    if corr > 0.7:
                        # 降低相关性高的资产权重
                        adjusted[asset1] *= (1 - corr * 0.3)

        # 重新归一化
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}

        return adjusted

    def execute_rebalance(self, current_weights: Dict[str, float],
                        target_weights: Dict[str, float],
                        positions: Dict[str, Dict]) -> Dict[str, Any]:
        """执行再平衡"""
        self._rebalance_count += 1

        trades = []
        for asset in target_weights:
            diff = target_weights[asset] - current_weights.get(asset, 0)
            value = positions.get(asset, {}).get("value", 0)
            quantity = diff * value if value > 0 else 0

            if abs(quantity) > 0.01:
                trades.append({
                    "asset": asset,
                    "action": "buy" if diff > 0 else "sell",
                    "quantity": round(quantity, 4),
                    "reason": "rebalance"
                })

        return {
            "rebalance_id": f"REB_{self._rebalance_count:06d}",
            "trades": trades,
            "num_trades": len(trades)
        }

    def get_allocation_report(self) -> Dict[str, Any]:
        return {
            "assets": list(self._allocations.keys()),
            "count": len(self._allocations),
            "rebalances": self._rebalance_count
        }


# ============ 全局实例管理 ============

_execution_enhancement: Optional[ExecutionEnhancement] = None
_risk_monitoring: Optional[RiskMonitoring] = None
_portfolio_optimization: Optional[PortfolioOptimization] = None


def get_execution_enhancement() -> ExecutionEnhancement:
    global _execution_enhancement
    if _execution_enhancement is None:
        _execution_enhancement = ExecutionEnhancement()
    return _execution_enhancement


def initialize_execution_enhancement() -> None:
    global _execution_enhancement
    _execution_enhancement = ExecutionEnhancement()


def get_risk_monitoring() -> RiskMonitoring:
    global _risk_monitoring
    if _risk_monitoring is None:
        _risk_monitoring = RiskMonitoring()
    return _risk_monitoring


def initialize_risk_monitoring() -> None:
    global _risk_monitoring
    _risk_monitoring = RiskMonitoring()


def get_portfolio_optimization() -> PortfolioOptimization:
    global _portfolio_optimization
    if _portfolio_optimization is None:
        _portfolio_optimization = PortfolioOptimization()
    return _portfolio_optimization


def initialize_portfolio_optimization() -> None:
    global _portfolio_optimization
    _portfolio_optimization = PortfolioOptimization()