"""增强版低风险套利引擎 V4.1

深度集成智能模块的套利引擎：
1. 集成风险预测 - 基于历史数据预测市场风险
2. 集成健康监控 - 系统状态实时监控和预防
3. 集成 Memo0 智能决策 - 基于历史知识的智能决策支持

核心特性：
- 多维度风险评估（市场风险 + 系统风险）
- 预测性风险管理（提前预警和预防）
- 智能参数优化（基于历史经验）
- 知识积累和学习（自动记录和改进）
- 动态风险调整（实时风险感知）
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from strategies.low_risk_arbitrage_engine import (
    ArbitrageExecution, ExecutionStatus, ExecutionStep, StepStatus,
    LowRiskArbitrageEngine, RiskLevel
)
from risk.deep_risk_manager import DeepRiskManager, get_deep_risk_manager

logger = logging.getLogger(__name__)


# ==================== 增强数据结构 ====================

@dataclass
class RiskPrediction:
    """风险预测

    Attributes:
        risk_type: 风险类型
        confidence: 置信度 (0-1)
        impact_level: 影响等级 (0-1)
        estimated_time: 预计发生时间（时间戳）
        recommendation: 建议措施
    """
    risk_type: str
    confidence: float
    impact_level: float
    estimated_time: float
    recommendation: str


@dataclass
class HealthStatus:
    """系统健康状态

    Attributes:
        health_score: 健康分数 (0-1)
        critical_issues: 关键问题列表
        warnings: 警告列表
        recommended_actions: 推荐行动列表
        timestamp: 时间戳
    """
    health_score: float
    critical_issues: List[str]
    warnings: List[str]
    recommended_actions: List[str]
    timestamp: float


@dataclass
class IntelligentDecision:
    """智能决策

    Attributes:
        decision_type: 决策类型
        action: 建议行动
        confidence: 置信度 (0-1)
        reasoning: 推理过程
        evidence: 证据列表
        alternatives: 替代方案
    """
    decision_type: str
    action: str
    confidence: float
    reasoning: str
    evidence: List[str]
    alternatives: List[str]


@dataclass
class EnhancedArbitrageExecution(ArbitrageExecution):
    """增强版套利执行记录

    Attributes:
        risk_prediction: 风险预测
        health_status: 健康状态
        intelligent_decision: 智能决策
        knowledge_id: 知识记录 ID
    """
    risk_prediction: Optional[RiskPrediction] = None
    health_status: Optional[HealthStatus] = None
    intelligent_decision: Optional[IntelligentDecision] = None
    knowledge_id: Optional[str] = None


# ==================== 增强版低风险套利引擎 ====================

class EnhancedLowRiskArbitrageEngine(LowRiskArbitrageEngine):
    """增强版低风险套利引擎 V4.1

    深度集成智能模块的低风险套利引擎。
    """

    def __init__(
        self,
        risk_manager: Optional[DeepRiskManager] = None,
        risk_predictor: Optional[Any] = None,
        health_monitor: Optional[Any] = None,
        knowledge_recorder: Optional[Any] = None,
        decision_assistant: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化增强版低风险套利引擎

        Args:
            risk_manager: 风险管理器实例
            risk_predictor: 风险预测器实例
            health_monitor: 健康监控器实例
            knowledge_recorder: 知识记录器实例
            decision_assistant: 决策辅助器实例
            config: 配置字典
        """
        # 初始化基类
        super().__init__(risk_manager, config)

        # V4.1 新增组件
        self.risk_predictor = risk_predictor
        self.health_monitor = health_monitor
        self.knowledge_recorder = knowledge_recorder
        self.decision_assistant = decision_assistant

        # V4.1 配置
        self.enable_risk_prediction = self.config.get('enable_risk_prediction', True)
        self.enable_health_monitoring = self.config.get('enable_health_monitoring', True)
        self.enable_intelligent_decision = self.config.get('enable_intelligent_decision', True)
        self.enable_knowledge_recording = self.config.get('enable_knowledge_recording', True)

        # V4.1 参数
        self.min_health_score = self.config.get('min_health_score', 0.7)
        self.max_risk_confidence = self.config.get('max_risk_confidence', 0.8)
        self.min_decision_confidence = self.config.get('min_decision_confidence', 0.6)

        # V4.1 统计数据
        self.risk_prediction_count = 0
        self.health_check_count = 0
        self.intelligent_decision_count = 0
        self.knowledge_record_count = 0

        logger.info("✅ 增强版低风险套利引擎 V4.1 初始化完成")
        logger.info(f"   - 风险预测: {'✅' if self.risk_predictor else '⚠️ 未启用'}")
        logger.info(f"   - 健康监控: {'✅' if self.health_monitor else '⚠️ 未启用'}")
        logger.info(f"   - 智能决策: {'✅' if self.decision_assistant else '⚠️ 未启用'}")
        logger.info(f"   - 知识记录: {'✅' if self.knowledge_recorder else '⚠️ 未启用'}")

    async def execute_arbitrage(
        self,
        opportunity: Dict[str, Any],
        execution_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """执行增强版低风险套利交易

        Args:
            opportunity: 套利机会
            execution_plan: 执行计划（步骤列表）

        Returns:
            执行结果字典
        """
        execution_id = f"arb_{int(time.time() * 1000)}"

        logger.info(f"开始执行增强版低风险套利: {execution_id}")

        # 创建增强版执行记录
        execution = EnhancedArbitrageExecution(
            execution_id=execution_id,
            opportunity=opportunity,
            steps=self._create_execution_steps(execution_plan),
            status=ExecutionStatus.PENDING,
            start_time=time.time()
        )

        self.active_executions[execution_id] = execution

        try:
            # V4.1: 预测风险
            if self.enable_risk_prediction and self.risk_predictor:
                execution.risk_prediction = await self._predict_risk(execution)
                self.risk_prediction_count += 1
                logger.info(f"✅ 风险预测: {execution.risk_prediction.risk_type}, "
                          f"置信度: {execution.risk_prediction.confidence:.2f}")

            # V4.1: 检查健康状态
            if self.enable_health_monitoring and self.health_monitor:
                execution.health_status = await self._check_health_status(execution)
                self.health_check_count += 1
                logger.info(f"✅ 健康检查: 分数={execution.health_status.health_score:.2f}")

            # V4.1: 获取智能决策建议
            if self.enable_intelligent_decision and self.decision_assistant:
                execution.intelligent_decision = await self._get_intelligent_decision(execution)
                self.intelligent_decision_count += 1
                logger.info(f"✅ 智能决策: {execution.intelligent_decision.action}, "
                          f"置信度: {execution.intelligent_decision.confidence:.2f}")

            # 1. 预检阶段
            if self.enable_pre_check:
                execution.status = ExecutionStatus.PRE_CHECKING
                await self._enhanced_pre_check_execution(execution)

            # 2. 执行阶段
            execution.status = ExecutionStatus.EXECUTING
            success = await self._execute_steps(execution)

            if success:
                # 3. 完成阶段
                execution.status = ExecutionStatus.COMPLETED
                execution.end_time = time.time()
                execution.actual_profit = self._calculate_actual_profit(execution)

                # V4.1: 记录知识
                if self.enable_knowledge_recording and self.knowledge_recorder:
                    execution.knowledge_id = await self._record_trade_knowledge(execution)
                    self.knowledge_record_count += 1
                    logger.info(f"✅ 知识记录: ID={execution.knowledge_id}")

                self._update_statistics(execution, success=True)
                logger.info(f"套利执行成功: {execution_id}, 利润: {execution.actual_profit:.2f}")

                return {
                    'execution_id': execution_id,
                    'status': 'completed',
                    'profit': execution.actual_profit,
                    'execution_time': execution.end_time - execution.start_time,
                    'steps_count': len(execution.steps),
                    'risk_level': execution.risk_level.value,
                    'risk_prediction': execution.risk_prediction.risk_type if execution.risk_prediction else None,
                    'health_score': execution.health_status.health_score if execution.health_status else None,
                    'decision_confidence': execution.intelligent_decision.confidence if execution.intelligent_decision else None,
                    'knowledge_id': execution.knowledge_id
                }
            else:
                # 执行失败，触发回滚
                execution.status = ExecutionStatus.FAILED
                execution.end_time = time.time()

                if self.enable_auto_rollback:
                    await self._rollback_execution(execution)
                    execution.status = ExecutionStatus.ROLLED_BACK

                self._update_statistics(execution, success=False)
                logger.error(f"套利执行失败: {execution_id}")

                return {
                    'execution_id': execution_id,
                    'status': 'failed',
                    'error': execution.error_message or "执行失败",
                    'execution_time': execution.end_time - execution.start_time,
                    'steps_completed': len([s for s in execution.steps if s.status == StepStatus.COMPLETED]),
                    'total_steps': len(execution.steps),
                    'rolled_back': execution.status == ExecutionStatus.ROLLED_BACK
                }

        except Exception as e:
            # 异常处理
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = time.time()

            logger.error(f"套利执行异常: {execution_id}, {e}")

            # 尝试回滚
            if self.enable_auto_rollback:
                try:
                    await self._rollback_execution(execution)
                except Exception as rollback_error:
                    logger.error(f"回滚失败: {rollback_error}")

            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'execution_time': execution.end_time - execution.start_time
            }

        finally:
            # 记录到历史
            self.execution_history.append(execution)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            # 通知风险管理器
            if self.risk_manager:
                await self.risk_manager.complete_trade_execution(
                    execution_id,
                    execution.opportunity
                )

    # ==================== V4.1 新增方法 ====================

    async def _predict_risk(
        self,
        execution: EnhancedArbitrageExecution
    ) -> RiskPrediction:
        """预测交易风险

        Args:
            execution: 执行记录

        Returns:
            风险预测
        """
        try:
            if not self.risk_predictor:
                return RiskPrediction(
                    risk_type="unknown",
                    confidence=0.0,
                    impact_level=0.0,
                    estimated_time=0.0,
                    recommendation="无法预测（风险预测器未启用）"
                )

            # 收集交易特征
            opportunity = execution.opportunity
            features = {
                'symbol': opportunity.get('symbol', ''),
                'profit_rate': opportunity.get('profit_rate', 0),
                'risk_score': execution.total_risk_score,
                'steps_count': len(execution.steps),
                'exchange': opportunity.get('exchange', ''),
                'strategy': opportunity.get('strategy', '')
            }

            # 调用风险预测器
            if hasattr(self.risk_predictor, 'predict_risk'):
                prediction = await self.risk_predictor.predict_risk(features)
                return prediction
            elif hasattr(self.risk_predictor, 'get_prediction'):
                prediction = self.risk_predictor.get_prediction(features)
                return prediction
            else:
                logger.warning("风险预测器不支持预测功能")
                return RiskPrediction(
                    risk_type="unknown",
                    confidence=0.0,
                    impact_level=0.0,
                    estimated_time=0.0,
                    recommendation="风险预测器功能不可用"
                )

        except Exception as e:
            logger.error(f"风险预测失败: {e}")
            return RiskPrediction(
                risk_type="prediction_error",
                confidence=0.0,
                impact_level=0.0,
                estimated_time=0.0,
                recommendation=f"预测失败: {e}"
            )

    async def _check_health_status(
        self,
        execution: EnhancedArbitrageExecution
    ) -> HealthStatus:
        """检查系统健康状态

        Args:
            execution: 执行记录

        Returns:
            健康状态
        """
        try:
            if not self.health_monitor:
                return HealthStatus(
                    health_score=1.0,
                    critical_issues=[],
                    warnings=[],
                    recommended_actions=[],
                    timestamp=time.time()
                )

            # 调用健康监控器
            if hasattr(self.health_monitor, 'get_health_prediction'):
                prediction = self.health_monitor.get_health_prediction()

                # 提取健康分数
                health_score = prediction.overall_health_score if prediction else 1.0

                # 提取关键问题和警告
                critical_issues = []
                warnings = []
                recommended_actions = []

                if prediction and prediction.anomalies:
                    for anomaly in prediction.anomalies:
                        if anomaly.confidence > 0.8:
                            critical_issues.append(
                                f"{anomaly.anomaly_type.value} (置信度: {anomaly.confidence:.2f})"
                            )
                        elif anomaly.confidence > 0.5:
                            warnings.append(
                                f"{anomaly.anomaly_type.value} (置信度: {anomaly.confidence:.2f})"
                            )

                if prediction and prediction.actions:
                    for action in prediction.actions:
                        recommended_actions.append(
                            f"{action.description} (优先级: {action.priority})"
                        )

                return HealthStatus(
                    health_score=health_score,
                    critical_issues=critical_issues,
                    warnings=warnings,
                    recommended_actions=recommended_actions,
                    timestamp=time.time()
                )
            else:
                logger.warning("健康监控器不支持健康预测")
                return HealthStatus(
                    health_score=1.0,
                    critical_issues=[],
                    warnings=[],
                    recommended_actions=[],
                    timestamp=time.time()
                )

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return HealthStatus(
                health_score=0.5,  # 保守的健康分数
                critical_issues=[f"健康检查失败: {e}"],
                warnings=[],
                recommended_actions=[],
                timestamp=time.time()
            )

    async def _get_intelligent_decision(
        self,
        execution: EnhancedArbitrageExecution
    ) -> IntelligentDecision:
        """获取智能决策建议

        Args:
            execution: 执行记录

        Returns:
            智能决策
        """
        try:
            if not self.decision_assistant:
                return IntelligentDecision(
                    decision_type="unknown",
                    action="无建议",
                    confidence=0.0,
                    reasoning="决策辅助器未启用",
                    evidence=[],
                    alternatives=[]
                )

            # 收集决策上下文
            opportunity = execution.opportunity
            context = {
                'symbol': opportunity.get('symbol', ''),
                'profit_rate': opportunity.get('profit_rate', 0),
                'risk_score': execution.total_risk_score,
                'risk_level': execution.risk_level.value,
                'risk_prediction': execution.risk_prediction,
                'health_score': execution.health_status.health_score if execution.health_status else 1.0
            }

            # 调用决策辅助器
            if hasattr(self.decision_assistant, 'advise_on_trade'):
                advice = await self.decision_assistant.advise_on_trade(context)

                return IntelligentDecision(
                    decision_type=advice.get('decision_type', 'trade'),
                    action=advice.get('action', 'proceed'),
                    confidence=advice.get('confidence', 0.0),
                    reasoning=advice.get('reasoning', ''),
                    evidence=advice.get('evidence', []),
                    alternatives=advice.get('alternatives', [])
                )
            else:
                logger.warning("决策辅助器不支持交易决策")
                return IntelligentDecision(
                    decision_type="unknown",
                    action="无建议",
                    confidence=0.0,
                    reasoning="决策辅助器功能不可用",
                    evidence=[],
                    alternatives=[]
                )

        except Exception as e:
            logger.error(f"智能决策失败: {e}")
            return IntelligentDecision(
                decision_type="error",
                action="谨慎执行",
                confidence=0.0,
                reasoning=f"决策失败: {e}",
                evidence=[],
                alternatives=["降低仓位", "推迟执行", "跳过此机会"]
            )

    async def _enhanced_pre_check_execution(
        self,
        execution: EnhancedArbitrageExecution
    ) -> None:
        """增强版预检

        Args:
            execution: 执行记录

        Raises:
            ValueError: 预检失败
        """
        logger.info(f"执行增强版预检: {execution.execution_id}")

        # 1. 基础风险预检
        await super()._pre_check_execution(execution)

        # 2. 检查风险预测
        if execution.risk_prediction:
            if execution.risk_prediction.confidence > self.max_risk_confidence:
                raise ValueError(
                    f"风险预测置信度过高: {execution.risk_prediction.confidence:.2f} > {self.max_risk_confidence}\n"
                    f"建议: {execution.risk_prediction.recommendation}"
                )

            if execution.risk_prediction.impact_level > 0.8:
                logger.warning(f"高风险预警: {execution.risk_prediction.recommendation}")

        # 3. 检查健康状态
        if execution.health_status:
            if execution.health_status.health_score < self.min_health_score:
                raise ValueError(
                    f"系统健康分数过低: {execution.health_status.health_score:.2f} < {self.min_health_score}\n"
                    f"关键问题: {execution.health_status.critical_issues}\n"
                    f"建议: {execution.health_status.recommended_actions}"
                )

            if execution.health_status.critical_issues:
                logger.warning(f"系统存在关键问题: {execution.health_status.critical_issues}")

        # 4. 检查智能决策
        if execution.intelligent_decision:
            if execution.intelligent_decision.confidence < self.min_decision_confidence:
                logger.warning(
                    f"决策置信度较低: {execution.intelligent_decision.confidence:.2f} < {self.min_decision_confidence}\n"
                    f"推理: {execution.intelligent_decision.reasoning}\n"
                    f"替代方案: {execution.intelligent_decision.alternatives}"
                )

            if execution.intelligent_decision.action.lower() == 'skip':
                raise ValueError(
                    f"智能决策建议跳过此机会\n"
                    f"推理: {execution.intelligent_decision.reasoning}"
                )

        logger.info(f"✅ 增强版预检通过")

    async def _record_trade_knowledge(
        self,
        execution: EnhancedArbitrageExecution
    ) -> Optional[str]:
        """记录交易知识

        Args:
            execution: 执行记录

        Returns:
            知识记录 ID，如果失败则返回 None
        """
        try:
            if not self.knowledge_recorder:
                return None

            # 准备交易数据
            trade_data = {
                'execution_id': execution.execution_id,
                'symbol': execution.opportunity.get('symbol', ''),
                'profit': execution.actual_profit,
                'profit_rate': execution.opportunity.get('profit_rate', 0),
                'risk_score': execution.total_risk_score,
                'risk_level': execution.risk_level.value,
                'strategy': execution.opportunity.get('strategy', ''),
                'execution_time': execution.end_time - execution.start_time,
                'status': execution.status.value,
                'timestamp': execution.start_time,
                # V4.1 增强数据
                'risk_prediction': execution.risk_prediction.risk_type if execution.risk_prediction else None,
                'risk_prediction_confidence': execution.risk_prediction.confidence if execution.risk_prediction else None,
                'health_score': execution.health_status.health_score if execution.health_status else None,
                'decision_action': execution.intelligent_decision.action if execution.intelligent_decision else None,
                'decision_confidence': execution.intelligent_decision.confidence if execution.intelligent_decision else None,
            }

            # 调用知识记录器
            if hasattr(self.knowledge_recorder, 'record_trade'):
                result = await self.knowledge_recorder.record_trade(trade_data)
                return result.get('knowledge_id')
            else:
                logger.warning("知识记录器不支持交易记录")
                return None

        except Exception as e:
            logger.error(f"记录交易知识失败: {e}")
            return None

    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """获取增强版统计

        Returns:
            统计数据字典
        """
        base_stats = self.get_execution_statistics()

        # V4.1 增强统计
        enhanced_stats = {
            **base_stats,
            'risk_prediction_count': self.risk_prediction_count,
            'health_check_count': self.health_check_count,
            'intelligent_decision_count': self.intelligent_decision_count,
            'knowledge_record_count': self.knowledge_record_count,
            'prediction_rate': (
                self.risk_prediction_count / self.total_executions
                if self.total_executions > 0 else 0
            ),
            'health_check_rate': (
                self.health_check_count / self.total_executions
                if self.total_executions > 0 else 0
            ),
            'decision_rate': (
                self.intelligent_decision_count / self.total_executions
                if self.total_executions > 0 else 0
            ),
            'knowledge_record_rate': (
                self.knowledge_record_count / self.total_executions
                if self.total_executions > 0 else 0
            )
        }

        return enhanced_stats


