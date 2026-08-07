"""
V102.0 - Market Making, Liquidity Pool & Cross-Exchange Enhancement
==========================================================================

数字货币交易系统 V102.0 - 做市商策略/流动性池/跨交易所增强

核心功能:
- MarketMakingEngine - 做市商引擎(双边报价/库存管理/风险对冲)
- LiquidityPoolV102 - 增强流动性池(TVL/深度聚合/滑点预估)
- CrossExchangeEnhanced - 跨交易所增强(价格聚合/最佳路由/延迟优化)

枚举类型:
- MarketMakingMode - 做市模式(CLASSIC/GRID/TWAP/ADAPTIVE)
- PoolStatus - 池状态(ACTIVE/PAUSED/DRAINED)
- RoutingStrategy - 路由策略(BEST_PRICE/LOWEST_FEE/FASTEST)

版本: 4.8.0
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import random
import math

# ============ 枚举类型 ============

class MarketMakingMode(Enum):
    """做市模式"""
    CLASSIC = "classic"
    GRID = "grid"
    TWAP = "twap"
    ADAPTIVE = "adaptive"


class PoolStatus(Enum):
    """池状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    DRAINED = "drained"
    REBALANCING = "rebalancing"


class RoutingStrategy(Enum):
    """路由策略"""
    BEST_PRICE = "best_price"
    LOWEST_FEE = "lowest_fee"
    FASTEST = "fastest"
    BALANCED = "balanced"


class OrderStatusV102(Enum):
    """订单状态V102"""
    PENDING = "pending"
    ACTIVE = "active"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SideV102(Enum):
    """订单方向V102"""
    BID = "bid"
    ASK = "ask"


class PoolSource(Enum):
    """流动性来源"""
    UNISWAP = "uniswap"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    BALANCER = "balancer"
    BINANCE = "binance"
    OKX = "okx"
    BYBIT = "bybit"


class PriceSource(Enum):
    """价格来源"""
    BINANCE = "binance"
    OKX = "okx"
    BYBIT = "bybit"
    COINBASE = "coinbase"


# ============ 数据结构 ============

@dataclass
class Quote:
    """报价"""
    price: float
    quantity: float
    side: SideV102
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketQuote:
    """市场报价(双边)"""
    symbol: str
    bid_price: float
    bid_quantity: float
    ask_price: float
    ask_quantity: float
    mid_price: float
    spread: float
    timestamp: datetime = field(default_factory=datetime.now)

    @staticmethod
    def create(symbol: str, mid_price: float, spread_pct: float = 0.001) -> "MarketQuote":
        """创建市场报价"""
        spread = mid_price * spread_pct
        return MarketQuote(
            symbol=symbol,
            bid_price=mid_price - spread / 2,
            bid_quantity=random.uniform(0.1, 10),
            ask_price=mid_price + spread / 2,
            ask_quantity=random.uniform(0.1, 10),
            mid_price=mid_price,
            spread=spread
        )


@dataclass
class MakerOrder:
    """做市订单"""
    order_id: str
    symbol: str
    side: SideV102
    price: float
    quantity: float
    filled: float = 0.0
    status: OrderStatusV102 = OrderStatusV102.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None

    def is_filled(self) -> bool:
        """是否完全成交"""
        return self.filled >= self.quantity

    def fill_rate(self) -> float:
        """成交比例"""
        if self.quantity == 0:
            return 0.0
        return self.filled / self.quantity


@dataclass
class InventoryPosition:
    """库存持仓"""
    symbol: str
    quantity: float
    avg_price: float
    current_value: float
    unrealized_pnl: float = 0.0

    def update_value(self, current_price: float) -> None:
        """更新价值"""
        self.current_value = self.quantity * current_price
        self.unrealized_pnl = (current_price - self.avg_price) * self.quantity


