"""V54.0 统一套利系统 - 跨链套利与ML预测集成

V54.0 统一系统，整合：
1. Memo0深度集成 (V52/V53)
2. 跨链套利引擎 (V54新增)
3. ML预测集成 (V54新增)
4. 信号融合 (V54新增)

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

from strategies.cross_chain_arbitrage import (
    CrossChainArbitrageEngine,
    CrossChainArbitrageType,
    CrossChainOpportunity,
    Blockchain,
    MLPredictor,
    MLPredictionResult,
    initialize_cross_chain_arbitrage_engine,
    get_cross_chain_arbitrage_engine,
    initialize_ml_predictor,
    get_ml_predictor
)
from strategies.memo0_arbitrage_system import (
    Memo0IntegratedArbitrageSystem,
    Memo0ArbitrageSignal,
    Memo0ArbitrageDecision,
    get_memo0_arbitrage_system
)
from storage.mem0_storage import (
    Memo0Storage,
    get_mem0_storage,
    initialize_mem0
)

logger = logging.getLogger(__name__)


class V54ExecutionMode(Enum):
    """V54执行模式"""
    CROSS_CHAIN = "cross_chain"       # 跨链模式
    TRADITIONAL = "traditional"     # 传统模式(跨交易所)
    FUSION = "fusion"             # 融合模式(两者结合)
    BACKTEST = "backtest"         # 回测模式


@dataclass
class V54ArbitrageSignal:
    """V54套利信号

    特性:
    - 跨链支持
    - ML预测增强
    - 多策略融合
    """
    signal_id: str
    opportunity_type: str
    token: str
    source: str
    target: str
    spread_pct: float
    expected_profit: float
    confidence: float
    risk_score: float
    ml_prediction: float
    cross_chain_data: Optional[Dict[str, Any]] = None
    traditional_data: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class V54ArbitrageDecision:
    """V54套利决策"""
    decision_id: str
    signal: V54ArbitrageSignal
    position_size: float
    entry_price: float
    exit_price: float
    stop_loss: float
    expected_profit: float
    risk_adjusted_profit: float
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)
    execution_mode: V54ExecutionMode = V54ExecutionMode.CROSS_CHAIN
    ttl: int = 60


@dataclass
class V54TradeResult:
    """V54交易结果"""
    decision_id: str
    status: str
    executed: bool
    profit: Optional[float] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    cross_chain_fees: float = 0.0
    ml_metrics: Dict[str, float] = field(default_factory=dict)


class UnifiedArbitrageSystemV54:
    """V54统一套利系统

    整合功能：
    - 跨链套利
    - ML预测
    - Memo0集成
    - 信号融合
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化V54系统

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 执行模式
        self.execution_mode = V54ExecutionMode(
            self.config.get('execution_mode', 'fusion')
        )

        # 核心组件
        self.cross_chain_engine: Optional[CrossChainArbitrageEngine] = None
        self.ml_predictor: Optional[MLPredictor] = None
        self.memo0_system: Optional[Memo0IntegratedArbitrageSystem] = None
        self.mem0_storage: Optional[Memo0Storage] = None

        # 初始化组件
        self._initialize_components()

        # 交易历史
        self.trade_history: List[V54TradeResult] = []
        self.active_decisions: Dict[str, V54ArbitrageDecision] = {}

        # 统计
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0

        logger.info("V54统一套利系统初始化完成")

    def _initialize_components(self) -> None:
        """初始化组件"""
        # Memo0存储
        try:
            self.mem0_storage = get_mem0_storage()
            if self.mem0_storage is None:
                self.mem0_storage = initialize_mem0()
        except Exception as e:
            logger.warning(f"Memo0存储初始化跳过: {e}")

        # Memo0套利系统
        try:
            self.memo0_system = get_memo0_arbitrage_system()
        except Exception:
            pass

        # 跨链套利引擎
        try:
            cross_chain_config = self.config.get('cross_chain_config', {})
            self.cross_chain_engine = initialize_cross_chain_arbitrage_engine(cross_chain_config)
        except Exception as e:
            logger.warning(f"跨链引擎初始化跳过: {e}")

        # ML预测器
        try:
            ml_config = self.config.get('ml_config', {})
            self.ml_predictor = initialize_ml_predictor(ml_config)

            # 绑定ML预测器到跨链引擎
            if self.cross_chain_engine and self.ml_predictor:
                self.cross_chain_engine.set_ml_predictor(self.ml_predictor)
        except Exception as e:
            logger.warning(f"ML预测器初始化跳过: {e}")

    async def scan_opportunities(self) -> List[V54ArbitrageSignal]:
        """扫描套利机会

        Returns:
            信号列表
        """
        signals = []

        # 跨链机会
        if self.cross_chain_engine:
            try:
                opportunities = self.cross_chain_engine.detect_opportunities()
                for opp in opportunities:
                    signal = self._convert_cross_chain_opportunity(opp)
                    signals.append(signal)
            except Exception as e:
                logger.warning(f"跨链机会扫描失败: {e}")

        # 传统机会 (通过Memo0系统)
        if self.memo0_system:
            try:
                # 预留接口
                pass
            except Exception as e:
                logger.warning(f"传统机会扫描失败: {e}")

        return signals

    def _convert_cross_chain_opportunity(
        self,
        opportunity: CrossChainOpportunity
    ) -> V54ArbitrageSignal:
        """转换跨链机会为信号

        Args:
            opportunity: 跨链机会

        Returns:
            V54信号
        """
        return V54ArbitrageSignal(
            signal_id=opportunity.opportunity_id,
            opportunity_type='cross_chain',
            token=opportunity.token,
            source=opportunity.source_chain.value,
            target=opportunity.target_chain.value,
            spread_pct=opportunity.spread_pct,
            expected_profit=opportunity.expected_profit,
            confidence=opportunity.confidence,
            risk_score=opportunity.risk_score,
            ml_prediction=opportunity.ml_prediction,
            cross_chain_data={
                'source_price': opportunity.source_price,
                'target_price': opportunity.target_price,
                'volume': opportunity.volume_available,
                'bridge_time': opportunity.bridge_time
            }
        )

    async def analyze_signal(
        self,
        signal: V54ArbitrageSignal
    ) -> Dict[str, Any]:
        """分析信号

        Args:
            signal: 信号

        Returns:
            分析结果
        """
        # ML增���分析
        ml_analysis = {}

        if self.ml_predictor and signal.token:
            try:
                # 尝试解析区块链
                source_chain = Blockchain(signal.source) if signal.source else None
                if source_chain:
                    price_result = self.ml_predictor.predict_price(
                        signal.token,
                        source_chain
                    )
                    ml_analysis['price_prediction'] = price_result.prediction
                    ml_analysis['price_confidence'] = price_result.confidence
            except Exception:
                pass

        return {
            'signal': signal,
            'ml_analysis': ml_analysis,
            'execution_recommendation': self._get_execution_recommendation(signal)
        }

    def _get_execution_recommendation(self, signal: V54ArbitrageSignal) -> str:
        """获取执行建议

        Args:
            signal: 信号

        Returns:
            建议
        """
        # 基于置信度和风险的决策
        if signal.confidence >= 0.8 and signal.risk_score <= 0.3:
            return 'execute'
        elif signal.confidence >= 0.6 and signal.risk_score <= 0.5:
            return 'consider'
        elif signal.confidence >= 0.4:
            return 'watch'
        else:
            return 'skip'

    async def decide(
        self,
        signal: V54ArbitrageSignal
    ) -> Optional[V54ArbitrageDecision]:
        """做出决策

        Args:
            signal: 信号

        Returns:
            决策或None
        """
        # 分析信号
        analysis = await self.analyze_signal(signal)

        # 检查建议
        recommendation = analysis.get('execution_recommendation', 'skip')
        if recommendation == 'skip':
            return None

        # 计算仓位
        position_size = self._calculate_position_size(signal)

        # 计算价格
        entry_price = signal.cross_chain_data.get('source_price', 0) if signal.cross_chain_data else 0
        exit_price = signal.cross_chain_data.get('target_price', 0) if signal.cross_chain_data else 0
        stop_loss = entry_price * (1 - signal.risk_score * 0.1)

        # 计算预期利润
        expected_profit = signal.expected_profit * 0.8  # 预留费用

        decision = V54ArbitrageDecision(
            decision_id=f"v54_{int(time.time() * 1000)}",
            signal=signal,
            position_size=position_size,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_loss=stop_loss,
            expected_profit=expected_profit,
            risk_adjusted_profit=expected_profit * (1 - signal.risk_score),
            execution_mode=self.execution_mode
        )

        # 保存到活跃决策
        self.active_decisions[decision.decision_id] = decision

        return decision

    def _calculate_position_size(self, signal: V54ArbitrageSignal) -> float:
        """计算仓位

        Args:
            signal: 信号

        Returns:
            仓位
        """
        # 基础仓位
        base_size = 1000.0

        # 根据置信度调整
        confidence_multiplier = signal.confidence

        # 根据风险调整
        risk_multiplier = 1.0 - signal.risk_score * 0.5

        # 最终仓位
        size = base_size * confidence_multiplier * risk_multiplier

        return max(size, 100)  # 最小100

    async def execute(
        self,
        decision: V54ArbitrageDecision
    ) -> V54TradeResult:
        """执行决策

        Args:
            decision: 决策

        Returns:
            结果
        """
        start_time = time.time()
        decision_id = decision.decision_id

        logger.info(f"V54执行交易: {decision_id}")

        try:
            # 模拟执行
            await asyncio.sleep(0.1)

            execution_time = time.time() - start_time

            result = V54TradeResult(
                decision_id=decision_id,
                status="completed",
                executed=True,
                profit=decision.expected_profit,
                execution_time=execution_time,
                cross_chain_fees=decision.expected_profit * 0.2,
                ml_metrics={
                    'confidence': decision.signal.confidence,
                    'ml_prediction': decision.signal.ml_prediction
                }
            )

            # 更新统计
            if result.executed:
                self.successful_trades += 1
            else:
                self.failed_trades += 1

            self.total_trades += 1
            self.trade_history.append(result)

            # 保存到Memo0
            await self._store_trade_result(result)

            return result

        except Exception as e:
            logger.error(f"V54执行失败: {e}")

            return V54TradeResult(
                decision_id=decision_id,
                status="failed",
                executed=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

        finally:
            if decision_id in self.active_decisions:
                del self.active_decisions[decision_id]

    async def _store_trade_result(self, result: V54TradeResult) -> None:
        """保存交易结果到Memo0

        Args:
            result: 结果
        """
        if self.mem0_storage is None:
            return

        try:
            memory = {
                'type': 'v54_trade_result',
                'decision_id': result.decision_id,
                'status': result.status,
                'executed': result.executed,
                'profit': result.profit,
                'timestamp': time.time()
            }

            await self.mem0_storage.add(
                memory=json.dumps(memory),
                metadata={'category': 'v54_trade'}
            )
        except Exception as e:
            logger.warning(f"保存交易结果失败: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计

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
            'execution_mode': self.execution_mode.value,
            'cross_chain_engine': self.cross_chain_engine is not None,
            'ml_predictor': self.ml_predictor is not None
        }


# 全局单例
_v54_system: Optional[UnifiedArbitrageSystemV54] = None


def initialize_v54_system(
    config: Optional[Dict[str, Any]] = None
) -> UnifiedArbitrageSystemV54:
    """初始化V54系统

    Args:
        config: 配置字典

    Returns:
        V54系统实例
    """
    global _v54_system

    _v54_system = UnifiedArbitrageSystemV54(config)
    return _v54_system


def get_v54_system() -> Optional[UnifiedArbitrageSystemV54]:
    """获取V54系统

    Returns:
        V54系统实例
    """
    return _v54_system