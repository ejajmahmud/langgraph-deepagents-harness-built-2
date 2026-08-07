"""V16.0 集成测试脚本

测试实时知识更新系统与Memo0深度集成的功能。

测试场景：
1. 模块初始化测试
2. 实时数据采集测试
3. 知识提取测试
4. Memo0存储测试
5. 知识图谱更新测试
6. 质量评估测试
7. 低风险套利决策测试
8. 端到端集成测试
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult:
    """测试结果"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.duration_ms = 0.0
        self.details = ""
        self.errors = []

    def add_result(self, success: bool, detail: str = "", error: str = ""):
        """添加测试结果"""
        self.success = success
        if detail:
            self.details = detail
        if error:
            self.errors.append(error)

    def __str__(self):
        status = "[PASS]" if self.success else "[FAIL]"
        return f"{status} {self.test_name} ({self.duration_ms:.2f}ms)"


async def test_module_initialization() -> TestResult:
    """测试1: 模块初始化"""
    result = TestResult("模块初始化")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.realtime_knowledge_mem0_integration import (
            RealtimeKnowledgeMemo0Integration,
            IntegrationMode
        )
        from storage.mem0_storage import get_mem0_storage

        # 检查Memo0
        mem0_storage = get_mem0_storage()
        result.add_result(
            True,
            f"Memo0状态: {'已连接' if mem0_storage else '本地存储'}"
        )

        # 创建集成实例
        integration = RealtimeKnowledgeMemo0Integration(
            integration_mode=IntegrationMode.BATCH,
            config={"test_mode": True}
        )

        result.add_result(
            True,
            f"集成实例创建成功 (版本: {integration._version})"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_realtime_data_collection() -> TestResult:
    """测试2: 实时数据采集"""
    result = TestResult("实时数据采集")
    start_time = asyncio.get_event_loop().time()

    try:
        from data_collection.real_time_collector import (
            RealTimeDataCollector,
            Exchange,
            DataType
        )

        # 创建采集器
        collector = RealTimeDataCollector()

        # 模拟数据采集
        collected_count = 0
        for exchange in [Exchange.BINANCE, Exchange.OKEX]:
            for data_type in [DataType.PRICE, DataType.VOLUME]:
                try:
                    # 使用模拟数据
                    data = await collector.collect_data(exchange, "BTC/USDT", data_type)
                    if data:
                        collected_count += 1
                except Exception as e:
                    logger.debug(f"采集失败: {e}")
                    continue

        result.add_result(
            collected_count > 0,
            f"成功采集 {collected_count} 条数据"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_knowledge_extraction() -> TestResult:
    """测试3: 知识提取"""
    result = TestResult("知识提取")
    start_time = asyncio.get_event_loop().time()

    try:
        from knowledge_extraction.extraction_engine import KnowledgeExtractionEngine
        from data_collection.real_time_collector import MarketData, Exchange, DataType

        # 创建提取引擎
        extractor = KnowledgeExtractionEngine()

        # 模拟市场数据
        import time
        now = time.time()

        market_data = MarketData(
            exchange=Exchange.BINANCE,
            symbol="BTC/USDT",
            data_type=DataType.PRICE,
            timestamp=now,
            data={
                "price": 65000.0,
                "volume": 1000.0,
                "open": 64800.0,
                "high": 65200.0,
                "low": 64700.0,
                "close": 65000.0
            }
        )

        # 提取知识
        extracted = extractor.extract_from_data([market_data])

        result.add_result(
            len(extracted) > 0,
            f"提取 {len(extracted)} 条知识"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_memo0_storage() -> TestResult:
    """测试4: Memo0存储"""
    result = TestResult("Memo0存储")
    start_time = asyncio.get_event_loop().time()

    try:
        from storage.mem0_storage import get_mem0_storage, load_mem0_config

        # 检查Memo0配置
        config = load_mem0_config()
        result.add_result(
            bool(config.get('api_key')),
            f"API Key: {'已配置' if config.get('api_key') else '未配置'}"
        )

        # 获取存储实例
        storage = get_mem0_storage()

        if storage:
            # 测试添加知识
            success = storage.add_knowledge(
                category="test",
                content="测试知识：V16.0集成成功",
                metadata={"test": True}
            )
            result.add_result(success, "添加测试知识成功")

            # 测试搜索
            if success:
                results = storage.search_knowledge("测试", top_k=1)
                result.add_result(
                    len(results) > 0,
                    f"搜索返回 {len(results)} 条结果"
                )
        else:
            result.add_result(
                False,
                "Memo0未启用，使用本地存储"
            )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_graph_update() -> TestResult:
    """测试5: 知识图谱更新"""
    result = TestResult("知识图谱更新")
    start_time = asyncio.get_event_loop().time()

    try:
        from knowledge.graph_dynamic_updater import (
            GraphDynamicUpdater,
            UpdatePriority
        )

        # 创建更新器
        updater = GraphDynamicUpdater()

        # 模拟更新任务
        test_knowledge = {
            "knowledge_id": "test_001",
            "content": "测试知识：Binance-Okex套利机会",
            "confidence": 0.8
        }

        # 执行更新
        success = await updater.add_knowledge(
            test_knowledge,
            UpdatePriority.HIGH
        )

        result.add_result(
            success,
            f"知识图谱更新: {'成功' if success else '失败'}"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_quality_assessment() -> TestResult:
    """测试6: 质量评估"""
    result = TestResult("质量评估")
    start_time = asyncio.get_event_loop().time()

    try:
        from quality.quality_assessor import QualityAssessor

        # 创建评估器
        assessor = QualityAssessor()

        # 模拟知识数据
        test_knowledge = {
            "content": "测试知识：BTC价格创新高",
            "confidence": 0.75,
            "evidence": ["价格上涨", "成交量放大"],
            "created_at": 1714560000.0,
            "type": "market_pattern"
        }

        # 执行评估
        assessment = await assessor.assess_knowledge(test_knowledge)

        overall_score = assessment.get('overall_score', 0)
        quality_level = assessment.get('quality_level', 'unknown')

        result.add_result(
            overall_score > 60,
            f"总体分数: {overall_score:.2f}, 质量等级: {quality_level}"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_arbitrage_decision() -> TestResult:
    """测试7: 低风险套利决策"""
    result = TestResult("低风险套利决策")
    start_time = asyncio.get_event_loop().time()

    try:
        from strategies.low_risk_arbitrage_engine import LowRiskArbitrageEngine
        from integration.realtime_knowledge_mem0_integration import MarketContext
        from datetime import datetime

        # 创建套利引擎
        engine = LowRiskArbitrageEngine()

        # 模拟套利机会
        opportunity = {
            "symbol": "BTC/USDT",
            "exchange_a": "Binance",
            "exchange_b": "Okex",
            "price_diff": 0.5,
            "potential_profit": 50.0,
            "estimated_time": 2.0
        }

        # 模拟执行计划
        execution_plan = [
            {"step": 1, "action": "verify_opportunity", "params": opportunity},
            {"step": 2, "action": "check_risk", "params": {"level": "LOW"}},
            {"step": 3, "action": "execute_trade", "params": opportunity}
        ]

        # 执行套利
        result = await engine.execute_arbitrage(opportunity, execution_plan)

        status = result.get('status', 'UNKNOWN')
        result.add_result(
            status == 'completed',
            f"套利执行状态: {status}"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_end_to_end_integration() -> TestResult:
    """测试8: 端到端集成"""
    result = TestResult("端到端集成")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.realtime_knowledge_mem0_integration import (
            RealtimeKnowledgeMemo0Integration,
            IntegrationMode
        )

        # 创建完整集成实例
        integration = RealtimeKnowledgeMemo0Integration(
            integration_mode=IntegrationMode.BATCH,
            config={"test_mode": True}
        )

        # 测试批量更新
        from data_collection.real_time_collector import MarketData, Exchange, DataType
        import time

        test_data = [
            MarketData(
                exchange=Exchange.BINANCE,
                symbol="BTC/USDT",
                data_type=DataType.PRICE,
                timestamp=time.time(),
                data={"price": 65000.0, "volume": 1000.0}
            ),
            MarketData(
                exchange=Exchange.OKEX,
                symbol="ETH/USDT",
                data_type=DataType.PRICE,
                timestamp=time.time(),
                data={"price": 3500.0, "volume": 500.0}
            )
        ]

        update_result = await integration.batch_update_knowledge(test_data)

        result.add_result(
            update_result.success,
            f"批量更新: {update_result.knowledge_count} 条知识, "
            f"存储: {update_result.mem0_stored} 条, "
            f"耗时: {update_result.duration_ms:.2f}ms"
        )

        # 获取集成状态
        status = integration.get_integration_status()
        result.add_result(
            status.get('success_rate', 0) > 0,
            f"成功率: {status.get('success_rate', 0)*100:.1f}%, "
            f"总更新: {status.get('total_updates', 0)}"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def run_all_tests() -> None:
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("V16.0 集成测试开始")
    print("=" * 80)
    print("开始时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 测试列表
    tests = [
        ("模块初始化", test_module_initialization),
        ("实时数据采集", test_realtime_data_collection),
        ("知识提取", test_knowledge_extraction),
        ("Memo0存储", test_memo0_storage),
        ("知识图谱更新", test_graph_update),
        ("质量评估", test_quality_assessment),
        ("低风险套利决策", test_arbitrage_decision),
        ("端到端集成", test_end_to_end_integration)
    ]

    # 运行测试
    results = []
    for test_name, test_func in tests:
        print(f"\n运行测试: {test_name}...")
        result = await test_func()
        results.append(result)
        print(result)

        # 小延迟
        await asyncio.sleep(0.1)

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    passed = sum(1 for r in results if r.success)
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    for result in results:
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} {result.test_name} ({result.duration_ms:.2f}ms)")

    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"通过率: {pass_rate:.1f}%")

    if pass_rate >= 80:
        print("\n[SUCCESS] V16.0集成测试通过！系统就绪。")
    else:
        print(f"\n[WARNING] 部分测试失败，通过率 {pass_rate:.1f}%")

    print("结束时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == "__main__":
    asyncio.run(run_all_tests())
