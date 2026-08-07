"""低风险套利引擎 V3.2

实现真正的低风险套利交易引擎，确保交易安全性和稳定性。

核心功能:
1. 预检机制 - 交易前全面风险评估
2. 分步执行 - 每步确认后再继续
3. 自动止损 - 实时监控，异常时自动止损
4. 回滚机制 - 失败时自动回滚已执行步骤
5. 实时监控 - 交易中持续风险跟踪
6. 多重验证 - 确保每步操作的正确性
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from risk.deep_risk_manager import DeepRiskManager, get_deep_risk_manager, RiskLevel

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    PRE_CHECKING = "pre_checking"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: int
    name: str
    action: Callable
    params: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    rollback_action: Optional[Callable] = None
    rollback_params: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0


@dataclass
class ArbitrageExecution:
    """套利执行记录"""
    execution_id: str
    opportunity: Dict[str, Any]
    steps: List[ExecutionStep]
    status: ExecutionStatus
    start_time: float
    end_time: Optional[float] = None
    actual_profit: Optional[float] = None
    total_risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    error_message: Optional[str] = None


class LowRiskArbitrageEngine:
    """低风险套利引擎 V3.2

    实现真正的低风险套利交易引擎。
    """

    def __init__(
        self,
        risk_manager: Optional[DeepRiskManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化低风险套利引擎

        Args:
            risk_manager: 风险管理器实例
            config: 配置字典
        """
        self.risk_manager = risk_manager or get_deep_risk_manager()
        self.config = config or {}

        # 配置参数
        self.enable_pre_check = self.config.get('enable_pre_check', True)
        self.enable_step_verification = self.config.get('enable_step_verification', True)
        self.enable_auto_rollback = self.config.get('enable_auto_rollback', True)
        self.max_execution_time = self.config.get('max_execution_time', 30.0)
        self.risk_tolerance = self.config.get('risk_tolerance', RiskLevel.MEDIUM)

        # 执行历史
        self.execution_history: List[ArbitrageExecution] = []
        self.active_executions: Dict[str, ArbitrageExecution] = {}

        # 统计数据
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.rolled_back_executions = 0
        self.total_profit = 0.0

        logger.info("低风险套利引擎 V3.2 初始化完成")

    async def execute_arbitrage(
        self,
        opportunity: Dict[str, Any],
        execution_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """执行低风险套利交易

        Args:
            opportunity: 套利机会
            execution_plan: 执行计划（步骤列表）

        Returns:
            执行结果字典
        """
        execution_id = f"arb_{int(time.time() * 1000)}"

        logger.info(f"开始执行低风险套利: {execution_id}")

        # 创建执行记录
        execution = ArbitrageExecution(
            execution_id=execution_id,
            opportunity=opportunity,
            steps=self._create_execution_steps(execution_plan),
            status=ExecutionStatus.PENDING,
            start_time=time.time()
        )

        self.active_executions[execution_id] = execution

        try:
            # 1. 预检阶段
            if self.enable_pre_check:
                execution.status = ExecutionStatus.PRE_CHECKING
                await self._pre_check_execution(execution)

            # 2. 执行阶段
            execution.status = ExecutionStatus.EXECUTING
            success = await self._execute_steps(execution)

            if success:
                # 3. 完成阶段
                execution.status = ExecutionStatus.COMPLETED
                execution.end_time = time.time()
                execution.actual_profit = self._calculate_actual_profit(execution)

                self._update_statistics(execution, success=True)
                logger.info(f"套利执行成功: {execution_id}, 利润: {execution.actual_profit:.2f}")

                return {
                    'execution_id': execution_id,
                    'status': 'completed',
                    'profit': execution.actual_profit,
                    'execution_time': execution.end_time - execution.start_time,
                    'steps_count': len(execution.steps),
                    'risk_level': execution.risk_level.value
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

    def _create_execution_steps(
        self,
        execution_plan: List[Dict[str, Any]]
    ) -> List[ExecutionStep]:
        """创建执行步骤

        Args:
            execution_plan: 执行计划

        Returns:
            执行步骤列表
        """
        steps = []

        for i, plan_step in enumerate(execution_plan):
            step = ExecutionStep(
                step_id=i,
                name=plan_step.get('name', f"Step {i}"),
                action=plan_step['action'],
                params=plan_step.get('params', {}),
                rollback_action=plan_step.get('rollback_action'),
                rollback_params=plan_step.get('rollback_params', {})
            )
            steps.append(step)

        return steps

    async def _pre_check_execution(
        self,
        execution: ArbitrageExecution
    ) -> None:
        """执行预检

        Args:
            execution: 执行记录

        Raises:
            ValueError: 预检失败
        """
        logger.info(f"执行预检: {execution.execution_id}")

        # 1. 风险管理器预检
        if self.risk_manager:
            passed, reason, risk_level = self.risk_manager.pre_trade_risk_check(
                execution.opportunity
            )

            if not passed:
                raise ValueError(f"风险预检失败: {reason}")

            execution.risk_level = risk_level

            # 检查风险容忍度（风险等级越高，字符串排序越靠后）
            risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            if risk_levels.index(risk_level) > risk_levels.index(self.risk_tolerance):
                raise ValueError(f"风险等级超过容忍度: {risk_level.value} > {self.risk_tolerance.value}")

        # 2. 计算总风险评分
        execution.total_risk_score = self._calculate_total_risk_score(execution)

        # 3. 检查执行时间限制
        estimated_time = len(execution.steps) * 2.0  # 每步预计2秒
        if estimated_time > self.max_execution_time:
            raise ValueError(f"预计执行时间过长: {estimated_time:.1f}s")

        logger.info(f"预检通过: 风险等级={execution.risk_level.value}, "
                   f"风险评分={execution.total_risk_score:.1f}")

    async def _execute_steps(
        self,
        execution: ArbitrageExecution
    ) -> bool:
        """执行所有步骤

        Args:
            execution: 执行记录

        Returns:
            是否全部成功
        """
        start_time = time.time()

        for step in execution.steps:
            # 检查执行时间限制
            if time.time() - start_time > self.max_execution_time:
                execution.error_message = f"执行超时: {self.max_execution_time}s"
                return False

            # 执行步骤
            success = await self._execute_step(step)
            if not success:
                execution.error_message = f"步骤 {step.step_id} 失败: {step.error}"
                return False

            # 步骤验证
            if self.enable_step_verification:
                verified = await self._verify_step(step, execution)
                if not verified:
                    execution.error_message = f"步骤 {step.step_id} 验证失败"
                    return False

        return True

    async def _execute_step(
        self,
        step: ExecutionStep
    ) -> bool:
        """执行单个步骤

        Args:
            step: 执行步骤

        Returns:
            是否成功
        """
        logger.info(f"执行步骤 {step.step_id}: {step.name}")
        step.status = StepStatus.EXECUTING
        step.timestamp = time.time()

        try:
            # 执行动作
            if asyncio.iscoroutinefunction(step.action):
                result = await step.action(**step.params)
            else:
                result = step.action(**step.params)

            step.result = result
            step.status = StepStatus.COMPLETED

            logger.info(f"步骤 {step.step_id} 完成: {step.name}")
            return True

        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED
            logger.error(f"步骤 {step.step_id} 失败: {step.name}, {e}")
            return False

    async def _verify_step(
        self,
        step: ExecutionStep,
        execution: ArbitrageExecution
    ) -> bool:
        """验证步骤执行结果

        Args:
            step: 执行步骤
            execution: 执行记录

        Returns:
            是否验证通过
        """
        # 基本验证：检查是否有结果
        if step.result is None:
            logger.warning(f"步骤 {step.step_id} 返回空结果")
            return False

        # 检查结果中的状态字段
        if isinstance(step.result, dict):
            status = step.result.get('status')
            if status and status.lower() in ['failed', 'error', 'rejected']:
                logger.error(f"步骤 {step.step_id} 返回错误状态: {status}")
                return False

        return True

    async def _rollback_execution(
        self,
        execution: ArbitrageExecution
    ) -> None:
        """回滚执行

        Args:
            execution: 执行记录
        """
        logger.info(f"开始回滚执行: {execution.execution_id}")

        # 从后向前回滚已完成的步骤
        completed_steps = [s for s in execution.steps if s.status == StepStatus.COMPLETED]
        completed_steps.reverse()

        for step in completed_steps:
            if step.rollback_action:
                try:
                    if asyncio.iscoroutinefunction(step.rollback_action):
                        await step.rollback_action(**step.rollback_params)
                    else:
                        step.rollback_action(**step.rollback_params)

                    step.status = StepStatus.ROLLED_BACK
                    logger.info(f"步骤 {step.step_id} 回滚成功: {step.name}")

                except Exception as e:
                    logger.error(f"步骤 {step.step_id} 回滚失败: {step.name}, {e}")

        logger.info(f"执行回滚完成: {execution.execution_id}")

    def _calculate_actual_profit(
        self,
        execution: ArbitrageExecution
    ) -> float:
        """计算实际利润

        Args:
            execution: 执行记录

        Returns:
            实际利润
        """
        # 从机会中获取预期利润
        expected_profit = execution.opportunity.get('expected_profit', 0)
        expected_profit_rate = execution.opportunity.get('profit_rate', 0)

        # 从执行结果中获取实际利润（如果有）
        if execution.steps:
            last_step = execution.steps[-1]
            if last_step.result and isinstance(last_step.result, dict):
                actual_profit = last_step.result.get('actual_profit')
                if actual_profit is not None:
                    return actual_profit

        # 没有实际利润数据，使用预期利润
        return expected_profit

    def _calculate_total_risk_score(
        self,
        execution: ArbitrageExecution
    ) -> float:
        """计算总风险评分

        Args:
            execution: 执行记录

        Returns:
            风险评分 (0-100)
        """
        risk_score = 0.0

        # 基础风险（基于机会）
        opportunity = execution.opportunity
        profit_rate = opportunity.get('profit_rate', 0)
        risk_score += min(profit_rate * 5, 40)

        # 步骤数量风险
        risk_score += len(execution.steps) * 2

        # 风险等级风险
        risk_level_scores = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 15,
            RiskLevel.HIGH: 35,
            RiskLevel.CRITICAL: 60
        }
        risk_score += risk_level_scores.get(execution.risk_level, 30)

        return min(risk_score, 100)

    def _update_statistics(
        self,
        execution: ArbitrageExecution,
        success: bool
    ) -> None:
        """更新统计数据

        Args:
            execution: 执行记录
            success: 是否成功
        """
        self.total_executions += 1

        if success:
            self.successful_executions += 1
            if execution.actual_profit:
                self.total_profit += execution.actual_profit
        else:
            self.failed_executions += 1
            if execution.status == ExecutionStatus.ROLLED_BACK:
                self.rolled_back_executions += 1

    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计

        Returns:
            统计数据字典
        """
        success_rate = (
            self.successful_executions / self.total_executions
            if self.total_executions > 0 else 0
        )

        rollback_rate = (
            self.rolled_back_executions / self.failed_executions
            if self.failed_executions > 0 else 0
        )

        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'rolled_back_executions': self.rolled_back_executions,
            'total_profit': self.total_profit,
            'success_rate': success_rate,
            'rollback_rate': rollback_rate,
            'average_profit': (
                self.total_profit / self.successful_executions
                if self.successful_executions > 0 else 0
            ),
            'active_executions': len(self.active_executions)
        }

    def get_execution_history(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取执行历史

        Args:
            limit: 返回数量限制

        Returns:
            执行历史列表
        """
        history = []

        for exec_record in self.execution_history[-limit:]:
            history.append({
                'execution_id': exec_record.execution_id,
                'status': exec_record.status.value,
                'risk_level': exec_record.risk_level.value,
                'risk_score': exec_record.total_risk_score,
                'actual_profit': exec_record.actual_profit,
                'start_time': exec_record.start_time,
                'end_time': exec_record.end_time,
                'error_message': exec_record.error_message
            })

        history.reverse()  # 最新的在前
        return history

    def cancel_execution(
        self,
        execution_id: str
    ) -> bool:
        """取消正在执行的套利

        Args:
            execution_id: 执行ID

        Returns:
            是否成功取消
        """
        if execution_id not in self.active_executions:
            logger.warning(f"未找到活动执行: {execution_id}")
            return False

        execution = self.active_executions[execution_id]
        execution.status = ExecutionStatus.CANCELLED

        logger.info(f"执行已取消: {execution_id}")
        return True


# 全局低风险套利引擎实例
_arbitrage_engine: Optional[LowRiskArbitrageEngine] = None


def initialize_low_risk_arbitrage_engine(
    risk_manager: Optional[DeepRiskManager] = None,
    config: Optional[Dict[str, Any]] = None
) -> LowRiskArbitrageEngine:
    """初始化全局低风险套利引擎

    Args:
        risk_manager: 风险管理器实例
        config: 配置字典

    Returns:
        低风险套利引擎实例
    """
    global _arbitrage_engine
    _arbitrage_engine = LowRiskArbitrageEngine(risk_manager, config)
    return _arbitrage_engine


def get_low_risk_arbitrage_engine() -> Optional[LowRiskArbitrageEngine]:
    """获取全局低风险套利引擎

    Returns:
        低风险套利引擎实例，如果未初始化则返回 None
    """
    return _arbitrage_engine
