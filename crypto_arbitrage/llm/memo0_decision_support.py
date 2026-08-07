"""Memo0 深度智能决策支持系统 V3.7
利用 Memo0 的语义搜索和知识推理能力，为实时交易决策提供智能支持
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from storage.mem0_storage import Memo0Storage


logger = logging.getLogger(__name__)


@dataclass
class MarketContext:
    """市场上下文信息"""
    timestamp: datetime
    symbol: str
    price: float
    volume_24h: float
    volatility: float
    trend: str  # 'uptrend', 'downtrend', 'sideways'
    market_regime: str  # 'bullish', 'bearish', 'volatile', 'stable'
    technical_indicators: Dict[str, float]
    sentiment_score: float  # -1 to 1
    liquidity_score: float  # 0 to 1


@dataclass
class KnowledgeQueryResult:
    """知识查询结果"""
    content: str
    relevance_score: float
    category: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class DecisionInsight:
    """决策洞察"""
    insight_type: str  # 'opportunity', 'risk', 'optimization', 'warning'
    description: str
    confidence: float  # 0 to 1
    supporting_knowledge: List[KnowledgeQueryResult]
    recommended_action: Optional[str]
    reasoning: str


class MarketContextBuilder:
    """市场上下文构建器"""

    def __init__(self):
        self.indicator_calculators = {}

    async def build_context(self, market_data: Dict[str, Any]) -> MarketContext:
        """构建市场上下文

        Args:
            market_data: 市场数据字典

        Returns:
            市场上下文对象
        """
        # 基础信息
        context = MarketContext(
            timestamp=datetime.now(),
            symbol=market_data.get('symbol', 'UNKNOWN'),
            price=market_data.get('price', 0.0),
            volume_24h=market_data.get('volume_24h', 0.0),
            volatility=market_data.get('volatility', 0.0),
            trend=self._determine_trend(market_data),
            market_regime=self._determine_regime(market_data),
            technical_indicators=market_data.get('technical_indicators', {}),
            sentiment_score=market_data.get('sentiment_score', 0.0),
            liquidity_score=market_data.get('liquidity_score', 0.5)
        )

        logger.info(f"构建市场上下文: {context.symbol} - {context.market_regime}")
        return context

    def _determine_trend(self, market_data: Dict[str, Any]) -> str:
        """确定价格趋势"""
        ma_short = market_data.get('ma_short', 0)
        ma_long = market_data.get('ma_long', 0)
        rsi = market_data.get('rsi', 50)

        if ma_short > ma_long and rsi > 50:
            return 'uptrend'
        elif ma_short < ma_long and rsi < 50:
            return 'downtrend'
        else:
            return 'sideways'

    def _determine_regime(self, market_data: Dict[str, Any]) -> str:
        """确定市场制式"""
        volatility = market_data.get('volatility', 0)
        trend = self._determine_trend(market_data)

        if volatility > 0.05:  # 高波动
            return 'volatile'
        elif trend == 'uptrend':
            return 'bullish'
        elif trend == 'downtrend':
            return 'bearish'
        else:
            return 'stable'


class Memo0DecisionSupport:
    """Memo0 驱动的智能决策支持系统"""

    def __init__(self, memo0_storage: Memo0Storage):
        """初始化决策支持系统

        Args:
            memo0_storage: Memo0 存储实例
        """
        self.memo0 = memo0_storage
        self.context_builder = MarketContextBuilder()
        self.query_cache = {}  # 查询缓存
        self.cache_ttl = 300  # 缓存有效期（秒）

        logger.info("Memo0 智能决策支持系统初始化完成")

    async def get_relevant_knowledge(
        self,
        market_context: MarketContext,
        query_type: str = "general",
        limit: int = 5
    ) -> List[KnowledgeQueryResult]:
        """获取与当前市场状态相关的知识

        Args:
            market_context: 市场上下文
            query_type: 查询类型
            limit: 返回结果数量限制

        Returns:
            相关知识列表
        """
        try:
            # 构建多维查询
            queries = self._build_multi_dim_queries(market_context, query_type)

            # 并行查询多个维度
            all_results = []
            for query in queries:
                results = await self._execute_query(query, limit)
                all_results.extend(results)

            # 去重和排序
            unique_results = self._deduplicate_and_rank(all_results)

            logger.info(f"获取到 {len(unique_results)} 条相关知识")
            return unique_results[:limit]

        except Exception as e:
            logger.error(f"获取相关知识失败: {e}")
            return []

    def _build_multi_dim_queries(
        self,
        context: MarketContext,
        query_type: str
    ) -> List[str]:
        """构建多维查询

        Args:
            context: 市场上下文
            query_type: 查询类型

        Returns:
            查询字符串列表
        """
        queries = []

        # 1. 市场制式查询
        queries.append(f"{context.market_regime} market {context.trend} trading strategy")

        # 2. 波动性查询
        volatility_level = "high" if context.volatility > 0.05 else "low"
        queries.append(f"{volatility_level} volatility risk management")

        # 3. 技术指标查询
        if context.technical_indicators:
            rsi = context.technical_indicators.get('rsi', 50)
            if rsi > 70:
                queries.append("overbought conditions trading strategy")
            elif rsi < 30:
                queries.append("oversold conditions trading strategy")

        # 4. 情绪查询
        if context.sentiment_score > 0.3:
            queries.append("bullish sentiment trading opportunities")
        elif context.sentiment_score < -0.3:
            queries.append("bearish sentiment risk management")

        # 5. 特定类型查询
        if query_type == "arbitrage":
            queries.append(f"{context.symbol} arbitrage opportunities")
        elif query_type == "risk":
            queries.append(f"{context.market_regime} market risk factors")

        return queries

    async def _execute_query(
        self,
        query: str,
        limit: int
    ) -> List[KnowledgeQueryResult]:
        """执行查询

        Args:
            query: 查询字符串
            limit: 结果数量限制

        Returns:
            查询结果列表
        """
        # 检查缓存
        cache_key = f"{query}_{limit}"
        if cache_key in self.query_cache:
            cached_result, cached_time = self.query_cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                return cached_result

        try:
            # 调用 Memo0 搜索
            search_results = await self.memo0.search(query, limit=limit)

            # 转换为标准格式
            results = []
            for item in search_results:
                result = KnowledgeQueryResult(
                    content=item.get('content', ''),
                    relevance_score=item.get('score', 0.0),
                    category=item.get('category', 'general'),
                    source=item.get('source', 'memo0'),
                    timestamp=datetime.fromisoformat(item.get('created_at', datetime.now().isoformat())),
                    metadata=item.get('metadata', {})
                )
                results.append(result)

            # 缓存结果
            self.query_cache[cache_key] = (results, datetime.now())

            return results

        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            return []

    def _deduplicate_and_rank(
        self,
        results: List[KnowledgeQueryResult]
    ) -> List[KnowledgeQueryResult]:
        """去重和排序结果

        Args:
            results: 原始结果列表

        Returns:
            去重排序后的结果列表
        """
        # 按内容去重
        seen_contents = set()
        unique_results = []

        for result in results:
            if result.content not in seen_contents:
                seen_contents.add(result.content)
                unique_results.append(result)

        # 按相关性分数排序
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return unique_results

    async def reason_about_opportunity(
        self,
        opportunity: Dict[str, Any],
        market_context: MarketContext
    ) -> DecisionInsight:
        """对交易机会进行知识推理

        Args:
            opportunity: 交易机会信息
            market_context: 市场上下文

        Returns:
            决策洞察
        """
        try:
            # 获取相关知识
            knowledge = await self.get_relevant_knowledge(
                market_context,
                query_type="arbitrage",
                limit=3
            )

            # 分析机会
            insight_type = self._analyze_opportunity_type(opportunity, market_context)
            confidence = self._calculate_confidence(opportunity, market_context, knowledge)

            # 生成推理
            reasoning = self._generate_reasoning(opportunity, market_context, knowledge)

            # 推荐行动
            recommended_action = self._recommend_action(insight_type, confidence, knowledge)

            insight = DecisionInsight(
                insight_type=insight_type,
                description=reasoning,
                confidence=confidence,
                supporting_knowledge=knowledge,
                recommended_action=recommended_action,
                reasoning=reasoning
            )

            logger.info(f"生成决策洞察: {insight_type} (置信度: {confidence:.2%})")
            return insight

        except Exception as e:
            logger.error(f"机会推理失败: {e}")
            return DecisionInsight(
                insight_type="error",
                description=f"推理过程出错: {str(e)}",
                confidence=0.0,
                supporting_knowledge=[],
                recommended_action=None,
                reasoning=""
            )

    def _analyze_opportunity_type(
        self,
        opportunity: Dict[str, Any],
        context: MarketContext
    ) -> str:
        """分析机会类型"""
        profit_potential = opportunity.get('expected_profit', 0)
        risk_level = opportunity.get('risk_level', 'medium')

        if profit_potential > 0.02:  # > 2% 预期收益
            if risk_level == 'low':
                return 'opportunity'
            else:
                return 'warning'
        elif context.volatility > 0.08:  # 高波动环境
            return 'risk'
        else:
            return 'optimization'

    def _calculate_confidence(
        self,
        opportunity: Dict[str, Any],
        context: MarketContext,
        knowledge: List[KnowledgeQueryResult]
    ) -> float:
        """计算置信度"""
        base_confidence = 0.5

        # 基于机会质量调整
        profit_potential = opportunity.get('expected_profit', 0)
        if profit_potential > 0.01:
            base_confidence += 0.2

        # 基于市场环境调整
        if context.market_regime == 'stable':
            base_confidence += 0.1
        elif context.market_regime == 'volatile':
            base_confidence -= 0.1

        # 基于知识支持调整
        if knowledge and knowledge[0].relevance_score > 0.8:
            base_confidence += 0.1

        # 限制在 0-1 范围内
        return max(0.0, min(1.0, base_confidence))

    def _generate_reasoning(
        self,
        opportunity: Dict[str, Any],
        context: MarketContext,
        knowledge: List[KnowledgeQueryResult]
    ) -> str:
        """生成推理说明"""
        reasoning_parts = []

        # 机会描述
        reasoning_parts.append(f"发现{opportunity.get('type', '套利')}机会")

        # 市场环境
        reasoning_parts.append(f"当前市场制式: {context.market_regime}, 趋势: {context.trend}")

        # 风险分析
        volatility_desc = "高" if context.volatility > 0.05 else "低"
        reasoning_parts.append(f"市场波动性: {volatility_desc}")

        # 知识支持
        if knowledge:
            reasoning_parts.append(f"基于 {len(knowledge)} 条相关知识进行分析")

        return ". ".join(reasoning_parts) + "."

    def _recommend_action(
        self,
        insight_type: str,
        confidence: float,
        knowledge: List[KnowledgeQueryResult]
    ) -> Optional[str]:
        """推荐行动"""
        if insight_type == "opportunity" and confidence > 0.7:
            return "建议执行交易"
        elif insight_type == "warning":
            return "建议谨慎评估风险"
        elif insight_type == "risk":
            return "建议暂停交易"
        elif insight_type == "optimization":
            return "建议优化参数后执行"
        else:
            return None

    async def update_knowledge_from_trade(
        self,
        trade_result: Dict[str, Any]
    ) -> bool:
        """从交易结果中更新知识

        Args:
            trade_result: 交易结果数据

        Returns:
            是否成功更新
        """
        try:
            # 提取知识
            knowledge_content = self._extract_knowledge_from_trade(trade_result)

            # 存储到 Memo0
            await self.memo0.add(
                content=knowledge_content,
                metadata={
                    'source': 'trade_result',
                    'trade_id': trade_result.get('trade_id'),
                    'strategy': trade_result.get('strategy'),
                    'profit': trade_result.get('profit'),
                    'timestamp': datetime.now().isoformat()
                }
            )

            logger.info(f"从交易结果中更新知识: {trade_result.get('trade_id')}")
            return True

        except Exception as e:
            logger.error(f"更新知识失败: {e}")
            return False

    def _extract_knowledge_from_trade(self, trade_result: Dict[str, Any]) -> str:
        """从交易结果中提取知识"""
        profit = trade_result.get('profit', 0)
        strategy = trade_result.get('strategy', 'unknown')

        if profit > 0:
            return f"成功的{strategy}策略交易，盈利{profit:.2f}。市场条件: {trade_result.get('market_conditions', 'N/A')}"
        else:
            return f"失败的{strategy}策略交易，亏损{abs(profit):.2f}。可能原因: {trade_result.get('failure_reason', 'N/A')}"

    async def get_decision_summary(
        self,
        market_context: MarketContext
    ) -> Dict[str, Any]:
        """获取决策摘要

        Args:
            market_context: 市场上下文

        Returns:
            决策摘要字典
        """
        try:
            # 获取相关知识
            knowledge = await self.get_relevant_knowledge(market_context)

            # 分析市场状态
            market_analysis = {
                'regime': market_context.market_regime,
                'trend': market_context.trend,
                'volatility': market_context.volatility,
                'sentiment': market_context.sentiment_score,
                'liquidity': market_context.liquidity_score
            }

            # 生成建议
            suggestions = []
            if knowledge:
                for item in knowledge[:3]:
                    suggestions.append({
                        'category': item.category,
                        'insight': item.content[:100] + '...' if len(item.content) > 100 else item.content,
                        'relevance': item.relevance_score
                    })

            return {
                'timestamp': datetime.now().isoformat(),
                'market_analysis': market_analysis,
                'available_knowledge': len(knowledge),
                'top_suggestions': suggestions,
                'overall_sentiment': 'positive' if market_context.sentiment_score > 0.2 else 'negative' if market_context.sentiment_score < -0.2 else 'neutral'
            }

        except Exception as e:
            logger.error(f"生成决策摘要失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# 便捷函数
async def create_decision_support(
    memo0_storage: Memo0Storage
) -> Memo0DecisionSupport:
    """创建决策支持系统实例

    Args:
        memo0_storage: Memo0 存储实例

    Returns:
        决策支持系统实例
    """
    return Memo0DecisionSupport(memo0_storage)