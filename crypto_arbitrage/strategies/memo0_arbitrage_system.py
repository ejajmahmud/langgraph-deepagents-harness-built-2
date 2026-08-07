"""V52.0 Memo0深度集成的低风险套利交易系统

V52.0新增功能 - Memo0深度集成:
1. Memory-Driven Trading - 基于记忆的交易决策
2. Knowledge-Augmented Arbitrage - 知识增强套利
3. Smart Execution - 智能订单执行
4. Risk-Aware Decision - 风险感知决策
5. Adaptive Learning - 自适应学习

创建时间：2026-05-08
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 导入现有模块
from strategies.low_risk_arbitrage_engine import (
    LowRiskArbitrageEngine,
    ExecutionStatus,
    StepStatus,
    ExecutionStep,
    ArbitrageExecution,
    get_low_risk_arbitrage_engine,
    initialize_low_risk_arbitrage_engine
)
from strategies.advanced_leverage_manager import AdvancedLeverageManager
from strategies.smart_order_router import SmartOrderRouter
from trading.enhanced_risk_monitor import EnhancedRiskMonitor
from storage.mem0_storage import (
    Memo0Storage,
    get_mem0_storage,
    initialize_mem0
)

logger = logging.getLogger(__name__)


class Memo0ArbitrageSignalType(Enum):
    """Memo0增强套利信号类型"""
    TRIANGULAR = "triangular"           # 三角套利
    CROSS_EXCHANGE = "cross_exchange"    # 跨交易所套利
    FUNDING_RATE = "funding_rate"        # 资金费率套利
    STATISTICAL = "statistical"          # 统计套利
    GRID = "grid"                    # 网格交易
    PERPETUAL = "perpetual"           # 永续期货


class DecisionConfidence(Enum):
    """决策置信度"""
    VERY_HIGH = "very_high"          # 非常高 (>90%)
    HIGH = "high"                    # 高 (70-90%)
    MEDIUM = "medium"                # 中 (50-70%)
    LOW = "low"                      # 低 (30-50%)
    VERY_LOW = "very_low"            # 非常低 (<30%)


class ExecutionMode(Enum):
    """执行模式"""
    PAPER = "paper"                  # 模拟交易
    LIVE = "live"                    # 实盘交易
    BACKTEST = "backtest"            # 回测模式


@dataclass
class Memo0ArbitrageSignal:
    """Memo0增强套利信号

    Attributes:
        signal_type: 信号类型
        confidence: 置信度
        strength: 信号强度 (0-1)
        reasoning: 推理过程
        evidence: 证据列表
        historical_matches: 历史匹配数
        success_rate: 历史成功率
        risk_score: 风险评分
    """
    signal_type: Memo0ArbitrageSignalType
    confidence: DecisionConfidence
    strength: float = 0.5
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    historical_matches: int = 0
    success_rate: float = 0.5
    risk_score: float = 0.5
    timestamp: float = field(default_factory=time.time)


@dataclass
class Memo0ArbitrageDecision:
    """Memo0套利决策

    Attributes:
        decision_id: 决策ID
        opportunity_id: 机会ID
        symbol: 交易对
        side: 方向 (long/short)
        entry_price: 入场价
        position_size: 仓位
        expected_profit: 预期利润
        risk_adjusted_profit: 风险调整后利润
        stop_loss: 止损价
        take_profit: 止盈价
        ttl: 有效时间(秒)
        risk_score: 风险评分
        signal: Memo0增强信号
        execution_plan: 执行计划
    """
    decision_id: str
    opportunity_id: str
    symbol: str
    side: str
    entry_price: float
    position_size: float
    expected_profit: float
    risk_adjusted_profit: float
    stop_loss: float
    take_profit: float
    ttl: int = 30
    risk_score: float = 0.0
    signal: Optional[Memo0ArbitrageSignal] = None
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ArbitrageTradeResult:
    """套利交易结果"""
    decision_id: str
    status: str
    executed: bool
    profit: Optional[float] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    steps_completed: int = 0
    total_steps: int = 0
    rolled_back: bool = False
    risk_metrics: Dict[str, float] = field(default_factory=dict)


class Memo0IntegratedArbitrageSystem:
    """Memo0深度集成的套利交易系统

    核心功能：
    - 基于Memo0记忆的交易决策
    - 自适应学习改进
    - 风险感知决策
    - 智能订单执行
    """

    def __init__(
        self,
        mem0_storage: Optional[Memo0Storage] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化Memo0套利系统

        Args:
            mem0_storage: Memo0存储实例
            config: 配置字典
        """
        # 初始化Memo0存储
        self.mem0 = mem0_storage or get_mem0_storage()
        if self.mem0 is None:
            self.mem0 = initialize_mem0()

        self.config = config or {}

        # 执行模式
        self.execution_mode = ExecutionMode(
            self.config.get('execution_mode', 'paper')
        )

        # 核心组件 - 使用try/except优雅处理缺失
        self.arbitrage_engine = None
        self.leverage_manager = None
        self.order_router = None
        self.risk_monitor = None

        try:
            self.arbitrage_engine = get_low_risk_arbitrage_engine()
            if self.arbitrage_engine is None:
                self.arbitrage_engine = initialize_low_risk_arbitrage_engine(
                    config=self.config.get('arbitrage_config')
                )
        except Exception as e:
            logger.warning(f"套利引擎初始化跳过: {e}")

        try:
            from strategies.advanced_leverage_manager import get_advanced_leverage_manager
            self.leverage_manager = get_advanced_leverage_manager()
        except Exception:
            pass

        try:
            from strategies.smart_order_router import get_smart_order_router
            self.order_router = get_smart_order_router()
        except Exception:
            pass

        try:
            from trading.enhanced_risk_monitor import get_enhanced_risk_monitor
            self.risk_monitor = get_enhanced_risk_monitor()
        except Exception:
            pass

        # 交易历史
        self.trade_history: List[ArbitrageTradeResult] = []
        self.active_trades: Dict[str, Memo0ArbitrageDecision] = {}

        # 统计
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0

        # 信号阈值
        self.min_confidence = DecisionConfidence(
            self.config.get('min_confidence', 'medium')
        )
        self.min_success_rate = self.config.get('min_success_rate', 0.4)
        self.max_risk_score = self.config.get('max_risk_score', 0.6)

        logger.info("Memo0套利系统 V52.0 初始化完成")

    async def analyze_opportunity(
        self,
        opportunity: Dict[str, Any]
    ) -> Memo0ArbitrageSignal:
        """分析套利机会

        Args:
            opportunity: 套利机会数据

        Returns:
            Memo0增强信号
        """
        signal_type = self._determine_signal_type(opportunity)

        # 构建查询上下文
        query_context = self._build_query_context(opportunity)

        # 从Memo0检索相关经验
        historical_matches = await self._retrieve_historical_experience(
            query_context
        )

        # 计算置信度和成功率
        confidence, success_rate = self._calculate_confidence(
            opportunity,
            historical_matches
        )

        # 计算风险评分
        risk_score = await self._calculate_risk_score(
            opportunity,
            success_rate
        )

        # 生成推理过程
        reasoning = self._generate_reasoning(
            opportunity,
            historical_matches,
            success_rate
        )

        signal = Memo0ArbitrageSignal(
            signal_type=signal_type,
            confidence=confidence,
            strength=min(success_rate, 1.0),
            reasoning=reasoning,
            historical_matches=len(historical_matches),
            success_rate=success_rate,
            risk_score=risk_score
        )

        return signal

    async def decide(
        self,
        opportunity: Dict[str, Any]
    ) -> Optional[Memo0ArbitrageDecision]:
        """做出交易决策

        Args:
            opportunity: 套利机会

        Returns:
            决策结果，如果不符合条件则返回None
        """
        # 分析信号
        signal = await self.analyze_opportunity(opportunity)

        # 检查是否满足交易条件
        if not self._meets_trading_criteria(signal):
            logger.info(f"机会不符合交易条件: confidence={signal.confidence}, "
                         f"success_rate={signal.success_rate}, "
                         f"risk_score={signal.risk_score}")
            return None

        # 计算仓位和杠杆
        position_size = await self._calculate_position_size(
            opportunity,
            signal
        )

        # 计算风险调整后利润
        risk_adjusted_profit = self._calculate_risk_adjusted_profit(
            opportunity,
            signal
        )

        # 生成执行计划
        execution_plan = self._generate_execution_plan(
            opportunity,
            signal
        )

        decision = Memo0ArbitrageDecision(
            decision_id=f"dec_{int(time.time() * 1000)}",
            opportunity_id=opportunity.get('id', 'unknown'),
            symbol=opportunity.get('symbol', ''),
            side=opportunity.get('side', 'long'),
            entry_price=opportunity.get('entry_price', 0),
            position_size=position_size,
            expected_profit=opportunity.get('expected_profit', 0),
            risk_adjusted_profit=risk_adjusted_profit,
            stop_loss=opportunity.get('stop_loss', 0),
            take_profit=opportunity.get('take_profit', 0),
            ttl=opportunity.get('ttl', 30),
            risk_score=signal.risk_score,
            signal=signal,
            execution_plan=execution_plan
        )

        # 保存到Memo0
        await self._store_decision(decision)

        return decision

    async def execute(
        self,
        decision: Memo0ArbitrageDecision
    ) -> ArbitrageTradeResult:
        """执行交易决策

        Args:
            decision: 交易决策

        Returns:
            交易结果
        """
        start_time = time.time()
        decision_id = decision.decision_id

        logger.info(f"开始执行交易: {decision_id}")

        self.active_trades[decision_id] = decision
        self.total_trades += 1

        try:
            # 检查执行模式
            if self.execution_mode == ExecutionMode.PAPER:
                # 模拟交易
                result = await self._execute_paper_trade(decision)
            elif self.execution_mode == ExecutionMode.LIVE:
                # 实盘交易
                result = await self._execute_live_trade(decision)
            else:
                # 回测模式
                result = await self._execute_backtest(decision)

            # 更新统计
            if result.executed:
                self.successful_trades += 1
            else:
                self.failed_trades += 1

            # 保存结果到历史
            self.trade_history.append(result)

            # 保存到Memo0
            await self._store_trade_result(result)

            return result

        finally:
            if decision_id in self.active_trades:
                del self.active_trades[decision_id]

    async def _retrieve_historical_experience(
        self,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """从Memo0检索历史经验

        Args:
            context: 查询上下文

        Returns:
            历史匹配列表
        """
        if self.mem0 is None:
            return []

        try:
            # 构建查询
            query = self._build_search_query(context)

            # 搜索记忆
            results = await self.mem0.search(
                query=query,
                limit=5
            )

            return results if results else []

        except Exception as e:
            logger.warning(f"检索历史经验失败: {e}")
            return []

    async def _store_decision(
        self,
        decision: Memo0ArbitrageDecision
    ) -> None:
        """保存决策到Memo0

        Args:
            decision: 交易决策
        """
        if self.mem0 is None:
            return

        try:
            memory = {
                'type': 'arbitrage_decision',
                'decision_id': decision.decision_id,
                'symbol': decision.symbol,
                'side': decision.side,
                'confidence': decision.signal.confidence.value if decision.signal else 'unknown',
                'success_rate': decision.signal.success_rate if decision.signal else 0,
                'risk_score': decision.risk_score,
                'expected_profit': decision.expected_profit,
                'timestamp': time.time()
            }

            await self.mem0.add(
                memory=json.dumps(memory),
                metadata={'category': 'arbitrage_decision'}
            )

        except Exception as e:
            logger.warning(f"保存决策失败: {e}")

    async def _store_trade_result(
        self,
        result: ArbitrageTradeResult
    ) -> None:
        """保存交易结果到Memo0

        Args:
            result: 交易结果
        """
        if self.mem0 is None:
            return

        try:
            memory = {
                'type': 'trade_result',
                'decision_id': result.decision_id,
                'status': result.status,
                'executed': result.executed,
                'profit': result.profit,
                'execution_time': result.execution_time,
                'timestamp': time.time()
            }

            await self.mem0.add(
                memory=json.dumps(memory),
                metadata={'category': 'trade_result'}
            )

        except Exception as e:
            logger.warning(f"保存交易结果失败: {e}")

    async def _execute_paper_trade(
        self,
        decision: Memo0ArbitrageDecision
    ) -> ArbitrageTradeResult:
        """执行模拟交易

        Args:
            decision: 交易决策

        Returns:
            交易结果
        """
        start_time = time.time()

        # 模拟交易执行
        await asyncio.sleep(0.1)

        execution_time = time.time() - start_time

        return ArbitrageTradeResult(
            decision_id=decision.decision_id,
            status="completed",
            executed=True,
            profit=decision.expected_profit,
            execution_time=execution_time,
            steps_completed=len(decision.execution_plan),
            total_steps=len(decision.execution_plan),
            risk_metrics={
                'risk_score': decision.risk_score,
                'position_size': decision.position_size
            }
        )

    async def _execute_live_trade(
        self,
        decision: Memo0ArbitrageDecision
    ) -> ArbitrageTradeResult:
        """执行实盘交易

        Args:
            decision: 交易决策

        Returns:
            交易结果
        """
        if self.execution_mode != ExecutionMode.LIVE:
            return await self._execute_paper_trade(decision)

        start_time = time.time()

        try:
            # 使用已有的套利引擎执行
            result = await self.arbitrage_engine.execute_arbitrage(
                opportunity={
                    'symbol': decision.symbol,
                    'side': decision.side,
                    'entry_price': decision.entry_price,
                    'position_size': decision.position_size,
                    'expected_profit': decision.expected_profit,
                    'risk_score': decision.risk_score
                },
                execution_plan=decision.execution_plan
            )

            execution_time = time.time() - start_time

            return ArbitrageTradeResult(
                decision_id=decision.decision_id,
                status=result.get('status', 'failed'),
                executed=result.get('status') == 'completed',
                profit=result.get('profit'),
                error=result.get('error'),
                execution_time=execution_time,
                steps_completed=result.get('steps_completed', 0),
                total_steps=result.get('total_steps', 0),
                rolled_back=result.get('rolled_back', False)
            )

        except Exception as e:
            logger.error(f"实盘交易执行失败: {e}")

            return ArbitrageTradeResult(
                decision_id=decision.decision_id,
                status="failed",
                executed=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _execute_backtest(
        self,
        decision: Memo0ArbitrageDecision
    ) -> ArbitrageTradeResult:
        """执行回测

        Args:
            decision: 交易决策

        Returns:
            交易结果
        """
        return await self._execute_paper_trade(decision)

    def _determine_signal_type(
        self,
        opportunity: Dict[str, Any]
    ) -> Memo0ArbitrageSignalType:
        """确定信号类型

        Args:
            opportunity: 套利机会

        Returns:
            信号类型
        """
        strategy = opportunity.get('strategy', '').lower()

        if 'triangular' in strategy:
            return Memo0ArbitrageSignalType.TRIANGULAR
        elif 'cross' in strategy or 'exchange' in strategy:
            return Memo0ArbitrageSignalType.CROSS_EXCHANGE
        elif 'funding' in strategy:
            return Memo0ArbitrageSignalType.FUNDING_RATE
        elif 'statistical' in strategy:
            return Memo0ArbitrageSignalType.STATISTICAL
        elif 'grid' in strategy:
            return Memo0ArbitrageSignalType.GRID
        elif 'perpetual' in strategy:
            return Memo0ArbitrageSignalType.PERPETUAL

        return Memo0ArbitrageSignalType.CROSS_EXCHANGE

    def _build_query_context(
        self,
        opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建查询上下文

        Args:
            opportunity: 套利机会

        Returns:
            上下文字典
        """
        return {
            'symbol': opportunity.get('symbol', ''),
            'strategy': opportunity.get('strategy', ''),
            'side': opportunity.get('side', ''),
            'market': opportunity.get('market', ''),
            'timeframe': opportunity.get('timeframe', '')
        }

    def _build_search_query(
        self,
        context: Dict[str, Any]
    ) -> str:
        """构建搜索查询

        Args:
            context: 上下文

        Returns:
            查询字符串
        """
        parts = []
        for key, value in context.items():
            if value:
                parts.append(f"{key}={value}")

        return ", ".join(parts) if parts else "arbitrage trading"

    def _calculate_confidence(
        self,
        opportunity: Dict[str, Any],
        historical_matches: List[Dict[str, Any]]
    ) -> Tuple[DecisionConfidence, float]:
        """计算置信度

        Args:
            opportunity: 套利机会
            historical_matches: 历史匹配

        Returns:
            (置信度, 成功率)
        """
        if not historical_matches:
            return DecisionConfidence.MEDIUM, 0.5

        # 计算历史成功率
        success_count = 0
        total_count = len(historical_matches)

        for match in historical_matches:
            match_data = json.loads(match.get('memory', '{}'))
            if match_data.get('status') == 'completed':
                success_count += 1

        success_rate = success_count / total_count if total_count > 0 else 0.5

        # 确定置信度
        if success_rate >= 0.9:
            confidence = DecisionConfidence.VERY_HIGH
        elif success_rate >= 0.7:
            confidence = DecisionConfidence.HIGH
        elif success_rate >= 0.5:
            confidence = DecisionConfidence.MEDIUM
        elif success_rate >= 0.3:
            confidence = DecisionConfidence.LOW
        else:
            confidence = DecisionConfidence.VERY_LOW

        return confidence, success_rate

    async def _calculate_risk_score(
        self,
        opportunity: Dict[str, Any],
        success_rate: float
    ) -> float:
        """计算风险评分

        Args:
            opportunity: 套利机会
            success_rate: 成功率

        Returns:
            风险评分 (0-1)
        """
        # 基础风险评分
        base_risk = 1.0 - success_rate

        # 利润风险调整
        profit_rate = opportunity.get('profit_rate', 0)
        profit_risk = max(0, 0.3 - profit_rate * 0.1)

        # 仓位风险
        position_size = opportunity.get('position_size', 0)
        size_risk = min(position_size / 10000, 0.2)

        # 综合风险
        risk_score = base_risk * 0.5 + profit_risk + size_risk

        return min(risk_score, 1.0)

    def _generate_reasoning(
        self,
        opportunity: Dict[str, Any],
        historical_matches: List[Dict[str, Any]],
        success_rate: float
    ) -> str:
        """生成推理过程

        Args:
            opportunity: 套利机会
            historical_matches: 历史匹配
            success_rate: 成功率

        Returns:
            推理过程描述
        """
        symbol = opportunity.get('symbol', 'unknown')
        strategy = opportunity.get('strategy', 'unknown')
        matches = len(historical_matches)

        reasoning = f"基于{symbol}的{strategy}策略"

        if matches > 0:
            reasoning += f"，找到{matches}个历史匹配"
            reasoning += f"，历史成功率为{success_rate:.1%}"

            if success_rate >= 0.7:
                reasoning += "，信号强"
            elif success_rate >= 0.5:
                reasoning += "，信号中等"
            else:
                reasoning += "，信号弱"
        else:
            reasoning += "，无历史数据，使用默认置信度"

        return reasoning

    def _meets_trading_criteria(
        self,
        signal: Memo0ArbitrageSignal
    ) -> bool:
        """检查是否满足交易条件

        Args:
            signal: 信号

        Returns:
            是否满足条件
        """
        # 检查置信度
        confidence_levels = [
            DecisionConfidence.VERY_HIGH,
            DecisionConfidence.HIGH,
            DecisionConfidence.MEDIUM,
            DecisionConfidence.LOW,
            DecisionConfidence.VERY_LOW
        ]

        min_index = confidence_levels.index(self.min_confidence)
        signal_index = confidence_levels.index(signal.confidence)

        if signal_index > min_index:
            return False

        # 检查成功率
        if signal.success_rate < self.min_success_rate:
            return False

        # 检查风险评分
        if signal.risk_score > self.max_risk_score:
            return False

        return True

    async def _calculate_position_size(
        self,
        opportunity: Dict[str, Any],
        signal: Memo0ArbitrageSignal
    ) -> float:
        """计算仓位大小

        Args:
            opportunity: 套利机会
            signal: 信号

        Returns:
            仓位大小
        """
        # 基础仓位
        base_size = opportunity.get('position_size', 1000)

        # 使用杠杆管理器调整
        if self.leverage_manager:
            leverage_config = {
                'risk_score': signal.risk_score,
                'success_rate': signal.success_rate
            }
            leverage_result = await self.leverage_manager.calculate_leverage(
                base_size,
                leverage_config
            )
            return leverage_result.position_size

        return base_size

    def _calculate_risk_adjusted_profit(
        self,
        opportunity: Dict[str, Any],
        signal: Memo0ArbitrageSignal
    ) -> float:
        """计算风险调整后利润

        Args:
            opportunity: 套利机会
            signal: 信号

        Returns:
            风险调整后利润
        """
        expected_profit = opportunity.get('expected_profit', 0)

        # 风险调整
        risk_multiplier = 1.0 - signal.risk_score * 0.5

        # 置信度调整
        confidence_multiplier = signal.strength

        return expected_profit * risk_multiplier * confidence_multiplier

    def _generate_execution_plan(
        self,
        opportunity: Dict[str, Any],
        signal: Memo0ArbitrageSignal
    ) -> List[Dict[str, Any]]:
        """生成执行计划

        Args:
            opportunity: 套利机会
            signal: 信号

        Returns:
            执行计划列表
        """
        return [
            {
                'name': 'pre_check',
                'action': self._pre_check_action,
                'params': {'opportunity': opportunity},
                'rollback_action': None,
                'rollback_params': {}
            },
            {
                'name': 'execute_order',
                'action': self._execute_order_action,
                'params': {'opportunity': opportunity},
                'rollback_action': self._cancel_order_action,
                'rollback_params': {}
            },
            {
                'name': 'verify_execution',
                'action': self._verify_action,
                'params': {},
                'rollback_action': None,
                'rollback_params': {}
            }
        ]

    async def _pre_check_action(
        self,
        opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预检动作"""
        return {'status': 'ok', 'step': 'pre_check'}

    async def _execute_order_action(
        self,
        opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行订单动作"""
        return {
            'status': 'ok',
            'step': 'execute_order',
            'order_id': f"order_{int(time.time() * 1000)}"
        }

    async def _cancel_order_action(
        self,
        **kwargs
    ) -> Dict[str, Any]:
        """取消订单动作"""
        return {'status': 'ok', 'step': 'cancel_order'}

    async def _verify_action(
        self,
        **kwargs
    ) -> Dict[str, Any]:
        """验证动作"""
        return {'status': 'ok', 'step': 'verify'}

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        success_rate = (
            self.successful_trades / self.total_trades
            if self.total_trades > 0 else 0
        )

        return {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'success_rate': success_rate,
            'active_trades': len(self.active_trades),
            'execution_mode': self.execution_mode.value
        }

    def get_active_trades(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取活跃交易

        Args:
            limit: 限制数量

        Returns:
            交易列表
        """
        trades = []

        for trade in list(self.active_trades.values())[-limit:]:
            trades.append({
                'decision_id': trade.decision_id,
                'symbol': trade.symbol,
                'side': trade.side,
                'position_size': trade.position_size,
                'expected_profit': trade.expected_profit,
                'risk_score': trade.risk_score
            })

        return trades

    def get_trade_history(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取交易历史

        Args:
            limit: 限制数量

        Returns:
            历史列表
        """
        history = []

        for result in self.trade_history[-limit:]:
            history.append({
                'decision_id': result.decision_id,
                'status': result.status,
                'executed': result.executed,
                'profit': result.profit,
                'execution_time': result.execution_time
            })

        history.reverse()
        return history


# 全局单例
_arbitrage_system: Optional[Memo0IntegratedArbitrageSystem] = None


def initialize_memo0_arbitrage_system(
    config: Optional[Dict[str, Any]] = None
) -> Memo0IntegratedArbitrageSystem:
    """初始化Memo0套利系统

    Args:
        config: 配置字典

    Returns:
        Memo0套利系统实例
    """
    global _arbitrage_system

    _arbitrage_system = Memo0IntegratedArbitrageSystem(
        config=config
    )

    return _arbitrage_system


def get_memo0_arbitrage_system() -> Optional[Memo0IntegratedArbitrageSystem]:
    """获取Memo0套利系统

    Returns:
        Memo0套利系统实例
    """
    return _arbitrage_system