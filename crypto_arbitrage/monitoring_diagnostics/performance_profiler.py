"""性能分析器 - Phase 9核心模块

详细的性能指标采集和分析。

核心功能：
1. 函数性能分析 - 详细的分析函数性能
2. 存储操作分析 - 存储操作性能分析
3. 性能报告生成 - 生成详细的性能报告
4. 瓶颈识别 - 自动识别性能瓶颈

创建时间：2026-04-19 18:57:00
"""

import asyncio
import json
import logging
import time
import psutil
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceProfile:
    """性能分析结果

    存储单次性能分析的结果。
    """

    def __init__(
        self,
        name: str,
        duration: float,
        memory_before: float,
        memory_after: float,
        cpu_usage: float,
    ):
        self.name = name
        self.duration = duration
        self.memory_before = memory_before
        self.memory_after = memory_after
        self.cpu_usage = cpu_usage

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            结果字典
        """
        return {
            'name': self.name,
            'duration_ms': self.duration * 1000,
            'memory_before_mb': self.memory_before,
            'memory_after_mb': self.memory_after,
            'memory_used_mb': self.memory_after - self.memory_before,
            'cpu_usage': self.cpu_usage,
        }


class PerformanceProfiler:
    """性能分析器

    详细的性能指标采集和分析。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化性能分析器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.profiles: List[PerformanceProfile] = []

        logger.info("性能分析器初始化完成")

    async def profile_function(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """分析函数性能

        Args:
            func: 要分析的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            分析结果字典
        """
        # 记录开始状态
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        start_time = time.perf_counter()
        cpu_start = psutil.cpu_percent()

        # 执行函数
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数执行失败: {e}")
            raise

        # 记录结束状态
        end_time = time.perf_counter()
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_end = psutil.cpu_percent()

        duration = end_time - start_time
        cpu_usage = (cpu_start + cpu_end) / 2

        # 创建性能分析结果
        profile = PerformanceProfile(
            name=func.__name__,
            duration=duration,
            memory_before=memory_before,
            memory_after=memory_after,
            cpu_usage=cpu_usage
        )

        self.profiles.append(profile)

        return {
            'result': result,
            'profile': profile.to_dict()
        }

    async def profile_storage_operations(
        self,
        storage,
        operations: List[str],
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """分析存储操作性能

        Args:
            storage: 存储实例
            operations: 操作列表
            config: 测试配置

        Returns:
            分析结果字典
        """
        if config is None:
            config = {'iterations': 10}

        results = {}

        for operation in operations:
            try:
                if operation == 'add_knowledge':
                    profile = await self._profile_add_knowledge(storage, config)
                elif operation == 'search_knowledge':
                    profile = await self._profile_search_knowledge(storage, config)
                elif operation == 'get_knowledge':
                    profile = await self._profile_get_knowledge(storage, config)
                else:
                    logger.warning(f"未知操作: {operation}")
                    continue

                results[operation] = profile

            except Exception as e:
                logger.error(f"分析操作 {operation} 失败: {e}")
                results[operation] = {'error': str(e)}

        return {
            'timestamp': datetime.now().isoformat(),
            'storage_type': type(storage).__name__,
            'operations': operations,
            'config': config,
            'results': results,
            'summary': self._summarize_storage_profiles(results)
        }

    async def _profile_add_knowledge(self, storage, config: Dict[str, Any]) -> Dict[str, Any]:
        """分析添加知识操作

        Args:
            storage: 存储实例
            config: 配置字典

        Returns:
            分析结果
        """
        iterations = config.get('iterations', 10)
        durations = []

        for i in range(iterations):
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            start_time = time.perf_counter()

            await storage.add_knowledge(f"Profile test {i}", {'index': i})

            end_time = time.perf_counter()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024

            durations.append(end_time - start_time)

        return {
            'iterations': iterations,
            'total_duration_s': sum(durations),
            'avg_duration_ms': (sum(durations) / len(durations)) * 1000 if durations else 0,
            'min_duration_ms': min(durations) * 1000 if durations else 0,
            'max_duration_ms': max(durations) * 1000 if durations else 0,
            'memory_usage_mb': memory_after - memory_before,
        }

    async def _profile_search_knowledge(self, storage, config: Dict[str, Any]) -> Dict[str, Any]:
        """分析搜索知识操作

        Args:
            storage: 存储实例
            config: 配置字典

        Returns:
            分析结果
        """
        iterations = config.get('iterations', 10)
        durations = []

        for i in range(iterations):
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            start_time = time.perf_counter()

            await storage.search_knowledge(f"Profile test query {i}")

            end_time = time.perf_counter()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024

            durations.append(end_time - start_time)

        return {
            'iterations': iterations,
            'total_duration_s': sum(durations),
            'avg_duration_ms': (sum(durations) / len(durations)) * 1000 if durations else 0,
            'min_duration_ms': min(durations) * 1000 if durations else 0,
            'max_duration_ms': max(durations) * 1000 if durations else 0,
            'memory_usage_mb': memory_after - memory_before,
        }

    async def _profile_get_knowledge(self, storage, config: Dict[str, Any]) -> Dict[str, Any]:
        """分析获取知识操作

        Args:
            storage: 存储实例
            config: 配置字典

        Returns:
            分析结果
        """
        iterations = config.get('iterations', 10)

        # 首先添加一些知识
        knowledge_ids = []
        for i in range(iterations):
            kid = await storage.add_knowledge(f"Profile test {i}", {'index': i})
            knowledge_ids.append(kid)

        durations = []

        for i, kid in enumerate(knowledge_ids):
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            start_time = time.perf_counter()

            await storage.get_knowledge(kid)

            end_time = time.perf_counter()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024

            durations.append(end_time - start_time)

        return {
            'iterations': iterations,
            'total_duration_s': sum(durations),
            'avg_duration_ms': (sum(durations) / len(durations)) * 1000 if durations else 0,
            'min_duration_ms': min(durations) * 1000 if durations else 0,
            'max_duration_ms': max(durations) * 1000 if durations else 0,
            'memory_usage_mb': memory_after - memory_before,
        }

    def _summarize_storage_profiles(self, profiles: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """总结存储性能分析结果

        Args:
            profiles: 性能分析结果字典

        Returns:
            摘要字典
        """
        summary = {
            'slowest_operation': None,
            'fastest_operation': None,
            'highest_memory': None,
            'total_time': 0,
            'operation_count': 0,
        }

        avg_times = {}
        memory_usage = {}

        for name, profile in profiles.items():
            if 'error' in profile:
                continue

            avg_times[name] = profile.get('avg_duration_ms', 0)
            memory_usage[name] = profile.get('memory_usage_mb', 0)

            summary['total_time'] += profile.get('total_duration_s', 0)
            summary['operation_count'] += profile.get('iterations', 0)

        if avg_times:
            summary['slowest_operation'] = max(avg_times.items(), key=lambda x: x[1])
            summary['fastest_operation'] = min(avg_times.items(), key=lambda x: x[1])

        if memory_usage:
            summary['highest_memory'] = max(memory_usage.items(), key=lambda x: x[1])

        return summary

    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告

        Returns:
            性能报告字典
        """
        if not self.profiles:
            return {'error': 'No profiles available'}

        report = {
            'timestamp': datetime.now().isoformat(),
            'profile_count': len(self.profiles),
            'profiles': [p.to_dict() for p in self.profiles],
            'summary': {
                'total_duration': sum(p.duration for p in self.profiles),
                'avg_duration': sum(p.duration for p in self.profiles) / len(self.profiles),
                'max_duration': max(p.duration for p in self.profiles),
                'min_duration': min(p.duration for p in self.profiles),
                'total_memory_used': sum(p.memory_after - p.memory_before for p in self.profiles),
                'avg_cpu_usage': sum(p.cpu_usage for p in self.profiles) / len(self.profiles),
            }
        }

        return report

    def export_report(self, report: Dict[str, Any], filepath: str) -> None:
        """导出性能报告

        Args:
            report: 性能报告
            filepath: 导出文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"性能报告已导出到: {filepath}")


# ========== 便捷函数 ==========

async def profile_function_call(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """分析函数调用

    Args:
        func: 要分析的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        分析结果字典
    """
    profiler = PerformanceProfiler()
    return await profiler.profile_function(func, *args, **kwargs)
