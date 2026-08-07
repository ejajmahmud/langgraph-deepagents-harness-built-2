"""实时知识更新系统与Memo0深度集成 V16.0

将Phase 3的实时知识更新系统与Memo0存储深度集成，
构建完整的知识→决策→套利闭环。

V16.0核心升级：
1. 实时数据采集与Memo0集成
2. 知识提取引擎与Memo0存储对接
3. 图谱动态更新与Memo0同步
4. 质量评估与Memo0知识验证
5. 低风险套利引擎与Memo0决策支持集成

基于：
- V15.9 Phase 3实时知识更新系统
- V5.9深度Memo0集成
- V3.2低风险套利引擎
"""

import asyncio
import logging
import time
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 导入Phase 3模块
from data_collection.real_time_collector import (
    RealTimeDataCollector,
    DataType,
    Exchange,
    MarketData,
    DataQualityMetrics
)
from knowledge_extraction.extraction_engine import (
    KnowledgeExtractionEngine,
    KnowledgeType,
    ExtractedKnowledge,
    ExtractionMetrics
)
from knowledge.graph_dynamic_updater import (
    GraphDynamicUpdater,
    UpdatePriority,
    UpdateTask,
    UpdateStatus
)
from quality.quality_assessor import (
    QualityAssessor,
    QualityScore
)

# 导入Memo0和低风险套利
from storage.mem0_storage import Memo0Storage, get_mem0_storage, load_mem0_config
from strategies.low_risk_arbitrage_engine import LowRiskArbitrageEngine
from llm.memo0_decision_support import MarketContext, DecisionInsight

logger = logging.getLogger(__name__)


class IntegrationMode(Enum):
    """集成模式"""
    REAL_TIME = "real_time"  # 实时集成
    BATCH = "batch"  # 批量集成
    HYBRID = "hybrid"  # 混合模式


@dataclass
class KnowledgeUpdateResult:
    """知识更新结果"""
    success: bool
    knowledge_count: int
    mem0_stored: int
    graph_updated: int
    quality_assessed: int
    duration_ms: float
    errors: List[str] = field(default_factory=list)


@dataclass
class ArbitrageDecision:
    """套利决策"""
    decision_id: str
    opportunity: Dict[str, Any]
    confidence: float
    risk_level: str
    recommended_action: str
    supporting_knowledge: List[Dict[str, Any]]
    timestamp: float = field(default_factory=time.time)


