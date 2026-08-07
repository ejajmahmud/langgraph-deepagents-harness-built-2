"""知识循环管理器 (KnowledgeCycleManager) - V4.0

管理完整的知识循环：决策 → 记录 → 学习 → 优化 → 决策

核心功能：
1. 执行决策并记录
2. 自动知识积累
3. 知识分析和学习
4. 决策优化和改进
5. 持续循环和进化

集成范围：
- 知识记录器
- 智能决策辅助器
- 所有业务模块
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .knowledge_recorder import KnowledgeRecorder, get_knowledge_recorder, KnowledgeType
from .decision_assistant import DecisionAssistant, get_decision_assistant, DecisionAdvice, DecisionType

logger = logging.getLogger(__name__)


class CycleStatus(Enum):
    """循环状态"""
    PENDING = "pending"  # 待执行
    EXECUTING = "executing"  # 执行中
    RECORDING = "recording"  # 记录中
    LEARNING = "learning"  # 学习中
    OPTIMIZING = "optimizing"  # 优化中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败


@dataclass
class CycleIteration:
    """循环迭代

    Attributes:
        iteration_id: 迭代 ID
        context: 决策上下文
        advice: 决策建议
        execution_result: 执行结果
        status: 状态
        start_time: 开始时间
        end_time: 结束时间
        learning_insights: 学习洞察
        improvements: 改进建议
    """
    iteration_id: str
    context: Dict[str, Any]
    advice: Optional[DecisionAdvice]
    execution_result: Optional[Dict[str, Any]]
    status: CycleStatus
    start_time: float
    end_time: Optional[float] = None
    learning_insights: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)


class KnowledgeCycleManager:
    """知识循环管理器

    管理完整的知识循环：决策 → 记录 → 学习 → 优化 → 决策
    """

    def __init__(
        self,
        recorder: Optional[KnowledgeRecorder] = None,
        assistant: Optional[DecisionAssistant] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化知识循环管理器

        Args:
            recorder: 知识记录器实例
            assistant: 决策辅助器实例
            config: 配置字典
        """
        self.recorder = recorder or get_knowledge_recorder()
        self.assistant = assistant or get_decision_assistant()
        self.config = config or {}

        # 配置参数
        self.enable_auto_cycle = self.config.get('enable_auto_cycle', True)
        self.enable_learning = self.config.get('enable_learning', True)
        self.cycle_interval = self.config.get('cycle_interval', 60)  # 秒
        self.max_history = self.config.get('max_history', 1000)

        # 循环历史
        self.cycle_history: List[CycleIteration] = []

        # 统计数据
        self.total_cycles = 0
        self.successful_cycles = 0
        self.failed_cycles = 0
        self.total_learning = 0

        logger.info("✅ 知识循环管理器初始化完成")

    async def execute_trade_cycle(
        self,
        trade_context: Dict[str, Any],
        executor: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """执行交易知识循环

        Args:
            trade_context: 交易上下文
            executor: 执行函数（可选）

        Returns:
            执行结果字典
        """
        iteration_id = f"cycle_{int(time.time() * 1000)}"
        start_time = time.time()

        # 创建迭代记录
        iteration = CycleIteration(
            iteration_id=iteration_id,
            context=trade_context,
            advice=None,
            execution_result=None,
            status=CycleStatus.PENDING,
            start_time=start_time
        )

        self.cycle_history.append(iterition)

        try:
            # ===== 阶段 1: 获取决策建议 =====
            iteration.status = CycleStatus.EXECUTING
            logger.info(f"[{iteration_id}] 开始交易知识循环")

            advice = await self.assistant.advise_on_trade(trade_context)
            iteration.advice = advice

            logger.info(f"[{iteration_id}] 决策建议: {advice.recommendation} (置信度: {advice.confidence:.2f})")

            # ===== 阶段 2: 执行决策 =====
            if executor:
                # 使用提供的执行函数
                execution_result = await executor(trade_context, advice)
            else:
                # 默认执行逻辑
                execution_result = await self._execute_trade(trade_context, advice)

            iteration.execution_result = execution_result

            # ===== 阶段 3: 记录知识 =====
            iteration.status = CycleStatus.RECORDING

            # 记录决策知识
            await self.recorder.record_decision({
                "decision_type": DecisionType.TRADE.value,
                "context": trade_context,
                "action": advice.recommendation,
                "outcome": execution_result.get("status", "unknown"),
                "confidence": advice.confidence,
                "reasoning": advice.reasoning
            })

            # 如果交易完成，记录交易知识
            if execution_result.get("status") == "completed":
                await self.recorder.record_trade({
                    "symbol": trade_context.get("symbol"),
                    "strategy": trade_context.get("strategy"),
                    "profit": execution_result.get("profit", 0),
                    "risk_score": trade_context.get("risk_score", 0),
                    "execution_time": execution_result.get("execution_time", 0),
                    "status": execution_result.get("status"),
                })
                self.successful_cycles += 1
            else:
                self.failed_cycles += 1

            # ===== 阶段 4: 学习和优化（如果启用）=====
            if self.enable_learning:
                iteration.status = CycleStatus.LEARNING
                insights = await self._learn_from_execution(iteration)

                if insights:
                    iteration.learning_insights = insights
                    self.total_learning += 1

                    # 记录学习知识
                    for insight in insights:
                        await self.recorder.record_learning({
                            "insight": insight,
                            "pattern": self._extract_pattern(iteration),
                            "improvement": self._generate_improvement(iteration),
                            "validation": execution_result.get("validation")
                        })

                # ===== 阶段 5: 优化决策 =====
                iteration.status = CycleStatus.OPTIMIZING
                improvements = await self._optimize_decision(iteration)

                if improvements:
                    iteration.improvements = improvements

            # ===== 完成循环 =====
            iteration.status = CycleStatus.COMPLETED
            iteration.end_time = time.time()

            self.total_cycles += 1

            # 限制历史大小
            if len(self.cycle_history) > self.max_history:
                self.cycle_history = self.cycle_history[-self.max_history:]

            execution_time = iteration.end_time - iteration.start_time
            logger.info(f"[{iteration_id}] 循环完成，耗时: {execution_time:.2f}秒")

            return {
                "iteration_id": iteration_id,
                "advice": advice,
                "execution_result": execution_result,
                "learning_insights": iteration.learning_insights,
                "improvements": iteration.improvements,
                "status": iteration.status.value,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"[{iteration_id}] 循环执行失败: {e}")
            iteration.status = CycleStatus.FAILED
            iteration.end_time = time.time()
            self.failed_cycles += 1

            return {
                "iteration_id": iteration_id,
                "error": str(e),
                "status": "failed"
            }

    async def execute_risk_cycle(
        self,
        risk_context: Dict[str, Any],
        executor: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """执行风险管理知识循环

        Args:
            risk_context: 风险上下文
            executor: 执行函数（可选）

        Returns:
            执行结果字典
        """
        iteration_id = f"risk_cycle_{int(time.time() * 1000)}"
        start_time = time.time()

        iteration = CycleIteration(
            iteration_id=iteration_id,
            context=risk_context,
            advice=None,
            execution_result=None,
            status=CycleStatus.PENDING,
            start_time=start_time
        )

        self.cycle_history.append(iteration)

        try:
            # 获取决策建议
            iteration.status = CycleStatus.EXECUTING
            advice = await self.assistant.advise_on_risk(risk_context)
            iteration.advice = advice

            # 执行决策
            if executor:
                execution_result = await executor(risk_context, advice)
            else:
                execution_result = await self._execute_risk_management(risk_context, advice)

            iteration.execution_result = execution_result

            # 记录知识
            iteration.status = CycleStatus.RECORDING
            await self.recorder.record_decision({
                "decision_type": DecisionType.RISK.value,
                "context": risk_context,
                "action": advice.recommendation,
                "outcome": execution_result.get("status", "unknown"),
                "confidence": advice.confidence,
                "reasoning": advice.reasoning
            })

            # 记录风险预测知识
            await self.recorder.record_risk_prediction({
                "risk_level": risk_context.get("risk_level"),
                "risk_score": risk_context.get("current_risk_score", 0),
                "prediction_confidence": advice.confidence,
                "recommendations": [advice.recommendation],
                "metrics": risk_context
            })

            # 学习和优化
            if self.enable_learning:
                iteration.status = CycleStatus.LEARNING
                insights = await self._learn_from_execution(iteration)

                if insights:
                    iteration.learning_insights = insights
                    self.total_learning += 1

                iteration.status = CycleStatus.OPTIMIZING
                improvements = await self._optimize_decision(iteration)

                if improvements:
                    iteration.improvements = improvements

            iteration.status = CycleStatus.COMPLETED
            iteration.end_time = time.time()
            self.total_cycles += 1

            return {
                "iteration_id": iteration_id,
                "advice": advice,
                "execution_result": execution_result,
                "learning_insights": iteration.learning_insights,
                "improvements": iteration.improvements,
                "status": iteration.status.value
            }

        except Exception as e:
            logger.error(f"[{iteration_id}] 风险循环执行失败: {e}")
            iteration.status = CycleStatus.FAILED
            iteration.end_time = time.time()
            self.failed_cycles += 1

            return {
                "iteration_id": iteration_id,
                "error": str(e),
                "status": "failed"
            }

    async def _execute_trade(
        self,
        context: Dict[str, Any],
        advice: DecisionAdvice
    ) -> Dict[str, Any]:
        """执行交易（默认实现）

        Args:
            context: 交易上下文
            advice: 决策建议

        Returns:
            执行结果
        """
        try:
            # 根据建议执行交易
            if "建议执行交易" in advice.recommendation:
                # 模拟执行
                logger.info(f"执行交易: {context['symbol']}，策略: {context['strategy']}")

                # 这里应该调用实际的交易引擎
                # 为了示例，我们返回模拟结果
                await asyncio.sleep(0.1)  # 模拟执行时间

                return {
                    "status": "completed",
                    "profit": context.get("expected_profit", 0),
                    "execution_time": 0.1,
                    "timestamp": time.time()
                }
            else:
                # 跳过交易
                logger.info(f"跳过交易: {advice.recommendation}")

                return {
                    "status": "skipped",
                    "reason": advice.recommendation,
                    "timestamp": time.time()
                }

        except Exception as e:
            logger.error(f"交易执行失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            }

    async def _execute_risk_management(
        self,
        context: Dict[str, Any],
        advice: DecisionAdvice
    ) -> Dict[str, Any]:
        """执行风险管理（默认实现）

        Args:
            context: 风险上下文
            advice: 决策建议

        Returns:
            执行结果
        """
        try:
            # 根据建议调整风险管理
            logger.info(f"执行风险管理: {advice.recommendation}")

            # 这里应该调用实际的风险管理器
            # 为了示例，我们返回模拟结果
            await asyncio.sleep(0.1)

            return {
                "status": "completed",
                "action_taken": advice.recommendation,
                "new_risk_level": context.get("current_risk_score", 0),
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"风险管理执行失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            }

    async def _learn_from_execution(
        self,
        iteration: CycleIteration
    ) -> List[str]:
        """从执行中学习

        Args:
            iteration: 迭代记录

        Returns:
            学习洞察列表
        """
        insights = []

        try:
            # 分析执行结果
            result = iteration.execution_result
            advice = iteration.advice

            if not result or not advice:
                return insights

            # 洞察 1: 决策准确性
            if result.get("status") == "completed":
                if advice.confidence > 0.8:
                    insights.append("高置信度决策成功，可以信任此类建议")
                else:
                    insights.append(f"中等置信度决策成功，建议提高此类情况的数据质量")

            # 洞察 2: 执行效率
            execution_time = result.get("execution_time", 0)
            if execution_time > 1.0:
                insights.append("执行时间较长，建议优化执行流程")
            elif execution_time < 0.1:
                insights.append("执行效率很高，保持当前流程")

            # 洞察 3: 上下文相关性
            if iteration.context:
                context_keys = list(iteration.context.keys())
                insights.append(f"关键上下文因素: {', '.join(context_keys)}")

            logger.debug(f"[{iteration.iteration_id}] 学习洞察: {insights}")

        except Exception as e:
            logger.error(f"学习过程失败: {e}")

        return insights

    async def _optimize_decision(
        self,
        iteration: CycleIteration
    ) -> List[str]:
        """优化决策

        Args:
            iteration: 迭代记录

        Returns:
            改进建议列表
        """
        improvements = []

        try:
            # 分析历史表现
            recent_iterations = self.cycle_history[-20:]  # 最近20次迭代

            if len(recent_iterations) < 5:
                return improvements

            # 统计成功率
            successful = [i for i in recent_iterations if i.status == CycleStatus.COMPLETED]
            success_rate = len(successful) / len(recent_iterations) if recent_iterations else 0

            # 改进建议 1: 成功率优化
            if success_rate < 0.8:
                improvements.append("建议提高决策质量，增加上下文分析深度")
            elif success_rate > 0.95:
                improvements.append("决策质量优秀，可以适当增加自动化程度")

            # 改进建议 2: 置信度校准
            confidences = [i.advice.confidence for i in successful if i.advice]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence < 0.6:
                    improvements.append("建议提高决策置信度，增加验证步骤")
                elif avg_confidence > 0.9:
                    improvements.append("高置信度决策多，建议增加多样性")

            # 改进建议 3: 学习效率
            learning_iterations = [i for i in recent_iterations if i.learning_insights]
            learning_rate = len(learning_iterations) / len(recent_iterations) if recent_iterations else 0

            if learning_rate < 0.5:
                improvements.append("建议增强学习能力，提取更多洞察")
            else:
                improvements.append("学习能力良好，可以扩展学习范围")

            logger.debug(f"[{iteration.iteration_id}] 改进建议: {improvements}")

        except Exception as e:
            logger.error(f"优化过程失败: {e}")

        return improvements

    def _extract_pattern(
        self,
        iteration: CycleIteration
    ) -> Optional[Dict[str, Any]]:
        """提取模式

        Args:
            iteration: 迭代记录

        Returns:
            模式字典
        """
        try:
            if not iteration.context or not iteration.execution_result:
                return None

            # 提取关键模式
            pattern = {
                "context": iteration.context,
                "decision": iteration.advice.recommendation if iteration.advice else "",
                "outcome": iteration.execution_result.get("status", "unknown"),
                "confidence": iteration.advice.confidence if iteration.advice else 0,
            }

            return pattern

        except Exception as e:
            logger.error(f"提取模式失败: {e}")
            return None

    def _generate_improvement(
        self,
        iteration: CycleIteration
    ) -> Optional[str]:
        """生成改进建议

        Args:
            iteration: 迭代记录

        Returns:
            改进建议
        """
        try:
            if not iteration.execution_result:
                return None

            result = iteration.execution_result

            # 基于结果生成建议
            if result.get("status") == "completed":
                if result.get("profit", 0) > 0:
                    return "盈利交易，建议记录成功因素"
                else:
                    return "亏损交易，建议分析失败原因"
            elif result.get("status") == "failed":
                return "执行失败，建议检查系统状态和网络连接"
            else:
                return None

        except Exception as e:
            logger.error(f"生成改进建议失败: {e}")
            return None

    async def start_auto_cycle(self, executor: Callable = None) -> None:
        """启动自动循环

        Args:
            executor: 执行函数（可选）
        """
        if not self.enable_auto_cycle:
            logger.info("自动循环未启用")
            return

        logger.info(f"启动自动知识循环，间隔: {self.cycle_interval}秒")

        while True:
            try:
                # 示例：模拟交易上下文
                context = {
                    "symbol": "BTC/USDT",
                    "strategy": "cross_exchange",
                    "expected_profit": 100.0,
                    "risk_score": 0.3
                }

                # 执行循环
                await self.execute_trade_cycle(context, executor)

                # 等待下一次循环
                await asyncio.sleep(self.cycle_interval)

            except asyncio.CancelledError:
                logger.info("自动循环已停止")
                break
            except Exception as e:
                logger.error(f"自动循环错误: {e}")
                await asyncio.sleep(self.cycle_interval)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        success_rate = self.successful_cycles / self.total_cycles if self.total_cycles > 0 else 0
        avg_learning = self.total_learning / self.total_cycles if self.total_cycles > 0 else 0

        return {
            "total_cycles": self.total_cycles,
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "success_rate": success_rate,
            "total_learning": self.total_learning,
            "avg_learning_per_cycle": avg_learning,
            "history_size": len(self.cycle_history),
        }


# 全局单例
_knowledge_cycle_manager: Optional[KnowledgeCycleManager] = None


def get_knowledge_cycle_manager(
    recorder: Optional[KnowledgeRecorder] = None,
    assistant: Optional[DecisionAssistant] = None,
    config: Optional[Dict[str, Any]] = None
) -> KnowledgeCycleManager:
    """获取知识循环管理器实例

    Args:
        recorder: 知识记录器实例
        assistant: 决策辅助器实例
        config: 配置字典

    Returns:
        KnowledgeCycleManager 实例
    """
    global _knowledge_cycle_manager

    if _knowledge_cycle_manager is None:
        _knowledge_cycle_manager = KnowledgeCycleManager(recorder, assistant, config)

    return _knowledge_cycle_manager
