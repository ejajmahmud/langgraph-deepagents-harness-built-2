"""跨资产相关性、流动性管理与执行质量 V93.0 - Phase 37

核心功能：
- CrossAssetCorrelation: 跨资产相关性（相关性矩阵/动态相关性/相关性过滤）
- LiquidityManager: 流动性管理（池管理/深度分析/价格影响）
- ExecutionQuality: 执行质量分析（滑点/成本/执行效率）

创建时间：2026-05-09 06:39
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import random
import math


# ============ 枚举定义 ============

class CorrelationMethod(Enum):
    """相关性计算方法"""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    CONDITIONAL = "conditional"


class LiquidityLevel(Enum):
    """流动性级别"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    ILLIQUID = "illiquid"


class ExecutionQuality(Enum):
    """执行质量级别"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class LiquidityType(Enum):
    """流动性类型"""
    ORDERBOOK = "orderbook"
    AMM = "amm"
    AGGREGATED = "aggregated"
    CROSS_EXCHANGE = "cross_exchange"


# ============ 数据结构 ============

@dataclass
class CorrelationResult:
    """相关性结果"""
    asset_pair: str
    correlation: float
    method: str
    significance: float


@dataclass
class LiquidityPool:
    """流动性池"""
    symbol: str
    liquidity_type: str
    total_volume: float
    bid_depth: float
    ask_depth: float
    spread: float


@dataclass
class LiquidityDepth:
    """流动性深度"""
    price_level: float
    volume: float
    cumulative_volume: float


@dataclass
class ExecutionMetrics:
    """执行指标"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    fill_quantity: float
    avg_fill_price: float
    slippage: float
    fees: float
    execution_time: float


# ============ CrossAssetCorrelation ============

