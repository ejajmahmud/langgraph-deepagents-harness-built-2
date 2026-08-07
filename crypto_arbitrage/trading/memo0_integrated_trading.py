"""V32.0 Memo0深度集成智能交易系统

V32.0新增功能 - 深度memo0集成:
1. Memory-Driven Trading - 记忆驱动的交易决策
2. Knowledge-Augmented Signals - 知识增强信号
3. Adaptive Learning - 自适应学习
4. Smart Order Execution - 智能订单执行
5. Risk-Aware Arbitrage - 风险感知套利

创建时间：2026-05-07 19:40
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class TradingSignalType(Enum):
    """交易信号类型"""
    ARBITRAGE = "arbitrage"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    FUNDING = "funding"


class DecisionConfidence(Enum):
    """决策置信度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class KnowledgeAugmentedSignal:
    """知识增强信号

    Attributes:
        signal_type: 信号类型
        confidence: 置信度
        reasoning: 推理过程
        evidence: 证据列表
        historical_matches: 历史匹配数
        success_rate: 历史成功率
        risk_score: 风险评分
    """
    signal_type: TradingSignalType
    confidence: DecisionConfidence
    strength: float  # 0-1
    reasoning: str
    evidence: List[str] = field(default_factory=list)
    historical_matches: int = 0
    success_rate: float = 0.5
    risk_score: float = 0.5
    timestamp: float = field(default_factory=time.time)


@dataclass
class ArbitrageDecision:
    """套利决策

    Attributes:
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
        signal: 知识增强信号
    """
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
    signal: Optional[KnowledgeAugmentedSignal] = None


