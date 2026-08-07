"""memo0驱动的决策系统 - V5.10 Phase 2集成管理器

集成知识驱动决策、实时更新、置信度计算和反馈循环四大核心模块。

核心功能：
1. 统一的决策API
2. 模块间数据流管理
3. 系统级监控和报告
4. 完整的端到端流程

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# 导入Phase 1模块
from .modules import (
    AutoKnowledgeExtractor,
    IntelligentKnowledgeClassifier,
    KnowledgeQualityOptimizer,
    KnowledgeTrendAnalyzer
)

# 导入Phase 2模块
from .modules.knowledge_based_decision_maker import (
    KnowledgeBasedDecisionMaker,
    Decision,
    DecisionContext,
    DecisionType,
    DecisionRationale
)
from .modules.real_time_knowledge_updater import (
    RealTimeKnowledgeUpdater,
    MarketDataSnapshot,
    UpdatePriority
)
from .modules.decision_confidence_calculator import (
    DecisionConfidenceCalculator,
    ConfidenceReport,
    ConfidenceLevel
)
from .modules.knowledge_feedback_loop import (
    KnowledgeFeedbackLoop,
    DecisionOutcome,
    OutcomeType
)

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """系统状态"""
    INITIALIZING = "initializing"  # 初始化中
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    total_decisions: int
    successful_decisions: int
    average_confidence: float
    knowledge_base_size: int
    updates_processed: int
    learning_cycles_completed: int
    system_health: float  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_decisions": self.total_decisions,
            "successful_decisions": self.successful_decisions,
            "average_confidence": self.average_confidence,
            "knowledge_base_size": self.knowledge_base_size,
            "updates_processed": self.updates_processed,
            "learning_cycles_completed": self.learning_cycles_completed,
            "system_health": self.system_health
        }


@dataclass
class DecisionRequest:
    """决策请求"""
    request_id: str
    market_data: Dict[str, Any]
    trading_parameters: Dict[str, Any]
    risk_profile: Dict[str, Any]
    time_constraints: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionResponse:
    """决策响应"""
    request_id: str
    decision: Decision
    confidence_report: ConfidenceReport
    processing_time: float
    system_status: SystemStatus
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "decision": self.decision.to_dict(),
            "confidence_report": self.confidence_report.to_dict(),
            "processing_time": self.processing_time,
            "system_status": self.system_status.value,
            "timestamp": self.timestamp.isoformat()
        }


class Memo0DrivenDecisionSystem:
    """memo0驱动的决策系统

    整合知识驱动决策、实时更新、置信度计算和反馈循环的完整系统。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化决策系统

        Args:
            config: 配置字典
        """
        self.config = config

        # 系统状态
        self.status = SystemStatus.INITIALIZING
        self._request_id_counter = 0

        # Phase 1模块
        self.knowledge_extractor: Optional[AutoKnowledgeExtractor] = None
        self.knowledge_classifier: Optional[IntelligentKnowledgeClassifier] = None
        self.knowledge_optimizer: Optional[KnowledgeQualityOptimizer] = None
        self.trend_analyzer: Optional[KnowledgeTrendAnalyzer] = None

        # Phase 2模块
        self.decision_maker: Optional[KnowledgeBasedDecisionMaker] = None
        self.knowledge_updater: Optional[RealTimeKnowledgeUpdater] = None
        self.confidence_calculator: Optional[DecisionConfidenceCalculator] = None
        self.feedback_loop: Optional[KnowledgeFeedbackLoop] = None

        # 共享数据
        self.knowledge_base: Dict[str, Dict[str, Any]] = {}
        self.decision_history: List[Decision] = []

        # 系统指标
        self.metrics_history: List[SystemMetrics] = []

        logger.info("🚀 memo0驱动的决策系统初始化开始")

    async def initialize(self) -> None:
        """初始化系统"""
        try:
            logger.info("初始化Phase 1模块...")

            # 初始化Phase 1模块
            self.knowledge_extractor = AutoKnowledgeExtractor(self.config.get('extractor_config', {}))
            self.knowledge_classifier = IntelligentKnowledgeClassifier(self.config.get('classifier_config', {}))
            self.knowledge_optimizer = KnowledgeQualityOptimizer(self.config.get('optimizer_config', {}))
            self.trend_analyzer = KnowledgeTrendAnalyzer(self.config.get('analyzer_config', {}))

            logger.info("初始化Phase 2模块...")

            # 初始化Phase 2模块
            self.decision_maker = KnowledgeBasedDecisionMaker(self.config.get('decision_maker_config', {}))
            self.knowledge_updater = RealTimeKnowledgeUpdater(self.config.get('updater_config', {}))
            self.confidence_calculator = DecisionConfidenceCalculator(self.config.get('calculator_config', {}))
            self.feedback_loop = KnowledgeFeedbackLoop(self.config.get('feedback_config', {}))

            # 注入共享知识库
            self.decision_maker.knowledge_base = self.knowledge_base
            self.knowledge_updater.knowledge_base = self.knowledge_base
            self.feedback_loop.knowledge_base = self.knowledge_base

            # 注册回调
            await self._register_callbacks()

            logger.info("✅ 系统初始化完成")
            self.status = SystemStatus.RUNNING

        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            self.status = SystemStatus.ERROR
            raise

    async def start(self) -> None:
        """启动系统"""
        if self.status == SystemStatus.RUNNING:
            logger.warning("系统已在运行")
            return

        logger.info("启动memo0驱动的决策系统...")

        # 启动实时更新器
        if self.knowledge_updater:
            await self.knowledge_updater.start()

        # 启动反馈循环
        if self.feedback_loop:
            await self.feedback_loop.start()

        logger.info("✅ 系统已启动")
        self.status = SystemStatus.RUNNING

    async def stop(self) -> None:
        """停止系统"""
        if self.status == SystemStatus.STOPPED:
            return

        logger.info("停止memo0驱动的决策系统...")

        self.status = SystemStatus.STOPPING

        # 停止反馈循环
        if self.feedback_loop:
            await self.feedback_loop.stop()

        # 停止实时更新器
        if self.knowledge_updater:
            await self.knowledge_updater.stop()

        self.status = SystemStatus.STOPPED
        logger.info("✅ 系统已停止")

    async def make_decision(
        self,
        request: DecisionRequest
    ) -> DecisionResponse:
        """制定决策

        Args:
            request: 决策请求

        Returns:
            决策响应
        """
        start_time = datetime.now()

        try:
            logger.info(f"处理决策请求: {request.request_id}")

            # 1. 创建决策上下文
            context = DecisionContext(
                market_data=request.market_data,
                trading_parameters=request.trading_parameters,
                risk_profile=request.risk_profile,
                time_constraints=request.time_constraints,
                metadata=request.metadata
            )

            # 2. 提取相关知识
            knowledge_matches = await self.decision_maker.retrieve_relevant_knowledge(context)

            # 3. 生成决策
            decision = await self.decision_maker.make_decision(context)

            # 4. 计算置信度
            confidence_report = await self.confidence_calculator.generate_confidence_report(
                decision.decision_id,
                {
                    "market_data": request.market_data,
                    "trading_parameters": request.trading_parameters,
                    "risk_profile": request.risk_profile
                },
                [km.to_dict() for km in decision.knowledge_matches]
            )

            # 5. 记录决策
            self.decision_history.append(decision)

            # 6. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 7. 创建响应
            response = DecisionResponse(
                request_id=request.request_id,
                decision=decision,
                confidence_report=confidence_report,
                processing_time=processing_time,
                system_status=self.status,
                timestamp=datetime.now()
            )

            logger.info(f"决策完成: {decision.decision_id}, 置信度: {confidence_report.confidence_score.overall_score:.3f}")

            return response

        except Exception as e:
            logger.error(f"决策制定失败: {e}")
            raise

    async def record_outcome(
        self,
        decision_id: str,
        outcome_type: OutcomeType,
        actual_return: float,
        actual_risk: float,
        execution_time: float,
        market_conditions: Dict[str, Any]
    ) -> None:
        """记录决策结果

        Args:
            decision_id: 决策ID
            outcome_type: 结果类型
            actual_return: 实际收益
            actual_risk: 实际风险
            execution_time: 执行时间
            market_conditions: 市场条件
        """
        if not self.feedback_loop:
            logger.warning("反馈循环未初始化")
            return

        # 记录到反馈循环
        await self.feedback_loop.track_decision_outcome(
            decision_id=decision_id,
            outcome_type=outcome_type,
            actual_return=actual_return,
            actual_risk=actual_risk,
            execution_time=execution_time,
            market_conditions=market_conditions
        )

        logger.info(f"记录决策结果: {decision_id}, 类型: {outcome_type.value}")

    async def add_knowledge(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """添加知识

        Args:
            content: 知识内容
            metadata: 元数据

        Returns:
            知识ID
        """
        import hashlib

        # 生成知识ID
        knowledge_id = f"knowledge_{hashlib.md5(content.encode()).hexdigest()[:12]}"

        # 添加到知识库
        self.knowledge_base[knowledge_id] = {
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "quality_score": 0.7,
            "value_score": 0.6
        }

        logger.info(f"添加知识: {knowledge_id}")

        return knowledge_id

    async def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        # 收集各模块统计
        decision_stats = self.decision_maker.get_decision_stats() if self.decision_maker else {}
        updater_stats = self.knowledge_updater.get_statistics() if self.knowledge_updater else {}
        feedback_stats = self.feedback_loop.get_statistics() if self.feedback_loop else {}

        # 计算系统健康度
        system_health = self._calculate_system_health()

        metrics = SystemMetrics(
            timestamp=datetime.now(),
            total_decisions=decision_stats.get('total_decisions', 0),
            successful_decisions=feedback_stats.get('successful_outcomes', 0),
            average_confidence=decision_stats.get('average_confidence', 0.0),
            knowledge_base_size=len(self.knowledge_base),
            updates_processed=updater_stats.get('total_updates', 0),
            learning_cycles_completed=feedback_stats.get('completed_cycles', 0),
            system_health=system_health
        )

        self.metrics_history.append(metrics)

        return metrics

    async def get_decision_history(
        self,
        limit: int = 100
    ) -> List[Decision]:
        """获取决策历史

        Args:
            limit: 返回数量限制

        Returns:
            决策列表
        """
        return self.decision_history[-limit:]

    async def get_knowledge_base_summary(self) -> Dict[str, Any]:
        """获取知识库摘要"""
        # 使用Phase 1模块分析知识库
        if self.knowledge_classifier:
            classification = await self.knowledge_classifier.classify_knowledge(self.knowledge_base)
        else:
            classification = {}

        if self.trend_analyzer:
            trends = await self.trend_analyzer.analyze_knowledge_trends(self.knowledge_base)
        else:
            trends = {}

        return {
            "total_knowledge": len(self.knowledge_base),
            "classification": classification,
            "trends": trends
        }

    async def optimize_knowledge_base(self) -> Dict[str, Any]:
        """优化知识库"""
        if not self.knowledge_optimizer:
            return {"status": "not_available"}

        # 优化知识
        optimization_result = await self.knowledge_optimizer.optimize_knowledge(self.knowledge_base)

        logger.info("知识库优化完成")

        return optimization_result

    async def generate_system_report(self) -> Dict[str, Any]:
        """生成系统报告"""
        # 获取系统指标
        metrics = await self.get_system_metrics()

        # 获取各模块统计
        decision_stats = self.decision_maker.get_decision_stats() if self.decision_maker else {}
        updater_stats = self.knowledge_updater.get_statistics() if self.knowledge_updater else {}
        calculator_stats = self.confidence_calculator.get_statistics() if self.confidence_calculator else {}
        feedback_stats = self.feedback_loop.get_statistics() if self.feedback_loop else {}

        # 获取知识库摘要
        knowledge_summary = await self.get_knowledge_base_summary()

        # 生成报告
        report = {
            "system_status": self.status.value,
            "metrics": metrics.to_dict(),
            "decision_maker": decision_stats,
            "knowledge_updater": updater_stats,
            "confidence_calculator": calculator_stats,
            "feedback_loop": feedback_stats,
            "knowledge_base": knowledge_summary,
            "generated_at": datetime.now().isoformat()
        }

        return report

    def _calculate_system_health(self) -> float:
        """计算系统健康度"""
        health_score = 1.0

        # 检查模块状态
        if not self.decision_maker or not self.knowledge_updater or not self.confidence_calculator or not self.feedback_loop:
            health_score -= 0.5

        # 检查知识库
        if len(self.knowledge_base) < 10:
            health_score -= 0.2

        # 检查系统状态
        if self.status != SystemStatus.RUNNING:
            health_score -= 0.3

        return max(0.0, health_score)

    async def _register_callbacks(self) -> None:
        """注册回调函数"""
        # 知识更新回调
        if self.knowledge_updater and self.feedback_loop:
            self.knowledge_updater.register_callback(
                'knowledge_gap',
                lambda task: self._handle_knowledge_gap(task)
            )

        # 优化触发回调
        if self.feedback_loop:
            self.feedback_loop.register_callback(
                'update_knowledge',
                lambda trigger: self._handle_knowledge_update(trigger)
            )

    async def _handle_knowledge_gap(self, task) -> None:
        """处理知识缺口"""
        logger.info(f"处理知识缺口: {task.task_id}")

        # 触发知识提取
        if self.knowledge_extractor and self.knowledge_updater:
            # 这里可以实现具体的知识提取逻辑
            pass

    async def _handle_knowledge_update(self, trigger) -> None:
        """处理知识更新"""
        logger.info(f"处理知识更新: {trigger.trigger_id}")

        # 更新知识库
        for knowledge_id in trigger.target_knowledge_ids:
            if knowledge_id in self.knowledge_base:
                # 标记为需要更新
                self.knowledge_base[knowledge_id]['needs_update'] = True

    def _generate_request_id(self) -> str:
        """生成请求ID"""
        self._request_id_counter += 1
        return f"request_{self._request_id_counter:06d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


async def create_decision_system(
    config: Dict[str, Any],
    auto_start: bool = True
) -> Memo0DrivenDecisionSystem:
    """创建决策系统实例

    Args:
        config: 配置字典
        auto_start: 是否自动启动

    Returns:
        决策系统实例
    """
    system = Memo0DrivenDecisionSystem(config)

    # 初始化系统
    await system.initialize()

    # 自动启动
    if auto_start:
        await system.start()

    return system


# 便捷函数
async def quick_decision(
    market_data: Dict[str, Any],
    trading_parameters: Dict[str, Any],
    risk_profile: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> DecisionResponse:
    """快速决策

    Args:
        market_data: 市场数据
        trading_parameters: 交易参数
        risk_profile: 风险配置
        config: 系统配置

    Returns:
        决策响应
    """
    if config is None:
        config = {}

    # 创建系统
    system = await create_decision_system(config, auto_start=False)
    await system.start()

    try:
        # 创建请求
        request = DecisionRequest(
            request_id=system._generate_request_id(),
            market_data=market_data,
            trading_parameters=trading_parameters,
            risk_profile=risk_profile,
            time_constraints={}
        )

        # 制定决策
        response = await system.make_decision(request)

        return response

    finally:
        # 停止系统
        await system.stop()
