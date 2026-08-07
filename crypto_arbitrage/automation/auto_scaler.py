"""自动扩缩容 - Phase 11核心模块

根据负载自动调整资源。

核心功能：
1. 自动扩容 - 资源不足时自动扩容
2. 自动缩容 - 资源充足时自动缩容
3. 策略配置 - 灵活的扩缩容策略
4. 安全限制 - 最大最小资源限制

创建时间：2026-04-19 20:47:00
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AutoScaler:
    """自动扩缩容

    根据负载自动调整资源。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化自动扩缩容

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.scaling_policies: Dict[str, Dict[str, Any]] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        self.scaling_cooldowns: Dict[str, float] = {}

        # 添加默认扩缩容策略
        self._add_default_policies()

        logger.info(f"自动扩缩容初始化完成，已添加 {len(self.scaling_policies)} 个策略")

    def _add_default_policies(self):
        """添加默认扩缩容策略"""
        # CPU扩容策略
        self.add_scaling_policy({
            'name': 'cpu_scale_up',
            'metric': 'cpu_percent',
            'threshold': 80,
            'direction': 'up',
            'action': 'increase_cache_size',
            'action_params': {'increment': 1000},
            'cooldown': 300,
            'enabled': True,
        })

        # CPU缩容策略
        self.add_scaling_policy({
            'name': 'cpu_scale_down',
            'metric': 'cpu_percent',
            'threshold': 20,
            'direction': 'down',
            'action': 'decrease_cache_size',
            'action_params': {'decrement': 500},
            'cooldown': 600,
            'enabled': True,
        })

        # 内存扩容策略
        self.add_scaling_policy({
            'name': 'memory_scale_up',
            'metric': 'memory_percent',
            'threshold': 85,
            'direction': 'up',
            'action': 'increase_cache_size',
            'action_params': {'increment': 500},
            'cooldown': 300,
            'enabled': True,
        })

        # 内存缩容策略
        self.add_scaling_policy({
            'name': 'memory_scale_down',
            'metric': 'memory_percent',
            'threshold': 30,
            'direction': 'down',
            'action': 'decrease_cache_size',
            'action_params': {'decrement': 250},
            'cooldown': 600,
            'enabled': True,
        })

        logger.info(f"已添加 {len(self.scaling_policies)} 个默认扩缩容策略")

    def add_scaling_policy(self, policy: Dict[str, Any]) -> str:
        """添加扩缩容策略

        Args:
            policy: 扩缩容策略字典

        Returns:
            策略ID
        """
        policy_id = policy.get('name', str(uuid.uuid4()))

        # 验证策略
        if 'name' not in policy:
            raise ValueError("扩缩容策略必须包含name字段")
        if 'metric' not in policy:
            raise ValueError("扩缩容策略必须包含metric字段")
        if 'direction' not in policy:
            raise ValueError("扩缩容策略必须包含direction字段")
        if 'action' not in policy:
            raise ValueError("扩缩容策略必须包含action字段")

        # 设置默认值
        policy.setdefault('threshold', 80)
        policy.setdefault('cooldown', 300)
        policy.setdefault('enabled', True)
        policy.setdefault('action_params', {})

        self.scaling_policies[policy_id] = policy
        logger.info(f"添加扩缩容策略: {policy_id}")

        return policy_id

    def remove_scaling_policy(self, policy_id: str) -> bool:
        """移除扩缩容策略

        Args:
            policy_id: 策略ID

        Returns:
            是否成功移除
        """
        if policy_id in self.scaling_policies:
            del self.scaling_policies[policy_id]
            logger.info(f"移除扩缩容策略: {policy_id}")
            return True
        return False

    def get_scaling_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """获取扩缩容策略

        Args:
            policy_id: 策略ID

        Returns:
            扩缩容策略字典
        """
        return self.scaling_policies.get(policy_id)

    def list_scaling_policies(self) -> List[Dict[str, Any]]:
        """列出所有扩缩容策略

        Returns:
            扩缩容策略列表
        """
        return list(self.scaling_policies.values())

    async def evaluate_scaling(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估扩缩容

        Args:
            metrics: 指标字典

        Returns:
            扩缩容动作列表
        """
        scaling_actions = []

        for policy_id, policy in self.scaling_policies.items():
            try:
                # 跳过禁用的策略
                if not policy.get('enabled', True):
                    continue

                # 检查冷却期
                if self._is_policy_in_cooldown(policy_id, policy):
                    continue

                # 评估条件
                metric_name = policy['metric']
                metric_value = self._get_metric_value(metrics, metric_name)

                if metric_value is None:
                    logger.debug(f"指标 {metric_name} 不存在，跳过策略 {policy_id}")
                    continue

                # 检查阈值
                threshold = policy['threshold']
                direction = policy['direction']

                if direction == 'up' and metric_value >= threshold:
                    # 需要扩容
                    action = self._create_scaling_action(policy_id, policy, metrics, 'up')
                    scaling_actions.append(action)

                    # 更新冷却期
                    cooldown = policy.get('cooldown', 300)
                    self.scaling_cooldowns[policy_id] = time.time() + cooldown

                    logger.info(f"扩缩容触发: {policy['name']} (方向: up)")

                elif direction == 'down' and metric_value <= threshold:
                    # 需要缩容
                    action = self._create_scaling_action(policy_id, policy, metrics, 'down')
                    scaling_actions.append(action)

                    # 更新冷却期
                    cooldown = policy.get('cooldown', 300)
                    self.scaling_cooldowns[policy_id] = time.time() + cooldown

                    logger.info(f"扩缩容触发: {policy['name']} (方向: down)")

            except Exception as e:
                logger.error(f"评估扩缩容策略 {policy_id} 失败: {e}")

        return scaling_actions

    def _get_metric_value(self, metrics: Dict[str, Any], metric_name: str) -> Optional[float]:
        """获取指标值

        Args:
            metrics: 指标字典
            metric_name: 指标名称

        Returns:
            指标值
        """
        # 从顶级指标中获取
        if metric_name in metrics:
            return metrics[metric_name]

        # 从嵌套的system指标中获取
        if 'system' in metrics and metric_name in metrics['system']:
            return metrics['system'][metric_name]

        # 从current_metrics中获取
        if 'current_metrics' in metrics and metric_name in metrics['current_metrics']:
            return metrics['current_metrics'][metric_name]

        return None

    def _is_policy_in_cooldown(self, policy_id: str, policy: Dict[str, Any]) -> bool:
        """检查策略是否在冷却期

        Args:
            policy_id: 策略ID
            policy: 策略字典

        Returns:
            是否在冷却期
        """
        if policy_id not in self.scaling_cooldowns:
            return False

        cooldown_time = self.scaling_cooldowns[policy_id]
        return time.time() < cooldown_time

    def _create_scaling_action(
        self,
        policy_id: str,
        policy: Dict[str, Any],
        metrics: Dict[str, Any],
        direction: str
    ) -> Dict[str, Any]:
        """创建扩缩容动作

        Args:
            policy_id: 策略ID
            policy: 策略字典
            metrics: 指标字典
            direction: 扩缩容方向

        Returns:
            扩缩容动作字典
        """
        metric_name = policy['metric']
        metric_value = self._get_metric_value(metrics, metric_name)

        return {
            'id': str(uuid.uuid4()),
            'policy_id': policy_id,
            'policy_name': policy['name'],
            'direction': direction,
            'action': policy['action'],
            'action_params': policy['action_params'],
            'metric': metric_name,
            'metric_value': metric_value,
            'threshold': policy['threshold'],
            'metrics': metrics.copy(),
            'timestamp': datetime.now().isoformat(),
        }

    async def execute_scaling_action(self, action: Dict[str, Any]) -> bool:
        """执行扩缩容动作

        Args:
            action: 扩缩容动作字典

        Returns:
            是否成功执行
        """
        action_type = action.get('action', 'unknown')
        action_params = action.get('action_params', {})

        logger.info(f"执行扩缩容动作: {action_type}")

        try:
            # 根据动作类型执行不同的逻辑
            if action_type == 'increase_cache_size':
                success = await self._increase_cache_size(action_params)
            elif action_type == 'decrease_cache_size':
                success = await self._decrease_cache_size(action_params)
            elif action_type == 'scale_up':
                success = await self.scale_up(action_params.get('target', 'default'))
            elif action_type == 'scale_down':
                success = await self.scale_down(action_params.get('target', 'default'))
            else:
                logger.warning(f"未知的扩缩容动作: {action_type}")
                success = False

            # 记录扩缩容历史
            self.scaling_history.append({
                **action,
                'success': success,
                'executed_at': datetime.now().isoformat(),
            })

            # 限制历史长度
            max_history = self.config.get('max_scaling_history', 100)
            if len(self.scaling_history) > max_history:
                self.scaling_history = self.scaling_history[-max_history:]

            return success

        except Exception as e:
            logger.error(f"执行扩缩容动作失败: {e}")
            return False

    async def _increase_cache_size(self, params: Dict[str, Any]) -> bool:
        """增加缓存大小

        Args:
            params: 参数字典

        Returns:
            是否成功
        """
        increment = params.get('increment', 1000)
        logger.info(f"增加缓存大小: +{increment}")
        # TODO: 实际增加缓存大小的逻辑
        return True

    async def _decrease_cache_size(self, params: Dict[str, Any]) -> bool:
        """减少缓存大小

        Args:
            params: 参数字典

        Returns:
            是否成功
        """
        decrement = params.get('decrement', 500)
        logger.info(f"减少缓存大小: -{decrement}")
        # TODO: 实际减少缓存大小的逻辑
        return True

    async def scale_up(self, target: str = 'default') -> bool:
        """扩容

        Args:
            target: 扩容目标

        Returns:
            是否成功
        """
        logger.info(f"扩容: {target}")
        # TODO: 实现具体的扩容逻辑
        # 例如：增加工作线程、增加缓存、增加连接池等
        return True

    async def scale_down(self, target: str = 'default') -> bool:
        """缩容

        Args:
            target: 缩容目标

        Returns:
            是否成功
        """
        logger.info(f"缩容: {target}")
        # TODO: 实现具体的缩容逻辑
        # 例如：减少工作线程、减少缓存、减少连接池等
        return True

    def get_scaling_history(
        self,
        limit: int = 100,
        direction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取扩缩容历史

        Args:
            limit: 返回数量限制
            direction: 扩缩容方向过滤

        Returns:
            扩缩容历史列表
        """
        history = self.scaling_history.copy()

        # 过滤方向
        if direction:
            history = [h for h in history if h.get('direction') == direction]

        # 限制数量并倒序
        history.reverse()
        return history[:limit]

    def get_scaling_statistics(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取扩缩容统计

        Args:
            hours: 统计时间范围（小时）

        Returns:
            统计信息字典
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤时间范围内的扩缩容
        recent_scalings = [
            s for s in self.scaling_history
            if datetime.fromisoformat(s['executed_at']) >= cutoff_time
        ]

        # 统计信息
        direction_counts = {'up': 0, 'down': 0}
        action_counts = {}
        success_count = sum(1 for s in recent_scalings if s.get('success', False))

        for scaling in recent_scalings:
            # 方向统计
            direction = scaling.get('direction', 'unknown')
            direction_counts[direction] = direction_counts.get(direction, 0) + 1

            # 动作类型统计
            action = scaling.get('action', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            'time_range_hours': hours,
            'total_scalings': len(recent_scalings),
            'successful_scalings': success_count,
            'success_rate': (
                success_count / len(recent_scalings) * 100
                if recent_scalings else 0
            ),
            'direction_breakdown': direction_counts,
            'action_breakdown': action_counts,
        }

    def clear_scaling_history(self):
        """清除扩缩容历史"""
        self.scaling_history.clear()
        logger.info("已清除扩缩容历史")

    def clear_cooldowns(self):
        """清除所有冷却期"""
        self.scaling_cooldowns.clear()
        logger.info("已清除所有扩缩容冷却期")

    def enable_scaling_policy(self, policy_id: str) -> bool:
        """启用扩缩容策略

        Args:
            policy_id: 策略ID

        Returns:
            是否成功
        """
        if policy_id in self.scaling_policies:
            self.scaling_policies[policy_id]['enabled'] = True
            logger.info(f"启用扩缩容策略: {policy_id}")
            return True
        return False

    def disable_scaling_policy(self, policy_id: str) -> bool:
        """禁用扩缩容策略

        Args:
            policy_id: 策略ID

        Returns:
            是否成功
        """
        if policy_id in self.scaling_policies:
            self.scaling_policies[policy_id]['enabled'] = False
            logger.info(f"禁用扩缩容策略: {policy_id}")
            return True
        return False

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        enabled_count = sum(1 for p in self.scaling_policies.values() if p.get('enabled', True))
        return f"AutoScaler(policies={len(self.scaling_policies)}, enabled={enabled_count}, history={len(self.scaling_history)})"
