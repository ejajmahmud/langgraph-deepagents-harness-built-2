"""性能基准测试套件 - Phase 9核心模块

建立系统性能基准，为优化提供参考数据。

核心功能：
1. 基准测试 - 单操作性能基准
2. 性能对比 - 不同配置下性能对比
3. 趋势分析 - 性能趋势分析
4. 报告生成 - 详细的性能报告

创建时间：2026-04-19 18:57:00
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from storage.knowledge_storage_interface import KnowledgeStorage, SearchResult

logger = logging.getLogger(__name__)


class BenchmarkResult:
    """基准测试结果

    存储基准测试的详细结果。
    """

    def __init__(
        self,
        name: str,
        operation: str,
        iterations: int,
        total_time: float,
        results: List[float]
    ):
        self.name = name
        self.operation = operation
        self.iterations = iterations
        self.total_time = total_time
        self.results = results

    @property
    def mean_time(self) -> float:
        """平均时间（毫秒）"""
        return statistics.mean(self.results) * 1000

    @property
    def median_time(self) -> float:
        """中位数时间（毫秒）"""
        return statistics.median(self.results) * 1000

    @property
    def min_time(self) -> float:
        """最小时间（毫秒）"""
        return min(self.results) * 1000

    @property
    def max_time(self) -> float:
        """最大时间（毫秒）"""
        return max(self.results) * 1000

    @property
    def std_dev(self) -> float:
        """标准差（毫秒）"""
        if len(self.results) <= 1:
            return 0.0
        return statistics.stdev(self.results) * 1000

    @property
    def throughput(self) -> float:
        """吞吐量（操作/秒）"""
        if self.total_time == 0:
            return 0.0
        return self.iterations / self.total_time

    @property
    def p95_time(self) -> float:
        """95百分位时间（毫秒）"""
        if len(self.results) < 20:
            return self.max_time
        sorted_results = sorted(self.results)
        index = int(len(sorted_results) * 0.95)
        return sorted_results[index] * 1000

    @property
    def p99_time(self) -> float:
        """99百分位时间（毫秒）"""
        if len(self.results) < 100:
            return self.max_time
        sorted_results = sorted(self.results)
        index = int(len(sorted_results) * 0.99)
        return sorted_results[index] * 1000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            结果字典
        """
        return {
            'name': self.name,
            'operation': self.operation,
            'iterations': self.iterations,
            'total_time': round(self.total_time, 3),
            'mean_time_ms': round(self.mean_time, 3),
            'median_time_ms': round(self.median_time, 3),
            'min_time_ms': round(self.min_time, 3),
            'max_time_ms': round(self.max_time, 3),
            'std_dev_ms': round(self.std_dev, 3),
            'throughput_ops': round(self.throughput, 3),
            'p95_time_ms': round(self.p95_time, 3),
            'p99_time_ms': round(self.p99_time, 3),
        }


