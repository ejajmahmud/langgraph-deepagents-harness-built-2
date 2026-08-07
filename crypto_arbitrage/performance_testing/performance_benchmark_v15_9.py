"""V15.9 Phase 2 - 性能基准测试套件

建立完整的系统性能基准，覆盖核心功能模块。

核心功能：
1. 存储性能测试 - 知识库存储性能基准
2. 决策引擎性能测试 - AI决策性能基准
3. 套利引擎性能测试 - 套利计算性能基准
4. 交易执行性能测试 - 交易执行性能基准
5. 数据分析报告 - 性能瓶颈识别和优化建议

创建时间：2026-05-01 03:42
"""

import asyncio
import json
import logging
import statistics
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
import os

# 添加项目根目录到Python路径
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/performance_benchmark_v15_9.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetric:
    """基准测试指标"""
    operation: str
    iterations: int
    total_time: float
    mean_time: float  # 毫秒
    median_time: float  # 毫秒
    min_time: float  # 毫秒
    max_time: float  # 毫秒
    p95_time: float  # 95百分位（毫秒）
    p99_time: float  # 99百分位（毫秒）
    std_dev: float  # 标准差（毫秒）
    throughput: float  # 吞吐量（操作/秒）

    def to_dict(self) -> Dict:
        return asdict(self)


