"""知识反馈循环 - V5.10 Phase 2.4

实现决策结果跟踪、知识价值评估、优化触发和学习循环管理。

核心功能：
1. 决策结果跟踪
2. 知识价值评估
3. 知识优化触发
4. 学习循环管理

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import statistics
import json

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """结果类型"""
    SUCCESS = "success"  # 成功
    PARTIAL_SUCCESS = "partial_success"  # 部分成功
    FAILURE = "failure"  # 失败
    NEUTRAL = "neutral"  # 中性


class KnowledgeValueLevel(Enum):
    """知识价值等级"""
    HIGH_VALUE = "high_value"  # 高价值
    MEDIUM_VALUE = "medium_value"  # 中等价值
    LOW_VALUE = "low_value"  # 低价值
    NEGATIVE_VALUE = "negative_value"  # 负价值


class OptimizationAction(Enum):
    """优化动作"""
    UPDATE_KNOWLEDGE = "update_knowledge"  # 更新知识
    ENHANCE_KNOWLEDGE = "enhance_knowledge"  # 增强知识
    RETIRE_KNOWLEDGE = "retire_knowledge"  # 退役知识
    MERGE_KNOWLEDGE = "merge_knowledge"  # 合并知识
    SPLIT_KNOWLEDGE = "split_knowledge"  # 拆分知识


@dataclass
class DecisionOutcome:
    """决策结果"""
    outcome_id: str
    decision_id: str
    outcome_type: OutcomeType
    actual_return: float
    actual_risk: float
    execution_time: float
    market_conditions: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "outcome_id": self.outcome_id,
            "decision_id": self.decision_id,
            "outcome_type": self.outcome_type.value,
            "actual_return": self.actual_return,
            "actual_risk": self.actual_risk,
            "execution_time": self.execution_time,
            "market_conditions": self.market_conditions,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class KnowledgeValueAssessment:
    """知识价值评估"""
    knowledge_id: str
    value_score: float  # 0-1
    value_level: KnowledgeValueLevel
    contribution_count: int
    success_rate: float
    average_effectiveness: float
    last_used: datetime
    assessment_timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "value_score": self.value_score,
            "value_level": self.value_level.value,
            "contribution_count": self.contribution_count,
            "success_rate": self.success_rate,
            "average_effectiveness": self.average_effectiveness,
            "last_used": self.last_used.isoformat(),
            "assessment_timestamp": self.assessment_timestamp.isoformat()
        }


@dataclass
class OptimizationTrigger:
    """优化触发"""
    trigger_id: str
    action: OptimizationAction
    target_knowledge_ids: List[str]
    reason: str
    priority: int  # 1-10
    triggered_at: datetime
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trigger_id": self.trigger_id,
            "action": action.value,
            "target_knowledge_ids": self.target_knowledge_ids,
            "reason": self.reason,
            "priority": self.priority,
            "triggered_at": self.triggered_at.isoformat(),
            "status": self.status
        }


@dataclass
class LearningCycle:
    """学习循环"""
    cycle_id: str
    start_time: datetime
    end_time: Optional[datetime]
    decisions_processed: int
    knowledge_optimized: int
    effectiveness_improvement: float
    status: str  # "running", "completed", "failed"
    insights: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cycle_id": self.cycle_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "decisions_processed": self.decisions_processed,
            "knowledge_optimized": self.knowledge_optimized,
            "effectiveness_improvement": self.effectiveness_improvement,
            "status": self.status,
            "insights": self.insights
        }


class KnowledgeFeedbackLoop:
    """知识反馈循环

    实现完整的决策-反馈-优化学习循环。
    """

    # 评估参数
    MIN_DECISIONS_FOR_ASSESSMENT = 5
    EFFECTIVENESS_THRESHOLD = 0.7
    LOW_VALUE_THRESHOLD = 0.3
    HIGH_VALUE_THRESHOLD = 0.8

    # 学习循环参数
    LEARNING_CYCLE_INTERVAL = 3600  # 秒（1小时）
    MIN_DECISIONS_PER_CYCLE = 10

    def __init__(self, config: Dict[str, Any]):
        """初始化知识反馈循环

        Args:
            config: 配置字典
        """
        self.config = config

        # 决策跟踪
        self.decision_outcomes: List[DecisionOutcome] = []
        self._outcome_id_counter = 0

        # 知识价值评估
        self.knowledge_assessments: Dict[str, KnowledgeValueAssessment] = {}

        # 优化触发
        self.optimization_triggers: List[OptimizationTrigger] = []
        self._trigger_id_counter = 0

        # 学习循环
        self.learning_cycles: List[LearningCycle] = []
        self.current_cycle: Optional[LearningCycle] = None

        # 统计信息
        self.stats = {
            "total_outcomes": 0,
            "successful_outcomes": 0,
            "failed_outcomes": 0,
            "average_effectiveness": 0.0,
            "total_optimizations": 0,
            "completed_cycles": 0
        }

        # 运行状态
        self._is_running = False
        self._cycle_task: Optional[asyncio.Task] = None

        # 外部依赖
        self.knowledge_base: Dict[str, Dict[str, Any]] = {}
        self.optimization_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        logger.info("[OK] 知识反馈循环初始化完成")

    # ========== 决策结果跟踪 ==========

    async def track_decision_outcome(
        self,
        decision_id: str,
        outcome_type: OutcomeType,
        actual_return: float,
        actual_risk: float,
        execution_time: float,
        market_conditions: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """跟踪决策结果

        Args:
            decision_id: 决策ID
            outcome_type: 结果类型
            actual_return: 实际收益
            actual_risk: 实际风险
            execution_time: 执行时间
            market_conditions: 市场条件
            metadata: 元数据

        Returns:
            结果ID
        """
        outcome = DecisionOutcome(
            outcome_id=self._generate_outcome_id(),
            decision_id=decision_id,
            outcome_type=outcome_type,
            actual_return=actual_return,
            actual_risk=actual_risk,
            execution_time=execution_time,
            market_conditions=market_conditions,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.decision_outcomes.append(outcome)

        # 更新统计
        self.stats["total_outcomes"] += 1
        if outcome_type in [OutcomeType.SUCCESS, OutcomeType.PARTIAL_SUCCESS]:
            self.stats["successful_outcomes"] += 1
        else:
            self.stats["failed_outcomes"] += 1

        # 更新平均有效性
        self._update_average_effectiveness(outcome)

        # 如果在学习循环中，记录到当前循环
        if self.current_cycle and self.current_cycle.status == "running":
            self.current_cycle.decisions_processed += 1

        logger.info(f"跟踪决策结果: {decision_id}, 类型: {outcome_type.value}")

        return outcome.outcome_id

    async def measure_decision_effectiveness(
        self,
        decision_id: str
    ) -> Optional[float]:
        """测量决策有效性

        Args:
            decision_id: 决策ID

        Returns:
            有效性分数 (0-1)
        """
        # 查找该决策的结果
        outcomes = [
            o for o in self.decision_outcomes
            if o.decision_id == decision_id
        ]

        if not outcomes:
            return None

        # 使用最新的结果
        latest_outcome = outcomes[-1]

        # 计算有效性：基于收益和风险的平衡
        if latest_outcome.actual_risk > 0:
            risk_adjusted_return = latest_outcome.actual_return / latest_outcome.actual_risk
        else:
            risk_adjusted_return = latest_outcome.actual_return

        # 归一化到0-1
        effectiveness = max(0.0, min(1.0, (risk_adjusted_return + 1.0) / 2.0))

        return effectiveness

    async def record_decision_feedback(
        self,
        decision_id: str,
        feedback: Dict[str, Any]
    ) -> None:
        """记录决策反馈

        Args:
            decision_id: 决策ID
            feedback: 反馈内容
        """
        # 查找该决策的结果
        for outcome in self.decision_outcomes:
            if outcome.decision_id == decision_id:
                outcome.metadata.update(feedback)
                break

        logger.info(f"记录决策反馈: {decision_id}")

    # ========== 知识价值评估 ==========

    async def assess_knowledge_value(
        self,
        knowledge_id: str
    ) -> KnowledgeValueAssessment:
        """评估知识价值

        Args:
            knowledge_id: 知识ID

        Returns:
            知识价值评估
        """
        # 查找使用该知识的决策
        related_outcomes = [
            o for o in self.decision_outcomes
            if knowledge_id in o.metadata.get('knowledge_ids', [])
        ]

        if not related_outcomes:
            # 新知识，给予默认评估
            assessment = KnowledgeValueAssessment(
                knowledge_id=knowledge_id,
                value_score=0.5,
                value_level=KnowledgeValueLevel.MEDIUM_VALUE,
                contribution_count=0,
                success_rate=0.0,
                average_effectiveness=0.0,
                last_used=datetime.now(),
                assessment_timestamp=datetime.now()
            )
        else:
            # 计算贡献次数
            contribution_count = len(related_outcomes)

            # 计算成功率
            successful = [
                o for o in related_outcomes
                if o.outcome_type in [OutcomeType.SUCCESS, OutcomeType.PARTIAL_SUCCESS]
            ]
            success_rate = len(successful) / contribution_count if contribution_count > 0 else 0.0

            # 计算平均有效性
            effectiveness_scores = []
            for outcome in related_outcomes:
                effectiveness = await self.measure_decision_effectiveness(outcome.decision_id)
                if effectiveness is not None:
                    effectiveness_scores.append(effectiveness)

            average_effectiveness = statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0

            # 计算价值分数
            value_score = (success_rate * 0.6 + average_effectiveness * 0.4)

            # 确定价值等级
            if value_score >= self.HIGH_VALUE_THRESHOLD:
                value_level = KnowledgeValueLevel.HIGH_VALUE
            elif value_score >= self.LOW_VALUE_THRESHOLD:
                value_level = KnowledgeValueLevel.MEDIUM_VALUE
            elif value_score > 0.2:
                value_level = KnowledgeValueLevel.LOW_VALUE
            else:
                value_level = KnowledgeValueLevel.NEGATIVE_VALUE

            # 最后使用时间
            last_used = max(o.timestamp for o in related_outcomes)

            assessment = KnowledgeValueAssessment(
                knowledge_id=knowledge_id,
                value_score=value_score,
                value_level=value_level,
                contribution_count=contribution_count,
                success_rate=success_rate,
                average_effectiveness=average_effectiveness,
                last_used=last_used,
                assessment_timestamp=datetime.now()
            )

        # 保存评估
        self.knowledge_assessments[knowledge_id] = assessment

        logger.info(f"评估知识价值: {knowledge_id}, 分数: {value_score:.3f}, 等级: {value_level.value}")

        return assessment

    async def identify_valuable_knowledge(
        self,
        min_value: float = 0.7
    ) -> List[str]:
        """识别有价值的知识

        Args:
            min_value: 最小价值分数

        Returns:
            知识ID列表
        """
        valuable_knowledge = []

        for knowledge_id, assessment in self.knowledge_assessments.items():
            if assessment.value_score >= min_value:
                valuable_knowledge.append(knowledge_id)

        logger.info(f"识别到 {len(valuable_knowledge)} 条高价值知识")

        return valuable_knowledge

    async def flag_underperforming_knowledge(
        self,
        max_value: float = 0.3
    ) -> List[str]:
        """标记表现不佳的知识

        Args:
            max_value: 最大价值分数

        Returns:
            知识ID列表
        """
        underperforming = []

        for knowledge_id, assessment in self.knowledge_assessments.items():
            if assessment.value_score <= max_value and assessment.contribution_count >= self.MIN_DECISIONS_FOR_ASSESSMENT:
                underperforming.append(knowledge_id)

        if underperforming:
            logger.warning(f"标记 {len(underperforming)} 条表现不佳的知识")

        return underperforming

    # ========== 知识优化触发 ==========

    async def trigger_knowledge_optimization(
        self,
        action: OptimizationAction,
        target_knowledge_ids: List[str],
        reason: str,
        priority: int = 5
    ) -> str:
        """触发知识优化

        Args:
            action: 优化动作
            target_knowledge_ids: 目标知识ID列表
            reason: 触发原因
            priority: 优先级 (1-10)

        Returns:
            触发ID
        """
        trigger = OptimizationTrigger(
            trigger_id=self._generate_trigger_id(),
            action=action,
            target_knowledge_ids=target_knowledge_ids,
            reason=reason,
            priority=priority,
            triggered_at=datetime.now()
        )

        self.optimization_triggers.append(trigger)
        self.stats["total_optimizations"] += 1

        # 调用回调
        for callback in self.optimization_callbacks.get(action.value, []):
            await callback(trigger)

        logger.info(f"触发知识优化: {action.value}, 目标: {len(target_knowledge_ids)} 条知识")

        return trigger.trigger_id

    async def suggest_knowledge_updates(
        self,
        knowledge_id: str
    ) -> List[str]:
        """建议知识更新

        Args:
            knowledge_id: 知识ID

        Returns:
            更新建议列表
        """
        suggestions = []

        # 获取评估
        assessment = self.knowledge_assessments.get(knowledge_id)
        if not assessment:
            return ["知识尚未被使用，无法生成建议"]

        # 基于价值等级生成建议
        if assessment.value_level == KnowledgeValueLevel.HIGH_VALUE:
            suggestions.append("知识表现优秀，考虑增强和推广")
            suggestions.append("可以基于此知识生成更多相关知识")
        elif assessment.value_level == KnowledgeValueLevel.MEDIUM_VALUE:
            suggestions.append("知识表现良好，持续监控其表现")
            suggestions.append("考虑增加该知识的应用场景")
        elif assessment.value_level == KnowledgeValueLevel.LOW_VALUE:
            suggestions.append("知识表现不佳，需要重新评估其内容")
            suggestions.append("考虑更新或增强该知识")
        else:  # NEGATIVE_VALUE
            suggestions.append("知识表现很差，强烈建议退役或重新训练")
            suggestions.append("检查该知识是否已过时或存在错误")

        # 基于使用频率生成建议
        days_since_last_use = (datetime.now() - assessment.last_used).days
        if days_since_last_use > 30:
            suggestions.append(f"知识已 {days_since_last_use} 天未使用，考虑退役")

        return suggestions

    async def recommend_knowledge_retirement(
        self,
        knowledge_id: str
    ) -> Tuple[bool, str]:
        """推荐知识退役

        Args:
            knowledge_id: 知识ID

        Returns:
            (是否推荐, 原因)
        """
        assessment = self.knowledge_assessments.get(knowledge_id)
        if not assessment:
            return False, "知识未被评估"

        # 检查退役条件
        reasons = []

        # 负价值
        if assessment.value_level == KnowledgeValueLevel.NEGATIVE_VALUE:
            reasons.append("知识价值为负")

        # 长期未使用
        days_since_last_use = (datetime.now() - assessment.last_used).days
        if days_since_last_use > 90:
            reasons.append(f"已 {days_since_last_use} 天未使用")

        # 低成功率且多次使用
        if (assessment.success_rate < 0.3 and
            assessment.contribution_count >= self.MIN_DECISIONS_FOR_ASSESSMENT * 2):
            reasons.append(f"成功率低 ({assessment.success_rate:.1%}) 且多次使用")

        # 综合判断
        if len(reasons) >= 2 or (len(reasons) == 1 and assessment.value_level == KnowledgeValueLevel.NEGATIVE_VALUE):
            return True, "; ".join(reasons)

        return False, ""

    # ========== 学习循环管理 ==========

    async def manage_learning_cycle(self) -> None:
        """管理学习循环"""
        logger.info("开始学习循环管理")

        while self._is_running:
            try:
                # 等待下一次循环
                await asyncio.sleep(self.LEARNING_CYCLE_INTERVAL)

                # 启动新的学习循环
                await self.start_learning_cycle()

                # 处理优化触发
                await self._process_optimization_triggers()

                # 生成洞察
                insights = await self._generate_cycle_insights()

                # 完成学习循环
                await self.complete_learning_cycle(insights)

            except Exception as e:
                logger.error(f"学习循环错误: {e}")
                if self.current_cycle:
                    self.current_cycle.status = "failed"
                await asyncio.sleep(60)  # 等待1分钟后重试

    async def start_learning_cycle(self) -> str:
        """开始学习循环

        Returns:
            循环ID
        """
        cycle_id = self._generate_cycle_id()

        self.current_cycle = LearningCycle(
            cycle_id=cycle_id,
            start_time=datetime.now(),
            end_time=None,
            decisions_processed=0,
            knowledge_optimized=0,
            effectiveness_improvement=0.0,
            status="running",
            insights=[]
        )

        logger.info(f"开始学习循环: {cycle_id}")

        return cycle_id

    async def optimize_feedback_frequency(self) -> Dict[str, Any]:
        """优化反馈频率

        Returns:
            优化建议
        """
        # 分析决策频率
        if len(self.decision_outcomes) < 10:
            return {"current_interval": self.LEARNING_CYCLE_INTERVAL, "suggestion": "maintain"}

        # 计算决策间隔
        timestamps = [o.timestamp for o in self.decision_outcomes[-20:]]
        intervals = [
            (timestamps[i] - timestamps[i-1]).total_seconds()
            for i in range(1, len(timestamps))
        ]

        if not intervals:
            return {"current_interval": self.LEARNING_CYCLE_INTERVAL, "suggestion": "maintain"}

        avg_interval = statistics.mean(intervals)

        # 优化建议
        if avg_interval < 300:  # 5分钟
            suggestion = "increase"
            suggested_interval = min(self.LEARNING_CYCLE_INTERVAL * 1.5, 7200)  # 最多2小时
        elif avg_interval > 3600:  # 1小时
            suggestion = "decrease"
            suggested_interval = max(self.LEARNING_CYCLE_INTERVAL * 0.8, 1800)  # 最少30分钟
        else:
            suggestion = "maintain"
            suggested_interval = self.LEARNING_CYCLE_INTERVAL

        return {
            "current_interval": self.LEARNING_CYCLE_INTERVAL,
            "average_decision_interval": avg_interval,
            "suggestion": suggestion,
            "suggested_interval": suggested_interval
        }

    async def balance_stability_adaptability(
        self
    ) -> Dict[str, Any]:
        """平衡稳定性和适应性

        Returns:
            平衡建议
        """
        # 计算稳定性指标
        if len(self.decision_outcomes) < 20:
            return {"stability_score": 0.5, "adaptability_score": 0.5, "balance": "balanced"}

        # 最近的20个决策
        recent_outcomes = self.decision_outcomes[-20:]

        # 稳定性：成功率方差
        success_rates = []
        window_size = 5
        for i in range(len(recent_outcomes) - window_size + 1):
            window = recent_outcomes[i:i+window_size]
            successful = sum(1 for o in window if o.outcome_type in [OutcomeType.SUCCESS, OutcomeType.PARTIAL_SUCCESS])
            success_rates.append(successful / window_size)

        if len(success_rates) > 1:
            stability_score = 1.0 - min(statistics.stdev(success_rates), 1.0)
        else:
            stability_score = 0.5

        # 适应性：改进率
        if len(success_rates) >= 2:
            improvement = (success_rates[-1] - success_rates[0])
            adaptability_score = max(0.0, min(1.0, improvement + 0.5))
        else:
            adaptability_score = 0.5

        # 平衡判断
        if stability_score > 0.8 and adaptability_score < 0.5:
            balance = "too_stable"
        elif adaptability_score > 0.8 and stability_score < 0.5:
            balance = "too_adaptive"
        else:
            balance = "balanced"

        return {
            "stability_score": stability_score,
            "adaptability_score": adaptability_score,
            "balance": balance
        }

    async def complete_learning_cycle(self, insights: List[str]) -> None:
        """完成学习循环"""
        if not self.current_cycle:
            return

        self.current_cycle.end_time = datetime.now()
        self.current_cycle.insights = insights
        self.current_cycle.status = "completed"

        # 计算有效性改进
        if len(self.decision_outcomes) >= self.MIN_DECISIONS_PER_CYCLE:
            recent_effectiveness = []
            for outcome in self.decision_outcomes[-self.MIN_DECISIONS_PER_CYCLE:]:
                effectiveness = await self.measure_decision_effectiveness(outcome.decision_id)
                if effectiveness is not None:
                    recent_effectiveness.append(effectiveness)

            if recent_effectiveness:
                self.current_cycle.effectiveness_improvement = statistics.mean(recent_effectiveness)

        # 添加到历史
        self.learning_cycles.append(self.current_cycle)
        self.stats["completed_cycles"] += 1

        logger.info(f"完成学习循环: {self.current_cycle.cycle_id}, 处理决策: {self.current_cycle.decisions_processed}")

        self.current_cycle = None

    # ========== 控制方法 ==========

    async def start(self) -> None:
        """启动反馈循环"""
        if self._is_running:
            logger.warning("反馈循环已在运行")
            return

        self._is_running = True

        # 启动学习循环任务
        self._cycle_task = asyncio.create_task(self.manage_learning_cycle())

        logger.info("[OK] 知识反馈循环已启动")

    async def stop(self) -> None:
        """停止反馈循环"""
        if not self._is_running:
            return

        self._is_running = False

        # 取消任务
        if self._cycle_task:
            self._cycle_task.cancel()

        # 等待任务完成
        try:
            await self._cycle_task
        except:
            pass

        logger.info("[OK] 知识反馈循环已停止")

    def register_callback(self, action: str, callback: Callable) -> None:
        """注册回调函数

        Args:
            action: 优化动作
            callback: 回调函数
        """
        self.optimization_callbacks[action].append(callback)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["total_knowledge_assessments"] = len(self.knowledge_assessments)
        stats["pending_triggers"] = len([t for t in self.optimization_triggers if t.status == "pending"])

        return stats

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_outcomes": 0,
            "successful_outcomes": 0,
            "failed_outcomes": 0,
            "average_effectiveness": 0.0,
            "total_optimizations": 0,
            "completed_cycles": 0
        }
        logger.info("统计信息已重置")

    # ========== 辅助方法 ==========

    def _update_average_effectiveness(self, outcome: DecisionOutcome) -> None:
        """更新平均有效性"""
        if outcome.actual_risk > 0:
            effectiveness = (outcome.actual_return / outcome.actual_risk + 1.0) / 2.0
            effectiveness = max(0.0, min(1.0, effectiveness))
        else:
            effectiveness = 0.5

        total = self.stats["average_effectiveness"] * (self.stats["total_outcomes"] - 1)
        self.stats["average_effectiveness"] = (total + effectiveness) / self.stats["total_outcomes"]

    async def _process_optimization_triggers(self) -> None:
        """处理优化触发"""
        # 按优先级排序
        pending_triggers = [
            t for t in self.optimization_triggers
            if t.status == "pending"
        ]
        pending_triggers.sort(key=lambda t: t.priority, reverse=True)

        # 处理触发
        for trigger in pending_triggers[:5]:  # 每次最多处理5个
            try:
                # 执行优化动作
                await self._execute_optimization(trigger)

                trigger.status = "completed"

                if self.current_cycle:
                    self.current_cycle.knowledge_optimized += len(trigger.target_knowledge_ids)

            except Exception as e:
                logger.error(f"执行优化失败: {trigger.trigger_id}, 错误: {e}")
                trigger.status = "failed"

    async def _execute_optimization(self, trigger: OptimizationTrigger) -> None:
        """执行优化"""
        # 这里可以实现具体的优化逻辑
        # 例如：更新知识、合并知识等
        logger.info(f"执行优化: {trigger.action.value}, 目标: {trigger.target_knowledge_ids}")

        # 调用回调
        for callback in self.optimization_callbacks.get(trigger.action.value, []):
            await callback(trigger)

    async def _generate_cycle_insights(self) -> List[str]:
        """生成循环洞察"""
        insights = []

        # 分析整体表现
        if self.stats["total_outcomes"] > 0:
            success_rate = self.stats["successful_outcomes"] / self.stats["total_outcomes"]
            insights.append(f"总体成功率: {success_rate:.1%}")

        # 识别高价值知识
        valuable_knowledge = await self.identify_valuable_knowledge()
        if valuable_knowledge:
            insights.append(f"发现 {len(valuable_knowledge)} 条高价值知识")

        # 识别低价值知识
        underperforming = await self.flag_underperforming_knowledge()
        if underperforming:
            insights.append(f"发现 {len(underperforming)} 条表现不佳的知识")

        # 稳定性和适应性平衡
        balance = await self.balance_stability_adaptability()
        if balance["balance"] != "balanced":
            insights.append(f"系统{balance['balance']}，需要调整")

        return insights

    def _generate_outcome_id(self) -> str:
        """生成结果ID"""
        self._outcome_id_counter += 1
        return f"outcome_{self._outcome_id_counter:06d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _generate_trigger_id(self) -> str:
        """生成触发ID"""
        self._trigger_id_counter += 1
        return f"trigger_{self._trigger_id_counter:06d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _generate_cycle_id(self) -> str:
        """生成循环ID"""
        return f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    def export_assessments(self, filepath: str) -> None:
        """导出评估结果"""
        data = {
            knowledge_id: assessment.to_dict()
            for knowledge_id, assessment in self.knowledge_assessments.items()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"知识评估已导出到: {filepath}")


def create_knowledge_feedback_loop(
    config: Dict[str, Any]
) -> KnowledgeFeedbackLoop:
    """创建知识反馈循环实例

    Args:
        config: 配置字典

    Returns:
        知识反馈循环实例
    """
    return KnowledgeFeedbackLoop(config)