@dataclass
class SpreadConfig:
    """价差配置"""
    min_spread: float = 0.0001
    max_spread: float = 0.01
    target_spread: float = 0.001
    adaptive_factor: float = 1.0


@dataclass
class InventoryConfig:
    """库存配置"""
    max_inventory: float
    target_inventory: float = 0.5
    rebalance_threshold: float = 0.2
    inventory_tolerance: float = 0.1


@dataclass
class MakerSnapshot:
    """做市快照"""
    timestamp: datetime
    bid_orders: int
    ask_orders: int
    filled_bids: int
    filled_asks: int
    total_volume: float
    revenue: float
    spread_earned: float


@dataclass
class PoolPosition:
    """池持仓"""
    token_a: str
    token_b: str
    reserve_a: float
    reserve_b: float
    liquidity: float
    apy: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PoolQuote:
    """池报价"""
    pool_id: str
    source: PoolSource
    token_pair: str
    price_a: float
    price_b: float
    tvl: float
    fee: float


@dataclass
class SwapQuote:
    """兑换报价"""
    from_token: str
    to_token: str
    amount_in: float
    amount_out: float
    price_impact: float
    fee: float
    route: List[str] = field(default_factory=list)


@dataclass
class ExchangePrice:
    """交易所价格"""
    source: PriceSource
    symbol: str
    bid: float
    ask: float
    volume: float
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AggregatedPrice:
    """聚合价格"""
    symbol: str
    best_bid: float
    best_ask: float
    best_source: PriceSource
    weighted_bid: float
    weighted_ask: float
    sources: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """路由决策"""
    source: PriceSource
    price: float
    fee: float
    total_cost: float
    estimated_time_ms: float
    confidence: float


# ============ Market Making Engine ============

