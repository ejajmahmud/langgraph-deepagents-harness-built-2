"""存储集成器 - Phase 12核心模块

集成Memo0存储，实现数据持久化和深度分析。

核心功能：
1. 监控数据持久化 - 将监控指标、告警历史保存到Memo0
2. 自动化数据持久化 - 将扩缩容、恢复、备份操作保存到Memo0
3. 交易数据持久化 - 将交易记录、策略执行保存到Memo0
4. 数据查询 - 从Memo0查询历史数据
5. 数据分析 - 基于历史数据的分析功能

创建时间：2026-04-19 21:40:00
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class StorageIntegrator:
    """存储集成器

    集成Memo0存储，实现数据持久化。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化存储集成器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 存储实例
        self.storage: Optional[Any] = None

        # 数据缓存
        self._metrics_cache: List[Dict] = []
        self._alerts_cache: List[Dict] = []
        self._actions_cache: List[Dict] = []

        # 缓存配置
        self.max_cache_size = self.config.get('max_cache_size', 100)
        self.persist_interval = self.config.get('persist_interval', 10)  # 秒
        self.enable_cache = self.config.get('enable_cache', True)

        # 统计信息
        self.stats = {
            'total_metrics_saved': 0,
            'total_alerts_saved': 0,
            'total_actions_saved': 0,
            'total_trades_saved': 0,
            'persist_errors': 0,
        }

        # 定期持久化任务
        self._persist_task: Optional[asyncio.Task] = None

        logger.info("✅ 存储集成器初始化完成")

    async def initialize(self) -> bool:
        """初始化存储

        Returns:
            是否成功
        """
        logger.info("📦 初始化存储集成器...")

        try:
            from storage.storage_factory import create_auto_storage

            # 创建存储实例
            self.storage = await create_auto_storage(self.config)

            # 启动定期持久化任务
            if self.enable_cache:
                self._start_persist_task()

            logger.info("✅ 存储集成器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 存储集成器初始化失败: {e}")
            return False

    async def close(self) -> None:
        """关闭存储集成器"""
        logger.info("📦 关闭存储集成器...")

        # 停止定期持久化任务
        if self._persist_task:
            self._persist_task.cancel()
            try:
                await self._persist_task
            except asyncio.CancelledError:
                pass

        # 持久化剩余缓存
        await self._flush_all_caches()

        # 关闭存储
        if self.storage and hasattr(self.storage, 'close'):
            await self.storage.close()

        logger.info("✅ 存储集成器关闭完成")

    # ========== 监控数据持久化 ==========

    async def persist_metrics(self, metrics: Dict[str, Any]) -> bool:
        """持久化监控指标

        Args:
            metrics: 监控指标字典

        Returns:
            是否成功
        """
        try:
            # 添加时间戳
            metrics_with_timestamp = {
                'timestamp': datetime.now().isoformat(),
                **metrics
            }

            # 添加到缓存
            if self.enable_cache:
                self._metrics_cache.append(metrics_with_timestamp)

                # 检查缓存大小
                if len(self._metrics_cache) >= self.max_cache_size:
                    await self._flush_metrics_cache()
            else:
                # 直接持久化
                await self._save_metrics_to_storage(metrics_with_timestamp)

            logger.debug(f"监控指标已保存: {metrics_with_timestamp.get('timestamp')}")
            return True

        except Exception as e:
            logger.error(f"❌ 持久化监控指标失败: {e}")
            self.stats['persist_errors'] += 1
            return False

    async def persist_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """持久化告警历史

        Args:
            alerts: 告警列表

        Returns:
            是否成功
        """
        try:
            for alert in alerts:
                # 添加时间戳
                alert_with_timestamp = {
                    'timestamp': datetime.now().isoformat(),
                    **alert
                }

                # 添加到缓存
                if self.enable_cache:
                    self._alerts_cache.append(alert_with_timestamp)

                    # 检查缓存大小
                    if len(self._alerts_cache) >= self.max_cache_size:
                        await self._flush_alerts_cache()
                else:
                    # 直接持久化
                    await self._save_alert_to_storage(alert_with_timestamp)

            logger.info(f"✅ {len(alerts)} 个告警已持久化")
            return True

        except Exception as e:
            logger.error(f"❌ 持久化告警失败: {e}")
            self.stats['persist_errors'] += 1
            return False

    async def persist_automation_actions(self, actions: List[Dict[str, Any]]) -> bool:
        """持久化自动化操作

        Args:
            actions: 自动化操作列表

        Returns:
            是否成功
        """
        try:
            for action in actions:
                # 添加时间戳
                action_with_timestamp = {
                    'timestamp': datetime.now().isoformat(),
                    **action
                }

                # 添加到缓存
                if self.enable_cache:
                    self._actions_cache.append(action_with_timestamp)

                    # 检查缓存大小
                    if len(self._actions_cache) >= self.max_cache_size:
                        await self._flush_actions_cache()
                else:
                    # 直接持久化
                    await self._save_action_to_storage(action_with_timestamp)

            logger.info(f"✅ {len(actions)} 个自动化操作已持久化")
            return True

        except Exception as e:
            logger.error(f"❌ 持久化自动化操作失败: {e}")
            self.stats['persist_errors'] += 1
            return False

    async def persist_trading_data(self, trading_data: Dict[str, Any]) -> bool:
        """持久化交易数据

        Args:
            trading_data: 交易数据字典

        Returns:
            是否成功
        """
        try:
            # 添加时间戳
            trading_with_timestamp = {
                'timestamp': datetime.now().isoformat(),
                **trading_data
            }

            # 直接持久化（交易数据不使用缓存）
            await self._save_trading_data_to_storage(trading_with_timestamp)

            logger.debug(f"交易数据已保存: {trading_with_timestamp.get('timestamp')}")
            return True

        except Exception as e:
            logger.error(f"❌ 持久化交易数据失败: {e}")
            self.stats['persist_errors'] += 1
            return False

    # ========== 数据查询 ==========

    async def query_historical_data(
        self,
        data_type: str,
        start_time: str,
        end_time: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """查询历史数据

        Args:
            data_type: 数据类型 [metrics, alerts, actions, trades]
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            filters: 过滤条件

        Returns:
            数据列表
        """
        try:
            # 构建查询
            query = self._build_query(data_type, start_time, end_time, filters)

            # 执行查询
            results = await self.storage.search_knowledge(
                query,
                top_k=100,
                filters=filters
            )

            # 转换为字典列表
            data_list = []
            for result in results:
                data_list.append({
                    'content': result.content,
                    'metadata': result.metadata,
                    'similarity': result.similarity_score,
                })

            logger.info(f"查询到 {len(data_list)} 条 {data_type} 数据")
            return data_list

        except Exception as e:
            logger.error(f"❌ 查询历史数据失败: {e}")
            return []

    async def get_metrics_trend(
        self,
        metric_name: str,
        time_range: str = "1h"
    ) -> Dict[str, Any]:
        """获取指标趋势

        Args:
            metric_name: 指标名称 [cpu_percent, memory_percent, etc.]
            time_range: 时间范围 [1h, 6h, 24h, 7d]

        Returns:
            趋势数据字典
        """
        try:
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - self._parse_time_range(time_range)

            # 查询指标数据
            metrics_data = await self.query_historical_data(
                'metrics',
                start_time.isoformat(),
                end_time.isoformat()
            )

            # 提取指定指标
            values = []
            for data in metrics_data:
                content = json.loads(data.get('content', '{}'))
                if metric_name in content:
                    values.append(content[metric_name])

            # 计算趋势
            if len(values) > 0:
                trend = {
                    'metric_name': metric_name,
                    'time_range': time_range,
                    'count': len(values),
                    'current': values[-1] if values else 0,
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'trend': self._calculate_trend(values),
                }
            else:
                trend = {
                    'metric_name': metric_name,
                    'time_range': time_range,
                    'count': 0,
                    'message': '无数据'
                }

            return trend

        except Exception as e:
            logger.error(f"❌ 获取指标趋势失败: {e}")
            return {}

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计

        Returns:
            告警统计字典
        """
        try:
            # 查询最近24小时的告警
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            alerts_data = await self.query_historical_data(
                'alerts',
                start_time.isoformat(),
                end_time.isoformat()
            )

            # 分析告警
            severity_count = defaultdict(int)
            rule_count = defaultdict(int)
            resolved_count = 0

            for data in alerts_data:
                content = json.loads(data.get('content', '{}'))
                severity = content.get('severity', 'INFO')
                rule = content.get('name', 'unknown')

                severity_count[severity] += 1
                rule_count[rule] += 1

                if content.get('resolved', False):
                    resolved_count += 1

            # 生成统计
            statistics = {
                'total_alerts': len(alerts_data),
                'resolved_alerts': resolved_count,
                'unresolved_alerts': len(alerts_data) - resolved_count,
                'severity_breakdown': dict(severity_count),
                'top_rules': dict(sorted(
                    rule_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]),
                'time_range': '24h',
            }

            return statistics

        except Exception as e:
            logger.error(f"❌ 获取告警统计失败: {e}")
            return {}

    # ========== 数据分析 ==========

    async def analyze_system_trends(self) -> Dict[str, Any]:
        """分析系统趋势

        Returns:
            趋势分析字典
        """
        try:
            # 分析关键指标趋势
            cpu_trend = await self.get_metrics_trend('cpu_percent', '24h')
            memory_trend = await self.get_metrics_trend('memory_percent', '24h')
            disk_trend = await self.get_metrics_trend('disk_percent', '24h')

            # 分析告警统计
            alert_stats = await self.get_alert_statistics()

            # 综合分析
            analysis = {
                'system_health': self._assess_system_health([cpu_trend, memory_trend, disk_trend]),
                'trends': {
                    'cpu': cpu_trend,
                    'memory': memory_trend,
                    'disk': disk_trend,
                },
                'alerts': alert_stats,
                'recommendations': self._generate_recommendations(
                    [cpu_trend, memory_trend, disk_trend],
                    alert_stats
                ),
                'analysis_time': datetime.now().isoformat(),
            }

            return analysis

        except Exception as e:
            logger.error(f"❌ 分析系统趋势失败: {e}")
            return {}

    async def generate_insights(self) -> Dict[str, Any]:
        """生成洞察报告

        Returns:
            洞察报告字典
        """
        try:
            # 分析系统趋势
            trend_analysis = await self.analyze_system_trends()

            # 查询最近的自动化操作
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            actions_data = await self.query_historical_data(
                'actions',
                start_time.isoformat(),
                end_time.isoformat()
            )

            # 分析自动化操作
            automation_efficiency = self._analyze_automation_efficiency(actions_data)

            # 生成综合洞察
            insights = {
                'system_insights': trend_analysis,
                'automation_insights': automation_efficiency,
                'overall_health': trend_analysis.get('system_health', 'unknown'),
                'actionable_items': self._identify_actionable_items(
                    trend_analysis,
                    automation_efficiency
                ),
                'generated_at': datetime.now().isoformat(),
            }

            return insights

        except Exception as e:
            logger.error(f"❌ 生成洞察失败: {e}")
            return {}

    # ========== 私有方法 ==========

    def _start_persist_task(self) -> None:
        """启动定期持久化任务"""
        self._persist_task = asyncio.create_task(
            self._persist_loop()
        )
        logger.info("定期持久化任务已启动")

    async def _persist_loop(self) -> None:
        """定期持久化循环"""
        while True:
            try:
                # 等待指定间隔
                await asyncio.sleep(self.persist_interval)

                # 持久化所有缓存
                await self._flush_all_caches()

            except asyncio.CancelledError:
                logger.info("定期持久化任务已取消")
                break
            except Exception as e:
                logger.error(f"定期持久化失败: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒

    async def _flush_all_caches(self) -> None:
        """刷新所有缓存"""
        await self._flush_metrics_cache()
        await self._flush_alerts_cache()
        await self._flush_actions_cache()

    async def _flush_metrics_cache(self) -> None:
        """刷新指标缓存"""
        if not self._metrics_cache:
            return

        try:
            for metrics in self._metrics_cache:
                await self._save_metrics_to_storage(metrics)

            self.stats['total_metrics_saved'] += len(self._metrics_cache)
            logger.debug(f"✅ {len(self._metrics_cache)} 条指标已持久化")
            self._metrics_cache.clear()

        except Exception as e:
            logger.error(f"刷新指标缓存失败: {e}")

    async def _flush_alerts_cache(self) -> None:
        """刷新告警缓存"""
        if not self._alerts_cache:
            return

        try:
            for alert in self._alerts_cache:
                await self._save_alert_to_storage(alert)

            self.stats['total_alerts_saved'] += len(self._alerts_cache)
            logger.debug(f"✅ {len(self._alerts_cache)} 条告警已持久化")
            self._alerts_cache.clear()

        except Exception as e:
            logger.error(f"刷新告警缓存失败: {e}")

    async def _flush_actions_cache(self) -> None:
        """刷新操作缓存"""
        if not self._actions_cache:
            return

        try:
            for action in self._actions_cache:
                await self._save_action_to_storage(action)

            self.stats['total_actions_saved'] += len(self._actions_cache)
            logger.debug(f"✅ {len(self._actions_cache)} 条操作已持久化")
            self._actions_cache.clear()

        except Exception as e:
            logger.error(f"刷新操作缓存失败: {e}")

    async def _save_metrics_to_storage(self, metrics: Dict[str, Any]) -> None:
        """保存指标到存储"""
        content = json.dumps(metrics)
        metadata = {
            'type': 'monitoring_metrics',
            'timestamp': metrics.get('timestamp', datetime.now().isoformat()),
            'category': 'monitoring'
        }

        await self.storage.add_knowledge(content, metadata=metadata)

    async def _save_alert_to_storage(self, alert: Dict[str, Any]) -> None:
        """保存告警到存储"""
        content = json.dumps(alert)
        metadata = {
            'type': 'alert_record',
            'severity': alert.get('severity', 'INFO'),
            'timestamp': alert.get('timestamp', datetime.now().isoformat()),
            'category': 'monitoring'
        }

        await self.storage.add_knowledge(content, metadata=metadata)

    async def _save_action_to_storage(self, action: Dict[str, Any]) -> None:
        """保存操作到存储"""
        content = json.dumps(action)
        metadata = {
            'type': 'automation_action',
            'action_type': action.get('action_type', 'unknown'),
            'timestamp': action.get('timestamp', datetime.now().isoformat()),
            'category': 'automation'
        }

        await self.storage.add_knowledge(content, metadata=metadata)

    async def _save_trading_data_to_storage(self, trading_data: Dict[str, Any]) -> None:
        """保存交易数据到存储"""
        content = json.dumps(trading_data)
        metadata = {
            'type': 'trade_record',
            'strategy': trading_data.get('strategy', 'unknown'),
            'symbol': trading_data.get('symbol', 'unknown'),
            'timestamp': trading_data.get('timestamp', datetime.now().isoformat()),
            'category': 'trading'
        }

        await self.storage.add_knowledge(content, metadata=metadata)
        self.stats['total_trades_saved'] += 1

    def _build_query(
        self,
        data_type: str,
        start_time: str,
        end_time: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建查询

        Args:
            data_type: 数据类型
            start_time: 开始时间
            end_time: 结束时间
            filters: 过滤条件

        Returns:
            查询字符串
        """
        query_parts = [
            f"{data_type}",
            f"from {start_time}",
            f"to {end_time}"
        ]

        if filters:
            for key, value in filters.items():
                query_parts.append(f"{key} {value}")

        return " ".join(query_parts)

    def _parse_time_range(self, time_range: str) -> timedelta:
        """解析时间范围

        Args:
            time_range: 时间范围字符串

        Returns:
            timedelta对象
        """
        # 简单解析
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return timedelta(days=days)
        elif time_range.endswith('m'):
            minutes = int(time_range[:-1])
            return timedelta(minutes=minutes)
        else:
            return timedelta(hours=1)  # 默认1小时

    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势

        Args:
            values: 数值列表

        Returns:
            趋势字符串 [increasing, decreasing, stable]
        """
        if len(values) < 2:
            return 'stable'

        # 简单线性回归
        n = len(values)
        x = list(range(n))

        # 计算斜率
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # 判断趋势
        if slope > 0.01:
            return 'increasing'
        elif slope < -0.01:
            return 'decreasing'
        else:
            return 'stable'

    def _assess_system_health(self, trends: List[Dict]) -> str:
        """评估系统健康

        Args:
            trends: 趋势列表

        Returns:
            健康状态 [healthy, degraded, critical]
        """
        health_score = 0

        for trend in trends:
            # 检查是否有数据
            if trend.get('count', 0) == 0:
                continue

            # 获取当前值
            current = trend.get('current', 0)

            # CPU健康评估
            if 'cpu' in trend.get('metric_name', '').lower():
                if current > 90:
                    health_score -= 2
                elif current > 80:
                    health_score -= 1

            # 内存健康评估
            if 'memory' in trend.get('metric_name', '').lower():
                if current > 90:
                    health_score -= 2
                elif current > 80:
                    health_score -= 1

            # 磁盘健康评估
            if 'disk' in trend.get('metric_name', '').lower():
                if current > 95:
                    health_score -= 2
                elif current > 85:
                    health_score -= 1

        # 综合评估
        if health_score >= 0:
            return 'healthy'
        elif health_score >= -3:
            return 'degraded'
        else:
            return 'critical'

    def _generate_recommendations(
        self,
        trends: List[Dict],
        alert_stats: Dict
    ) -> List[str]:
        """生成推荐

        Args:
            trends: 趋势列表
            alert_stats: 告警统计

        Returns:
            推荐列表
        """
        recommendations = []

        # 基于趋势生成推荐
        for trend in trends:
            trend_direction = trend.get('trend', 'stable')
            metric_name = trend.get('metric_name', '')

            if trend_direction == 'increasing':
                if 'cpu' in metric_name.lower():
                    recommendations.append("CPU使用率持续上升，建议检查进程或考虑扩容")
                elif 'memory' in metric_name.lower():
                    recommendations.append("内存使用率持续上升，建议检查内存泄漏或增加内存")
                elif 'disk' in metric_name.lower():
                    recommendations.append("磁盘使用率持续上升，建议清理日志或扩展存储")

        # 基于告警生成推荐
        unresolved_alerts = alert_stats.get('unresolved_alerts', 0)
        if unresolved_alerts > 10:
            recommendations.append(f"存在 {unresolved_alerts} 个未解决告警，建议优先处理")

        return recommendations[:5]  # 最多返回5个推荐

    def _analyze_automation_efficiency(self, actions_data: List[Dict]) -> Dict[str, Any]:
        """分析自动化效率

        Args:
            actions_data: 操作数据列表

        Returns:
            效率分析字典
        """
        if not actions_data:
            return {'message': '无自动化操作数据'}

        # 按类型分组
        action_types = defaultdict(int)
        success_count = 0
        total_duration = 0

        for data in actions_data:
            content = json.loads(data.get('content', '{}'))
            action_type = content.get('action_type', 'unknown')
            result = content.get('result', 'unknown')
            duration = content.get('duration_seconds', 0)

            action_types[action_type] += 1
            if result == 'success':
                success_count += 1
            total_duration += duration

        # 计算效率指标
        efficiency = {
            'total_actions': len(actions_data),
            'success_rate': success_count / len(actions_data) if actions_data else 0,
            'average_duration': total_duration / len(actions_data) if actions_data else 0,
            'action_type_breakdown': dict(action_types),
            'most_frequent_action': max(
                action_types.items(),
                key=lambda x: x[1]
            )[0] if action_types else 'none',
        }

        return efficiency

    def _identify_actionable_items(
        self,
        trend_analysis: Dict,
        automation_efficiency: Dict
    ) -> List[str]:
        """识别可操作项

        Args:
            trend_analysis: 趋势分析
            automation_efficiency: 自动化效率

        Returns:
            可操作项列表
        """
        actionable_items = []

        # 系统健康检查
        health = trend_analysis.get('system_health', 'healthy')
        if health == 'degraded':
            actionable_items.append("系统状态降级，建议检查资源使用情况")
        elif health == 'critical':
            actionable_items.append("系统状态严重，建议立即采取行动")

        # 告警检查
        alert_stats = trend_analysis.get('alerts', {})
        unresolved = alert_stats.get('unresolved_alerts', 0)
        if unresolved > 5:
            actionable_items.append(f"存在 {unresolved} 个未解决告警，建议优先处理")

        # 自动化效率检查
        success_rate = automation_efficiency.get('success_rate', 0)
        if success_rate < 0.8:
            actionable_items.append("自动化操作成功率较低，建议检查配置")

        return actionable_items

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            'metrics_saved': self.stats['total_metrics_saved'],
            'alerts_saved': self.stats['total_alerts_saved'],
            'actions_saved': self.stats['total_actions_saved'],
            'trades_saved': self.stats['total_trades_saved'],
            'errors': self.stats['persist_errors'],
            'cache_sizes': {
                'metrics': len(self._metrics_cache),
                'alerts': len(self._alerts_cache),
                'actions': len(self._actions_cache),
            },
        }

    async def export_data(
        self,
        data_type: str,
        output_path: str,
        format: str = 'json'
    ) -> bool:
        """导出数据

        Args:
            data_type: 数据类型
            output_path: 输出路径
            format: 格式 [json, csv]

        Returns:
            是否成功
        """
        try:
            # 查询所有数据
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)  # 最近30天

            data = await self.query_historical_data(
                data_type,
                start_time.isoformat(),
                end_time.isoformat()
            )

            # 导出数据
            if format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            elif format == 'csv':
                import csv
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    if data:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=data[0].keys()
                        )
                        writer.writeheader()
                        writer.writerows(data)

            logger.info(f"✅ 数据已导出到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 导出数据失败: {e}")
            return False


# ========== 全局存储集成器实例 ==========

_integrator_instance: Optional[StorageIntegrator] = None


def get_storage_integrator() -> StorageIntegrator:
    """获取存储集成器单例

    Returns:
        存储集成器实例
    """
    global _integrator_instance
    if _integrator_instance is None:
        _integrator_instance = StorageIntegrator()
    return _integrator_instance
