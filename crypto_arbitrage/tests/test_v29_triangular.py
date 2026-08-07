"""三角套利策略测试"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from strategies.triangular_arbitrage import TriangularArbitrageStrategy


class TestTriangularArbitrage:
    """三角套利策略测试"""

    def test_strategy_initialization(self) -> bool:
        """测试策略初始化"""
        config = {
            'min_profit_rate': 0.5,
            'max_position_size': 1000,
            'triangles': [
                {
                    'base': 'USDT',
                    'path': [
                        {'from': 'USDT', 'to': 'BTC', 'pair': 'BTC/USDT'},
                        {'from': 'BTC', 'to': 'ETH', 'pair': 'ETH/BTC'},
                        {'from': 'ETH', 'to': 'USDT', 'pair': 'ETH/USDT'}
                    ]
                }
            ]
        }
        strategy = TriangularArbitrageStrategy(config)
        assert strategy is not None
        assert strategy.STRATEGY_NAME == "triangular"
        assert len(strategy.triangles) == 1
        print("[PASS] 策略初始化测试")
        return True

    def test_triangle_calculation(self) -> bool:
        """测试三角计算"""
        from strategies.triangular_arbitrage import calculate_triangle_profit

        # 测试用例: USDT -> BTC -> ETH -> USDT
        prices = {
            'BTC/USDT': 50000.0,  # 1 BTC = 50000 USDT
            'ETH/BTC': 0.02,        # 1 ETH = 0.02 BTC
            'ETH/USDT': 2500.0      # 1 ETH = 2500 USDT
        }

        # 计算路径利润率
        # USDT -> BTC: 1 USDT = 1/50000 BTC
        # BTC -> ETH: 1 BTC = 1/0.02 = 50 ETH
        # ETH -> USDT: 50 ETH = 50 * 2500 = 125000 USDT
        # 利润率 = (125000 - 1) / 1 * 100% = 12499900%
        # 实际应该是: 实际价格 vs 理论价格
        # 理论价格: 1/50000 * 1/0.02 * 2500 = 1
        # 如果实际价格不是1，则存在套利机会

        result = calculate_triangle_profit(prices)
        assert result is not None
        print(f"[PASS] 三角计算测试: profit_rate={result.get('profit_rate', 0):.4f}%")
        return True

    def test_profit_threshold(self) -> bool:
        """测试利润阈值过滤"""
        from strategies.triangular_arbitrage import is_profitable_triangle

        # 低于阈值
        assert is_profitable_triangle(0.3, 0.5) == False
        # 等于阈值
        assert is_profitable_triangle(0.5, 0.5) == True
        # 高于阈值
        assert is_profitable_triangle(1.0, 0.5) == True
        print("[PASS] 利润阈值测试")
        return True


async def run_tests():
    """运行测试"""
    print("\n=== 三角套利策略测试 ===")
    tester = TestTriangularArbitrage()

    tests = [
        ("策略初始化", tester.test_strategy_initialization),
        ("三角计算", tester.test_triangle_calculation),
        ("利润阈值", tester.test_profit_threshold),
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