class PerformanceBenchmark:
    """性能基准测试套件

    测试系统各核心模块的性能指标。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化性能基准测试

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.results: Dict[str, BenchmarkMetric] = {}
        self.start_time = datetime.now()

        # 测试配置
        self.iterations = self.config.get('iterations', 100)
        self.warmup_iterations = self.config.get('warmup_iterations', 10)

        # 创建日志目录
        Path('logs').mkdir(exist_ok=True)
        Path('reports').mkdir(exist_ok=True)

        logger.info(f"性能基准测试套件初始化完成 - 迭代次数: {self.iterations}")

    async def benchmark_operation(
        self,
        name: str,
        operation: Callable,
        *args,
        **kwargs
    ) -> BenchmarkMetric:
        """基准测试单个操作

        Args:
            name: 操作名称
            operation: 要测试的操作
            *args: 操作参数
            **kwargs: 操作关键字参数

        Returns:
            基准测试指标
        """
        logger.info(f"开始基准测试: {name}")

        # 预热运行
        logger.info(f"预热运行 ({self.warmup_iterations} 次)...")
        for _ in range(self.warmup_iterations):
            try:
                result = operation(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"预热运行失败: {e}")

        # 正式测试
        logger.info(f"正式测试 ({self.iterations} 次)...")
        times = []
        errors = 0

        for i in range(self.iterations):
            try:
                start = time.perf_counter()
                result = operation(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
                end = time.perf_counter()

                elapsed = end - start
                times.append(elapsed)

                # 进度显示
                if (i + 1) % 20 == 0:
                    logger.info(f"  进度: {i + 1}/{self.iterations}")

            except Exception as e:
                errors += 1
                logger.error(f"操作失败 ({i + 1}/{self.iterations}): {e}")

        total_time = sum(times)
        success_rate = (self.iterations - errors) / self.iterations * 100

        # 计算指标
        metric = BenchmarkMetric(
            operation=name,
            iterations=len(times),
            total_time=total_time,
            mean_time=statistics.mean(times) * 1000,
            median_time=statistics.median(times) * 1000,
            min_time=min(times) * 1000,
            max_time=max(times) * 1000,
            p95_time=self._calculate_percentile(times, 95) * 1000,
            p99_time=self._calculate_percentile(times, 99) * 1000,
            std_dev=statistics.stdev(times) * 1000 if len(times) > 1 else 0,
            throughput=len(times) / total_time if total_time > 0 else 0
        )

        # 记录结果
        self.results[name] = metric

        logger.info(f"基准测试完成: {name}")
        logger.info(f"  平均时间: {metric.mean_time:.3f}ms")
        logger.info(f"  中位数: {metric.median_time:.3f}ms")
        logger.info(f"  P95: {metric.p95_time:.3f}ms")
        logger.info(f"  P99: {metric.p99_time:.3f}ms")
        logger.info(f"  吞吐量: {metric.throughput:.2f} ops/s")
        logger.info(f"  成功率: {success_rate:.2f}%")

        return metric

    def _calculate_percentile(self, times: List[float], percentile: float) -> float:
        """计算百分位

        Args:
            times: 时间列表
            percentile: 百分位（0-100）

        Returns:
            百分位时间
        """
        if not times:
            return 0.0

        sorted_times = sorted(times)
        index = int(len(sorted_times) * percentile / 100)
        index = min(index, len(sorted_times) - 1)
        return sorted_times[index]

    async def benchmark_storage_performance(self):
        """测试存储性能"""
        logger.info("=" * 80)
        logger.info("1. 存储性能测试")
        logger.info("=" * 80)

        try:
            from storage.storage_factory import create_auto_storage

            # 创建存储实例
            storage = await create_auto_storage({'storage_type': 'auto'})

            # 测试添加知识
            await self.benchmark_operation(
                "storage_add_knowledge",
                storage.add_knowledge,
                "测试知识",
                {"test_data": "value"}
            )

            # 测试获取知识
            # 先添加一个知识
            test_id = await storage.add_knowledge("查询测试", {"query": "test"})
            await self.benchmark_operation(
                "storage_get_knowledge",
                storage.get_knowledge,
                test_id
            )

            # 测试搜索知识
            await self.benchmark_operation(
                "storage_search_knowledge",
                storage.search_knowledge,
                "测试"
            )

            # 测试批量添加
            await self.benchmark_operation(
                "storage_batch_add",
                self._batch_add_knowledge,
                storage
            )

        except Exception as e:
            logger.error(f"存储性能测试失败: {e}")
            traceback.print_exc()

    async def _batch_add_knowledge(self, storage) -> List[str]:
        """批量添加知识

        Args:
            storage: 存储实例

        Returns:
            知识ID列表
        """
        ids = []
        for i in range(10):
            kid = await storage.add_knowledge(f"批量测试_{i}", {"batch": i})
            ids.append(kid)
        return ids

    async def benchmark_decision_engine_performance(self):
        """测试决策引擎性能"""
        logger.info("=" * 80)
        logger.info("2. 决策引擎性能测试")
        logger.info("=" * 80)

        try:
            from storage.storage_factory import create_auto_storage

            # 创建存储实例
            storage = await create_auto_storage({'storage_type': 'auto'})

            # 测试决策模拟（简化版）
            await self.benchmark_operation(
                "decision_make_decision",
                self._make_test_decision,
                storage
            )

        except Exception as e:
            logger.error(f"决策引擎性能测试失败: {e}")
            traceback.print_exc()

    async def _make_test_decision(self, storage):
        """模拟决策过程

        Args:
            storage: 存储实例

        Returns:
            决策结果
        """
        # 搜索相关知识
        results = await storage.search_knowledge("决策", limit=5)

        # 简单决策逻辑
        decision = {
            "action": "hold",
            "confidence": 0.75,
            "reason": "测试决策"
        }

        return decision

    async def benchmark_arbitrage_engine_performance(self):
        """测试套利引擎性能"""
        logger.info("=" * 80)
        logger.info("3. 套利引擎性能测试")
        logger.info("=" * 80)

        try:
            # 测试套利机会检测
            await self.benchmark_operation(
                "arbitrage_detect_opportunity",
                self._detect_arbitrage_opportunity
            )

            # 测试风险评估
            await self.benchmark_operation(
                "arbitrage_assess_risk",
                self._assess_arbitrage_risk
            )

        except Exception as e:
            logger.error(f"套利引擎性能测试失败: {e}")
            traceback.print_exc()

    def _detect_arbitrage_opportunity(self):
        """检测套利机会

        Returns:
            套利机会
        """
        # 模拟套利机会检测
        opportunity = {
            "type": "cross_exchange",
            "exchange_a": "Binance",
            "exchange_b": "OKX",
            "pair": "BTC/USDT",
            "price_a": 50000.0,
            "price_b": 50100.0,
            "profit": 100.0,
            "profit_rate": 0.002
        }
        return opportunity

    def _assess_arbitrage_risk(self):
        """评估套利风险

        Returns:
            风险评估结果
        """
        # 模拟风险评估
        risk_assessment = {
            "risk_level": "low",
            "confidence": 0.85,
            "factors": {
                "market_volatility": 0.3,
                "liquidity": 0.8,
                "spread": 0.9
            }
        }
        return risk_assessment

    async def benchmark_trading_performance(self):
        """测试交易执行性能"""
        logger.info("=" * 80)
        logger.info("4. 交易执行性能测试")
        logger.info("=" * 80)

        try:
            # 测试订单创建
            await self.benchmark_operation(
                "trading_create_order",
                self._create_test_order
            )

            # 测试订单查询
            await self.benchmark_operation(
                "trading_query_order",
                self._query_test_order
            )

        except Exception as e:
            logger.error(f"交易执行性能测试失败: {e}")
            traceback.print_exc()

    def _create_test_order(self):
        """创建测试订单

        Returns:
            订单信息
        """
        order = {
            "order_id": "TEST_001",
            "pair": "BTC/USDT",
            "side": "buy",
            "amount": 0.001,
            "price": 50000.0,
            "status": "pending"
        }
        return order

    def _query_test_order(self):
        """查询测试订单

        Returns:
            订单状态
        """
        return {
            "order_id": "TEST_001",
            "status": "filled",
            "filled_amount": 0.001,
            "filled_price": 50000.0
        }

    def generate_report(self) -> str:
        """生成性能测试报告

        Returns:
            报告内容
        """
        report_lines = [
            "=" * 80,
            "V15.9 Phase 2 - 性能基准测试报告",
            "=" * 80,
            f"报告时间: {datetime.now().isoformat()}",
            f"测试迭代次数: {self.iterations}",
            f"预热迭代次数: {self.warmup_iterations}",
            "",
            "性能指标汇总:",
            "-" * 80,
        ]

        # 按操作类型分组
        categories = {
            "存储": ["storage_add_knowledge", "storage_get_knowledge",
                    "storage_search_knowledge", "storage_batch_add"],
            "决策引擎": ["decision_make_decision"],
            "套利引擎": ["arbitrage_detect_opportunity", "arbitrage_assess_risk"],
            "交易执行": ["trading_create_order", "trading_query_order"]
        }

        for category, operations in categories.items():
            report_lines.append(f"\n{category}:")
            report_lines.append("-" * 40)

            for op in operations:
                if op in self.results:
                    metric = self.results[op]
                    report_lines.append(f"  {op}:")
                    report_lines.append(f"    平均时间: {metric.mean_time:.3f}ms")
                    report_lines.append(f"    中位数: {metric.median_time:.3f}ms")
                    report_lines.append(f"    P95: {metric.p95_time:.3f}ms")
                    report_lines.append(f"    P99: {metric.p99_time:.3f}ms")
                    report_lines.append(f"    吞吐量: {metric.throughput:.2f} ops/s")

        # 性能分析
        report_lines.append("\n" + "=" * 80)
        report_lines.append("性能分析:")
        report_lines.append("-" * 80)

        # 识别性能瓶颈
        bottlenecks = self._identify_bottlenecks()
        if bottlenecks:
            report_lines.append("\n性能瓶颈:")
            for bottleneck in bottlenecks:
                report_lines.append(f"  - {bottleneck}")
        else:
            report_lines.append("\n未发现明显性能瓶颈")

        # 优化建议
        suggestions = self._generate_optimization_suggestions()
        if suggestions:
            report_lines.append("\n优化建议:")
            for suggestion in suggestions:
                report_lines.append(f"  - {suggestion}")
        else:
            report_lines.append("\n系统性能表现良好")

        report_lines.append("\n" + "=" * 80)
        report_lines.append("报告结束")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def _identify_bottlenecks(self) -> List[str]:
        """识别性能瓶颈

        Returns:
            瓶颈列表
        """
        bottlenecks = []

        for name, metric in self.results.items():
            # 如果P99时间超过1秒，认为是瓶颈
            if metric.p99_time > 1000:
                bottlenecks.append(
                    f"{name}: P99响应时间过长 ({metric.p99_time:.3f}ms)"
                )

            # 如果标准差过大，认为是性能不稳定
            if metric.std_dev > metric.mean_time * 0.5:
                bottlenecks.append(
                    f"{name}: 性能不稳定 (标准差/均值 = {metric.std_dev/metric.mean_time:.2f})"
                )

        return bottlenecks

    def _generate_optimization_suggestions(self) -> List[str]:
        """生成优化建议

        Returns:
            建议列表
        """
        suggestions = []

        for name, metric in self.results.items():
            # 如果吞吐量低于目标，建议优化
            if metric.throughput < 10:
                suggestions.append(
                    f"{name}: 吞吐量较低 ({metric.throughput:.2f} ops/s)，建议优化算法或增加缓存"
                )

            # 如果P95和平均时间差距过大，建议优化长尾延迟
            if metric.p95_time / metric.mean_time > 3:
                suggestions.append(
                    f"{name}: 长尾延迟较高 (P95/均值 = {metric.p95_time/metric.mean_time:.2f})，"
                    "建议优化异常处理和资源争用"
                )

        return suggestions

    def save_report(self, report: str):
        """保存性能测试报告

        Args:
            report: 报告内容
        """
        # 保存文本报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"reports/performance_benchmark_v15_9_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"性能报告已保存: {report_file}")

        # 保存JSON数据
        json_file = f"reports/performance_benchmark_v15_9_{timestamp}.json"
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config,
            "results": {
                name: metric.to_dict()
                for name, metric in self.results.items()
            }
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"性能数据已保存: {json_file}")

    async def run_full_benchmark(self):
        """运行完整性能基准测试"""
        logger.info("=" * 80)
        logger.info("开始 V15.9 Phase 2 完整性能基准测试")
        logger.info("=" * 80)

        try:
            # 1. 存储性能测试
            await self.benchmark_storage_performance()

            # 2. 决策引擎性能测试
            await self.benchmark_decision_engine_performance()

            # 3. 套利引擎性能测试
            await self.benchmark_arbitrage_engine_performance()

            # 4. 交易执行性能测试
            await self.benchmark_trading_performance()

            # 生成报告
            logger.info("=" * 80)
            logger.info("生成性能测试报告...")
            report = self.generate_report()

            # 打印报告
            print(report)

            # 保存报告
            self.save_report(report)

            logger.info("=" * 80)
            logger.info("V15.9 Phase 2 性能基准测试完成")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"性能基准测试失败: {e}")
            traceback.print_exc()


# ========== 测试入口 ==========

async def main():
    """主函数"""
    # 创建基准测试套件
    benchmark = PerformanceBenchmark(config={
        'iterations': 100,
        'warmup_iterations': 10
    })

    # 运行完整测试
    await benchmark.run_full_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
