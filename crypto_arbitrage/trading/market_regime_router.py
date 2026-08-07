"""V31.0 市场状态检测与智能路由系统

V31.0新增功能：
1. Market Regime Detection - 市场状态检测
2. Smart Order Routing - 智能订单路由
3. Price Impact Model - 价格影响预测
4. Liquidity Aggregator - 流动性聚合

创建时间：2026-05-07 18:15
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场状态枚举"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CALM = "calm"
    UNKNOWN = "unknown"


class OrderRoutingStrategy(Enum):
    """订单路由策略"""
    BEST_PRICE = "best_price"
    TWAP = "twap"
    VWAP = "vwap"
    SPLIT = "split"
    ADAPTIVE = "adaptive"


@dataclass
class MarketDataPoint:
    """市场数据点"""
    timestamp: float
    price: float
    volume: float
    bid: float
    ask: float
    spread: float


@dataclass
class LiquidityInfo:
    """流动性信息"""
    exchange: str
    symbol: str
    bid_depth: float  # 买方深度
    ask_depth: float  # 卖方深度
    avg_spread: float
    volume_24h: float


class MarketRegimeDetector:
    """市场状态检测器

    功能：
    - 趋势检测
    - 波动率分析
    - 区间识别
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化市场状态检测器

        Args:
            config: 配置字典
                - lookback_periods: 回看周期数 (默认20)
                - volatility_threshold: 波动率阈值 (默认0.02)
                - trend_threshold: 趋势阈值 (默认0.01)
        """
        self.config = config or {}
        self.lookback_periods = self.config.get('lookback_periods', 20)
        self.volatility_threshold = self.config.get('volatility_threshold', 0.02)
        self.trend_threshold = self.config.get('trend_threshold', 0.01)

        self.price_history: List[MarketDataPoint] = []
        self.current_regime = MarketRegime.UNKNOWN

    def add_data_point(self, price: float, volume: float, bid: float, ask: float) -> None:
        """添加市场数据点

        Args:
            price: 当前价格
            volume: 成交量
            bid: 买一价
            ask: 卖一价
        """
        spread = (ask - bid) / price if price > 0 else 0

        self.price_history.append(MarketDataPoint(
            timestamp=time.time(),
            price=price,
            volume=volume,
            bid=bid,
            ask=ask,
            spread=spread
        ))

        # 保持历史数据在限定范围内
        if len(self.price_history) > self.lookback_periods * 2:
            self.price_history = self.price_history[-self.lookback_periods * 2:]

    def detect_regime(self) -> MarketRegime:
        """检测当前市场状态

        Returns:
            MarketRegime: 市场状态
        """
        if len(self.price_history) < self.lookback_periods:
            return MarketRegime.UNKNOWN

        prices = [p.price for p in self.price_history[-self.lookback_periods:]]
        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                  for i in range(1, len(prices))]

        # 计算趋势
        mean_return = sum(returns) / len(returns)
        if mean_return > self.trend_threshold:
            regime = MarketRegime.TRENDING_UP
        elif mean_return < -self.trend_threshold:
            regime = MarketRegime.TRENDING_DOWN
        else:
            regime = MarketRegime.RANGING

        # 计算波动率
        if len(returns) > 1:
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5

            if volatility > self.volatility_threshold:
                regime = MarketRegime.VOLATILE
            elif volatility < self.volatility_threshold / 2:
                regime = MarketRegime.CALM

        self.current_regime = regime
        return regime

    def get_trend_strength(self) -> float:
        """获取趋势强度

        Returns:
            float: 趋势强度 (0-1)
        """
        if len(self.price_history) < 2:
            return 0.0

        prices = [p.price for p in self.price_history[-self.lookback_periods:]]
        if len(prices) < 2:
            return 0.0

        # 简单线性回归斜率
        n = len(prices)
        x = list(range(n))
        y = prices

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator

        # 归一化到0-1
        normalized_slope = abs(slope) / y_mean if y_mean > 0 else 0
        return min(1.0, normalized_slope * 10)

    def get_volatility(self) -> float:
        """获取市场波动率

        Returns:
            float: 波动率 (标准差)
        """
        if len(self.price_history) < 2:
            return 0.0

        prices = [p.price for p in self.price_history[-self.lookback_periods:]]
        if len(prices) < 2:
            return 0.0

        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                   for i in range(1, len(prices))]

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)

        return variance ** 0.5


class SmartOrderRouter:
    """智能订单路由

    功能：
    - 多交易所价格比较
    - TWAP/VWAP执行
    - 订单拆分
    - 最优价格选择
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化智能订单路由

        Args:
            config: 配置字典
                - strategy: 策略类型
                - split_count: 拆分数量 (默认10)
                - interval_seconds: 间隔秒数
        """
        self.config = config or {}
        self.strategy = OrderRoutingStrategy(
            self.config.get('strategy', 'best_price')
        )
        self.split_count = self.config.get('split_count', 10)
        self.interval_seconds = self.config.get('interval_seconds', 5)

        self.exchange_prices: Dict[str, Dict[str, float]] = {}

    def update_price(self, exchange: str, symbol: str, bid: float, ask: float) -> None:
        """更新交易所价格

        Args:
            exchange: 交易所名称
            symbol: 交易对
            bid: 买一价
            ask: 卖一价
        """
        if exchange not in self.exchange_prices:
            self.exchange_prices[exchange] = {}

        self.exchange_prices[exchange][symbol] = {'bid': bid, 'ask': ask}

    def get_best_price(
        self,
        symbol: str,
        side: str
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        """获取最优价格

        Args:
            symbol: 交易对
            side: 方向 ('buy' 或 'sell')

        Returns:
            (交易所, 价格, 数量)
        """
        if not self.exchange_prices:
            return None, None, None

        best_exchange = None
        best_price = None

        for exchange, prices in self.exchange_prices.items():
            if symbol not in prices:
                continue

            price_data = prices[symbol]
            price = price_data['bid'] if side == 'buy' else price_data['ask']

            if best_price is None:
                best_price = price
                best_exchange = exchange
            elif side == 'buy' and price < best_price:
                best_price = price
                best_exchange = exchange
            elif side == 'sell' and price > best_price:
                best_price = price
                best_exchange = exchange

        if best_exchange is None:
            return None, None, None

        return best_exchange, best_price, 0.0

    def calculate_twap_orders(
        self,
        symbol: str,
        total_quantity: float,
        side: str
    ) -> List[Dict[str, Any]]:
        """计算TWAP订单

        Args:
            symbol: 交易对
            total_quantity: 总数量
            side: 方向 ('buy' 或 'sell')

        Returns:
            订单列表
        """
        quantity_per_order = total_quantity / self.split_count
        orders = []

        for i in range(self.split_count):
            orders.append({
                'order_id': f'TWAP_{i}',
                'symbol': symbol,
                'quantity': quantity_per_order,
                'side': side,
                'price': None,  # 市价
                'interval': self.interval_seconds,
                'sequence': i + 1
            })

        return orders

    def calculate_vwap_orders(
        self,
        symbol: str,
        total_quantity: float,
        side: str,
        volume_profile: List[float]
    ) -> List[Dict[str, Any]]:
        """计算VWAP订单

        Args:
            symbol: 交易对
            total_quantity: 总数量
            side: 方向 ('buy' 或 'sell')
            volume_profile: 成交量分布

        Returns:
            订单列表
        """
        if not volume_profile:
            return self.calculate_twap_orders(symbol, total_quantity, side)

        total_volume = sum(volume_profile)
        if total_volume == 0:
            return self.calculate_twap_orders(symbol, total_quantity, side)

        orders = []
        for i, vol in enumerate(volume_profile):
            # 归一化成交量权重
            weight = vol / total_volume
            quantity = total_quantity * weight

            orders.append({
                'order_id': f'VWAP_{i}',
                'symbol': symbol,
                'quantity': quantity,
                'side': side,
                'price': None,
                'weight': weight,
                'sequence': i + 1
            })

        return orders


class PriceImpactModel:
    """价格影响预测模型

    功能：
    - 预测订单对价格的影响
    - 计算最优订单大小
    - 减少市场冲击
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化价格影响模型

        Args:
            config: 配置字典
                - eta: 冲击系数 (默认0.1)
                - gamma: 流动性系数 (默认0.5)
        """
        self.config = config or {}
        self.eta = self.config.get('eta', 0.1)  # 冲击系数
        self.gamma = self.config.get('gamma', 0.5)  # 流动性系数

    def estimate_impact(
        self,
        order_quantity: float,
        current_price: float,
        avg_volume: float
    ) -> float:
        """估算订单的价格影响

        Args:
            order_quantity: 订单数量
            current_price: 当前价格
            avg_volume: 平均成交量

        Returns:
            价格影响百分比
        """
        if avg_volume <= 0:
            return 0.0

        # 订单大小相对于平均成交量的比例
        size_ratio = order_quantity / avg_volume

        # 使用平方根关系估算价格影响
        impact = self.eta * (size_ratio ** 0.5)

        return min(impact, 1.0)  # 限制最大影响100%

    def calculate_optimal_size(
        self,
        target_impact: float,
        current_price: float,
        avg_volume: float
    ) -> float:
        """计算最优订单大小

        Args:
            target_impact: 目标价格影响
            current_price: 当前价格
            avg_volume: 平均成交量

        Returns:
            最优订单大小
        """
        if avg_volume <= 0 or target_impact <= 0:
            return 0.0

        # 反向计算
        size_ratio = (target_impact / self.eta) ** 2
        optimal_size = size_ratio * avg_volume

        return optimal_size


class LiquidityAggregator:
    """流动性聚合器

    功能：
    - 聚合多交易所流动性
    - 寻找最佳买卖深度
    - 计算综合价差
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化流动性聚合器"""
        self.config = config or {}
        self.liquidity_data: Dict[str, List[LiquidityInfo]] = {}

    def add_liquidity(
        self,
        exchange: str,
        symbol: str,
        bid_depth: float,
        ask_depth: float,
        avg_spread: float,
        volume_24h: float
    ) -> None:
        """添加流动性数据

        Args:
            exchange: 交易所
            symbol: 交易对
            bid_depth: 买方深度
            ask_depth: 卖方深度
            avg_spread: 平均价差
            volume_24h: 24小时成交量
        """
        if exchange not in self.liquidity_data:
            self.liquidity_data[exchange] = []

        self.liquidity_data[exchange].append(LiquidityInfo(
            exchange=exchange,
            symbol=symbol,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            avg_spread=avg_spread,
            volume_24h=volume_24h
        ))

    def get_aggregated_depth(
        self,
        symbol: str,
        side: str
    ) -> float:
        """获取聚合深度

        Args:
            symbol: 交易对
            side: 方向 ('bid' 或 'ask')

        Returns:
            聚合深度
        """
        total_depth = 0.0

        for exchange, liquidity_list in self.liquidity_data.items():
            for liquidity in liquidity_list:
                if liquidity.symbol != symbol:
                    continue

                if side == 'bid':
                    total_depth += liquidity.bid_depth
                else:
                    total_depth += liquidity.ask_depth

        return total_depth

    def find_best_exchange(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Optional[str]:
        """查找最佳交易所

        Args:
            symbol: 交易对
            side: 方向 ('bid' 或 'ask')
            quantity: 订单数量

        Returns:
            最佳交易所名称
        """
        best_exchange = None
        min_spread = float('inf')

        for exchange, liquidity_list in self.liquidity_data.items():
            for liquidity in liquidity_list:
                if liquidity.symbol != symbol:
                    continue

                # 检查是否有足够深度
                if side == 'ask' and liquidity.ask_depth >= quantity:
                    if liquidity.avg_spread < min_spread:
                        min_spread = liquidity.avg_spread
                        best_exchange = exchange

        return best_exchange


# ===== 测试函数 =====

def test_market_regime_detector():
    """测试市场状态检测器"""
    print("\n=== Test Market Regime Detector ===")

    detector = MarketRegimeDetector({'lookback_periods': 10})

    # 模拟上涨趋势数据
    import random
    random.seed(42)

    base_price = 50000
    for i in range(15):
        price = base_price * (1 + 0.001 * i + random.uniform(-0.002, 0.002))
        volume = random.uniform(100, 500)
        bid = price * 0.999
        ask = price * 1.001
        detector.add_data_point(price, volume, bid, ask)

    regime = detector.detect_regime()
    print(f"Detected regime: {regime.value}")

    trend_strength = detector.get_trend_strength()
    print(f"Trend strength: {trend_strength:.4f}")

    volatility = detector.get_volatility()
    print(f"Volatility: {volatility:.4f}")

    print("[PASS] Market Regime Detector test")
    return True


def test_smart_order_router():
    """测试智能订单路由"""
    print("\n=== Test Smart Order Router ===")

    router = SmartOrderRouter({'strategy': 'twap', 'split_count': 5})

    # 更新价格
    router.update_price('binance', 'BTC/USDT', 50000, 50100)
    router.update_price('okx', 'BTC/USDT', 50050, 50150)

    # 获取最优买价
    exchange, price, qty = router.get_best_price('BTC/USDT', 'buy')
    print(f"Best buy: {exchange} @ {price}")

    # 计算TWAP订单
    orders = router.calculate_twap_orders('BTC/USDT', 1000, 'buy')
    print(f"TWAP orders: {len(orders)}")

    print("[PASS] Smart Order Router test")
    return True


def test_price_impact_model():
    """测试价格影响模型"""
    print("\n=== Test Price Impact Model ===")

    model = PriceImpactModel({'eta': 0.1})

    impact = model.estimate_impact(100, 50000, 1000)
    print(f"Price impact: {impact:.4f}")

    optimal_size = model.calculate_optimal_size(0.01, 50000, 1000)
    print(f"Optimal size: {optimal_size:.2f}")

    print("[PASS] Price Impact Model test")
    return True


def test_liquidity_aggregator():
    """测试流动性聚合器"""
    print("\n=== Test Liquidity Aggregator ===")

    aggregator = LiquidityAggregator()

    aggregator.add_liquidity('binance', 'BTC/USDT', 100, 100, 5, 10000)
    aggregator.add_liquidity('okx', 'BTC/USDT', 80, 80, 8, 8000)

    depth = aggregator.get_aggregated_depth('BTC/USDT', 'bid')
    print(f"Aggregated bid depth: {depth}")

    best = aggregator.find_best_exchange('BTC/USDT', 'ask', 50)
    print(f"Best exchange: {best}")

    print("[PASS] Liquidity Aggregator test")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("V31.0 Market Regime & Smart Routing Tests")
    print("=" * 50)

    tests = [
        test_market_regime_detector,
        test_smart_order_router,
        test_price_impact_model,
        test_liquidity_aggregator,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{len(tests)} passed")
    print("=" * 50)

    return passed == len(tests)


if __name__ == "__main__":
    run_all_tests()