class MarketMakingEngine:
    """做市商引擎"""

    def __init__(self, symbol: str, mode: MarketMakingMode = MarketMakingMode.CLASSIC):
        self._symbol = symbol
        self._mode = mode
        self._enabled = False
        self._spread_config = SpreadConfig()
        self._inventory_config = InventoryConfig(max_inventory=1.0)
        self._inventory: Dict[str, float] = {}
        self._active_quotes: Dict[str, Quote] = {}
        self._order_history: List[MakerOrder] = []
        self._total_revenue = 0.0
        self._total_volume = 0.0
        self._snapshots: List[MakerSnapshot] = []

    def start(self) -> bool:
        """启动做市"""
        self._enabled = True
        return True

    def stop(self) -> None:
        """停止做市"""
        self._enabled = False

    def is_active(self) -> bool:
        """是否活跃"""
        return self._enabled

    def set_spread_config(self, min_spread: float, max_spread: float, target: float) -> None:
        """设置价差配置"""
        self._spread_config = SpreadConfig(
            min_spread=min_spread,
            max_spread=max_spread,
            target_spread=target
        )

    def set_inventory_config(self, max_inv: float, target: float) -> None:
        """设置库存配置"""
        self._inventory_config = InventoryConfig(
            max_inventory=max_inv,
            target_inventory=target
        )

    def generate_quotes(self, mid_price: float) -> tuple[Quote, Quote]:
        """生成双边报价"""
        spread = mid_price * self._spread_config.target_spread

        # 根据库存调整价差
        inv_ratio = self._inventory.get(self._symbol, 0) / self._inventory_config.max_inventory
        adaptive = self._spread_config.adaptive_factor * (1 + abs(inv_ratio - 0.5) * 2)
        adjusted_spread = spread * adaptive

        bid = Quote(
            price=mid_price - adjusted_spread / 2,
            quantity=self._calculate_quantity(SideV102.BID, inv_ratio),
            side=SideV102.BID
        )
        ask = Quote(
            price=mid_price + adjusted_spread / 2,
            quantity=self._calculate_quantity(SideV102.ASK, inv_ratio),
            side=SideV102.ASK
        )

        return bid, ask

    def _calculate_quantity(self, side: SideV102, inv_ratio: float) -> float:
        """计算报价数量"""
        base_qty = 1.0
        if side == SideV102.BID:
            # 做多时增加买入量
            return base_qty * (1 + 0.5 - inv_ratio)
        else:
            # 做空时增加卖出量
            return base_qty * (1 + inv_ratio)

    def submit_quote(self, quote: Quote) -> str:
        """提交报价"""
        quote_id = f"quote_{uuid.uuid4().hex[:8]}"
        self._active_quotes[quote_id] = quote
        return quote_id

    def cancel_quote(self, quote_id: str) -> bool:
        """取消报价"""
        if quote_id in self._active_quotes:
            del self._active_quotes[quote_id]
            return True
        return False

    def fill_order(self, quote_id: str, filled_qty: float) -> bool:
        """成交订单"""
        if quote_id not in self._active_quotes:
            return False

        quote = self._active_quotes[quote_id]
        quote.quantity -= filled_qty

        # 更新库存
        current = self._inventory.get(self._symbol, 0)
        if quote.side == SideV102.BID:
            self._inventory[self._symbol] = current + filled_qty
        else:
            self._inventory[self._symbol] = current - filled_qty

        # 记录收入
        self._total_revenue += filled_qty * quote.price * self._spread_config.target_spread
        self._total_volume += filled_qty * quote.price

        if quote.quantity <= 0:
            del self._active_quotes[quote_id]

        return True

    def get_inventory(self) -> Dict[str, float]:
        """获取库存"""
        return self._inventory.copy()

    def get_inventory_value(self, prices: Dict[str, float]) -> float:
        """获取库存价值"""
        total = 0.0
        for sym, qty in self._inventory.items():
            price = prices.get(sym, 0)
            total += qty * price
        return total

    def needs_rebalance(self) -> bool:
        """是否需要再平衡"""
        inv = self._inventory.get(self._symbol, 0)
        target = self._inventory_config.max_inventory * self._inventory_config.target_inventory
        return abs(inv - target) > self._inventory_config.rebalance_threshold * self._inventory_config.max_inventory

    def rebalance(self, target_price: float) -> tuple[float, float]:
        """再平衡仓位"""
        current = self._inventory.get(self._symbol, 0)
        target = self._inventory_config.max_inventory * self._inventory_config.target_inventory
        delta = target - current

        if delta > 0:
            # 需要买入
            return delta, target_price
        elif delta < 0:
            # 需要卖出
            return delta, target_price
        return 0.0, 0.0

    def add_snapshot(self) -> MakerSnapshot:
        """添加快照"""
        bid_count = sum(1 for q in self._active_quotes.values() if q.side == SideV102.BID)
        ask_count = sum(1 for q in self._active_quotes.values() if q.side == SideV102.ASK)

        snapshot = MakerSnapshot(
            timestamp=datetime.now(),
            bid_orders=bid_count,
            ask_orders=ask_count,
            filled_bids=0,
            filled_asks=0,
            total_volume=self._total_volume,
            revenue=self._total_revenue,
            spread_earned=self._total_revenue
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "enabled": self._enabled,
            "active_quotes": len(self._active_quotes),
            "total_revenue": self._total_revenue,
            "total_volume": self._total_volume,
            "inventory": self._inventory,
            "spread_earned_pct": (self._total_revenue / self._total_volume * 100) if self._total_volume > 0 else 0
        }


# ============ Liquidity Pool V102 ============