# ==================== 全局实例 ====================

_enhanced_arbitrage_engine: Optional[EnhancedLowRiskArbitrageEngine] = None


def initialize_enhanced_low_risk_arbitrage_engine(
    risk_manager: Optional[DeepRiskManager] = None,
    risk_predictor: Optional[Any] = None,
    health_monitor: Optional[Any] = None,
    knowledge_recorder: Optional[Any] = None,
    decision_assistant: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None
) -> EnhancedLowRiskArbitrageEngine:
    """初始化全局增强版低风险套利引擎

    Args:
        risk_manager: 风险管理器实例
        risk_predictor: 风险预测器实例
        health_monitor: 健康监控器实例
        knowledge_recorder: 知识记录器实例
        decision_assistant: 决策辅助器实例
        config: 配置字典

    Returns:
        增强版低风险套利引擎实例
    """
    global _enhanced_arbitrage_engine
    _enhanced_arbitrage_engine = EnhancedLowRiskArbitrageEngine(
        risk_manager=risk_manager,
        risk_predictor=risk_predictor,
        health_monitor=health_monitor,
        knowledge_recorder=knowledge_recorder,
        decision_assistant=decision_assistant,
        config=config
    )
    return _enhanced_arbitrage_engine


def get_enhanced_low_risk_arbitrage_engine() -> Optional[EnhancedLowRiskArbitrageEngine]:
    """获取全局增强版低风险套利引擎

    Returns:
        增强版低风险套利引擎实例，如果未初始化则返回 None
    """
    return _enhanced_arbitrage_engine
