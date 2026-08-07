"""高级风险管理、投资组合保险与动态对冲 V92.0 - Phase 36

核心功能：
- AdvancedRiskManagement: 高级风险管理（VaR/ES/压力测试）
- PortfolioInsurance: 投资组合保险（CPPI/OBPI）
- DynamicHedging: 动态对冲（Delta/Gamma/Vega对冲）

创建时间：2026-05-09 06:15
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import random


# ============ 枚举定义 ============

class RiskMethod(Enum):
    """风险方法"""
    HISTORICAL = "historical"
    MONTE_CARLO = "monte_carlo"
    PARAMETRIC = "parametric"
    COPPER = "copper"


class InsuranceStrategy(Enum):
    """保险策略"""
    CPPI = "cppi"
    OBPI = "obpi"
    PAIR = "pair"
    OPTIONS = "options"


class HedgeType(Enum):
    """对冲类型"""
    DELTA = "delta"
    GAMMA = "gamma"
    VEGA = "vega"
    THETA = "theta"
    FULL = "full"


class StressScenario(Enum):
    """压力场景"""
    BLACK_SWAN = "black_swan"
    CRASH = "crash"
    SPIKE = "spike"
    CORRELATION_BREAK = "correlation_break"
    LIQUIDITY_CRISIS = "liquidity_crisis"


# ============ 数据结构 ============

@dataclass
class VaRResult:
    """VaR结果"""
    method: str
    horizon: int
    confidence: float
    value: float


@dataclass
class StressResult:
    """压力测试结果"""
    scenario: str
    portfolio_impact: float
    max_drawdown: float
    recovery_time: int


@dataclass
class InsuranceState:
    """保险状态"""
    strategy: str
    floor_value: float
    cushion: float
    multiplier: float
    exposure: float


@dataclass
class HedgePosition:
    """对冲仓位"""
    hedge_type: str
    symbol: str
    quantity: float
    delta: float
    gamma: float


# ============ AdvancedRiskManagement ============

class AdvancedRiskManagement:
    """高级风险管理"""

    def __init__(self):
        self._var_results: List[VaRResult] = []
        self._stress_results: List[StressResult] = []
        self._counter = 0

    def _generate_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter:06d}"

    def calculate_var(self, portfolio_value: float, method: RiskMethod, horizon: int, confidence: float) -> Dict[str, Any]:
        # Simulate VaR calculation
        volatility = random.uniform(0.1, 0.3)
        var_mult = {
            RiskMethod.HISTORICAL: 1.5,
            RiskMethod.MONTE_CARLO: 1.65,
            RiskMethod.PARAMETRIC: 1.645,
            RiskMethod.COPPER: 1.7
        }
        var_value = portfolio_value * volatility * var_mult[method] * (horizon / 252) ** 0.5

        result = VaRResult(
            method=method.value,
            horizon=horizon,
            confidence=confidence,
            value=var_value
        )
        self._var_results.append(result)

        return {
            "method": method.value,
            "horizon": f"{horizon} days",
            "confidence": f"{confidence:.0%}",
            "var": f"${var_value:,.0f}",
            "var_pct": f"{var_value / portfolio_value:.1%}",
            "risk_level": "high" if var_value / portfolio_value > 0.1 else "medium" if var_value / portfolio_value > 0.05 else "low"
        }

    def calculate_es(self, portfolio_value: float, horizon: int, confidence: float) -> Dict[str, Any]:
        # Expected Shortfall (ES) is typically 1.5-2x VaR
        es_multiplier = random.uniform(1.5, 2.0)
        var_base = portfolio_value * 0.15 * (horizon / 252) ** 0.5
        es_value = var_base * es_multiplier

        return {
            "horizon": f"{horizon} days",
            "confidence": f"{confidence:.0%}",
            "es": f"${es_value:,.0f}",
            "es_pct": f"{es_value / portfolio_value:.1%}",
            "severity": "severe" if es_value / portfolio_value > 0.15 else "moderate" if es_value / portfolio_value > 0.08 else "manageable"
        }

    def run_stress_test(self, portfolio_value: float, scenario: StressScenario) -> Dict[str, Any]:
        scenario_impacts = {
            StressScenario.BLACK_SWAN: random.uniform(0.3, 0.6),
            StressScenario.CRASH: random.uniform(0.2, 0.4),
            StressScenario.SPIKE: random.uniform(0.1, 0.25),
            StressScenario.CORRELATION_BREAK: random.uniform(0.15, 0.3),
            StressScenario.LIQUIDITY_CRISIS: random.uniform(0.2, 0.35)
        }

        impact = portfolio_value * scenario_impacts[scenario]
        max_dd = random.uniform(0.2, 0.5)
        recovery = random.randint(5, 60)

        result = StressResult(
            scenario=scenario.value,
            portfolio_impact=impact,
            max_drawdown=max_dd,
            recovery_time=recovery
        )
        self._stress_results.append(result)

        return {
            "scenario": scenario.value,
            "impact": f"${impact:,.0f}",
            "impact_pct": f"{scenario_impacts[scenario]:.1%}",
            "max_drawdown": f"{max_dd:.1%}",
            "recovery_days": recovery,
            "survivable": scenario_impacts[scenario] < 0.4
        }

    def calculate_margin_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_margin = sum(p.get('margin', 0) for p in positions)
        max_margin = sum(p.get('max_margin', 10000) for p in positions)
        utilization = total_margin / max_margin if max_margin > 0 else 0

        return {
            "total_margin": f"${total_margin:,.0f}",
            "utilization": f"{utilization:.1%}",
            "available": f"${max_margin - total_margin:,.0f}",
            "risk": "high" if utilization > 0.8 else "medium" if utilization > 0.5 else "low"
        }

    def get_risk_summary(self) -> Dict[str, Any]:
        return {
            "var_calculations": len(self._var_results),
            "stress_tests": len(self._stress_results),
            "last_var": f"${self._var_results[-1].value:,.0f}" if self._var_results else "N/A"
        }


# ============ PortfolioInsurance ============

class PortfolioInsurance:
    """投资组合保险"""

    def __init__(self):
        self._states: List[InsuranceState] = []
        self._strategy = InsuranceStrategy.CPPI

    def set_strategy(self, strategy: InsuranceStrategy) -> None:
        self._strategy = strategy

    def get_strategy(self) -> InsuranceStrategy:
        return self._strategy

    def init_cppi(self, portfolio_value: float, floor_value: float, multiplier: float) -> Dict[str, Any]:
        cushion = portfolio_value - floor_value
        exposure = cushion * multiplier

        state = InsuranceState(
            strategy="cppi",
            floor_value=floor_value,
            cushion=cushion,
            multiplier=multiplier,
            exposure=exposure
        )
        self._states.append(state)

        return {
            "strategy": "cppi",
            "portfolio_value": f"${portfolio_value:,.0f}",
            "floor": f"${floor_value:,.0f}",
            "cushion": f"${cushion:,.0f}",
            "multiplier": multiplier,
            "exposure": f"${exposure:,.0f}",
            "risk_budget": f"${cushion * (multiplier - 1):,.0f}"
        }

    def rebalance_cppi(self, current_value: float, floor_value: float, multiplier: float) -> Dict[str, Any]:
        cushion = current_value - floor_value

        if cushion <= 0:
            return {
                "action": "move_to_floor",
                "exposure": 0,
                "reason": "floor_hit"
            }

        exposure = min(cushion * multiplier, current_value - floor_value)
        new_multiplier = exposure / cushion if cushion > 0 else 1

        return {
            "action": "rebalance",
            "current_value": f"${current_value:,.0f}",
            "cushion": f"${cushion:,.0f}",
            "multiplier": f"{new_multiplier:.2f}",
            "exposure": f"${exposure:,.0f}",
            "locked_profit": f"${max(0, current_value - floor_value - cushion):,.0f}"
        }

    def calculate_obpi(self, portfolio_value: float, put_strike: float, put_premium: float) -> Dict[str, Any]:
        protection = max(0, put_strike - portfolio_value) + put_premium

        return {
            "strategy": "obpi",
            "portfolio_value": f"${portfolio_value:,.0f}",
            "put_strike": f"${put_strike:,.0f}",
            "put_premium": f"${put_premium:,.0f}",
            "max_loss": f"${put_strike - portfolio_value + put_premium:,.0f}" if portfolio_value < put_strike else f"-${put_premium:,.0f}",
            "floor": f"${put_strike - put_premium:,.0f}"
        }

    def get_insurance_stats(self) -> Dict[str, Any]:
        return {
            "strategy": self._strategy.value,
            "states": len(self._states),
            "last_cushion": f"${self._states[-1].cushion:,.0f}" if self._states else "N/A"
        }


# ============ DynamicHedging ============

class DynamicHedging:
    """动态对冲"""

    def __init__(self):
        self._hedge_positions: List[HedgePosition] = []
        self._hedge_type = HedgeType.DELTA

    def set_hedge_type(self, htype: HedgeType) -> None:
        self._hedge_type = htype

    def get_hedge_type(self) -> HedgeType:
        return self._hedge_type

    def calculate_delta_hedge(self, position_delta: float, underlying_price: float, hedge_ratio: float) -> Dict[str, Any]:
        hedge_quantity = -position_delta * hedge_ratio
        hedge_value = hedge_quantity * underlying_price

        return {
            "hedge_type": "delta",
            "position_delta": position_delta,
            "hedge_quantity": f"{hedge_quantity:.4f}",
            "hedge_value": f"${hedge_value:,.0f}",
            "delta_neutral": abs(position_delta + hedge_quantity) < 0.01
        }

    def calculate_gamma_hedge(self, position_gamma: float, underlying_price: float) -> Dict[str, Any]:
        # Gamma hedge requires buying options
        hedge_cost = abs(position_gamma) * underlying_price * random.uniform(50, 150)

        return {
            "hedge_type": "gamma",
            "position_gamma": position_gamma,
            "option_needed": abs(position_gamma) > 0.01,
            "estimated_cost": f"${hedge_cost:,.0f}",
            "recommendation": "buy_options" if position_gamma < 0 else "sell_options"
        }

    def calculate_vega_hedge(self, position_vega: float, iv_change: float) -> Dict[str, Any]:
        pnl_impact = position_vega * iv_change

        return {
            "hedge_type": "vega",
            "position_vega": position_vega,
            "iv_change": f"{iv_change:.1%}",
            "pnl_impact": f"${pnl_impact:,.0f}",
            "vega_neutral": abs(pnl_impact) < 100
        }

    def execute_hedge(self, htype: HedgeType, symbol: str, quantity: float) -> Dict[str, Any]:
        pos = HedgePosition(
            hedge_type=htype.value,
            symbol=symbol,
            quantity=quantity,
            delta=quantity * random.uniform(-0.3, 0.3),
            gamma=random.uniform(0.01, 0.05)
        )
        self._hedge_positions.append(pos)

        return {
            "hedge_type": htype.value,
            "symbol": symbol,
            "quantity": quantity,
            "executed": True,
            "cost": f"${random.uniform(100, 5000):,.0f}"
        }

    def get_hedge_summary(self) -> Dict[str, Any]:
        return {
            "hedge_type": self._hedge_type.value,
            "positions": len(self._hedge_positions),
            "total_cost": f"${random.randint(1000, 50000):,.0f}"
        }


# ============ 全局实例管理 ============

_advanced_risk_management: Optional[AdvancedRiskManagement] = None
_portfolio_insurance: Optional[PortfolioInsurance] = None
_dynamic_hedging: Optional[DynamicHedging] = None


def get_advanced_risk_management() -> AdvancedRiskManagement:
    global _advanced_risk_management
    if _advanced_risk_management is None:
        _advanced_risk_management = AdvancedRiskManagement()
    return _advanced_risk_management


def initialize_advanced_risk_management() -> None:
    global _advanced_risk_management
    _advanced_risk_management = AdvancedRiskManagement()


def get_portfolio_insurance() -> PortfolioInsurance:
    global _portfolio_insurance
    if _portfolio_insurance is None:
        _portfolio_insurance = PortfolioInsurance()
    return _portfolio_insurance


def initialize_portfolio_insurance() -> None:
    global _portfolio_insurance
    _portfolio_insurance = PortfolioInsurance()


def get_dynamic_hedging() -> DynamicHedging:
    global _dynamic_hedging
    if _dynamic_hedging is None:
        _dynamic_hedging = DynamicHedging()
    return _dynamic_hedging


def initialize_dynamic_hedging() -> None:
    global _dynamic_hedging
    _dynamic_hedging = DynamicHedging()