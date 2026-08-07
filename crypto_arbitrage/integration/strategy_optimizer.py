"""策略优化器 - Phase 12核心模块

基于监控反馈优化交易策略，实现智能参数调整。

核心功能：
1. 监控反馈处理 - 接收监控指标和告警作为反馈
2. 策略参数调整 - 基于反馈自动调整策略参数
3. 性能评估 - 评估策略调整的效果
4. 参数优化 - 自动优化策略参数
5. A/B测试 - 策略A/B测试和比较

创建时间：2026-04-19 21:45:00
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """策略优化器

    基于监控反馈优化交易策略。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化策略优化器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 当前策略参数
        self.current_parameters = {
            'risk': {
                'stop_loss_percent': 1.0,
                'take_profit_percent': 2.0,
                'max_position_size': 10000,
                'position_size_factor': 1.0,
            },
            'execution': {
                'use_limit_orders': True,
                'slippage_tolerance': 0.003,
                'execution_timeout_seconds': 30,
            },
            'position': {
                'max_positions': 5,
                'position_scaling': 'normal',
                'min_profit_threshold': 0.005,
            },
        }

        # 基线性能
        self.performance_baseline = {
            'success_rate': 0.7,
            'average_profit': 0.01,
            'max_drawdown': 0.05,
            'total_trades': 0,
        }

        # 优化阈值
        self.optimization_thresholds = {
            'performance_degradation': 0.15,  # 性能下降15%
            'high_alert_frequency': 5,          # 5分钟内超过5个告警
            'success_rate_drop': 0.10,         # 成功率下降10%
            'volatility_spike': 0.8,           # 波动性超过0.8
        }

        # 优化历史
        self.optimization_history: List[Dict] = []
        self.max_history = 100

        # 统计信息
        self.stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'ab_tests_run': 0,
            'parameter_adjustments': 0,
        }

        # A/B测试状态
        self.ab_test_state = None

        # 反馈历史
        self.feedback_history: List[Dict] = []
        self.max_feedback_history = 1000

        logger.info("✅ 策略优化器初始化完成")

    async def initialize(self) -> bool:
        """初始化优化器

        Returns:
            是否成功
        """
        logger.info("🧠 初始化策略优化器...")

        try:
            # 加载历史优化记录
            await self._load_optimization_history()

            logger.info("✅ 策略优化器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 策略优化器初始化失败: {e}")
            return False

    async def process_monitoring_feedback(
        self,
        metrics: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """处理监控反馈

        Args:
            metrics: 监控指标字典
            alerts: 告警列表

        Returns:
            优化建议列表
        """
        try:
            # 记录反馈
            feedback_record = {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'alerts': alerts,
            }
            self._record_feedback(feedback_record)

            # 评估当前性能
            performance = await self._evaluate_performance(metrics)

            # 检测问题
            issues = self._detect_issues(performance, alerts)

            # 生成优化建议
            optimizations = await self._generate_optimizations(issues, performance)

            # 如果有问题，触发优化
            if issues:
                logger.warning(f"⚠️ 检测到 {len(issues)} 个问题，生成 {len(optimizations)} 个优化建议")
                self.stats['total_optimizations'] += 1

            return optimizations

        except Exception as e:
            logger.error(f"❌ 处理监控反馈失败: {e}")
            return []

    async def optimize_strategy(self, optimizations: List[Dict[str, Any]]) -> bool:
        """优化策略

        Args:
            optimizations: 优化建议列表

        Returns:
            是否成功
        """
        try:
            if not optimizations:
                logger.info("无优化建议，跳过优化")
                return True

            logger.info(f"🧠 开始优化策略（{len(optimizations)} 个优化项）...")

            # 应用优化
            for optimization in optimizations:
                await self._apply_optimization(optimization)

            # 记录优化
            await self._record_optimization(optimizations)

            # 更新统计
            self.stats['successful_optimizations'] += 1

            logger.info("✅ 策略优化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 策略优化失败: {e}")
            return False

    async def evaluate_optimization(
        self,
        before_parameters: Dict[str, Any],
        after_parameters: Dict[str, Any],
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估优化效果

        Args:
            before_parameters: 优化前参数
            after_parameters: 优化后参数
            performance_data: 性能数据

        Returns:
            评估结果字典
        """
        try:
            # 计算改进度
            improvement = self._calculate_improvement(
                before_parameters,
                after_parameters,
                performance_data
            )

            # 生成评估报告
            evaluation = {
                'before_parameters': before_parameters,
                'after_parameters': after_parameters,
                'improvement_score': improvement['overall'],
                'improvement_details': improvement,
                'performance_data': performance_data,
                'timestamp': datetime.now().isoformat(),
            }

            logger.info(f"优化评估完成，改进度: {improvement['overall']:.2%}")
            return evaluation

        except Exception as e:
            logger.error(f"❌ 评估优化失败: {e}")
            return {}

    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告

        Returns:
            优化报告字典
        """
        return {
            'current_parameters': self.current_parameters,
            'recent_optimizations': self.optimization_history[-10:],
            'statistics': self.stats,
            'ab_test_state': self.ab_test_state,
            'report_time': datetime.now().isoformat(),
        }

    # ========== 私有方法 ==========

    def _record_feedback(self, feedback: Dict[str, Any]) -> None:
        """记录反馈

        Args:
            feedback: 反馈字典
        """
        self.feedback_history.append(feedback)

        # 限制历史大小
        if len(self.feedback_history) > self.max_feedback_history:
            self.feedback_history = self.feedback_history[-self.max_feedback_history:]

    async def _evaluate_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """评估性能

        Args:
            metrics: 监控指标

        Returns:
            性能评估字典
        """
        performance = {
            'timestamp': datetime.now().isoformat(),
        }

        # 从指标中提取性能数据
        system_metrics = metrics.get('system', {})
        trading_metrics = metrics.get('trading', {})

        # 系统性能
        performance['system'] = {
            'cpu_usage': system_metrics.get('cpu_percent', 0),
            'memory_usage': system_metrics.get('memory_percent', 0),
            'disk_usage': system_metrics.get('disk_percent', 0),
        }

        # 交易性能
        performance['trading'] = {
            'success_rate': trading_metrics.get('success_rate', self.performance_baseline['success_rate']),
            'average_profit': trading_metrics.get('total_profit', 0) / max(trading_metrics.get('trades_executed', 1), 1),
            'total_trades': trading_metrics.get('trades_executed', 0),
        }

        # 综合评分
        performance['overall_score'] = self._calculate_overall_score(performance)

        return performance

    def _detect_issues(
        self,
        performance: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """检测问题

        Args:
            performance: 性能评估
            alerts: 告警列表

        Returns:
            问题列表
        """
        issues = []

        # 检查性能下降
        current_score = performance.get('overall_score', 0)
        baseline_score = self._calculate_baseline_score()
        if current_score < baseline_score * (1 - self.optimization_thresholds['performance_degradation']):
            issues.append('performance_degradation')

        # 检查告警频率
        recent_alerts = self._get_recent_alerts(alerts, minutes=5)
        if len(recent_alerts) > self.optimization_thresholds['high_alert_frequency']:
            issues.append('high_alert_frequency')

        # 检查成功率下降
        trading = performance.get('trading', {})
        success_rate = trading.get('success_rate', self.performance_baseline['success_rate'])
        if success_rate < self.performance_baseline['success_rate'] * (1 - self.optimization_thresholds['success_rate_drop']):
            issues.append('success_rate_drop')

        # 检查严重告警
        critical_alerts = [
            alert for alert in alerts
            if alert.get('severity') == 'CRITICAL'
        ]
        if critical_alerts:
            issues.append('critical_alerts')

        return issues

    async def _generate_optimizations(
        self,
        issues: List[str],
        performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议

        Args:
            issues: 问题列表
            performance: 性能评估

        Returns:
            优化建议列表
        """
        optimizations = []

        for issue in issues:
            # 根据问题类型生成优化建议
            if issue == 'performance_degradation':
                optimizations.extend(await self._optimize_for_performance(performance))
            elif issue == 'high_alert_frequency':
                optimizations.extend(await self._optimize_for_alerts(performance))
            elif issue == 'success_rate_drop':
                optimizations.extend(await self._optimize_for_success_rate(performance))
            elif issue == 'critical_alerts':
                optimizations.extend(await self._optimize_for_critical(performance))

        # 去重优化建议
        unique_optimizations = self._deduplicate_optimizations(optimizations)

        # 优先级排序
        prioritized = self._prioritize_optimizations(unique_optimizations)

        return prioritized[:5]  # 最多返回5个优化建议

    async def _optimize_for_performance(self, performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为性能问题生成优化

        Args:
            performance: 性能评估

        Returns:
            优化建议列表
        """
        optimizations = []

        # 检查CPU使用率
        cpu_usage = performance.get('system', {}).get('cpu_usage', 0)
        if cpu_usage > 80:
            optimizations.append({
                'type': 'reduce_execution_frequency',
                'category': 'execution',
                'description': f'CPU使用率过高（{cpu_usage}%），降低执行频率',
                'priority': 'high',
                'parameters': {
                    'execution_timeout_seconds': self.current_parameters['execution']['execution_timeout_seconds'] * 1.5,
                },
            })

        # 检查内存使用率
        memory_usage = performance.get('system', {}).get('memory_usage', 0)
        if memory_usage > 80:
            optimizations.append({
                'type': 'reduce_cache_size',
                'category': 'execution',
                'description': f'内存使用率过高（{memory_usage}%），减少缓存',
                'priority': 'high',
                'parameters': {
                    'cache_size': int(self.config.get('cache_size', 1000) * 0.5),
                },
            })

        return optimizations

    async def _optimize_for_alerts(self, performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为告警频率问题生成优化

        Args:
            performance: 性能评估

        Returns:
            优化建议列表
        """
        optimizations = []

        # 增加风险控制
        optimizations.append({
            'type': 'increase_risk_control',
            'category': 'risk',
            'description': '告警频繁，增加风险控制',
            'priority': 'medium',
            'parameters': {
                'stop_loss_percent': self.current_parameters['risk']['stop_loss_percent'] * 1.2,
                'max_position_size': int(self.current_parameters['risk']['max_position_size'] * 0.8),
            },
        })

        return optimizations

    async def _optimize_for_success_rate(self, performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为成功率下降生成优化

        Args:
            performance: 性能评估

        Returns:
            优化建议列表
        """
        optimizations = []

        # 调整风险参数
        optimizations.append({
            'type': 'adjust_risk_parameters',
            'category': 'risk',
            'description': '成功率下降，调整风险参数',
            'priority': 'high',
            'parameters': {
                'stop_loss_percent': self.current_parameters['risk']['stop_loss_percent'] * 0.8,
                'min_profit_threshold': self.current_parameters['position']['min_profit_threshold'] * 0.8,
            },
        })

        return optimizations

    async def _optimize_for_critical(self, performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为严重告警生成优化

        Args:
            performance: 性能评估

        Returns:
            优化建议列表
        """
        optimizations = []

        # 紧急停止策略
        optimizations.append({
            'type': 'emergency_stop',
            'category': 'execution',
            'description': '检测到严重告警，触发紧急停止',
            'priority': 'critical',
            'parameters': {
                'active': False,
            },
        })

        return optimizations

    async def _apply_optimization(self, optimization: Dict[str, Any]) -> None:
        """应用优化

        Args:
            optimization: 优化建议
        """
        category = optimization.get('category')
        parameters = optimization.get('parameters', {})

        # 根据类别更新参数
        if category in self.current_parameters:
            self.current_parameters[category].update(parameters)
            self.stats['parameter_adjustments'] += 1
            logger.info(f"应用优化: {optimization['description']}")

    async def _record_optimization(self, optimizations: List[Dict[str, Any]]) -> None:
        """记录优化

        Args:
            optimizations: 优化建议列表
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'optimizations': optimizations,
            'parameters_before': dict(self.current_parameters),
        }

        self.optimization_history.append(record)

        # 限制历史大小
        if len(self.optimization_history) > self.max_history:
            self.optimization_history = self.optimization_history[-self.max_history:]

    def _calculate_improvement(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
        performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算改进度

        Args:
            before: 优化前参数
            after: 优化后参数
            performance: 性能数据

        Returns:
            改进度字典
        """
        improvement = {
            'overall': 0.0,
            'details': {},
        }

        # 计算各项指标改进
        for category in before.keys():
            before_params = before.get(category, {})
            after_params = after.get(category, {})

            category_improvement = 0.0
            count = 0

            for param_name in before_params.keys():
                before_value = before_params.get(param_name, 0)
                after_value = after_params.get(param_name, 0)

                # 计算变化百分比
                if before_value != 0:
                    change = (after_value - before_value) / abs(before_value)
                    category_improvement += abs(change)
                    count += 1

            if count > 0:
                improvement['details'][category] = category_improvement / count

        # 计算综合改进度
        if improvement['details']:
            improvement['overall'] = sum(improvement['details'].values()) / len(improvement['details'])

        return improvement

    def _calculate_overall_score(self, performance: Dict[str, Any]) -> float:
        """计算综合评分

        Args:
            performance: 性能评估

        Returns:
            综合评分 (0-1)
        """
        scores = []

        # 系统性能评分
        system = performance.get('system', {})
        cpu_score = max(0, 1 - system.get('cpu_usage', 0) / 100)
        memory_score = max(0, 1 - system.get('memory_usage', 0) / 100)
        disk_score = max(0, 1 - system.get('disk_usage', 0) / 100)
        scores.append((cpu_score + memory_score + disk_score) / 3)

        # 交易性能评分
        trading = performance.get('trading', {})
        success_rate = trading.get('success_rate', 0)
        avg_profit = trading.get('average_profit', 0)
        trading_score = (success_rate * 0.7 + min(1, avg_profit * 100) * 0.3)
        scores.append(trading_score)

        # 综合评分
        overall_score = sum(scores) / len(scores) if scores else 0.5

        return overall_score

    def _calculate_baseline_score(self) -> float:
        """计算基线评分

        Returns:
            基线评分
        """
        return self.performance_baseline.get('success_rate', 0.7)

    def _get_recent_alerts(self, alerts: List[Dict], minutes: int = 5) -> List[Dict]:
        """获取最近的告警

        Args:
            alerts: 告警列表
            minutes: 时间范围（分钟）

        Returns:
            最近的告警列表
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        recent_alerts = [
            alert for alert in alerts
            if datetime.fromisoformat(alert.get('timestamp', '')) > cutoff_time
        ]

        return recent_alerts

    def _deduplicate_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重优化建议

        Args:
            optimizations: 优化建议列表

        Returns:
            去重后的优化建议列表
        """
        seen_types = set()
        unique_optimizations = []

        for opt in optimizations:
            opt_type = opt.get('type')
            if opt_type not in seen_types:
                seen_types.add(opt_type)
                unique_optimizations.append(opt)

        return unique_optimizations

    def _prioritize_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优先级排序优化建议

        Args:
            optimizations: 优化建议列表

        Returns:
            排序后的优化建议列表
        """
        priority_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
        }

        return sorted(
            optimizations,
            key=lambda x: priority_order.get(x.get('priority', 'low'), 4)
        )

    async def _load_optimization_history(self) -> None:
        """加载优化历史"""
        try:
            # 这里可以从存储加载历史
            logger.debug("优化历史加载（占位）")
        except Exception as e:
            logger.error(f"加载优化历史失败: {e}")

    # ========== A/B测试 ==========

    async def run_ab_test(
        self,
        strategy_a: Dict[str, Any],
        strategy_b: Dict[str, Any],
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """运行A/B测试

        Args:
            strategy_a: 策略A
            strategy_b: 策略B
            duration_minutes: 测试持续时间（分钟）

        Returns:
            A/B测试结果
        """
        try:
            logger.info(f"🧪 开始A/B测试（{duration_minutes}分钟）...")

            self.stats['ab_tests_run'] += 1

            # 记录测试开始
            test_start = datetime.now()

            # 这里应该实际的A/B测试逻辑
            # 暂时返回模拟结果
            result = {
                'test_id': f"ab_test_{int(time.time())}",
                'strategy_a': strategy_a,
                'strategy_b': strategy_b,
                'duration_minutes': duration_minutes,
                'start_time': test_start.isoformat(),
                'end_time': None,
                'results': None,
                'winner': None,
            }

            # 保存测试状态
            self.ab_test_state = result

            logger.info(f"✅ A/B测试已启动: {result['test_id']}")
            return result

        except Exception as e:
            logger.error(f"❌ 运行A/B测试失败: {e}")
            return {}

    async def finalize_ab_test(self, test_id: str) -> Dict[str, Any]:
        """完成A/B测试

        Args:
            test_id: 测试ID

        Returns:
            测试结果
        """
        try:
            logger.info(f"🧪 完成A/B测试: {test_id}")

            # 这里应该获取实际的测试结果
            # 暂时返回模拟结果
            result = {
                'test_id': test_id,
                'completed_at': datetime.now().isoformat(),
                'results': {
                    'strategy_a_performance': 0.75,
                    'strategy_b_performance': 0.80,
                    'difference': 0.05,
                    'statistical_significance': 0.95,
                },
                'winner': 'strategy_b',
            }

            # 更新测试状态
            if self.ab_test_state and self.ab_test_state.get('test_id') == test_id:
                self.ab_test_state.update(result)

            logger.info(f"✅ A/B测试完成，获胜者: {result['winner']}")
            return result

        except Exception as e:
            logger.error(f"❌ 完成A/B测试失败: {e}")
            return {}

    # ========== 参数管理 ==========

    async def save_optimization(self, optimization_id: str) -> bool:
        """保存优化配置

        Args:
            optimization_id: 优化ID

        Returns:
            是否成功
        """
        try:
            # 查找优化记录
            record = None
            for opt_record in self.optimization_history:
                if f"opt_{opt_record['timestamp']}" == optimization_id:
                    record = opt_record
                    break

            if not record:
                logger.error(f"未找到优化记录: {optimization_id}")
                return False

            # 保存到存储
            content = json.dumps(record)
            metadata = {
                'type': 'optimization_record',
                'optimization_id': optimization_id,
                'timestamp': record['timestamp'],
            }

            from integration.storage_integration import get_storage_integrator
            integrator = get_storage_integrator()
            if integrator.storage:
                await integrator.storage.add_knowledge(content, metadata=metadata)

            logger.info(f"✅ 优化配置已保存: {optimization_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存优化配置失败: {e}")
            return False

    async def load_optimization(self, optimization_id: str) -> bool:
        """加载优化配置

        Args:
            optimization_id: 优化ID

        Returns:
            是否成功
        """
        try:
            # 从存储加载
            from integration.storage_integration import get_storage_integrator
            integrator = get_storage_integrator()

            if not integrator.storage:
                logger.error("存储未初始化")
                return False

            # 搜索优化记录
            results = await integrator.storage.search_knowledge(
                f"optimization {optimization_id}",
                top_k=1
            )

            if not results:
                logger.error(f"未找到优化记录: {optimization_id}")
                return False

            # 应用参数
            result = results[0]
            record = json.loads(result.content)
            parameters = record.get('parameters_before', {})

            for category, params in parameters.items():
                if category in self.current_parameters:
                    self.current_parameters[category].update(params)

            logger.info(f"✅ 优化配置已加载: {optimization_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 加载优化配置失败: {e}")
            return False

    async def rollback_optimization(self, optimization_id: str) -> bool:
        """回滚优化

        Args:
            optimization_id: 优化ID

        Returns:
            是否成功
        """
        try:
            # 查找优化记录
            record = None
            for opt_record in self.optimization_history:
                if f"opt_{opt_record['timestamp']}" == optimization_id:
                    record = opt_record
                    break

            if not record:
                logger.error(f"未找到优化记录: {optimization_id}")
                return False

            # 恢复优化前的参数
            parameters_before = record.get('parameters_before', {})
            for category, params in parameters_before.items():
                if category in self.current_parameters:
                    self.current_parameters[category] = dict(params)

            logger.info(f"✅ 优化已回滚: {optimization_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 回滚优化失败: {e}")
            return False

    def get_optimization_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取优化历史

        Args:
            limit: 返回数量

        Returns:
            优化历史列表
        """
        history = self.optimization_history.copy()
        history.reverse()
        return history[:limit]


# ========== 全局策略优化器实例 ==========

_optimizer_instance: Optional[StrategyOptimizer] = None


def get_strategy_optimizer() -> StrategyOptimizer:
    """获取策略优化器单例

    Returns:
        策略优化器实例
    """
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = StrategyOptimizer()
    return _optimizer_instance
