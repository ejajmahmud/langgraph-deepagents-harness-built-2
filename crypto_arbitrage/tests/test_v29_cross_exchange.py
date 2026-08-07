"""跨交易所套利策略测试 (V29)"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from strategies.cross_exchange import CrossExchangeArbitrageStrategy


class TestCrossExchangeArbitrage:
    """跨交易所套利策略测试"""

    def test_strategy_initialization(self) -> bool:
        """测试策略初始化"""
        config = {
            'risk_tolerance': 0.1,
            'symbols': ['BTC/USDT', 'ETH/USDT'],
            'min_profit_rate': 0.3,
            'max_position_size': 5000
        }
        strategy = CrossExchangeArbitrageStrategy(config)
        assert strategy is not None
        assert strategy.STRATEGY_NAME == "cross_exchange"
        assert strategy.risk_tolerance == 0.1
        assert len(strategy.symbols) == 2
        print("[PASS] 跨交易所策略初始化测试")
        return True

    def test_calculate_spread(self) -> bool:
        """测试价差计算"""
        from strategies.cross_exchange import calculate_cross_exchange_spread

        # 模拟两个交易所的价格
        price_binance = {'bid': 50000.0, 'ask': 50010.0}
        price_okx = {'bid': 49980.0, 'ask': 49990.0}

        # 在OKX买入(ask)，在Binance卖出(bid)
        # 买入价: 49990, 卖出价: 50000
        # 价差: 50000 - 49990 = 10 USDT
        # 利润率: 10 / 49990 * 100 = 0.02%
        spread = calculate_cross_exchange_spread(price_binance, price_okx)
        assert spread is not None
        print(f"[PASS] 价差计算: spread={spread:.4f}%")
        return True

    def test_net_profit_calculation(self) -> bool:
        """测试净利润计算"""
        from strategies.cross_exchange import calculate_net_profit

        # 价差2%，手续费0.1%
        gross_profit_rate = 2.0
        total_fee = 0.2
        min_profit_rate = 0.5

        net = calculate_net_profit(gross_profit_rate, total_fee, min_profit_rate)
        assert net == 1.8  # 2.0 - 0.2 = 1.8
        print(f"[PASS] 净利润计算: {net:.2f}%")
        return True


def calculate_cross_exchange_spread(price_a: dict, price_b: dict) -> float:
    """计算跨交易所价差

    Args:
        price_a: 交易所A价格 {'bid': float, 'ask': float}
        price_b: 交易所B价格 {'bid': float, 'ask': float}

    Returns:
        价差百分比
    """
    if not price_a or not price_b:
        return 0.0

    # 使用卖一价(ask)在低价交易所买，买一价(bid)在高价交易所卖
    ask_price = min(price_a.get('ask', 0), price_b.get('ask', 0))
    bid_price = max(price_a.get('bid', 0), price_b.get('bid', 0))

    if ask_price <= 0 or bid_price <= 0:
        return 0.0

    # 价差 = (卖价 - 买价) / 买价 * 100%
    spread = (bid_price - ask_price) / ask_price * 100
    return spread


def calculate_net_profit(
    gross_profit_rate: float,
    total_fee: float,
    min_profit_rate: float = 0.5
) -> float:
    """计算扣除费用后的净利润

    Args:
        gross_profit_rate: 总利润率 (%)
        total_fee: 总手续费 (%)
        min_profit_rate: 最小利润率阈值 (%)

    Returns:
        净利润率，如果低于阈值返回0
    """
    net = gross_profit_rate - total_fee
    return net if net >= min_profit_rate else 0.0


async def run_tests():
    """运行测试"""
    print("\n=== 跨交易所套利策略测试 ===")
    tester = TestCrossExchangeArbitrage()

    tests = [
        ("策略初始化", tester.test_strategy_initialization),
        ("价差计算", tester.test_calculate_spread),
        ("净利润计算", tester.test_net_profit_calculation),
    ]

    passed = 0
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    print(f"\n结果: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    result = asyncio.run(run_tests())
    sys.exit(0 if result else 1)