class LiquidityPoolV102:
    """增强流动性池"""

    def __init__(self, token_a: str, token_b: str, source: PoolSource = PoolSource.UNISWAP):
        self._pool_id = f"pool_{uuid.uuid4().hex[:8]}"
        self._token_a = token_a
        self._token_b = token_b
        self._source = source
        self._status = PoolStatus.ACTIVE
        self._position = PoolPosition(
            token_a=token_a,
            token_b=token_b,
            reserve_a=0.0,
            reserve_b=0.0,
            liquidity=0.0
        )
        self._swap_history: List[SwapQuote] = []
        self._total_fees = 0.0

    def get_id(self) -> str:
        """获取池ID"""
        return self._pool_id

    def add_liquidity(self, amount_a: float, amount_b: float) -> float:
        """添加流动性"""
        if self._position.reserve_a == 0:
            # 首次添加
            self._position.reserve_a = amount_a
            self._position.reserve_b = amount_b
            self._position.liquidity = math.sqrt(amount_a * amount_b)
        else:
            # 按比例添加
            ratio = min(amount_a / self._position.reserve_a,
                       amount_b / self._position.reserve_b)
            self._position.reserve_a += amount_a
            self._position.reserve_b += amount_b
            self._position.liquidity += self._position.liquidity * ratio

        self._position.last_updated = datetime.now()
        return self._position.liquidity

    def remove_liquidity(self, liquidity: float) -> tuple[float, float]:
        """移除流动性"""
        if liquidity > self._position.liquidity:
            return 0.0, 0.0

        ratio = liquidity / self._position.liquidity
        amount_a = self._position.reserve_a * ratio
        amount_b = self._position.reserve_b * ratio

        self._position.reserve_a -= amount_a
        self._position.reserve_b -= amount_b
        self._position.liquidity -= liquidity

        return amount_a, amount_b

    def get_swap_quote(self, amount_in: float, from_token: str) -> Optional[SwapQuote]:
        """获取兑换报价"""
        if from_token == self._token_a and self._position.reserve_a > 0:
            # 计算输出(简化: 恒积公式)
            amount_out = self._position.reserve_b * amount_in / (self._position.reserve_a + amount_in)
            price_impact = amount_in / self._position.reserve_a
            fee = amount_out * 0.003  # 0.3% 手续费

            return SwapQuote(
                from_token=self._token_a,
                to_token=self._token_b,
                amount_in=amount_in,
                amount_out=amount_out - fee,
                price_impact=price_impact,
                fee=fee,
                route=[self._token_a, self._token_b]
            )
        elif from_token == self._token_b and self._position.reserve_b > 0:
            amount_out = self._position.reserve_a * amount_in / (self._position.reserve_b + amount_in)
            price_impact = amount_in / self._position.reserve_b
            fee = amount_out * 0.003

            return SwapQuote(
                from_token=self._token_b,
                to_token=self._token_a,
                amount_in=amount_in,
                amount_out=amount_out - fee,
                price_impact=price_impact,
                fee=fee,
                route=[self._token_b, self._token_a]
            )
        return None

    def execute_swap(self, quote: SwapQuote) -> bool:
        """执行兑换"""
        self._total_fees += quote.fee

        # 更新池储备
        if quote.from_token == self._token_a:
            self._position.reserve_a += quote.amount_in
            self._position.reserve_b -= quote.amount_out
        else:
            self._position.reserve_b += quote.amount_in
            self._position.reserve_a -= quote.amount_out

        self._swap_history.append(quote)
        self._position.last_updated = datetime.now()
        return True

    def get_tvl(self) -> float:
        """获取TVL(总锁仓价值)"""
        # 简化: 假设token_a价格
        return self._position.reserve_a + self._position.reserve_b

    def get_depth(self, levels: int = 5) -> Dict[str, List[float]]:
        """获取深度"""
        return {
            "bid_depths": [self._position.reserve_b * (1 - i * 0.1) for i in range(levels)],
            "ask_depths": [self._position.reserve_a * (1 - i * 0.1) for i in range(levels)]
        }

    def calculate_apy(self, days: int = 30) -> float:
        """计算APY"""
        if days == 0 or self._swap_history:
            recent_fees = sum(s.fee for s in self._swap_history[-100:] if s.fee)
            tvl = self.get_tvl()
            if tvl > 0:
                return (recent_fees / tvl) * (365 / min(days, 1)) * 100
        return 0.0

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "pool_id": self._pool_id,
            "token_pair": f"{self._token_a}/{self._token_b}",
            "source": self._source.value,
            "status": self._status.value,
            "reserve_a": self._position.reserve_a,
            "reserve_b": self._position.reserve_b,
            "liquidity": self._position.liquidity,
            "tvl": self.get_tvl(),
            "total_fees": self._total_fees,
            "apy": self.calculate_apy()
        }


