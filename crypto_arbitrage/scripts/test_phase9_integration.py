"""Phase 9 集成测试脚本

测试Phase 9核心功能：真实数据生成、性能测试、优化和监控。

创建时间：2026-04-19 18:57:00
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_generation.market_data_generator import (
    MarketDataGenerator,
    PriceSpreadSimulator,
    TradingScenarioBuilder
)

from performance_testing.benchmark_suite import BenchmarkSuite
from performance_testing.load_test import LoadTest

from performance_optimization.cache_optimizer import CacheOptimizer

from monitoring_diagnostics.performance_profiler import PerformanceProfiler

from storage.storage_factory import create_auto_storage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase9IntegrationTest:
    """Phase 9集成测试类"""

    def __init__(self):
        self.test_results = {}

    async def test_data_generation(self):
        """测试数据生成功能"""
        logger.info("=" * 60)
        logger.info("测试1: 真实数据生成")
        logger.info("=" * 60)

        try:
            # 创建市场数据生成器
            generator = MarketDataGenerator()

            # 测试K线生成
            logger.info("生成K线数据...")
            klines = generator.generate_klines(
                symbol='BTC/USDT',
                count=100,
                interval='1m',
                market_trend='bull'
            )
            assert len(klines) == 100, "K线数量不正确"
            assert all('open' in k for k in klines), "K线格式不正确"
            logger.info(f"✅ K线生成成功: {len(klines)} 条")

            # 测试订单簿生成
            logger.info("生成订单簿数据...")
            orderbook = generator.generate_orderbook('BTC/USDT', depth=20)
            assert 'bids' in orderbook, "订单簿缺少买单"
            assert 'asks' in orderbook, "订单簿缺少卖单"
            assert len(orderbook['bids']) == 20, "买单深度不正确"
            logger.info(f"✅ 订单簿生成成功: {len(orderbook['bids'])} 买单, {len(orderbook['asks'])} 卖单")

            # 测试价差模拟
            logger.info("模拟跨交易所价差...")
            spread_simulator = PriceSpreadSimulator()
            arbitrages = spread_simulator.simulate_cross_exchange_arbitrage(
                symbol='BTC/USDT',
                count=10
            )
            assert len(arbitrages) == 10, "套利机会数量不正确"
            logger.info(f"✅ 价差模拟成功: {len(arbitrages)} 条套利机会")

            # 测试场景构建
            logger.info("构建交易场景...")
            scenario_builder = TradingScenarioBuilder()
            scenario = scenario_builder.build_bull_market_scenario(
                duration_hours=1,
                symbols=['BTC/USDT']
            )
            assert scenario['type'] == 'bull_market', "场景类型不正确"
            logger.info(f"✅ 场景构建成功: {scenario['type']}")

            self.test_results['data_generation'] = 'PASSED'

        except Exception as e:
            logger.error(f"❌ 数据生成测试失败: {e}")
            self.test_results['data_generation'] = f'FAILED: {str(e)}'

    async def test_benchmark_suite(self):
        """测试基准测试套件"""
        logger.info("=" * 60)
        logger.info("测试2: 基准测试套件")
        logger.info("=" * 60)

        try:
            # 创建存储
            storage = await create_auto_storage({'storage_type': 'local_vector'})

            # 创建基准测试套件
            suite = BenchmarkSuite(storage)

            # 运行完整基准测试
            logger.info("运行基准测试...")
            benchmark_config = {
                'add_count': 10,
                'search_iterations': 10,
                'get_count': 10,
                'batch_size': 5,
                'batch_count': 2,
                'list_count': 5,
                'count_count': 5,
            }
            report = await suite.run_full_benchmark_suite(benchmark_config)

            assert 'results' in report, "基准测试报告缺少结果"
            assert len(report['results']) > 0, "基准测试没有结果"

            logger.info(f"✅ 基准测试完成: {len(report['results'])} 个操作")

            # 打印摘要
            summary = report['summary']
            logger.info(f"  总操作数: {summary['total_operations']}")
            logger.info(f"  最慢操作: {summary['slowest_operation']}")
            logger.info(f"  最快操作: {summary['fastest_operation']}")
            logger.info(f"  最高吞吐量: {summary['highest_throughput']}")

            self.test_results['benchmark_suite'] = 'PASSED'

        except Exception as e:
            logger.error(f"❌ 基准测试失败: {e}")
            self.test_results['benchmark_suite'] = f'FAILED: {str(e)}'

    async def test_cache_optimizer(self):
        """测试缓存优化器"""
        logger.info("=" * 60)
        logger.info("测试3: 缓存优化器")
        logger.info("=" * 60)

        try:
            # 创建存储
            storage = await create_auto_storage({'storage_type': 'local_vector'})

            # 创建缓存优化器
            cache_optimizer = CacheOptimizer(storage, {'max_size': 100, 'preload_size': 50})

            # 测试缓存功能
            logger.info("测试缓存功能...")

            async def fetch_data(key):
                """模拟数据获取"""
                return await storage.add_knowledge(f"Cache test {key}", {'key': key})

            # 测试带缓存获取
            key = "test_key_1"
            result1 = await cache_optimizer.get_with_cache(key, lambda: fetch_data(key))
            assert result1 is not None, "首次获取失败"

            result2 = await cache_optimizer.get_with_cache(key, lambda: fetch_data(key))
            assert result2 == result1, "缓存获取失败"

            # 检查缓存统计
            stats = cache_optimizer.get_cache_statistics()
            logger.info(f"  LRU缓存命中率: {stats['lru_cache']['hit_rate']:.2%}")

            # 测试缓存大小优化
            logger.info("测试缓存大小优化...")
            access_pattern = {f"key_{i}": 10 - i for i in range(10)}
            optimization = cache_optimizer.optimize_cache_size(access_pattern)
            logger.info(f"  推荐缓存大小: {optimization['recommended_size']}")

            logger.info("✅ 缓存优化器测试完成")
            self.test_results['cache_optimizer'] = 'PASSED'

        except Exception as e:
            logger.error(f"❌ 缓存优化器测试失败: {e}")
            self.test_results['cache_optimizer'] = f'FAILED: {str(e)}'

    async def test_performance_profiler(self):
        """测试性能分析器"""
        logger.info("=" * 60)
        logger.info("测试4: 性能分析器")
        logger.info("=" * 60)

        try:
            # 创建存储
            storage = await create_auto_storage({'storage_type': 'local_vector'})

            # 创建性能分析器
            profiler = PerformanceProfiler()

            # 测试函数性能分析
            logger.info("分析函数性能...")

            async def test_function():
                """测试函数"""
                await storage.add_knowledge("Profiler test", {'test': True})
                return "result"

            profile_result = await profiler.profile_function(test_function)

            assert 'profile' in profile_result, "分析结果缺少profile"
            assert 'duration_ms' in profile_result['profile'], "分析结果缺少duration_ms"

            logger.info(f"  函数执行时间: {profile_result['profile']['duration_ms']:.3f} ms")
            logger.info(f"  内存使用: {profile_result['profile']['memory_used_mb']:.2f} MB")

            # 测试存储操作分析
            logger.info("分析存储操作性能...")
            storage_profile = await profiler.profile_storage_operations(
                storage,
                ['add_knowledge', 'search_knowledge'],
                {'iterations': 5}
            )

            assert 'results' in storage_profile, "存储分析结果缺少results"
            logger.info(f"  分析的操作数: {len(storage_profile['results'])}")

            logger.info("✅ 性能分析器测试完成")
            self.test_results['performance_profiler'] = 'PASSED'

        except Exception as e:
            logger.error(f"❌ 性能分析器测试失败: {e}")
            self.test_results['performance_profiler'] = f'FAILED: {str(e)}'

    def print_summary(self):
        """打印测试摘要"""
        logger.info("=" * 60)
        logger.info("Phase 9 集成测试摘要")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == 'PASSED')
        failed_tests = total_tests - passed_tests

        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests}")
        logger.info(f"失败: {failed_tests}")
        logger.info(f"通过率: {(passed_tests / total_tests * 100) if total_tests > 0 else 0:.1f}%")

        logger.info("\n详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result == 'PASSED' else f"❌ {result}"
            logger.info(f"  {test_name}: {status}")

        logger.info("=" * 60)

        if failed_tests == 0:
            logger.info("🎉 Phase 9 所有测试通过！")
            return True
        else:
            logger.warning(f"⚠️  Phase 9 有 {failed_tests} 个测试失败")
            return False


async def main():
    """主函数"""
    logger.info("Phase 9 集成测试开始")
    logger.info("=" * 60)

    tester = Phase9IntegrationTest()

    # 运行所有测试
    await tester.test_data_generation()
    await tester.test_benchmark_suite()
    await tester.test_cache_optimizer()
    await tester.test_performance_profiler()

    # 打印摘要
    success = tester.print_summary()

    return 0 if success else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
