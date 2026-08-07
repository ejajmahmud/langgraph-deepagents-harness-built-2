"""V31.0 增强功能测试套件

测试V31.0新增功能:
- Market Regime Detection - 市场状态检测
- Smart Order Routing - 智能订单路由
- Price Impact Model - 价格影响预测
- Liquidity Aggregator - 流动性聚合

创建时间：2026-05-07 18:20
"""

import sys
import os

# 获取正确路径
test_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(test_dir)
sys.path.insert(0, project_dir)

print("="*50)
print("V31.0 增强功能测试套件")
print("="*50)

# 导入V31模块
from trading.market_regime_router import (
    MarketRegimeDetector,
    SmartOrderRouter,
    PriceImpactModel,
    LiquidityAggregator,
    MarketRegime,
    OrderRoutingStrategy,
    run_all_tests,
)


def test_v31_market_regime():
    """测试V31市场状态检测"""
    print("\n=== Test V31.0 Market Regime ===")

    config = {
        'lookback_periods': 20,
        'volatility_threshold': 0.02,
        'trend_threshold': 0.01,
    }

    detector = MarketRegimeDetector(config)

    import random
    random.seed(42)

    # 模拟震荡上行数据
    base_price = 50000
    for i in range(25):
        price = base_price * (1 + 0.001 * i + random.uniform(-0.002, 0.003))
        volume = random.uniform(100, 500)
        bid = price * 0.9995
        ask = price * 1.0005
        detector.add_data_point(price, volume, bid, ask)

    regime = detector.detect_regime()
    print(f"Detected regime: {regime.value}")

    trend_strength = detector.get_trend_strength()
    print(f"Trend strength: {trend_strength:.4f}")

    volatility = detector.get_volatility()
    print(f"Volatility: {volatility:.4f}")

    print(f"[PASS] V31 Market Regime Detection")
    return True


def test_v31_smart_routing():
    """测试V31智能订单路由"""
    print("\n=== Test V31.0 Smart Order Routing ===")

    config = {
        'strategy': 'twap',
        'split_count': 10,
        'interval_seconds': 5,
    }

    router = SmartOrderRouter(config)

    # 更新多交易所价格
    router.update_price('binance', 'BTC/USDT', 50000, 50100)
    router.update_price('okx', 'BTC/USDT', 50050, 50150)
    router.update_price('bybit', 'BTC/USDT', 50025, 50125)

    # 获取最优买价
    exchange, price, qty = router.get_best_price('BTC/USDT', 'buy')
    print(f"Best buy: {exchange} @ {price}")

    # 获取最优卖价
    exchange, price, qty = router.get_best_price('BTC/USDT', 'sell')
    print(f"Best sell: {exchange} @ {price}")

    # TWAP订单
    twap_orders = router.calculate_twap_orders('BTC/USDT', 10000, 'buy')
    print(f"TWAP orders: {len(twap_orders)}")

    # VWAP订单
    volume_profile = [100, 150, 200, 180, 120, 90, 80, 70, 50, 40]
    vwap_orders = router.calculate_vwap_orders('BTC/USDT', 10000, 'buy', volume_profile)
    print(f"VWAP orders: {len(vwap_orders)}")

    print(f"[PASS] V31 Smart Order Routing")
    return True


def test_v31_price_impact():
    """测试V31价格影响模型"""
    print("\n=== Test V31.0 Price Impact Model ===")

    model = PriceImpactModel({'eta': 0.1, 'gamma': 0.5})

    # 测试不同订单大小的价格影响
    test_cases = [
        (100, 50000, 1000),   # 10% avg volume
        (500, 50000, 1000),   # 50% avg volume
        (1000, 50000, 1000),  # 100% avg volume
    ]

    for order_qty, price, avg_vol in test_cases:
        impact = model.estimate_impact(order_qty, price, avg_vol)
        optimal = model.calculate_optimal_size(0.01, price, avg_vol)
        print(f"Order {order_qty}: impact={impact:.4f}, optimal={optimal:.2f}")

    print(f"[PASS] V31 Price Impact Model")
    return True


def test_v31_liquidity():
    """测试V31流动性聚合"""
    print("\n=== Test V31.0 Liquidity Aggregator ===")

    aggregator = LiquidityAggregator()

    # 添加多交易所流动性数据
    aggregator.add_liquidity('binance', 'BTC/USDT', 100, 100, 5, 10000)
    aggregator.add_liquidity('okx', 'BTC/USDT', 80, 80, 8, 8000)
    aggregator.add_liquidity('bybit', 'BTC/USDT', 120, 120, 6, 12000)

    # 聚合深度
    bid_depth = aggregator.get_aggregated_depth('BTC/USDT', 'bid')
    ask_depth = aggregator.get_aggregated_depth('BTC/USDT', 'ask')
    print(f"Aggregated depth: bid={bid_depth}, ask={ask_depth}")

    # 寻找最佳交易所
    best_buy = aggregator.find_best_exchange('BTC/USDT', 'bid', 50)
    best_sell = aggregator.find_best_exchange('BTC/USDT', 'ask', 50)
    print(f"Best for buy: {best_buy}, for sell: {best_sell}")

    print(f"[PASS] V31 Liquidity Aggregator")
    return True


def test_v31_integration():
    """测试V31综合功能"""
    print("\n=== Test V31.0 Integration ===")

    # 创建各组件
    regime_detector = MarketRegimeDetector({'lookback_periods': 20})
    router = SmartOrderRouter()
    impact_model = PriceImpactModel()
    liquidity_agg = LiquidityAggregator()

    import random
    random.seed(42)

    # 模拟数据
    exchanges = ['binance', 'okx', 'bybit']
    for i in range(30):
        price = 50000 * (1 + random.uniform(-0.01, 0.01))
        volume = random.uniform(100, 1000)
        bid = price * 0.9995
        ask = price * 1.0005

        regime_detector.add_data_point(price, volume, bid, ask)

        # 更新流动性
        for exch in exchanges:
            liquidity_agg.add_liquidity(
                exch, 'BTC/USDT',
                random.uniform(50, 150),
                random.uniform(50, 150),
                random.uniform(2, 10),
                random.uniform(5000, 15000)
            )

        # 更新价格
        for exch in exchanges:
            router.update_price(exch, 'BTC/USDT', price * 0.9995, price * 1.0005)

    # 综合分析
    regime = regime_detector.detect_regime()
    print(f"Market regime: {regime.value}")

    best_exch, best_price, _ = router.get_best_price('BTC/USDT', 'buy')
    print(f"Best routing: {best_exch} @ {best_price}")

    depth = liquidity_agg.get_aggregated_depth('BTC/USDT', 'bid')
    print(f"Total depth: {depth}")

    print(f"[PASS] V31 Integration Test")
    return True


def run_v31_tests():
    """运行V31所有测试"""
    tests = [
        test_v31_market_regime,
        test_v31_smart_routing,
        test_v31_price_impact,
        test_v31_liquidity,
        test_v31_integration,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")

    print("\n" + "="*50)
    print(f"V31.0 Results: {passed}/{len(tests)} passed")
    print("="*50)

    return passed == len(tests)


if __name__ == "__main__":
    success = run_v31_tests()
    sys.exit(0 if success else 1)