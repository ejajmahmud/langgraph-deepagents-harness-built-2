"""
V105.0 - Portfolio Rebalance, Risk Parity & Smart Routing
====================================================

数字货币交易系统 V105.0 - 组合再平衡/风险平价/智能路由

版本: 5.1.0
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid
import random
import math

# === 枚举类型 ===

class RebalanceType(Enum):
    THRESHOLD = "threshold"
    TIME = "time"
    VOLATILITY = "volatility"
    RISK_PARITY = "risk_parity"


class AssetClass(Enum):
    CRYPTO = "crypto"
    STOCK = "stock"
    BOND = "bond"
    COMMODITY = "commodity"


class RouteAlgorithm(Enum):
    SHORTEST = "shortest"
    CHEAPEST = "cheapest"
    LIQUIDITY = "liquidity"
    BALANCED = "balanced"


# === 数据结构 ===

@dataclass
class PortfolioAsset:
    symbol: str
    asset_class: AssetClass
    weight: float
    value: float
    volatility: float
    return_hist: float


@dataclass
class RebalanceAction:
    action_id: str
    symbol: str
    from_weight: float
    to_weight: float
    amount: float
    reason: str


@dataclass
class RiskParityConfig:
    target_vol: float
    max_weight: float
    min_weight: float


@dataclass
class Route:
    path: List[str]
    cost: float
    hops: int
    confidence: float


@dataclass
class RouterConfig:
    max_hops: int
    allowed_dex: List[str]


# === Portfolio Rebalancer ===

class PortfolioRebalancerV105:
    def __init__(self, rebalance_type: RebalanceType = RebalanceType.THRESHOLD):
        self._type = rebalance_type
        self._assets: Dict[str, PortfolioAsset] = {}
        self._history: List[RebalanceAction] = []

    def add_asset(self, symbol: str, asset_class: AssetClass, weight: float,
                  value: float, volatility: float, return_hist: float):
        self._assets[symbol] = PortfolioAsset(
            symbol=symbol, asset_class=asset_class, weight=weight,
            value=value, volatility=volatility, return_hist=return_hist
        )

    def get_imbalance(self) -> float:
        total = sum(abs(a.weight - 1.0/len(self._assets)) for a in self._assets.values())
        return total if self._assets else 0.0

    def should_rebalance(self, threshold: float = 0.05) -> bool:
        if self._type == RebalanceType.THRESHOLD:
            return self.get_imbalance() > threshold
        return False

    def generate_rebalance_actions(self) -> List[RebalanceAction]:
        # 目标: 等权重
        target_weight = 1.0 / len(self._assets) if self._assets else 0
        actions = []
        for sym, asset in self._assets.items():
            diff = target_weight - asset.weight
            if abs(diff) > 0.01:
                amount = diff * asset.value
                actions.append(RebalanceAction(
                    action_id=f"act_{uuid.uuid4().hex[:8]}", symbol=sym,
                    from_weight=asset.weight, to_weight=target_weight,
                    amount=amount, reason=f"rebalance to {target_weight:.2%}"
                ))
        return actions

    def rebalance(self) -> int:
        actions = self.generate_rebalance_actions()
        for a in actions:
            self._assets[a.symbol].weight = a.to_weight
            self._history.append(a)
        return len(actions)


# === Risk Parity Engine ===

class RiskParityV105:
    def __init__(self, config: RiskParityConfig):
        self._config = config
        self._assets: Dict[str, PortfolioAsset] = {}

    def add_asset(self, symbol: str, volatility: float, return_hist: float):
        self._assets[symbol] = PortfolioAsset(
            symbol=symbol, asset_class=AssetClass.CRYPTO, weight=0,
            value=1000, volatility=volatility, return_hist=return_hist
        )

    def calculate_weights(self) -> Dict[str, float]:
        if not self._assets:
            return {}

        # 风险平价计算: 各资产对组合风险贡献相等
        vols = [a.volatility for a in self._assets.values()]
        total_vol = sum(vols) or 1.0

        # 逆波动率加权
        weights = {}
        for sym, asset in self._assets.items():
            inv_vol = 1.0 / asset.volatility if asset.volatility > 0 else 1.0
            weights[sym] = min(inv_vol / total_vol * len(self._assets), self._config.max_weight)
            weights[sym] = max(weights[sym], self._config.min_weight)

        # 归一化
        total = sum(weights.values())
        if total > 0:
            for sym in weights:
                weights[sym] = weights[sym] / total

        # 更新组合
        for sym, w in weights.items():
            if sym in self._assets:
                self._assets[sym].weight = w
                self._assets[sym].value = w * 100000

        return weights

    def get_portfolio_volatility(self) -> float:
        # 简化: 组合波动率
        return sum(a.weight * a.volatility for a in self._assets.values())

    def get_contribution(self) -> Dict[str, float]:
        # 风险贡献
        port_vol = self.get_portfolio_volatility()
        contrib = {}
        for sym, asset in self._assets.items():
            contrib[sym] = (asset.weight * asset.volatility / port_vol) if port_vol > 0 else 0
        return contrib


# === Smart Routing ===

class SmartRoutingV105:
    def __init__(self, config: RouterConfig):
        self._config = config
        self._routes: Dict[str, List[Route]] = {}

    def find_route(self, from_token: str, to_token: str,
                  amount: float, algorithm: RouteAlgorithm) -> Optional[Route]:
        # 模拟路由查找
        paths = [
            [from_token, "DEX1", to_token],
            [from_token, "DEX2", "DEX1", to_token],
            [from_token, "DEX3", "DEX2", "DEX1", to_token],
        ]

        best = None
        for path in paths[:self._config.max_hops]:
            hops = len(path) - 1
            # 计算成本(模拟)
            base_cost = amount * 0.003 * hops
            cost = base_cost * random.uniform(0.8, 1.2)
            confidence = 1.0 - hops * 0.1

            route = Route(path=path, cost=cost, hops=hops, confidence=confidence)
            if algorithm == RouteAlgorithm.CHEAPEST:
                if not best or route.cost < best.cost:
                    best = route
            elif algorithm == RouteAlgorithm.SHORTEST:
                if not best or route.hops < best.hops:
                    best = route
            else:
                # BALANCED: 成本收益平衡
                score = route.confidence * 0.7 - route.cost / amount * 0.3
                if not best:
                    best = route
                elif score > (best.confidence * 0.7 - best.cost / amount * 0.3):
                    best = route

        return best

    def find_best_route(self, from_token: str, to_token: str, amount: float) -> Route:
        # 尝试所有算法,返回最佳
        candidates = []
        for algo in RouteAlgorithm:
            route = self.find_route(from_token, to_token, amount, algo)
            if route:
                candidates.append(route)

        if not candidates:
            return Route(path=[], cost=0, hops=0, confidence=0)

        # 选择成本最低的
        return min(candidates, key=lambda r: r.cost)

    def get_savings(self, from_token: str, to_token: str, amount: float) -> float:
        # 智能路由 vs 简单��由的节约
        simple_cost = amount * 0.01
        best = self.find_best_route(from_token, to_token, amount)
        return simple_cost - best.cost


# === 全局函数 ===

_portfolio: Optional[PortfolioRebalancerV105] = None
_risk_parity: Optional[RiskParityV105] = None
_router: Optional[SmartRoutingV105] = None


def get_portfolio() -> PortfolioRebalancerV105:
    global _portfolio
    if _portfolio is None:
        _portfolio = PortfolioRebalancerV105()
    return _portfolio


def get_risk_parity() -> RiskParityV105:
    global _risk_parity
    if _risk_parity is None:
        _risk_parity = RiskParityV105(RiskParityConfig(target_vol=0.1, max_weight=0.5, min_weight=0.05))
    return _risk_parity


def get_router() -> SmartRoutingV105:
    global _router
    if _router is None:
        _router = SmartRoutingV105(RouterConfig(max_hops=3, allowed_dex=["uniswap", "sushiswap", "curve"]))
    return _router


def initialize_portfolio(rtype: RebalanceType = RebalanceType.THRESHOLD) -> PortfolioRebalancerV105:
    global _portfolio
    _portfolio = PortfolioRebalancerV105(rtype)
    return _portfolio


def initialize_risk_parity(config: RiskParityConfig) -> RiskParityV105:
    global _risk_parity
    _risk_parity = RiskParityV105(config)
    return _risk_parity


def initialize_router(config: RouterConfig) -> SmartRoutingV105:
    global _router
    _router = SmartRoutingV105(config)
    return _router


__version__ = "5.1.0"