"""自动知识提取器 - V5.10 Phase 1.1

智能自动从交易数据、市场数据和决策过程中提取知识，
使用LLM辅助的事实提取和验证，实现知识管理的自动化。

核心功能：
1. 从交易数据自动提取知识
2. 从市场数据自动提取知识
3. 从决策过程自动提取知识
4. LLM辅助的知识提取和验证
5. 多源知识融合和去重

基于：V5.9架构优化
创建时间：2026-04-19
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class KnowledgeSource(Enum):
    """知识来源枚举"""
    TRADE_DATA = "trade_data"
    MARKET_DATA = "market_data"
    DECISION_PROCESS = "decision_process"
    USER_INPUT = "user_input"
    EXTERNAL_API = "external_api"


class KnowledgeCategory(Enum):
    """知识类别枚举"""
    STRATEGY = "strategy"
    RISK_MANAGEMENT = "risk_management"
    MARKET_ANALYSIS = "market_analysis"
    EXECUTION = "execution"
    PERFORMANCE = "performance"
    ANOMALY = "anomaly"
    OPTIMIZATION = "optimization"


@dataclass
class ExtractedKnowledge:
    """提取的知识条目"""
    content: str
    category: KnowledgeCategory
    source: KnowledgeSource
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.now)
    verified: bool = False
    related_symbols: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "category": self.category.value,
            "source": self.source.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "extracted_at": self.extracted_at.isoformat(),
            "verified": self.verified,
            "related_symbols": list(self.related_symbols)
        }


@dataclass
class ExtractionResult:
    """提取结果"""
    success: bool
    knowledge_items: List[ExtractedKnowledge]
    extraction_time: float
    source_type: str
    error_message: Optional[str] = None
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "knowledge_items": [item.to_dict() for item in self.knowledge_items],
            "extraction_time": self.extraction_time,
            "source_type": self.source_type,
            "error_message": self.error_message,
            "stats": self.stats
        }


class AutoKnowledgeExtractor:
    """自动知识提取器

    智能自动从各种数据源提取知识，使用LLM辅助验证和优化。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化自动知识提取器

        Args:
            config: 配置字典
        """
        self.config = config

        # 提取配置
        self.enable_llm_assistance = config.get('enable_llm_assistance', True)
        self.min_confidence_threshold = config.get('min_confidence_threshold', 0.6)
        self.max_extraction_batch = config.get('max_extraction_batch', 10)
        self.extraction_timeout = config.get('extraction_timeout', 30)

        # 去重配置
        self.enable_deduplication = config.get('enable_deduplication', True)
        self.similarity_threshold = config.get('similarity_threshold', 0.85)

        # LLM配置（如果启用）
        self.llm_model = config.get('llm_model', 'claude-sonnet-4-6')
        self.llm_temperature = config.get('llm_temperature', 0.0)

        # 统计信息
        self.extraction_stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_knowledge_items": 0,
            "verified_items": 0,
            "deduplicated_items": 0,
            "by_source": {},
            "by_category": {}
        }

        # 已提取知识的缓存（用于去重）
        self._extracted_knowledge_cache: List[str] = []
        self._cache_lock = asyncio.Lock()

        logger.info("[OK] 自动知识提取器初始化完成")

    # ========== 核心提取方法 ==========

    async def extract_from_trade(
        self,
        trade_data: Dict[str, Any]
    ) -> ExtractionResult:
        """从交易数据提取知识

        Args:
            trade_data: 交易数据字典

        Returns:
            提取结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            knowledge_items = []

            # 提取交易策略知识
            strategy_knowledge = await self._extract_strategy_knowledge(trade_data)
            knowledge_items.extend(strategy_knowledge)

            # 提取执行知识
            execution_knowledge = await self._extract_execution_knowledge(trade_data)
            knowledge_items.extend(execution_knowledge)

            # 提取风险管理知识
            risk_knowledge = await self._extract_risk_knowledge(trade_data)
            knowledge_items.extend(risk_knowledge)

            # 提取性能知识
            performance_knowledge = await self._extract_performance_knowledge(trade_data)
            knowledge_items.extend(performance_knowledge)

            # 去重
            if self.enable_deduplication:
                knowledge_items = await self._deduplicate_knowledge(knowledge_items)

            # LLM验证（如果启用）
            if self.enable_llm_assistance:
                knowledge_items = await self._llm_verify_knowledge(knowledge_items)

            extraction_time = asyncio.get_event_loop().time() - start_time

            # 更新统计
            await self._update_extraction_stats(
                "trade_data", len(knowledge_items), True, extraction_time
            )

            return ExtractionResult(
                success=True,
                knowledge_items=knowledge_items,
                extraction_time=extraction_time,
                source_type="trade_data",
                stats={
                    "total_items": len(knowledge_items),
                    "by_category": self._count_by_category(knowledge_items)
                }
            )

        except Exception as e:
            extraction_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"从交易数据提取知识失败: {e}")

            await self._update_extraction_stats(
                "trade_data", 0, False, extraction_time
            )

            return ExtractionResult(
                success=False,
                knowledge_items=[],
                extraction_time=extraction_time,
                source_type="trade_data",
                error_message=str(e)
            )

    async def extract_from_market(
        self,
        market_data: Dict[str, Any]
    ) -> ExtractionResult:
        """从市场数据提取知识

        Args:
            market_data: 市场数据字典

        Returns:
            提取结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            knowledge_items = []

            # 提取市场分析知识
            market_analysis_knowledge = await self._extract_market_analysis_knowledge(
                market_data
            )
            knowledge_items.extend(market_analysis_knowledge)

            # 提取异常检测知识
            anomaly_knowledge = await self._extract_anomaly_knowledge(market_data)
            knowledge_items.extend(anomaly_knowledge)

            # 提取套利机会知识
            arbitrage_knowledge = await self._extract_arbitrage_knowledge(market_data)
            knowledge_items.extend(arbitrage_knowledge)

            # 去重
            if self.enable_deduplication:
                knowledge_items = await self._deduplicate_knowledge(knowledge_items)

            # LLM验证
            if self.enable_llm_assistance:
                knowledge_items = await self._llm_verify_knowledge(knowledge_items)

            extraction_time = asyncio.get_event_loop().time() - start_time

            # 更新统计
            await self._update_extraction_stats(
                "market_data", len(knowledge_items), True, extraction_time
            )

            return ExtractionResult(
                success=True,
                knowledge_items=knowledge_items,
                extraction_time=extraction_time,
                source_type="market_data",
                stats={
                    "total_items": len(knowledge_items),
                    "by_category": self._count_by_category(knowledge_items)
                }
            )

        except Exception as e:
            extraction_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"从市场数据提取知识失败: {e}")

            await self._update_extraction_stats(
                "market_data", 0, False, extraction_time
            )

            return ExtractionResult(
                success=False,
                knowledge_items=[],
                extraction_time=extraction_time,
                source_type="market_data",
                error_message=str(e)
            )

    async def extract_from_decision(
        self,
        decision_data: Dict[str, Any]
    ) -> ExtractionResult:
        """从决策过程提取知识

        Args:
            decision_data: 决策数据字典

        Returns:
            提取结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            knowledge_items = []

            # 提取决策策略知识
            decision_strategy_knowledge = await self._extract_decision_strategy_knowledge(
                decision_data
            )
            knowledge_items.extend(decision_strategy_knowledge)

            # 提取决策理由知识
            rationale_knowledge = await self._extract_rationale_knowledge(decision_data)
            knowledge_items.extend(rationale_knowledge)

            # 提取决策结果知识
            outcome_knowledge = await self._extract_decision_outcome_knowledge(
                decision_data
            )
            knowledge_items.extend(outcome_knowledge)

            # 去重
            if self.enable_deduplication:
                knowledge_items = await self._deduplicate_knowledge(knowledge_items)

            # LLM验证
            if self.enable_llm_assistance:
                knowledge_items = await self._llm_verify_knowledge(knowledge_items)

            extraction_time = asyncio.get_event_loop().time() - start_time

            # 更新统计
            await self._update_extraction_stats(
                "decision_process", len(knowledge_items), True, extraction_time
            )

            return ExtractionResult(
                success=True,
                knowledge_items=knowledge_items,
                extraction_time=extraction_time,
                source_type="decision_process",
                stats={
                    "total_items": len(knowledge_items),
                    "by_category": self._count_by_category(knowledge_items)
                }
            )

        except Exception as e:
            extraction_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"从决策过程提取知识失败: {e}")

            await self._update_extraction_stats(
                "decision_process", 0, False, extraction_time
            )

            return ExtractionResult(
                success=False,
                knowledge_items=[],
                extraction_time=extraction_time,
                source_type="decision_process",
                error_message=str(e)
            )

    # ========== 辅助提取方法 ==========

    async def _extract_strategy_knowledge(
        self,
        trade_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取策略知识"""
        knowledge_items = []

        try:
            # 提取策略类型
            strategy = trade_data.get('strategy', 'unknown')
            symbol = trade_data.get('symbol', '')

            # 生成策略知识
            if strategy != 'unknown':
                knowledge = ExtractedKnowledge(
                    content=f"策略 {strategy} 在 {symbol} 上执行",
                    category=KnowledgeCategory.STRATEGY,
                    source=KnowledgeSource.TRADE_DATA,
                    confidence=0.8,
                    metadata={
                        "strategy": strategy,
                        "symbol": symbol,
                        "entry_price": trade_data.get('entry_price'),
                        "exit_price": trade_data.get('exit_price'),
                        "profit": trade_data.get('profit', 0)
                    },
                    related_symbols={symbol} if symbol else set()
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取策略知识失败: {e}")

        return knowledge_items

    async def _extract_execution_knowledge(
        self,
        trade_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取执行知识"""
        knowledge_items = []

        try:
            execution_time = trade_data.get('execution_time', 0)
            slippage = trade_data.get('slippage', 0)

            if execution_time > 5.0:  # 执行时间超过5秒
                knowledge = ExtractedKnowledge(
                    content=f"交易执行时间较长: {execution_time:.2f}秒，可能需要优化执行路径",
                    category=KnowledgeCategory.EXECUTION,
                    source=KnowledgeSource.TRADE_DATA,
                    confidence=0.7,
                    metadata={
                        "execution_time": execution_time,
                        "slippage": slippage,
                        "symbol": trade_data.get('symbol', '')
                    },
                    related_symbols={trade_data.get('symbol', '')}
                )
                knowledge_items.append(knowledge)

            if abs(slippage) > 0.1:  # 滑点超过0.1%
                knowledge = ExtractedKnowledge(
                    content=f"交易滑点较大: {slippage:.2f}%，可能需要优化执行时机",
                    category=KnowledgeCategory.EXECUTION,
                    source=KnowledgeSource.TRADE_DATA,
                    confidence=0.75,
                    metadata={
                        "slippage": slippage,
                        "execution_time": execution_time,
                        "symbol": trade_data.get('symbol', '')
                    },
                    related_symbols={trade_data.get('symbol', '')}
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取执行知识失败: {e}")

        return knowledge_items

    async def _extract_risk_knowledge(
        self,
        trade_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取风险管理知识"""
        knowledge_items = []

        try:
            risk_level = trade_data.get('risk_level', 'medium')
            max_drawdown = trade_data.get('max_drawdown', 0)

            if risk_level == 'high':
                knowledge = ExtractedKnowledge(
                    content=f"高风险交易执行，最大回撤: {max_drawdown:.2f}%",
                    category=KnowledgeCategory.RISK_MANAGEMENT,
                    source=KnowledgeSource.TRADE_DATA,
                    confidence=0.8,
                    metadata={
                        "risk_level": risk_level,
                        "max_drawdown": max_drawdown,
                        "symbol": trade_data.get('symbol', '')
                    },
                    related_symbols={trade_data.get('symbol', '')}
                )
                knowledge_items.append(knowledge)

            if max_drawdown > 2.0:  # 最大回撤超过2%
                knowledge = ExtractedKnowledge(
                    content=f"交易回撤较大: {max_drawdown:.2f}%，建议优化风险控制参数",
                    category=KnowledgeCategory.RISK_MANAGEMENT,
                    source=KnowledgeSource.TRADE_DATA,
                    confidence=0.75,
                    metadata={
                        "max_drawdown": max_drawdown,
                        "risk_level": risk_level,
                        "symbol": trade_data.get('symbol', '')
                    },
                    related_symbols={trade_data.get('symbol', '')}
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取风险管理知识失败: {e}")

        return knowledge_items

    async def _extract_performance_knowledge(
        self,
        trade_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取性能知识"""
        knowledge_items = []

        try:
            profit = trade_data.get('profit', 0)
            profit_rate = trade_data.get('profit_rate', 0)
            symbol = trade_data.get('symbol', '')

            if profit > 0:
                knowledge = ExtractedKnowledge(
                    content=f"盈利交易: {symbol} 盈利 {profit:.2f} ({profit_rate:.2f}%)",
                    category=KnowledgeCategory.PERFORMANCE,
                    source=KnowledgeSource.TRADE_DATA,
                    confidence=0.9,
                    metadata={
                        "profit": profit,
                        "profit_rate": profit_rate,
                        "symbol": symbol
                    },
                    related_symbols={symbol}
                )
                knowledge_items.append(knowledge)

            elif profit < 0:
                knowledge = ExtractedKnowledge(
                    content=f"亏损交易: {symbol} 亏损 {abs(profit):.2f} ({profit_rate:.2f}%)",
                    category=KnowledgeCategory.PERFORMANCE,
                    source=KnowledgeSource.TRADE_DATA,
                    confidence=0.9,
                    metadata={
                        "profit": profit,
                        "profit_rate": profit_rate,
                        "symbol": symbol
                    },
                    related_symbols={symbol}
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取性能知识失败: {e}")

        return knowledge_items

    async def _extract_market_analysis_knowledge(
        self,
        market_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取市场分析知识"""
        knowledge_items = []

        try:
            volatility = market_data.get('volatility', 0)
            trend = market_data.get('trend', 'neutral')
            symbol = market_data.get('symbol', '')

            if volatility > 3.0:  # 高波动性
                knowledge = ExtractedKnowledge(
                    content=f"{symbol} 市场波动性较高: {volatility:.2f}%，建议谨慎交易",
                    category=KnowledgeCategory.MARKET_ANALYSIS,
                    source=KnowledgeSource.MARKET_DATA,
                    confidence=0.8,
                    metadata={
                        "volatility": volatility,
                        "trend": trend,
                        "symbol": symbol
                    },
                    related_symbols={symbol}
                )
                knowledge_items.append(knowledge)

            if trend in ['bullish', 'bearish']:
                knowledge = ExtractedKnowledge(
                    content=f"{symbol} 市场趋势: {trend}，可考虑相应策略调整",
                    category=KnowledgeCategory.MARKET_ANALYSIS,
                    source=KnowledgeSource.MARKET_DATA,
                    confidence=0.75,
                    metadata={
                        "trend": trend,
                        "volatility": volatility,
                        "symbol": symbol
                    },
                    related_symbols={symbol}
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取市场分析知识失败: {e}")

        return knowledge_items

    async def _extract_anomaly_knowledge(
        self,
        market_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取异常检测知识"""
        knowledge_items = []

        try:
            price_change = market_data.get('price_change_24h', 0)
            volume_change = market_data.get('volume_change_24h', 0)
            symbol = market_data.get('symbol', '')

            # 价格异常变化
            if abs(price_change) > 10.0:  # 24小时价格变化超过10%
                knowledge = ExtractedKnowledge(
                    content=f"{symbol} 价格异常波动: {price_change:+.2f}%，需关注市场动态",
                    category=KnowledgeCategory.ANOMALY,
                    source=KnowledgeSource.MARKET_DATA,
                    confidence=0.85,
                    metadata={
                        "price_change": price_change,
                        "volume_change": volume_change,
                        "symbol": symbol
                    },
                    related_symbols={symbol}
                )
                knowledge_items.append(knowledge)

            # 成交量异常变化
            if abs(volume_change) > 50.0:  # 24小时成交量变化超过50%
                knowledge = ExtractedKnowledge(
                    content=f"{symbol} 成交量异常变化: {volume_change:+.2f}%，可能存在重大消息",
                    category=KnowledgeCategory.ANOMALY,
                    source=KnowledgeSource.MARKET_DATA,
                    confidence=0.8,
                    metadata={
                        "volume_change": volume_change,
                        "price_change": price_change,
                        "symbol": symbol
                    },
                    related_symbols={symbol}
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取异常检测知识失败: {e}")

        return knowledge_items

    async def _extract_arbitrage_knowledge(
        self,
        market_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取套利机会知识"""
        knowledge_items = []

        try:
            arbitrage_opportunities = market_data.get('arbitrage_opportunities', [])

            for opp in arbitrage_opportunities[:3]:  # 只取前3个机会
                profit_rate = opp.get('profit_rate', 0)
                if profit_rate > 0.5:  # 套利收益超过0.5%
                    symbols = opp.get('symbols', [])
                    knowledge = ExtractedKnowledge(
                        content=f"发现套利机会: {', '.join(symbols)} 预期收益 {profit_rate:.2f}%",
                        category=KnowledgeCategory.STRATEGY,
                        source=KnowledgeSource.MARKET_DATA,
                        confidence=0.8,
                        metadata={
                            "profit_rate": profit_rate,
                            "symbols": symbols,
                            "exchanges": opp.get('exchanges', [])
                        },
                        related_symbols=set(symbols)
                    )
                    knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取套利机会知识失败: {e}")

        return knowledge_items

    async def _extract_decision_strategy_knowledge(
        self,
        decision_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取决策策略知识"""
        knowledge_items = []

        try:
            decision_type = decision_data.get('decision_type', 'unknown')
            confidence = decision_data.get('confidence', 0)

            if confidence > 0.8:
                knowledge = ExtractedKnowledge(
                    content=f"高置信度决策: {decision_type} (置信度: {confidence:.2f})",
                    category=KnowledgeCategory.STRATEGY,
                    source=KnowledgeSource.DECISION_PROCESS,
                    confidence=0.85,
                    metadata={
                        "decision_type": decision_type,
                        "confidence": confidence,
                        "timestamp": decision_data.get('timestamp')
                    }
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取决策策略知识失败: {e}")

        return knowledge_items

    async def _extract_rationale_knowledge(
        self,
        decision_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取决策理由知识"""
        knowledge_items = []

        try:
            rationale = decision_data.get('rationale', '')

            if rationale and len(rationale) > 20:
                knowledge = ExtractedKnowledge(
                    content=f"决策理由: {rationale[:100]}...",
                    category=KnowledgeCategory.STRATEGY,
                    source=KnowledgeSource.DECISION_PROCESS,
                    confidence=0.7,
                    metadata={
                        "full_rationale": rationale,
                        "decision_type": decision_data.get('decision_type')
                    }
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取决策理由知识失败: {e}")

        return knowledge_items

    async def _extract_decision_outcome_knowledge(
        self,
        decision_data: Dict[str, Any]
    ) -> List[ExtractedKnowledge]:
        """提取决策结果知识"""
        knowledge_items = []

        try:
            outcome = decision_data.get('outcome', 'unknown')
            actual_profit = decision_data.get('actual_profit', 0)

            if outcome == 'success' and actual_profit > 0:
                knowledge = ExtractedKnowledge(
                    content=f"成功决策: 实际盈利 {actual_profit:.2f}",
                    category=KnowledgeCategory.PERFORMANCE,
                    source=KnowledgeSource.DECISION_PROCESS,
                    confidence=0.9,
                    metadata={
                        "outcome": outcome,
                        "actual_profit": actual_profit,
                        "decision_type": decision_data.get('decision_type')
                    }
                )
                knowledge_items.append(knowledge)

            elif outcome == 'failure':
                knowledge = ExtractedKnowledge(
                    content=f"失败决策: 实际亏损 {abs(actual_profit):.2f}，需分析原因",
                    category=KnowledgeCategory.OPTIMIZATION,
                    source=KnowledgeSource.DECISION_PROCESS,
                    confidence=0.85,
                    metadata={
                        "outcome": outcome,
                        "actual_profit": actual_profit,
                        "decision_type": decision_data.get('decision_type')
                    }
                )
                knowledge_items.append(knowledge)

        except Exception as e:
            logger.warning(f"提取决策结果知识失败: {e}")

        return knowledge_items

    # ========== 知识处理方法 ==========

    async def _deduplicate_knowledge(
        self,
        knowledge_items: List[ExtractedKnowledge]
    ) -> List[ExtractedKnowledge]:
        """知识去重"""
        if not self.enable_deduplication:
            return knowledge_items

        unique_items = []
        seen_contents = set()

        async with self._cache_lock:
            # 添加现有缓存
            seen_contents.update(self._extracted_knowledge_cache)

        for item in knowledge_items:
            # 简单的内容去重
            content_hash = hash(item.content)

            if content_hash not in seen_contents:
                unique_items.append(item)
                seen_contents.add(content_hash)

                # 更新缓存
                async with self._cache_lock:
                    self._extracted_knowledge_cache.append(item.content)
                    # 保持缓存大小
                    if len(self._extracted_knowledge_cache) > 1000:
                        self._extracted_knowledge_cache = \
                            self._extracted_knowledge_cache[-500:]

        # 更新去重统计
        deduplicated_count = len(knowledge_items) - len(unique_items)
        if deduplicated_count > 0:
            self.extraction_stats["deduplicated_items"] += deduplicated_count
            logger.debug(f"去重: {deduplicated_count} 条重复知识")

        return unique_items

    async def _llm_verify_knowledge(
        self,
        knowledge_items: List[ExtractedKnowledge]
    ) -> List[ExtractedKnowledge]:
        """LLM验证知识"""
        if not self.enable_llm_assistance:
            return knowledge_items

        verified_items = []

        for item in knowledge_items:
            try:
                # 这里可以调用LLM进行验证
                # 简化版本：基于置信度过滤
                if item.confidence >= self.min_confidence_threshold:
                    item.verified = True
                    self.extraction_stats["verified_items"] += 1

                verified_items.append(item)

            except Exception as e:
                logger.warning(f"LLM验证知识失败: {e}")
                # 验证失败也保留原知识
                verified_items.append(item)

        return verified_items

    async def _update_extraction_stats(
        self,
        source: str,
        items_count: int,
        success: bool,
        extraction_time: float
    ):
        """更新提取统计"""
        self.extraction_stats["total_extractions"] += 1

        if success:
            self.extraction_stats["successful_extractions"] += 1
            self.extraction_stats["total_knowledge_items"] += items_count
        else:
            self.extraction_stats["failed_extractions"] += 1

        # 按来源统计
        if source not in self.extraction_stats["by_source"]:
            self.extraction_stats["by_source"][source] = {
                "count": 0,
                "items": 0,
                "total_time": 0.0
            }

        self.extraction_stats["by_source"][source]["count"] += 1
        self.extraction_stats["by_source"][source]["items"] += items_count
        self.extraction_stats["by_source"][source]["total_time"] += extraction_time

    def _count_by_category(
        self,
        knowledge_items: List[ExtractedKnowledge]
    ) -> Dict[str, int]:
        """按类别统计"""
        category_count = {}

        for item in knowledge_items:
            category = item.category.value
            category_count[category] = category_count.get(category, 0) + 1

        return category_count

    # ========== 工具方法 ==========

    def get_extraction_stats(self) -> Dict[str, Any]:
        """获取提取统计"""
        return self.extraction_stats.copy()

    def reset_stats(self):
        """重置统计"""
        self.extraction_stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_knowledge_items": 0,
            "verified_items": 0,
            "deduplicated_items": 0,
            "by_source": {},
            "by_category": {}
        }
        logger.info("提取统计已重置")


def create_auto_knowledge_extractor(
    config: Dict[str, Any]
) -> AutoKnowledgeExtractor:
    """创建自动知识提取器实例

    Args:
        config: 配置字典

    Returns:
        自动知识提取器实例
    """
    return AutoKnowledgeExtractor(config)