class Memo0IntegratedTrading:
    """Memo0深度集成交易系统

    核心功能：
    - 基于历史知识的信号增强
    - 自适应学习改进
    - 风险感知决策
    - 智能订单执行
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化V32交易系统

        Args:
            config: 配置字典
                - min_confidence: 最低置信度
                - min_success_rate: 最低历史成功率
                - lookback_matches: 回看历史匹配数
                - enable_adaptive: 启用自适应学习
        """
        self.config = config
        self.min_confidence = config.get('min_confidence', DecisionConfidence.MEDIUM)
        self.min_success_rate = config.get('min_success_rate', 0.5)
        self.lookback_matches = config.get('lookback_matches', 10)
        self.enable_adaptive = config.get('enable_adaptive', True)

        # 信号历史缓存
        self._signal_history: List[KnowledgeAugmentedSignal] = []
        self._decision_history: List[ArbitrageDecision] = []

        # 学习统计
        self._total_signals = 0
        self._successful_signals = 0

        # memo0集成（延迟初始化）
        self._mem0 = None
        self._initialized = False

        logger.info("[OK] Memo0集成交易系统 V32.0 初始化完成")

    async def initialize(self) -> bool:
        """初始化memo0连接"""
        try:
            from storage.mem0_storage import initialize_mem0
            self._mem0 = await initialize_mem0()
            self._initialized = True
            logger.info("[OK] Memo0连接已建立")
            return True
        except Exception as e:
            logger.warning(f"Memo0初始化失败，使用本地缓存: {e}")
            self._initialized = False
            return False

    async def enhance_signal(
        self,
        base_signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> KnowledgeAugmentedSignal:
        """增强信号 - 基于memo0知识库

        Args:
            base_signal: 基础信号
            market_context: 市场上下文

        Returns:
            知识增强信号
        """
        # 构建查询
        query = self._build_signal_query(base_signal, market_context)

        # 搜索历史知识
        historical_matches = await self._search_knowledge(query)

        # 计算增强
        if historical_matches:
            success_rate = self._calculate_success_rate(historical_matches)
            confidence = self._determine_confidence(
                len(historical_matches), success_rate
            )
            reasoning = self._generate_reasoning(
                base_signal, historical_matches
            )
        else:
            success_rate = 0.5
            confidence = DecisionConfidence.LOW
            reasoning = "No historical matches found"

        # 创建增强信号
        enhanced = KnowledgeAugmentedSignal(
            signal_type=TradingSignalType(base_signal.get('type', 'arbitrage')),
            confidence=confidence,
            strength=base_signal.get('strength', 0.5),
            reasoning=reasoning,
            historical_matches=len(historical_matches),
            success_rate=success_rate,
            evidence=[m.get('outcome', '') for m in historical_matches[:5]]
        )

        # 缓存信号
        self._signal_history.append(enhanced)
        self._total_signals += 1

        # 自适应学习
        if self.enable_adaptive:
            await self._adaptive_learn(base_signal, market_context, enhanced)

        return enhanced

    async def _search_knowledge(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索memo0知识库

        Args:
            query: 查询字符串
            limit: 返回数量

        Returns:
            知识匹配列表
        """
        if not self._initialized or not self._mem0:
            return []

        try:
            # 简单搜索实现
            results = await self._mem0.search(
                query,
                limit=min(limit, self.lookback_matches)
            )
            return results if results else []
        except Exception as e:
            logger.debug(f"知识库搜索失败: {e}")
            return []

    def _build_signal_query(
        self,
        signal: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """构建信号查询字符串"""
        symbol = signal.get('symbol', '')
        regime = context.get('regime', 'unknown')
        volatility = context.get('volatility', 0)

        return f"{symbol} {regime} volatility {volatility:.2%}"

    def _calculate_success_rate(
        self,
        matches: List[Dict[str, Any]]
    ) -> float:
        """计算���史成功率"""
        if not matches:
            return 0.5

        successful = sum(
            1 for m in matches
            if m.get('outcome') == 'profit'
        )
        return successful / len(matches)

    def _determine_confidence(
        self,
        match_count: int,
        success_rate: float
    ) -> DecisionConfidence:
        """确定置信度"""
        if match_count >= 10 and success_rate >= 0.7:
            return DecisionConfidence.HIGH
        elif match_count >= 5 and success_rate >= 0.5:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW

    def _generate_reasoning(
        self,
        signal: Dict[str, Any],
        matches: List[Dict[str, Any]]
    ) -> str:
        """生成推理过程"""
        match_count = len(matches)
        success_rate = self._calculate_success_rate(matches)

        return (
            f"Found {match_count} historical patterns with "
            f"{success_rate:.1%} success rate. "
            f"Signal Type: {signal.get('type', 'unknown')}"
        )

    async def _adaptive_learn(
        self,
        signal: Dict[str, Any],
        context: Dict[str, Any],
        enhanced: KnowledgeAugmentedSignal
    ) -> None:
        """自适应学习 - 从信号中学习"""
        if not self._initialized or not self._mem0:
            return

        try:
            # 记录信号模式
            learning_data = {
                'signal_type': enhanced.signal_type.value,
                'context': context,
                'success_rate': enhanced.success_rate,
                'confidence': enhanced.confidence.value,
            }
            await self._mem0.add(learning_data)
        except Exception as e:
            logger.debug(f"自适应学习失败: {e}")

    def create_arbitrage_decision(
        self,
        opportunity: Dict[str, Any],
        signal: KnowledgeAugmentedSignal
    ) -> Optional[ArbitrageDecision]:
        """创建套利决策

        Args:
            opportunity: 套利机会
            signal: 知识增强信号

        Returns:
            套利决策或None(如果信号不足)
        """
        # 检查置信度
        confidence_order = {
            DecisionConfidence.HIGH: 3,
            DecisionConfidence.MEDIUM: 2,
            DecisionConfidence.LOW: 1,
        }

        if confidence_order.get(signal.confidence, 0) < confidence_order.get(self.min_confidence, 2):
            return None

        # 检查成功率
        if signal.success_rate < self.min_success_rate:
            return None

        # 计算风险调整后利润
        risk_factor = 1.0 - signal.risk_score * 0.5
        expected_profit = opportunity.get('expected_profit', 0)
        risk_adjusted = expected_profit * risk_factor

        # 计算止损止盈
        entry = opportunity.get('entry_price', 0)
        risk_pct = 0.02  # 2%风险
        stop_loss = entry * (1 - risk_pct) if opportunity.get('side') == 'long' else entry * (1 + risk_pct)
        take_profit = entry * (1 + risk_pct * 2) if opportunity.get('side') == 'long' else entry * (1 - risk_pct * 2)

        decision = ArbitrageDecision(
            opportunity_id=opportunity.get('id', f"arb_{int(time.time())}"),
            symbol=opportunity.get('symbol', ''),
            side=opportunity.get('side', 'long'),
            entry_price=entry,
            position_size=opportunity.get('size', 1000),
            expected_profit=expected_profit,
            risk_adjusted_profit=risk_adjusted,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_score=1.0 - signal.success_rate,
            signal=signal
        )

        # 缓存决策
        self._decision_history.append(decision)

        return decision

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_signals': self._total_signals,
            'successful_signals': self._successful_signals,
            'success_rate': (
                self._successful_signals / self._total_signals
                if self._total_signals > 0 else 0
            ),
            'signal_history_size': len(self._signal_history),
            'decision_history_size': len(self._decision_history),
            'memo0_initialized': self._initialized,
        }


async def create_memo0_trading(config: Dict[str, Any]) -> Memo0IntegratedTrading:
    """创建Memo0集成交易系统

    Args:
        config: 配置字典

    Returns:
        Memo0集成交易系统实例
    """
    trading = Memo0IntegratedTrading(config)
    await trading.initialize()
    return trading