# ============ Cross Exchange Enhanced ============

class CrossExchangeEnhanced:
    """跨交易所增强"""

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.BALANCED):
        self._strategy = strategy
        self._prices: Dict[PriceSource, ExchangePrice] = {}
        self._latency_history: Dict[PriceSource, List[float]] = {}
        self._routing_decisions: List[RoutingDecision] = []

    def add_price(self, source: PriceSource, symbol: str, bid: float, ask: float, volume: float) -> None:
        """添加价格"""
        price = ExchangePrice(
            source=source,
            symbol=symbol,
            bid=bid,
            ask=ask,
            volume=volume,
            latency_ms=random.uniform(10, 100)
        )
        self._prices[source] = price

        # 记录延迟历史
        if source not in self._latency_history:
            self._latency_history[source] = []
        self._latency_history[source].append(price.latency_ms)
        if len(self._latency_history[source]) > 100:
            self._latency_history[source] = self._latency_history[source][-100:]

    def get_aggregated_price(self, symbol: str) -> Optional[AggregatedPrice]:
        """获取聚合价格"""
        if not self._prices:
            return None

        # 找最佳买卖价
        best_bid = max(self._prices.values(), key=lambda p: p.bid)
        best_ask = min(self._prices.values(), key=lambda p: p.ask)

        # 计算加权平均
        total_vol = sum(p.volume for p in self._prices.values())
        weighted_bid = sum(p.bid * p.volume for p in self._prices.values()) / total_vol if total_vol > 0 else 0
        weighted_ask = sum(p.ask * p.volume for p in self._prices.values()) / total_vol if total_vol > 0 else 0

        return AggregatedPrice(
            symbol=symbol,
            best_bid=best_bid.bid,
            best_ask=best_ask.ask,
            best_source=best_ask.source,
            weighted_bid=weighted_bid,
            weighted_ask=weighted_ask,
            sources=[s.value for s in self._prices.keys()]
        )

    def get_routing_decision(self, symbol: str, side: SideV102, quantity: float) -> Optional[RoutingDecision]:
        """获取路由决策"""
        agg_price = self.get_aggregated_price(symbol)
        if not agg_price:
            return None

        candidates = []
        for source, price in self._prices.items():
            # 计算交易成本
            if side == SideV102.BID:
                price_level = price.ask
            else:
                price_level = price.bid

            fee = price_level * quantity * 0.001  # 0.1% 手续费
            total_cost = (price_level * quantity) + fee

            # 延迟分数(越低越好)
            avg_latency = sum(self._latency_history.get(source, [50])) / max(len(self._latency_history.get(source, [1])), 1)
            latency_score = 100 - avg_latency  # 转换为分数

            candidates.append(RoutingDecision(
                source=source,
                price=price_level,
                fee=fee,
                total_cost=total_cost,
                estimated_time_ms=avg_latency,
                confidence=latency_score / 100
            ))

        if not candidates:
            return None

        # 根据策略选择
        if self._strategy == RoutingStrategy.BEST_PRICE:
            selected = min(candidates, key=lambda c: c.price)
        elif self._strategy == RoutingStrategy.LOWEST_FEE:
            selected = min(candidates, key=lambda c: c.fee)
        elif self._strategy == RoutingStrategy.FASTEST:
            selected = min(candidates, key=lambda c: c.estimated_time_ms)
        else:  # BALANCED
            selected = min(candidates, key=lambda c: c.total_cost * 0.5 + c.estimated_time_ms * 0.5)

        self._routing_decisions.append(selected)
        return selected

    def get_best_price(self, symbol: str, side: SideV102) -> tuple[PriceSource, float]:
        """获取最佳价格"""
        if not self._prices:
            return PriceSource.BINANCE, 0.0

        if side == SideV102.BID:
            source, price = min(((s, p.bid) for s, p in self._prices.items()), key=lambda x: x[1])
        else:
            source, price = min(((s, p.ask) for s, p in self._prices.items()), key=lambda x: x[1])

        return source, price

    def calculate_savings(self, symbol: str, quantity: float) -> Dict[str, float]:
        """计算节约"""
        agg_price = self.get_aggregated_price(symbol)
        if not agg_price:
            return {"savings": 0, "improvement_pct": 0}

        # 单一交易所成本
        _, best_price = self.get_best_price(symbol, SideV102.BID)
        best_cost = best_price * quantity

        # 使用聚合价格
        weighted_cost = agg_price.weighted_bid * quantity

        savings = best_cost - weighted_cost
        improvement = (savings / best_cost * 100) if best_cost > 0 else 0

        return {"savings": savings, "improvement_pct": improvement}

    def get_performance(self) -> Dict[str, Any]:
        """获取性能"""
        total_decisions = len(self._routing_decisions)
        if total_decisions == 0:
            return {"total_routes": 0, "avg_latency": 0, "strategy": self._strategy.value}

        avg_latency = sum(d.estimated_time_ms for d in self._routing_decisions) / total_decisions
        avg_confidence = sum(d.confidence for d in self._routing_decisions) / total_decisions

        return {
            "total_routes": total_decisions,
            "avg_latency_ms": avg_latency,
            "avg_confidence": avg_confidence,
            "strategy": self._strategy.value
        }


