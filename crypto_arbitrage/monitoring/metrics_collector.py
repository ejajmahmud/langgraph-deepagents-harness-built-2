"""指标收集器 - Phase 11核心模块

实时收集系统和应用指标。

核心功能：
1. 系统指标 - CPU/内存/磁盘/网络
2. 应用指标 - 存储性能/交易性能
3. 业务指标 - 套利机会/交易成功率
4. 指标历史 - 保存和查询指标历史

创建时间：2026-04-19 20:35:00
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器

    实时收集系统和应用指标。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化指标收集器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.collection_interval = self.config.get('metrics_interval_seconds', 30)
        self.is_collecting = False

        logger.info(f"指标收集器初始化完成，间隔: {self.collection_interval}秒")

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标

        Returns:
            系统指标字典
        """
        try:
            import psutil

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存使用
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_available_mb = memory.available / 1024 / 1024

            # 磁盘使用
            disk = psutil.disk_usage('.')
            disk_percent = disk.percent
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_free_gb = disk.free / 1024 / 1024 / 1024
            disk_total_gb = disk.total / 1024 / 1024 / 1024

            # 网络流量
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / 1024 / 1024
            network_recv_mb = network.bytes_recv / 1024 / 1024

            # 进程信息
            process = psutil.Process()
            process_cpu_percent = process.cpu_percent()
            process_memory_mb = process.memory_info().rss / 1024 / 1024

            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'memory_used_mb': round(memory_used_mb, 2),
                'memory_available_mb': round(memory_available_mb, 2),
                'disk_percent': round(disk_percent, 2),
                'disk_used_gb': round(disk_used_gb, 2),
                'disk_free_gb': round(disk_free_gb, 2),
                'disk_total_gb': round(disk_total_gb, 2),
                'network_sent_mb': round(network_sent_mb, 2),
                'network_recv_mb': round(network_recv_mb, 2),
                'process_cpu_percent': round(process_cpu_percent, 2),
                'process_memory_mb': round(process_memory_mb, 2),
            }

        except ImportError:
            logger.warning("psutil未安装，无法收集系统指标")
            return {}
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return {}

    async def collect_storage_metrics(self, storage=None) -> Dict[str, Any]:
        """收集存储指标

        Args:
            storage: 存储实例（可选）

        Returns:
            存储指标字典
        """
        try:
            if storage is None:
                return {
                    'storage_type': 'unknown',
                    'operation_latency_ms': 0,
                    'total_knowledge': 0,
                }

            # 测试存储性能
            start_time = time.perf_counter()

            # 执行测试操作
            test_id = await storage.add_knowledge(
                "metrics_test",
                {'test': True, 'timestamp': datetime.now().isoformat()}
            )

            # 执行搜索测试
            search_result = await storage.search_knowledge("metrics_test", limit=1)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # 获取知识数量
            try:
                total_knowledge = await storage.count_knowledge()
            except:
                total_knowledge = 0

            # 清理测试数据
            try:
                await storage.delete_knowledge(test_id)
            except:
                pass

            return {
                'storage_type': getattr(storage, 'storage_type', 'unknown'),
                'operation_latency_ms': round(duration_ms, 3),
                'search_latency_ms': round(duration_ms, 3),
                'total_knowledge': total_knowledge,
            }

        except Exception as e:
            logger.error(f"收集存储指标失败: {e}")
            return {
                'storage_type': 'error',
                'error': str(e),
            }

    async def collect_trading_metrics(self) -> Dict[str, Any]:
        """收集交易指标

        Returns:
            交易指标字典
        """
        try:
            # 这里可以从交易日志或数据库读取
            # 目前返回模拟数据
            return {
                'opportunities_found': 0,
                'trades_executed': 0,
                'success_rate': 0.0,
                'total_profit': 0.0,
                'total_loss': 0.0,
                'win_rate': 0.0,
                'avg_profit_per_trade': 0.0,
            }

        except Exception as e:
            logger.error(f"收集交易指标失败: {e}")
            return {}

    async def collect_all_metrics(self, storage=None) -> Dict[str, Any]:
        """收集所有指标

        Args:
            storage: 存储实例（可选）

        Returns:
            所有指标字典
        """
        timestamp = datetime.now().isoformat()

        # 并行收集各类指标
        system_metrics, storage_metrics, trading_metrics = await asyncio.gather(
            self.collect_system_metrics(),
            self.collect_storage_metrics(storage),
            self.collect_trading_metrics(),
            return_exceptions=True
        )

        # 处理异常
        if isinstance(system_metrics, Exception):
            logger.error(f"系统指标收集异常: {system_metrics}")
            system_metrics = {}

        if isinstance(storage_metrics, Exception):
            logger.error(f"存储指标收集异常: {storage_metrics}")
            storage_metrics = {}

        if isinstance(trading_metrics, Exception):
            logger.error(f"交易指标收集异常: {trading_metrics}")
            trading_metrics = {}

        all_metrics = {
            'timestamp': timestamp,
            'system': system_metrics,
            'storage': storage_metrics,
            'trading': trading_metrics,
        }

        # 保存历史
        self._save_metrics_history(all_metrics)

        logger.debug(f"收集所有指标完成: {timestamp}")

        return all_metrics

    def _save_metrics_history(self, metrics: Dict[str, Any]):
        """保存指标历史

        Args:
            metrics: 指标字典
        """
        timestamp = metrics['timestamp']

        for category, category_metrics in metrics.items():
            if category == 'timestamp':
                continue

            if not category_metrics:  # 跳过空指标
                continue

            if category not in self.metrics_history:
                self.metrics_history[category] = []

            # 添加时间戳
            metrics_with_timestamp = {
                'timestamp': timestamp,
                **category_metrics
            }

            self.metrics_history[category].append(metrics_with_timestamp)

            # 限制历史长度（保留最近1000条）
            max_history = self.config.get('max_history_per_category', 1000)
            if len(self.metrics_history[category]) > max_history:
                self.metrics_history[category] = self.metrics_history[category][-max_history:]

    def get_metrics_history(
        self,
        category: str,
        limit: int = 100,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取指标历史

        Args:
            category: 指标类别（system/storage/trading）
            limit: 返回数量限制
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）

        Returns:
            指标历史列表
        """
        if category not in self.metrics_history:
            return []

        history = self.metrics_history[category].copy()

        # 时间过滤
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            history = [h for h in history if datetime.fromisoformat(h['timestamp']) >= start_dt]

        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            history = [h for h in history if datetime.fromisoformat(h['timestamp']) <= end_dt]

        # 限制数量并倒序（最新的在前）
        history.reverse()
        return history[:limit]

    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """获取最新指标

        Returns:
            最新指标字典
        """
        if not self.metrics_history:
            return None

        # 获取所有类别的最新指标
        latest = {}

        for category, history in self.metrics_history.items():
            if history:
                latest[category] = history[-1]

        if not latest:
            return None

        # 添加总体时间戳（使用最新的）
        latest_timestamp = max(
            h['timestamp'] for h in self.metrics_history.values() if h
        )
        latest['timestamp'] = latest_timestamp

        return latest

    def get_metric_summary(
        self,
        category: str,
        metric_name: str,
        limit: int = 100
    ) -> Dict[str, float]:
        """获取指标统计摘要

        Args:
            category: 指标类别
            metric_name: 指标名称
            limit: 样本数量限制

        Returns:
            统计摘要字典
        """
        history = self.get_metrics_history(category, limit)

        if not history:
            return {}

        # 提取指标值
        values = [h.get(metric_name) for h in history if metric_name in h]

        if not values:
            return {}

        # 计算统计信息
        values.sort()

        return {
            'count': len(values),
            'min': values[0],
            'max': values[-1],
            'avg': sum(values) / len(values),
            'median': values[len(values) // 2],
            'p95': values[int(len(values) * 0.95)] if len(values) > 20 else values[-1],
            'p99': values[int(len(values) * 0.99)] if len(values) > 100 else values[-1],
        }

    def clear_history(self, category: Optional[str] = None):
        """清除指标历史

        Args:
            category: 指标类别（None表示清除全部）
        """
        if category:
            if category in self.metrics_history:
                del self.metrics_history[category]
                logger.info(f"已清除 {category} 指标历史")
        else:
            self.metrics_history.clear()
            logger.info("已清除所有指标历史")

    async def start_collection(self, storage=None):
        """启动指标收集

        Args:
            storage: 存储实例（可选）
        """
        if self.is_collecting:
            logger.warning("指标收集已在运行中")
            return

        self.is_collecting = True
        logger.info(f"启动指标收集，间隔: {self.collection_interval}秒")

        while self.is_collecting:
            try:
                await self.collect_all_metrics(storage)
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"指标收集异常: {e}")
                await asyncio.sleep(self.collection_interval)

    def stop_collection(self):
        """停止指标收集"""
        self.is_collecting = False
        logger.info("已停止指标收集")

    def get_collection_status(self) -> Dict[str, Any]:
        """获取收集状态

        Returns:
            收集状态字典
        """
        total_metrics = sum(len(history) for history in self.metrics_history.values())

        return {
            'is_collecting': self.is_collecting,
            'collection_interval_seconds': self.collection_interval,
            'total_metrics_collected': total_metrics,
            'categories': list(self.metrics_history.keys()),
            'metrics_per_category': {
                cat: len(history)
                for cat, history in self.metrics_history.items()
            },
        }

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        status = "running" if self.is_collecting else "stopped"
        return f"MetricsCollector(status={status}, categories={list(self.metrics_history.keys())})"