class RealtimeKnowledgeMemo0Integration:
    """实时知识更新系统与Memo0深度集成 V16.0

    集成Phase 3的实时知识更新系统与Memo0存储，
    实现完整的知识→决策→套利闭环。
    """

    def __init__(
        self,
        integration_mode: IntegrationMode = IntegrationMode.HYBRID,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化实时知识Memo0集成

        Args:
            integration_mode: 集成模式
            config: 配置字典
        """
        self.integration_mode = integration_mode
        self.config = config or {}
        self._version = "V16.0"

        # 初始化Memo0存储
        self._mem0_config = load_mem0_config()
        self._mem0_storage = get_mem0_storage()

        # 初始化Phase 3模块
        self._data_collector = RealTimeDataCollector(config=self.config)
        self._extraction_engine = KnowledgeExtractionEngine(config=self.config)
        self._graph_updater = GraphDynamicUpdater(config=self.config)
        self._quality_assessor = QualityAssessor(config=self.config)

        # 初始化低风险套利引擎
        self._arbitrage_engine = LowRiskArbitrageEngine(config=self.config)

        # 集成指标
        self._total_updates = 0
        self._successful_updates = 0
        self._total_knowledge_stored = 0
        self._arbitrage_decisions_made = 0

        # 预热缓存
        self._knowledge_cache: Dict[str, ExtractedKnowledge] = {}
        self._context_cache: Dict[str, MarketContext] = {}

        logger.info(f"[OK] 实时知识Memo0集成 {self._version} 初始化完成")
        logger.info(f"集成模式: {self.integration_mode.value}")
        logger.info(f"Memo0状态: {'已连接' if self._mem0_storage else '本地存储'}")

    async def start_realtime_integration(self) -> None:
        """启动实时集成

        开始实时数据采集、知识提取、Memo0存储的完整闭环。
        """
        logger.info("启动实时知识更新与Memo0集成")

        try:
            # 启动实时数据采集
            await self._data_collector.start_stream()

            # 启动知识提取和存储循环
            integration_task = asyncio.create_task(self._integration_loop())

            # 启动低风险套利监控
            arbitrage_task = asyncio.create_task(self._arbitrage_monitor_loop())

            # 等待任务
            await asyncio.gather([integration_task, arbitrage_task])

        except Exception as e:
            logger.error(f"实时集成失败: {e}")
            raise

    async def _integration_loop(self) -> None:
        """知识集成主循环

        持续采集数据、提取知识、存储到Memo0。
        """
        logger.info("启动知识集成循环")

        while True:
            try:
                # 1. 采集实时数据
                market_data = await self._collect_realtime_data()

                if not market_data:
                    await asyncio.sleep(1)
                    continue

                # 2. 提取知识
                extracted_knowledge = await self._extract_knowledge(market_data)

                # 3. 存储到Memo0
                await self._store_to_memo0(extracted_knowledge)

                # 4. 更新知识图谱
                await self._update_graph(extracted_knowledge)

                # 5. 质量评估
                await self._assess_quality(extracted_knowledge)

                # 更新统计
                self._total_updates += 1

                # 根据集成模式调整频率
                if self.integration_mode == IntegrationMode.REAL_TIME:
                    await asyncio.sleep(0.1)  # 高频率
                else:
                    await asyncio.sleep(1.0)  # 低频率

            except Exception as e:
                logger.error(f"集成循环错误: {e}")
                await asyncio.sleep(5)

    async def _collect_realtime_data(self) -> Optional[MarketData]:
        """采集实时数据

        Returns:
            市场数据对象
        """
        try:
            # 采集关键交易对数据
            exchanges_to_monitor = [Exchange.BINANCE, Exchange.OKEX]
            data_types = [DataType.PRICE, DataType.VOLUME, DataType.ORDERBOOK]

            for exchange in exchanges_to_monitor:
                for data_type in data_types:
                    for symbol in ["BTC/USDT", "ETH/USDT", "ETH/BTC"]:
                        try:
                            data = await self._data_collector.collect_data(
                                exchange, symbol, data_type
                            )
                            if data:
                                return data
                        except Exception as e:
                            logger.debug(f"采集数据失败 {exchange}/{symbol}/{data_type}: {e}")
                            continue

            return None

        except Exception as e:
            logger.error(f"实时数据采集错误: {e}")
            return None

    async def _extract_knowledge(
        self,
        market_data: MarketData
    ) -> List[ExtractedKnowledge]:
        """提取知识

        Args:
            market_data: 市场数据

        Returns:
            提取的知识列表
        """
        try:
            # 使用Phase 3的知识提取引擎
            extracted = self._extraction_engine.extract_from_data(market_data)

            logger.debug(f"提取知识: {len(extracted)} 条")
            return extracted

        except Exception as e:
            logger.error(f"知识提取错误: {e}")
            return []

    async def _store_to_memo0(
        self,
        knowledge_list: List[ExtractedKnowledge]
    ) -> int:
        """存储知识到Memo0

        Args:
            knowledge_list: 知识列表

        Returns:
            成功存储的数量
        """
        if not self._mem0_storage:
            logger.warning("Memo0未连接，跳过存储")
            return 0

        stored_count = 0
        for knowledge in knowledge_list:
            try:
                # 构建Memo0存储内容
                content = knowledge.content
                metadata = {
                    "knowledge_type": knowledge.knowledge_type.value,
                    "confidence": knowledge.confidence,
                    "evidence": knowledge.evidence,
                    "timestamp": knowledge.created_at
                }

                # 存储到Memo0
                success = self._mem0_storage.add_knowledge(
                    category="arbitrage",
                    content=content,
                    metadata=metadata
                )

                if success:
                    stored_count += 1
                    self._total_knowledge_stored += 1

                    # 更新本地缓存
                    self._knowledge_cache[knowledge.knowledge_id] = knowledge

            except Exception as e:
                logger.error(f"存储知识到Memo0失败: {e}")
                continue

        logger.debug(f"存储到Memo0: {stored_count}/{len(knowledge_list)}")
        return stored_count

    async def _update_graph(
        self,
        knowledge_list: List[ExtractedKnowledge]
    ) -> int:
        """更新知识图谱

        Args:
            knowledge_list: 知识列表

        Returns:
            更新的知识数量
        """
        updated_count = 0
        for knowledge in knowledge_list:
            try:
                # 使用Phase 3的图谱动态更新器
                task_id = hashlib.md5(
                    knowledge.knowledge_id.encode()
                ).hexdigest()

                # 根据知识类型确定优先级
                if knowledge.confidence >= 0.8:
                    priority = UpdatePriority.HIGH
                elif knowledge.confidence >= 0.6:
                    priority = UpdatePriority.MEDIUM
                else:
                    priority = UpdatePriority.LOW

                # 创建更新任务
                task = UpdateTask(
                    task_id=task_id,
                    knowledge_data=knowledge.to_dict(),
                    priority=priority,
                    status=UpdateStatus.PENDING,  # 这里需要import
                    created_at=time.time()
                )

                # 执行更新
                success = await self._graph_updater.add_knowledge(
                    knowledge.to_dict(),
                    priority
                )

                if success:
                    updated_count += 1

            except Exception as e:
                logger.error(f"更新知识图谱失败: {e}")
                continue

        logger.debug(f"更新知识图谱: {updated_count}/{len(knowledge_list)}")
        return updated_count

    async def _assess_quality(
        self,
        knowledge_list: List[ExtractedKnowledge]
    ) -> List[QualityScore]:
        """评估知识质量

        Args:
            knowledge_list: 知识列表

        Returns:
            质量评估列表
        """
        assessments = []
        for knowledge in knowledge_list:
            try:
                # 使用Phase 3的质量评估器
                assessment = await self._quality_assessor.assess_knowledge(
                    knowledge.to_dict()
                )
                assessments.append(assessment)

            except Exception as e:
                logger.error(f"质量评估失败: {e}")
                continue

        return assessments

    async def _arbitrage_monitor_loop(self) -> None:
        """套利监控循环

        基于Memo0存储的知识进行低风险套利决策。
        """
        logger.info("启动套利监控循环")

        while True:
            try:
                # 1. 从Memo0检索相关知识
                relevant_knowledge = await self._query_memo0_knowledge()

                # 2. 构建市场上下文
                market_context = await self._build_market_context()

                # 3. 生成套利决策
                decision = await self._make_arbitrage_decision(
                    market_context,
                    relevant_knowledge
                )

                # 4. 执行低风险套利
                if decision and decision.confidence >= 0.7:
                    await self._execute_arbitrage(decision)

                # 更新决策统计
                if decision:
                    self._arbitrage_decisions_made += 1

                # 控制频率
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"套利监控错误: {e}")
                await asyncio.sleep(30)

    async def _query_memo0_knowledge(self) -> List[Dict[str, Any]]:
        """从Memo0查询相关知识

        Returns:
            相关知识列表
        """
        if not self._mem0_storage:
            logger.warning("Memo0未连接，使用本地缓存")
            return [k.to_dict() for k in self._knowledge_cache.values()]

        try:
            # 查询套利相关知识
            results = self._mem0_storage.search_knowledge(
                query="arbitrage opportunity risk",
                top_k=5
            )

            return results

        except Exception as e:
            logger.error(f"Memo0查询失败: {e}")
            return []

    async def _build_market_context(self) -> MarketContext:
        """构建市场上下文

        Returns:
            市场上下文对象
        """
        try:
            # 采集当前市场数据
            price_data = await self._collect_realtime_data()

            if not price_data:
                # 使用默认值
                return MarketContext(
                    timestamp=datetime.now(),
                    symbol="BTC/USDT",
                    price=0.0,
                    volume_24h=0.0,
                    volatility=0.0,
                    trend="sideways",
                    market_regime="stable",
                    technical_indicators={},
                    sentiment_score=0.0,
                    liquidity_score=0.5
                )

            # 构建上下文
            context = MarketContext(
                timestamp=datetime.now(),
                symbol=price_data.symbol,
                price=price_data.data.get('price', 0.0),
                volume_24h=price_data.data.get('volume', 0.0),
                volatility=price_data.data.get('volatility', 0.0),
                trend=self._determine_trend(price_data.data),
                market_regime=self._determine_regime(price_data.data),
                technical_indicators=price_data.data.get('indicators', {}),
                sentiment_score=price_data.data.get('sentiment', 0.0),
                liquidity_score=price_data.data.get('liquidity', 0.5)
            )

            # 缓存上下文
            self._context_cache[context.symbol] = context

            return context

        except Exception as e:
            logger.error(f"构建市场上下文失败: {e}")
            raise

    def _determine_trend(self, data: Dict[str, Any]) -> str:
        """确定趋势"""
        price = data.get('price', 0)
        prev_price = data.get('prev_price', price)
        if price > prev_price * 1.01:
            return "uptrend"
        elif price < prev_price * 0.99:
            return "downtrend"
        else:
            return "sideways"

    def _determine_regime(self, data: Dict[str, Any]) -> str:
        """确定市场制式"""
        volatility = data.get('volatility', 0)
        if volatility < 0.01:
            return "stable"
        elif volatility < 0.03:
            return "volatile"
        else:
            return "highly_volatile"

    async def _make_arbitrage_decision(
        self,
        context: MarketContext,
        knowledge: List[Dict[str, Any]]
    ) -> Optional[ArbitrageDecision]:
        """生成套利决策

        Args:
            context: 市场上下文
            knowledge: 相关知识列表

        Returns:
            套利决策对象
        """
        try:
            # 分析知识
            confidence_sum = sum(k.get('confidence', 0) for k in knowledge)
            avg_confidence = confidence_sum / len(knowledge) if knowledge else 0

            # 评估风险
            risk_level = "LOW"
            if context.volatility > 0.03:
                risk_level = "MEDIUM"
            if context.volatility > 0.05:
                risk_level = "HIGH"

            # 生成决策
            decision = ArbitrageDecision(
                decision_id=f"decision_{int(time.time() * 1000)}",
                opportunity={
                    "symbol": context.symbol,
                    "market_regime": context.market_regime,
                    "trend": context.trend,
                    "volatility": context.volatility
                },
                confidence=avg_confidence,
                risk_level=risk_level,
                recommended_action="ANALYZE" if avg_confidence < 0.7 else "EXECUTE",
                supporting_knowledge=knowledge
            )

            logger.info(f"生成套利决策: {decision.decision_id}, 置信度: {decision.confidence:.2f}")
            return decision

        except Exception as e:
            logger.error(f"生成套利决策失败: {e}")
            return None

    async def _execute_arbitrage(
        self,
        decision: ArbitrageDecision
    ) -> Dict[str, Any]:
        """执行低风险套利

        Args:
            decision: 套利决策

        Returns:
            执行结果
        """
        try:
            # 使用低风险套利引擎
            execution_plan = [
                {"step": 1, "action": "verify_opportunity", "params": decision.opportunity},
                {"step": 2, "action": "check_risk", "params": {"level": decision.risk_level}},
                {"step": 3, "action": "execute_trade", "params": decision.opportunity}
            ]

            result = await self._arbitrage_engine.execute_arbitrage(
                opportunity=decision.opportunity,
                execution_plan=execution_plan
            )

            self._successful_updates += 1

            logger.info(f"执行套利: {decision.decision_id}, 结果: {result.get('status', 'UNKNOWN')}")
            return result

        except Exception as e:
            logger.error(f"执行套利失败: {e}")
            return {"success": False, "error": str(e)}

    async def stop_realtime_integration(self) -> None:
        """停止实时集成"""
        logger.info("停止实时知识更新与Memo0集成")

        try:
            # 停止数据采集
            await self._data_collector.stop_stream()

        except Exception as e:
            logger.error(f"停止数据采集失败: {e}")

    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态

        Returns:
            状态字典
        """
        return {
            "version": self._version,
            "integration_mode": self.integration_mode.value,
            "mem0_connected": self._mem0_storage is not None,
            "total_updates": self._total_updates,
            "successful_updates": self._successful_updates,
            "total_knowledge_stored": self._total_knowledge_stored,
            "arbitrage_decisions_made": self._arbitrage_decisions_made,
            "cache_size": len(self._knowledge_cache),
            "success_rate": (
                self._successful_updates / self._total_updates
                if self._total_updates > 0 else 0
            )
        }

    async def batch_update_knowledge(
        self,
        data_list: List[MarketData]
    ) -> KnowledgeUpdateResult:
        """批量更新知识

        Args:
            data_list: 市场数据列表

        Returns:
            更新结果
        """
        start_time = time.time()

        total_extracted = 0
        total_stored = 0
        total_updated = 0
        total_assessed = 0
        errors = []

        for data in data_list:
            try:
                # 提取知识
                extracted = await self._extract_knowledge(data)
                total_extracted += len(extracted)

                # 存储到Memo0
                stored = await self._store_to_memo0(extracted)
                total_stored += stored

                # 更新图谱
                updated = await self._update_graph(extracted)
                total_updated += updated

                # 质量评估
                assessed = await self._assess_quality(extracted)
                total_assessed += len(assessed)

            except Exception as e:
                error_msg = f"处理数据失败: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        duration_ms = (time.time() - start_time) * 1000

        return KnowledgeUpdateResult(
            success=len(errors) == 0,
            knowledge_count=total_extracted,
            mem0_stored=total_stored,
            graph_updated=total_updated,
            quality_assessed=total_assessed,
            duration_ms=duration_ms,
            errors=errors
        )


# 导入缺失的枚举
from knowledge.graph_dynamic_updater import UpdateStatus


async def main():
    """主函数 - 测试实时知识Memo0集成"""
    print("=" * 80)
    print("实时知识更新系统与Memo0深度集成 V16.0")
    print("=" * 80)
    print("开始时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    try:
        # 创建集成实例
        integration = RealtimeKnowledgeMemo0Integration(
            integration_mode=IntegrationMode.HYBRID,
            config={
                "enable_auto_rollback": True,
                "max_execution_time": 30.0,
                "risk_tolerance": "MEDIUM"
            }
        )

        # 启动集成
        await integration.start_realtime_integration()

    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
        await integration.stop_realtime_integration()
    except Exception as e:
        logger.error(f"主程序错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 打印最终统计
        status = integration.get_integration_status()
        print("\n" + "=" * 80)
        print("集成统计")
        print("=" * 80)
        for key, value in status.items():
            print(f"  {key}: {value}")

        print("\n结束时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