# ============ 全局函数 ============

_market_making_engine: Optional[MarketMakingEngine] = None
_liquidity_pools: Dict[str, LiquidityPoolV102] = {}
_cross_exchange: Optional[CrossExchangeEnhanced] = None


def get_market_making_engine() -> MarketMakingEngine:
    """获取做市引擎"""
    global _market_making_engine
    if _market_making_engine is None:
        _market_making_engine = MarketMakingEngine("BTCUSDT")
    return _market_making_engine


def initialize_market_making_engine(symbol: str, mode: MarketMakingMode = MarketMakingMode.CLASSIC) -> MarketMakingEngine:
    """初始化做市引擎"""
    global _market_making_engine
    _market_making_engine = MarketMakingEngine(symbol, mode)
    return _market_making_engine


def get_liquidity_pool(pool_id: str) -> Optional[LiquidityPoolV102]:
    """获取流动性池"""
    return _liquidity_pools.get(pool_id)


def create_liquidity_pool(token_a: str, token_b: str, source: PoolSource = PoolSource.UNISWAP) -> str:
    """创建流动性池"""
    pool = LiquidityPoolV102(token_a, token_b, source)
    _liquidity_pools[pool.get_id()] = pool
    return pool.get_id()


def get_liquidity_pools() -> List[LiquidityPoolV102]:
    """获取所有流动性池"""
    return list(_liquidity_pools.values())


def get_cross_exchange() -> CrossExchangeEnhanced:
    """获取跨交易所"""
    global _cross_exchange
    if _cross_exchange is None:
        _cross_exchange = CrossExchangeEnhanced()
    return _cross_exchange


def initialize_cross_exchange(strategy: RoutingStrategy = RoutingStrategy.BALANCED) -> CrossExchangeEnhanced:
    """初始化跨交易所"""
    global _cross_exchange
    _cross_exchange = CrossExchangeEnhanced(strategy)
    return _cross_exchange


# ============ 版本信息 ============

__version__ = "4.8.0"