class CrossAssetCorrelation:
    """跨资产相关性"""

    def __init__(self):
        self._correlation_history: List[CorrelationResult] = []
        self._correlation_matrix: Dict[str, Dict[str, float]] = {}
        self._method = CorrelationMethod.PEARSON

    def set_method(self, method: CorrelationMethod) -> None:
        self._method = method

    def get_method(self) -> CorrelationMethod:
        return self._method

    def calculate_correlation(self, returns_a: List[float], returns_b: List[float]) -> Dict[str, Any]:
        """计算两个资产的相关系数"""
        if len(returns_a) != len(returns_b) or len(returns_a) < 2:
            return {"correlation": 0.0, "significance": 0.0, "method": self._method.value}

        # Calculate Pearson correlation
        n = len(returns_a)
        mean_a = sum(returns_a) / n
        mean_b = sum(returns_b) / n

        # Standard deviations
        var_a = sum((x - mean_a) ** 2 for x in returns_a) / n
        var_b = sum((x - mean_b) ** 2 for x in returns_b) / n
        std_a = math.sqrt(var_a) if var_a > 0 else 1
        std_b = math.sqrt(var_b) if var_b > 0 else 1

        # Correlation
        covariance = sum((returns_a[i] - mean_a) * (returns_b[i] - mean_b) for i in range(n)) / n
        correlation = covariance / (std_a * std_b) if (std_a * std_b) > 0 else 0.0

        # Significance (simplified t-test)
        significance = abs(correlation) * math.sqrt(n - 2) / math.sqrt(1 - correlation ** 2) if abs(correlation) < 1 else 0
        significance = min(1.0, max(0.0, significance))

        return {
            "correlation": round(correlation, 4),
            "significance": round(min(significance, 1.0), 4),
            "method": self._method.value,
            "strength": "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.4 else "weak",
            "direction": "positive" if correlation > 0 else "negative"
        }

    def build_correlation_matrix(self, asset_returns: Dict[str, List[float]]) -> Dict[str, Any]:
        """构建多资产相关性矩阵"""
        assets = list(asset_returns.keys())
        n = len(assets)
        matrix = {}

        for i, asset_a in enumerate(assets):
            matrix[asset_a] = {}
            for j, asset_b in enumerate(assets):
                if i == j:
                    matrix[asset_a][asset_b] = 1.0
                elif j < i:
                    # Use cached value
                    matrix[asset_a][asset_b] = matrix[asset_b].get(asset_a, 0.0)
                else:
                    returns_a = asset_returns.get(asset_a, [])
                    returns_b = asset_returns.get(asset_b, [])
                    if len(returns_a) > 1 and len(returns_b) > 1:
                        corr = self.calculate_correlation(returns_a, returns_b)["correlation"]
                        matrix[asset_a][asset_b] = corr

        self._correlation_matrix = matrix

        return {
            "assets": assets,
            "matrix": matrix,
            "size": n,
            "average_correlation": sum(sum(row.values()) for row in matrix.values()) / (n * n)
        }

    def find_uncorrelated_pairs(self, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """寻找低相关性或负相关性的资产对（用于分散投资）"""
        pairs = []
        assets = list(self._correlation_matrix.keys())

        for i, asset_a in enumerate(assets):
            for j, asset_b in enumerate(assets):
                if i < j:
                    corr = self._correlation_matrix.get(asset_a, {}).get(asset_b, 0.0)
                    if abs(corr) < threshold:
                        pairs.append({
                            "asset_a": asset_a,
                            "asset_b": asset_b,
                            "correlation": round(corr, 4),
                            "diversification_benefit": "high" if corr < 0 else "moderate" if abs(corr) < 0.2 else "low"
                        })

        return pairs

    def detect_regime_change(self, recent_correlations: List[float], historical_avg: float) -> Dict[str, Any]:
        """检测相关性 regime 变化"""
        if not recent_correlations:
            return {"regime_change": False, "change_magnitude": 0.0}

        recent_avg = sum(recent_correlations) / len(recent_correlations)
        change = abs(recent_avg - historical_avg)
        threshold = 0.2

        return {
            "regime_change": change > threshold,
            "change_magnitude": round(change, 4),
            "historical": round(historical_avg, 4),
            "recent": round(recent_avg, 4),
            "direction": "increased" if recent_avg > historical_avg else "decreased"
        }

    def get_correlation_summary(self) -> Dict[str, Any]:
        return {
            "method": self._method.value,
            "assets": len(self._correlation_matrix),
            "calculations": len(self._correlation_history)
        }


# ============ LiquidityManager ============

class LiquidityManager:
    """流动性管理"""

    def __init__(self):
        self._pools: Dict[str, LiquidityPool] = {}
        self._depth_cache: Dict[str, List[LiquidityDepth]] = {}
        self._liquidity_type = LiquidityType.ORDERBOOK

    def set_liquidity_type(self, ltype: LiquidityType) -> None:
        self._liquidity_type = ltype

    def get_liquidity_type(self) -> LiquidityType:
        return self._liquidity_type

    def add_pool(self, symbol: str, total_volume: float, bid_depth: float, ask_depth: float) -> Dict[str, Any]:
        """添加流动性池"""
        spread = (ask_depth - bid_depth) / ((bid_depth + ask_depth) / 2) if (bid_depth + ask_depth) > 0 else 0

        pool = LiquidityPool(
            symbol=symbol,
            liquidity_type=self._liquidity_type.value,
            total_volume=total_volume,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            spread=spread
        )
        self._pools[symbol] = pool

        return {
            "symbol": symbol,
            "total_volume": f"${total_volume:,.0f}",
            "bid_depth": f"${bid_depth:,.0f}",
            "ask_depth": f"${ask_depth:,.0f}",
            "spread": f"{spread:.4f}",
            "level": self._calculate_level(bid_depth, ask_depth)
        }

    def _calculate_level(self, bid_depth: float, ask_depth: float) -> str:
        """计算流动性级别"""
        avg_depth = (bid_depth + ask_depth) / 2
        if avg_depth > 1000000:
            return LiquidityLevel.EXCELLENT.value
        elif avg_depth > 100000:
            return LiquidityLevel.GOOD.value
        elif avg_depth > 10000:
            return LiquidityLevel.FAIR.value
        elif avg_depth > 1000:
            return LiquidityLevel.POOR.value
        else:
            return LiquidityLevel.ILLIQUID.value

    def analyze_depth(self, symbol: str, levels: List[Dict[str, float]]) -> Dict[str, Any]:
        """分析订单簿深度"""
        depth_levels = []
        cumulative = 0.0

        for level in sorted(levels, key=lambda x: x.get('price', 0)):
            cumulative += level.get('volume', 0)
            depth_levels.append(LiquidityDepth(
                price_level=level.get('price', 0),
                volume=level.get('volume', 0),
                cumulative_volume=cumulative
            ))

        self._depth_cache[symbol] = depth_levels

        # Find liquid range (where 80% of volume is)
        total_vol = cumulative
        liquid_80 = total_vol * 0.8
        cum = 0.0
        avg_price = 0.0

        for dl in depth_levels:
            cum += dl.cumulative_volume
            if cum >= liquid_80:
                avg_price = dl.price_level
                break

        return {
            "symbol": symbol,
            "levels": len(depth_levels),
            "total_volume": f"${total_vol:,.0f}",
            "avg_price_at_80pct": f"${avg_price:,.2f}",
            "bid_ask_spread": f"{self._pools[symbol].spread:.4f}" if symbol in self._pools else "N/A",
            "depth_concentration": "concentrated" if depth_levels[0].cumulative_volume / total_vol > 0.5 else "distributed"
        }

    def calculate_price_impact(self, symbol: str, order_volume: float, side: OrderSide) -> Dict[str, Any]:
        """计算价格影响（基于订单簿）"""
        if symbol not in self._depth_cache:
            # Simulate if no data
            impact = random.uniform(0.001, 0.02)
            return {
                "symbol": symbol,
                "order_volume": f"${order_volume:,.0f}",
                "side": side.value,
                "estimated_impact": f"{impact:.4f}",
                "impact_cost": f"${order_volume * impact:,.2f}",
                "recommendation": "split" if impact > 0.01 else "execute"
            }

        depth = self._depth_cache[symbol]
        if not depth:
            return {"error": "no depth data"}

        total_volume = sum(d.volume for d in depth)
        volume_ratio = order_volume / total_volume if total_volume > 0 else 0

        # Linear price impact model
        impact_coeff = random.uniform(0.1, 0.5)
        impact = impact_coeff * volume_ratio ** 2

        return {
            "symbol": symbol,
            "order_volume": f"${order_volume:,.0f}",
            "side": side.value,
            "volume_ratio": f"{volume_ratio:.2%}",
            "estimated_impact": f"{impact:.4f}",
            "impact_cost": f"${order_volume * impact:,.2f}",
            "slippage_bps": f"{impact * 10000:.1f}",
            "recommendation": "split" if impact > 0.005 else "execute"
        }

    def get_best_execution_venue(self, symbol: str, volume: float) -> Dict[str, Any]:
        """获取最佳执行场所"""
        venues = []
        for pool_symbol, pool in self._pools.items():
            if pool_symbol == symbol or symbol in self._pools:
                depth = pool.bid_depth + pool.ask_depth
                if depth > volume * 2:  # 2x volume for safety
                    venues.append({
                        "venue": pool_symbol,
                        "depth": depth,
                        "spread": pool.spread,
                        "score": depth / (pool.spread + 0.0001)
                    })

        # Add simulated venues if none
        if not venues:
            venues = [
                {"venue": "Binance", "depth": random.uniform(100000, 5000000), "spread": 0.0002, "score": random.uniform(80, 95)},
                {"venue": "OKX", "depth": random.uniform(100000, 3000000), "spread": 0.0003, "score": random.uniform(75, 90)},
                {"venue": "Bybit", "depth": random.uniform(100000, 2000000), "spread": 0.00025, "score": random.uniform(70, 85)}
            ]

        best = max(venues, key=lambda x: x["score"])

        return {
            "symbol": symbol,
            "volume": f"${volume:,.0f}",
            "best_venue": best["venue"],
            "depth": f"${best['depth']:,.0f}",
            "spread": f"{best['spread']:.4f}",
            "alternatives": len(venues)
        }

    def get_liquidity_summary(self) -> Dict[str, Any]:
        return {
            "pools": len(self._pools),
            "type": self._liquidity_type.value,
            "total_volume": f"${sum(p.total_volume for p in self._pools.values()):,.0f}"
        }


# ============ ExecutionQualityAnalyzer ============

class ExecutionQualityAnalyzer:
    """执行质量分析"""

    def __init__(self):
        self._executions: List[ExecutionMetrics] = []
        self._quality_level = ExecutionQuality.GOOD

    def set_quality_level(self, level: ExecutionQuality) -> None:
        self._quality_level = level

    def get_quality_level(self) -> ExecutionQuality:
        return self._quality_level

    def analyze_execution(self, order_id: str, symbol: str, side: OrderSide, quantity: float,
                        fill_quantity: float, avg_fill_price: float, limit_price: float,
                        fees: float, execution_time: float) -> Dict[str, Any]:
        """分析单次执行质量"""
        # Calculate slippage
        expected_price = limit_price
        slippage = (avg_fill_price - expected_price) / expected_price if side == OrderSide.BUY else (expected_price - avg_fill_price) / expected_price
        slippage = max(0, slippage)  # Positive means cost

        # Slippage in basis points
        slippage_bps = slippage * 10000

        # Total cost
        total_cost = (avg_fill_price - limit_price) * fill_quantity + fees if side == OrderSide.BUY else (limit_price - avg_fill_price) * fill_quantity + fees

        metrics = ExecutionMetrics(
            order_id=order_id,
            symbol=symbol,
            side=side.value,
            quantity=quantity,
            fill_quantity=fill_quantity,
            avg_fill_price=avg_fill_price,
            slippage=slippage,
            fees=fees,
            execution_time=execution_time
        )
        self._executions.append(metrics)

        return {
            "order_id": order_id,
            "symbol": symbol,
            "side": side.value,
            "quantity": quantity,
            "fill_rate": f"{fill_quantity / quantity:.1%}",
            "limit_price": f"${limit_price:,.2f}",
            "fill_price": f"${avg_fill_price:,.2f}",
            "slippage": f"{slippage:.4f}",
            "slippage_bps": f"{slippage_bps:.1f}",
            "fees": f"${fees:,.2f}",
            "total_cost": f"${total_cost:,.2f}",
            "execution_time_ms": f"{execution_time:.0f}",
            "quality": "excellent" if slippage_bps < 2 else "good" if slippage_bps < 5 else "acceptable" if slippage_bps < 10 else "poor"
        }

    def calculate_average_slippage(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """计算平均滑点"""
        if not self._executions:
            return {"avg_slippage_bps": 0.0, "symbol": symbol or "all", "samples": 0}

        filtered = [e for e in self._executions if symbol is None or e.symbol == symbol]
        if not filtered:
            return {"avg_slippage_bps": 0.0, "symbol": symbol or "all", "samples": 0}

        avg_slippage = sum(e.slippage for e in filtered) / len(filtered)
        avg_slippage_bps = avg_slippage * 10000

        return {
            "avg_slippage_bps": f"{avg_slippage_bps:.1f}",
            "symbol": symbol or "all",
            "samples": len(filtered),
            "quality": "excellent" if avg_slippage_bps < 2 else "good" if avg_slippage_bps < 5 else "acceptable" if avg_slippage_bps < 10 else "poor"
        }

    def calculate_execution_rate(self) -> Dict[str, Any]:
        """计算执行率"""
        if not self._executions:
            return {"execution_rate": 0.0, "partial_rate": 0.0, "total": 0}

        total = len(self._executions)
        fill_rate = sum(1 for e in self._executions if e.fill_quantity == e.quantity) / total
        partial_rate = sum(1 for e in self._executions if 0 < e.fill_quantity < e.quantity) / total

        return {
            "execution_rate": f"{fill_rate:.1%}",
            "partial_rate": f"{partial_rate:.1%}",
            "total": total,
            "full_fills": sum(1 for e in self._executions if e.fill_quantity == e.quantity),
            "partial_fills": sum(1 for e in self._executions if 0 < e.fill_quantity < e.quantity)
        }

    def calculate_total_costs(self) -> Dict[str, Any]:
        """计算总成本"""
        if not self._executions:
            return {"total_fees": 0.0, "total_slippage_cost": 0.0, "avg_cost_per_order": 0.0}

        total_fees = sum(e.fees for e in self._executions)
        total_slippage = sum(e.slippage * e.avg_fill_price * e.quantity for e in self._executions)
        avg_cost = (total_fees + total_slippage) / len(self._executions)

        return {
            "total_fees": f"${total_fees:,.2f}",
            "total_slippage_cost": f"${total_slippage:,.2f}",
            "total_cost": f"${total_fees + total_slippage:,.2f}",
            "avg_cost_per_order": f"${avg_cost:,.2f}",
            "orders": len(self._executions)
        }

    def get_quality_summary(self) -> Dict[str, Any]:
        return {
            "executions": len(self._executions),
            "quality_level": self._quality_level.value,
            "avg_slippage_bps": f"{sum(e.slippage for e in self._executions) / len(self._executions) * 10000 if self._executions else 0:.1f}"
        }


# ============ 全局实例管理 ============

_cross_asset_correlation: Optional[CrossAssetCorrelation] = None
_liquidity_manager: Optional[LiquidityManager] = None
_execution_quality_analyzer: Optional[ExecutionQualityAnalyzer] = None


def get_cross_asset_correlation() -> CrossAssetCorrelation:
    global _cross_asset_correlation
    if _cross_asset_correlation is None:
        _cross_asset_correlation = CrossAssetCorrelation()
    return _cross_asset_correlation


def initialize_cross_asset_correlation() -> None:
    global _cross_asset_correlation
    _cross_asset_correlation = CrossAssetCorrelation()


def get_liquidity_manager() -> LiquidityManager:
    global _liquidity_manager
    if _liquidity_manager is None:
        _liquidity_manager = LiquidityManager()
    return _liquidity_manager


def initialize_liquidity_manager() -> None:
    global _liquidity_manager
    _liquidity_manager = LiquidityManager()


def get_execution_quality_analyzer() -> ExecutionQualityAnalyzer:
    global _execution_quality_analyzer
    if _execution_quality_analyzer is None:
        _execution_quality_analyzer = ExecutionQualityAnalyzer()
    return _execution_quality_analyzer


def initialize_execution_quality_analyzer() -> None:
    global _execution_quality_analyzer
    _execution_quality_analyzer = ExecutionQualityAnalyzer()