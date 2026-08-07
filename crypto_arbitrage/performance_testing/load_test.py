"""负载测试 - Phase 9核心模块

测试系统在渐增负载下的性能表现。

核心功能：
1. 渐增负载测试 - 逐步增加负载
2. 持续负载测试 - 持续高负载
3. 突发负载测试 - 模拟突发流量
4. 性能退化检测 - 检测性能退化

创建时间：2026-04-19 18:57:00
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from storage.knowledge_storage_interface import KnowledgeStorage

logger = logging.getLogger(__name__)


class LoadTest:
    """负载测试

    测试系统在渐增负载下的性能表现。
    """

    def __init__(self, storage: KnowledgeStorage, config: Dict[str, Any] = None):
        """初始化负载测试

        Args:
            storage: 存储实例
            config: 配置字典
        """
        self.storage = storage
        self.config = config or {}

        logger.info("负载测试初始化完成")

    async def run_ramp_up_test(
        self,
        initial_ops: int = 10,
        final_ops: int = 100,
        duration: int = 60,
        operation: str = 'add_knowledge'
    ) -> Dict[str, Any]:
        """运行渐增负载测试

        Args:
            initial_ops: 初始操作数
            final_ops: 最终操作数
            duration: 持续时间（秒）
            operation: 操作类型

        Returns:
            负载测试报告
        """
        logger.info(f"渐增负载测试: {initial_ops} -> {final_ops} ops, {duration}秒")

        results = []
        start_time = time.time()

        # 计算每秒增加的操作数
        ops_per_second_increment = (final_ops - initial_ops) / duration

        current_ops = initial_ops
        current_time = start_time

        while current_time - start_time < duration:
            # 执行操作
            operation_start = time.time()

            for _ in range(int(current_ops)):
                try:
                    await self._execute_operation(operation, int(current_time - start_time))
                except Exception as e:
                    logger.error(f"操作失败: {e}")

            operation_end = time.time()
            operation_duration = operation_end - operation_start

            # 记录结果
            results.append({
                'timestamp': int((current_time - start_time) * 1000),
                'operations': int(current_ops),
                'duration': operation_duration,
                'throughput': current_ops / operation_duration if operation_duration > 0 else 0,
            })

            # 增加负载
            current_ops = min(current_ops + ops_per_second_increment, final_ops)

            # 等待下一秒
            await asyncio.sleep(1)
            current_time = time.time()

        total_duration = time.time() - start_time

        report = {
            'type': 'ramp_up',
            'timestamp': datetime.now().isoformat(),
            'duration': round(total_duration, 3),
            'initial_ops': initial_ops,
            'final_ops': final_ops,
            'operation': operation,
            'results': results,
            'summary': self._analyze_load_test_results(results)
        }

        logger.info(f"渐增负载测试完成: {total_duration:.3f}秒")
        return report

    async def run_sustained_load_test(
        self,
        ops_per_second: int = 50,
        duration: int = 120,
        operation: str = 'add_knowledge'
    ) -> Dict[str, Any]:
        """运行持续负载测试

        Args:
            ops_per_second: 每秒操作数
            duration: 持续时间（秒）
            operation: 操作类型

        Returns:
            负载测试报告
        """
        logger.info(f"持续负载测试: {ops_per_second} ops/s, {duration}秒")

        results = []
        start_time = time.time()

        second = 0
        while second < duration:
            second_start = time.time()

            # 执行操作
            success_count = 0
            failure_count = 0

            for _ in range(ops_per_second):
                try:
                    await self._execute_operation(operation, second)
                    success_count += 1
                except Exception as e:
                    logger.error(f"操作失败: {e}")
                    failure_count += 1

            second_end = time.time()
            second_duration = second_end - second_start

            # 记录结果
            results.append({
                'second': second,
                'success_count': success_count,
                'failure_count': failure_count,
                'duration': second_duration,
                'throughput': success_count / second_duration if second_duration > 0 else 0,
                'error_rate': failure_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0,
            })

            # 等待下一秒
            if second_duration < 1.0:
                await asyncio.sleep(1.0 - second_duration)

            second += 1

        total_duration = time.time() - start_time

        report = {
            'type': 'sustained_load',
            'timestamp': datetime.now().isoformat(),
            'duration': round(total_duration, 3),
            'target_ops_per_second': ops_per_second,
            'operation': operation,
            'results': results,
            'summary': self._analyze_sustained_load_results(results)
        }

        logger.info(f"持续负载测试完成: {total_duration:.3f}秒")
        return report

    async def run_spike_test(
        self,
        normal_ops: int = 20,
        spike_ops: int = 200,
        spike_duration: int = 10,
        normal_duration: int = 30,
        operation: str = 'add_knowledge'
    ) -> Dict[str, Any]:
        """运行突发负载测试

        Args:
            normal_ops: 正常操作数
            spike_ops: 突发操作数
            spike_duration: 突发持续时间（秒）
            normal_duration: 正常持续时间（秒）
            operation: 操作类型

        Returns:
            负载测试报告
        """
        logger.info(f"突发负载测试: {normal_ops} -> {spike_ops} -> {normal_ops}")

        results = []
        start_time = time.time()
        second = 0

        while second < normal_duration * 2 + spike_duration:
            # 确定当前操作数
            if normal_duration <= second < normal_duration + spike_duration:
                current_ops = spike_ops
                phase = 'spike'
            else:
                current_ops = normal_ops
                phase = 'normal'

            second_start = time.time()

            # 执行操作
            success_count = 0
            failure_count = 0

            for _ in range(current_ops):
                try:
                    await self._execute_operation(operation, second)
                    success_count += 1
                except Exception as e:
                    logger.error(f"操作失败: {e}")
                    failure_count += 1

            second_end = time.time()
            second_duration = second_end - second_start

            # 记录结果
            results.append({
                'second': second,
                'phase': phase,
                'target_ops': current_ops,
                'success_count': success_count,
                'failure_count': failure_count,
                'duration': second_duration,
                'throughput': success_count / second_duration if second_duration > 0 else 0,
                'error_rate': failure_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0,
            })

            # 等待下一秒
            if second_duration < 1.0:
                await asyncio.sleep(1.0 - second_duration)

            second += 1

        total_duration = time.time() - start_time

        report = {
            'type': 'spike',
            'timestamp': datetime.now().isoformat(),
            'duration': round(total_duration, 3),
            'normal_ops': normal_ops,
            'spike_ops': spike_ops,
            'spike_duration': spike_duration,
            'operation': operation,
            'results': results,
            'summary': self._analyze_spike_test_results(results)
        }

        logger.info(f"突发负载测试完成: {total_duration:.3f}秒")
        return report

    async def _execute_operation(self, operation: str, index: int) -> None:
        """执行操作

        Args:
            operation: 操作类型
            index: 索引
        """
        if operation == 'add_knowledge':
            await self.storage.add_knowledge(
                f"Load test knowledge {index}",
                {'index': index, 'load_test': True}
            )
        elif operation == 'search_knowledge':
            await self.storage.search_knowledge(f"Load test query {index}")
        elif operation == 'get_knowledge':
            await self.storage.get_knowledge(f"load_test_{index}")
        else:
            raise ValueError(f"未知操作: {operation}")

    def _analyze_load_test_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析负载测试结果

        Args:
            results: 测试结果列表

        Returns:
            分析结果
        """
        if not results:
            return {}

        throughputs = [r['throughput'] for r in results]
        durations = [r['duration'] for r in results]

        return {
            'max_throughput': max(throughputs) if throughputs else 0,
            'min_throughput': min(throughputs) if throughputs else 0,
            'avg_throughput': sum(throughputs) / len(throughputs) if throughputs else 0,
            'max_duration': max(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'avg_duration': sum(durations) / len(durations) if durations else 0,
        }

    def _analyze_sustained_load_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析持续负载测试结果

        Args:
            results: 测试结果列表

        Returns:
            分析结果
        """
        if not results:
            return {}

        throughputs = [r['throughput'] for r in results]
        error_rates = [r['error_rate'] for r in results]

        return {
            'avg_throughput': sum(throughputs) / len(throughputs) if throughputs else 0,
            'max_throughput': max(throughputs) if throughputs else 0,
            'min_throughput': min(throughputs) if throughputs else 0,
            'avg_error_rate': sum(error_rates) / len(error_rates) if error_rates else 0,
            'max_error_rate': max(error_rates) if error_rates else 0,
            'total_success': sum(r['success_count'] for r in results),
            'total_failure': sum(r['failure_count'] for r in results),
        }

    def _analyze_spike_test_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析突发负载测试结果

        Args:
            results: 测试结果列表

        Returns:
            分析结果
        """
        if not results:
            return {}

        normal_results = [r for r in results if r['phase'] == 'normal']
        spike_results = [r for r in results if r['phase'] == 'spike']

        def analyze_phase(phase_results):
            if not phase_results:
                return {}

            throughputs = [r['throughput'] for r in phase_results]
            error_rates = [r['error_rate'] for r in phase_results]

            return {
                'avg_throughput': sum(throughputs) / len(throughputs) if throughputs else 0,
                'avg_error_rate': sum(error_rates) / len(error_rates) if error_rates else 0,
                'total_success': sum(r['success_count'] for r in phase_results),
                'total_failure': sum(r['failure_count'] for r in phase_results),
            }

        return {
            'normal_phase': analyze_phase(normal_results),
            'spike_phase': analyze_phase(spike_results),
        }


# ========== 便捷函数 ==========

async def run_ramp_up_test(
    storage: KnowledgeStorage,
    initial_ops: int = 10,
    final_ops: int = 100,
    duration: int = 60
) -> Dict[str, Any]:
    """运行渐增负载测试

    Args:
        storage: 存储实例
        initial_ops: 初始操作数
        final_ops: 最终操作数
        duration: 持续时间（秒）

    Returns:
        负载测试报告
    """
    load_test = LoadTest(storage)
    return await load_test.run_ramp_up_test(initial_ops, final_ops, duration)


async def run_sustained_load_test(
    storage: KnowledgeStorage,
    ops_per_second: int = 50,
    duration: int = 120
) -> Dict[str, Any]:
    """运行持续负载测试

    Args:
        storage: 存储实例
        ops_per_second: 每秒操作数
        duration: 持续时间（秒）

    Returns:
        负载测试报告
    """
    load_test = LoadTest(storage)
    return await load_test.run_sustained_load_test(ops_per_second, duration)