class BenchmarkSuite:
    """基准测试套件

    建立系统性能基准。
    """

    def __init__(self, storage: KnowledgeStorage, config: Dict[str, Any] = None):
        """初始化基准测试套件

        Args:
            storage: 存储实例
            config: 配置字典
        """
        self.storage = storage
        self.config = config or {}
        self.baselines: Dict[str, BenchmarkResult] = {}

        logger.info("基准测试套件初始化完成")

    async def benchmark_add_knowledge(
        self,
        count: int = 100,
        content_template: str = "Knowledge item {}"
    ) -> BenchmarkResult:
        """基准测试：添加知识

        Args:
            count: 测试数量
            content_template: 内容模板

        Returns:
            基准测试结果
        """
        logger.info(f"基准测试：添加知识 ({count} 条)")

        times = []
        for i in range(count):
            content = content_template.format(i)
            metadata = {'index': i, 'benchmark': True}

            start_time = time.perf_counter()
            await self.storage.add_knowledge(content, metadata)
            end_time = time.perf_counter()

            times.append(end_time - start_time)

        result = BenchmarkResult(
            name="add_knowledge",
            operation="add_knowledge",
            iterations=count,
            total_time=sum(times),
            results=times
        )

        self.baselines['add_knowledge'] = result
        logger.info(f"基准测试完成：平均 {result.mean_time:.3f}ms, 吞吐量 {result.throughput:.3f} ops/s")
        return result

    async def benchmark_search_knowledge(
        self,
        query: str = "search query",
        top_k: int = 10,
        iterations: int = 100
    ) -> BenchmarkResult:
        """基准测试：搜索知识

        Args:
            query: 查询内容
            top_k: 返回数量
            iterations: 测试次数

        Returns:
            基准测试结果
        """
        logger.info(f"基准测试：搜索知识 ({iterations} 次)")

        times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            await self.storage.search_knowledge(query, top_k)
            end_time = time.perf_counter()

            times.append(end_time - start_time)

        result = BenchmarkResult(
            name="search_knowledge",
            operation="search_knowledge",
            iterations=iterations,
            total_time=sum(times),
            results=times
        )

        self.baselines['search_knowledge'] = result
        logger.info(f"基准测试完成：平均 {result.mean_time:.3f}ms, 吞吐量 {result.throughput:.3f} ops/s")
        return result

    async def benchmark_get_knowledge(
        self,
        count: int = 100
    ) -> BenchmarkResult:
        """基准测试：获取知识

        Args:
            count: 测试数量

        Returns:
            基准测试结果
        """
        # 首先添加一些知识
        knowledge_ids = []
        for i in range(count):
            knowledge_id = await self.storage.add_knowledge(
                f"Test knowledge {i}",
                {'index': i, 'benchmark': True}
            )
            knowledge_ids.append(knowledge_id)

        logger.info(f"基准测试：获取知识 ({count} 条)")

        times = []
        for kid in knowledge_ids:
            start_time = time.perf_counter()
            await self.storage.get_knowledge(kid)
            end_time = time.perf_counter()

            times.append(end_time - start_time)

        result = BenchmarkResult(
            name="get_knowledge",
            operation="get_knowledge",
            iterations=count,
            total_time=sum(times),
            results=times
        )

        self.baselines['get_knowledge'] = result
        logger.info(f"基准测试完成：平均 {result.mean_time:.3f}ms, 吞吐量 {result.throughput:.3f} ops/s")
        return result

    async def benchmark_batch_operations(
        self,
        batch_size: int = 10,
        batches: int = 10
    ) -> BenchmarkResult:
        """基准测试：批量操作

        Args:
            batch_size: 批量大小
            batches: 批量次数

        Returns:
            基准测试结果
        """
        logger.info(f"基准测试：批量操作 ({batch_size} x {batches})")

        times = []
        total_operations = 0

        for batch_idx in range(batches):
            start_time = time.perf_counter()

            # 批量添加知识
            for i in range(batch_size):
                await self.storage.add_knowledge(
                    f"Batch {batch_idx} - Item {i}",
                    {'batch': batch_idx, 'index': i}
                )
                total_operations += 1

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        result = BenchmarkResult(
            name="batch_operations",
            operation="batch_operations",
            iterations=batches,
            total_time=sum(times),
            results=times
        )

        self.baselines['batch_operations'] = result
        logger.info(f"基准测试完成：平均 {result.mean_time:.3f}ms, 总操作 {total_operations}")
        return result

    async def benchmark_list_knowledge(
        self,
        count: int = 10,
        limit: int = 100
    ) -> BenchmarkResult:
        """基准测试：列出知识

        Args:
            count: 测试次数
            limit: 列表限制

        Returns:
            基准测试结果
        """
        logger.info(f"基准测试：列出知识 ({count} 次)")

        times = []
        for _ in range(count):
            start_time = time.perf_counter()
            await self.storage.list_knowledge(limit=limit)
            end_time = time.perf_counter()

            times.append(end_time - start_time)

        result = BenchmarkResult(
            name="list_knowledge",
            operation="list_knowledge",
            iterations=count,
            total_time=sum(times),
            results=times
        )

        self.baselines['list_knowledge'] = result
        logger.info(f"基准测试完成：平均 {result.mean_time:.3f}ms, 吞吐量 {result.throughput:.3f} ops/s")
        return result

    async def benchmark_count_knowledge(
        self,
        count: int = 100
    ) -> BenchmarkResult:
        """基准测试：统计知识数量

        Args:
            count: 测试次数

        Returns:
            基准测试结果
        """
        logger.info(f"基准测试：统计知识数量 ({count} 次)")

        times = []
        for _ in range(count):
            start_time = time.perf_counter()
            await self.storage.count_knowledge()
            end_time = time.perf_counter()

            times.append(end_time - start_time)

        result = BenchmarkResult(
            name="count_knowledge",
            operation="count_knowledge",
            iterations=count,
            total_time=sum(times),
            results=times
        )

        self.baselines['count_knowledge'] = result
        logger.info(f"基准测试完成：平均 {result.mean_time:.3f}ms, 吞吐量 {result.throughput:.3f} ops/s")
        return result

    async def run_full_benchmark_suite(
        self,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """运行完整基准测试套件

        Args:
            config: 测试配置

        Returns:
            完整基准测试报告
        """
        if config is None:
            config = {
                'add_count': 100,
                'search_iterations': 100,
                'get_count': 100,
                'batch_size': 10,
                'batch_count': 10,
                'list_count': 10,
                'count_count': 100,
            }

        logger.info("开始运行完整基准测试套件")

        results = {}
        start_time = time.time()

        try:
            # 测试1: 添加知识
            results['add_knowledge'] = (
                await self.benchmark_add_knowledge(count=config['add_count'])
            ).to_dict()

            # 测试2: 搜索知识
            results['search_knowledge'] = (
                await self.benchmark_search_knowledge(iterations=config['search_iterations'])
            ).to_dict()

            # 测试3: 获取知识
            results['get_knowledge'] = (
                await self.benchmark_get_knowledge(count=config['get_count'])
            ).to_dict()

            # 测试4: 批量操作
            results['batch_operations'] = (
                await self.benchmark_batch_operations(
                    batch_size=config['batch_size'],
                    batches=config['batch_count']
                )
            ).to_dict()

            # 测试5: 列出知识
            results['list_knowledge'] = (
                await self.benchmark_list_knowledge(count=config['list_count'])
            ).to_dict()

            # 测试6: 统计知识
            results['count_knowledge'] = (
                await self.benchmark_count_knowledge(count=config['count_count'])
            ).to_dict()

        except Exception as e:
            logger.error(f"基准测试失败: {e}")
            raise

        total_time = time.time() - start_time

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': round(total_time, 3),
            'storage_type': type(self.storage).__name__,
            'config': config,
            'results': results,
            'summary': self._generate_summary(results)
        }

        logger.info(f"完整基准测试套件完成，总耗时 {total_time:.3f}秒")
        return report

    def _generate_summary(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """生成测试摘要

        Args:
            results: 测试结果字典

        Returns:
            摘要字典
        """
        summary = {
            'slowest_operation': None,
            'fastest_operation': None,
            'highest_throughput': None,
            'total_operations': 0,
            'critical_operations': []
        }

        mean_times = {}
        throughputs = {}

        for name, result in results.items():
            mean_times[name] = result['mean_time_ms']
            throughputs[name] = result.get('throughput_ops', 0)
            summary['total_operations'] += result['iterations']

        if mean_times:
            # 最慢操作
            summary['slowest_operation'] = max(mean_times.items(), key=lambda x: x[1])

            # 最快操作
            summary['fastest_operation'] = min(mean_times.items(), key=lambda x: x[1])

        if throughputs:
            # 最高吞吐量
            summary['highest_throughput'] = max(throughputs.items(), key=lambda x: x[1])

        # 关键操作（P99 > 100ms）
        for name, result in results.items():
            if result['p99_time_ms'] > 100:
                summary['critical_operations'].append({
                    'operation': name,
                    'p99_time_ms': result['p99_time_ms'],
                    'throughput_ops': result.get('throughput_ops', 0)
                })

        return summary

    def export_report(self, report: Dict[str, Any], filepath: str) -> None:
        """导出基准测试报告

        Args:
            report: 基准测试报告
            filepath: 导出文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"基准测试报告已导出到: {filepath}")

    def compare_with_baseline(
        self,
        current_results: Dict[str, Dict[str, Any]],
        baseline_file: str
    ) -> Dict[str, Any]:
        """与基准线对比

        Args:
            current_results: 当前测试结果
            baseline_file: 基准线文件路径

        Returns:
            对比报告
        """
        try:
            with open(baseline_file, 'r', encoding='utf-8') as f:
                baseline = json.load(f)

            comparison = {
                'timestamp': datetime.now().isoformat(),
                'baseline_file': baseline_file,
                'improvements': [],
                'regressions': [],
                'changes': {}
            }

            for name, current in current_results.items():
                if name in baseline.get('results', {}):
                    baseline_result = baseline['results'][name]
                    current_mean = current['mean_time_ms']
                    baseline_mean = baseline_result['mean_time_ms']

                    if baseline_mean > 0:
                        change_pct = ((current_mean - baseline_mean) / baseline_mean) * 100
                        comparison['changes'][name] = {
                            'baseline_ms': baseline_mean,
                            'current_ms': current_mean,
                            'change_pct': round(change_pct, 2)
                        }

                        if change_pct < -5:  # 改善超过5%
                            comparison['improvements'].append({
                                'operation': name,
                                'improvement_pct': round(abs(change_pct), 2)
                            })
                        elif change_pct > 5:  # 退化超过5%
                            comparison['regressions'].append({
                                'operation': name,
                                'regression_pct': round(change_pct, 2)
                            })

            return comparison

        except Exception as e:
            logger.error(f"基准线对比失败: {e}")
            raise


class PerformanceMetrics:
    """性能指标

    收集和计算各种性能指标。
    """

    def __init__(self):
        self.metrics = {}

    def record_metric(self, name: str, value: float) -> None:
        """记录指标

        Args:
            name: 指标名称
            value: 指标值
        """
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_statistics(self, name: str) -> Dict[str, float]:
        """获取指标统计

        Args:
            name: 指标名称

        Returns:
            统计字典
        """
        if name not in self.metrics or len(self.metrics[name]) == 0:
            return {}

        values = self.metrics[name]

        return {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
            'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
        }

    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """获取所有指标统计

        Returns:
            所有指标的统计
        """
        return {name: self.get_statistics(name) for name in self.metrics}


# ========== 便捷函数 ==========

async def run_benchmark_suite(
    storage: KnowledgeStorage,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """运行基准测试套件

    Args:
        storage: 存储实例
        config: 测试配置

    Returns:
        基准测试报告
    """
    suite = BenchmarkSuite(storage, config)
    return await suite.run_full_benchmark_suite(config)


async def run_single_benchmark(
    storage: KnowledgeStorage,
    operation: str,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """运行单个基准测试

    Args:
        storage: 存储实例
        operation: 操作名称
        config: 测试配置

    Returns:
        基准测试结果
    """
    suite = BenchmarkSuite(storage, config)

    if operation == 'add_knowledge':
        result = await suite.benchmark_add_knowledge(**config)
    elif operation == 'search_knowledge':
        result = await suite.benchmark_search_knowledge(**config)
    elif operation == 'get_knowledge':
        result = await suite.benchmark_get_knowledge(**config)
    elif operation == 'batch_operations':
        result = await suite.benchmark_batch_operations(**config)
    else:
        raise ValueError(f"未知操作: {operation}")

    return result.to_dict()
