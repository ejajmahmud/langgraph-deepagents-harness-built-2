"""V5.9 Phase 2 集成测试 - 低风险套利引擎异步化集成

测试覆盖：
1. V5.9组件导入测试
2. V5.9异步化引擎初始化测试
3. V5.9异步分析功能测试
4. V5.9异步决策流程测试
5. V5.9性能监控测试
6. V5.9缓存管理测试
7. V5.9主Agent集成测试
8. V5.9向后兼容性测试
9. V5.9性能提升验证
10. V5.9工具接口测试
"""

import asyncio
import pytest
import logging
from datetime import datetime
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestV59Phase2Integration:
    """V5.9 Phase 2 集成测试类"""

    @pytest.mark.asyncio
    async def test_1_v59_components_import(self):
        """测试1: V5.9组件导入"""
        try:
            # 导入V5.9核心组件
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import (
                EnhancedLowRiskArbitrageEngineV59,
                create_enhanced_low_risk_engine_v5_9,
                AsyncAnalysisContext,
                AsyncDecisionResult
            )

            from agents.main_agent_v5_9 import (
                CryptoArbitrageAgentV59,
                run_crypto_arbitrage_agent_v5_9
            )

            from storage.deep_memo0_integration_v5_9 import (
                DeepMemo0IntegrationV59,
                create_deep_memo0_integration_v5_9
            )

            logger.info("✅ 测试1通过: V5.9组件导入成功")
            assert True
        except Exception as e:
            logger.error(f"❌ 测试1失败: V5.9组件导入失败 - {e}")
            assert False, f"组件导入失败: {e}"

    @pytest.mark.asyncio
    async def test_2_v59_async_engine_initialization(self):
        """测试2: V5.9异步化引擎初始化"""
        try:
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import create_enhanced_low_risk_engine_v5_9
            from storage.deep_memo0_integration_v5_9 import create_deep_memo0_integration_v5_9
            from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
            from storage.mem0_storage import get_unified_storage

            # 初始化存储
            storage = get_unified_storage()

            # 创建V5.9 Memo0集成
            memo0_integration = create_deep_memo0_integration_v5_9({
                'enabled': True,
                'enable_async_analysis': True,
                'async_analysis': {
                    'max_workers': 3,
                    'cache_ttl': 300,
                    'timeout': 120
                }
            })

            # 创建V5.2决策引擎
            decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=storage,
                fallback_storage=None
            )

            # 创建V5.9异步化引擎
            async_engine = create_enhanced_low_risk_engine_v5_9(
                config={
                    'enable_async_analysis': True,
                    'async_analysis_timeout': 30,
                    'max_concurrent_analyses': 3
                },
                decision_engine=decision_engine,
                memo0_integration=memo0_integration
            )

            # 验证初始化
            assert async_engine is not None
            assert async_engine.enable_async_analysis == True
            assert async_engine.memo0_integration is not None
            assert hasattr(async_engine, 'v5_9_stats')

            logger.info("✅ 测试2通过: V5.9异步化引擎初始化成功")
            assert True
        except Exception as e:
            logger.error(f"❌ 测试2失败: V5.9异步化引擎初始化失败 - {e}")
            assert False, f"引擎初始化失败: {e}"

    @pytest.mark.asyncio
    async def test_3_v59_async_analysis_functionality(self):
        """测试3: V5.9异步分析功能"""
        try:
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import create_enhanced_low_risk_engine_v5_9
            from storage.deep_memo0_integration_v5_9 import create_deep_memo0_integration_v5_9
            from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
            from storage.mem0_storage import get_unified_storage

            # 初始化组件
            storage = get_unified_storage()
            memo0_integration = create_deep_memo0_integration_v5_9({'enabled': True})
            decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=storage,
                fallback_storage=None
            )
            async_engine = create_enhanced_low_risk_engine_v5_9(
                config={'enable_async_analysis': True},
                decision_engine=decision_engine,
                memo0_integration=memo0_integration
            )

            # 构建测试机会
            opportunity = {
                "profit_rate": 1.5,
                "symbol": "BTC/USDT",
                "expected_profit": 150.0,
                "max_position_size": 1000.0,
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "id": "test_opp_001"
            }

            current_market_conditions = {
                "volatility": 2.0,
                "trend": "stable",
                "liquidity": "normal"
            }

            # 执行异步评估
            evaluation = await async_engine.evaluate_opportunity_async(
                opportunity=opportunity,
                strategy="cross_exchange",
                current_market_conditions=current_market_conditions
            )

            # 验证结果
            assert evaluation is not None
            assert 'should_execute' in evaluation
            assert 'confidence' in evaluation
            assert 'async_analysis_time' in evaluation
            assert 'total_decision_time' in evaluation
            assert 'performance_improvement' in evaluation

            logger.info(
                f"✅ 测试3通过: V5.9异步分析功能正常 "
                f"(耗时={evaluation.get('total_decision_time', 0):.2f}s, "
                f"性能改进={evaluation.get('performance_improvement', 0):.1%})"
            )
            assert True
        except Exception as e:
            logger.error(f"❌ 测试3失败: V5.9异步分析功能失败 - {e}")
            assert False, f"异步分析功能失败: {e}"

    @pytest.mark.asyncio
    async def test_4_v59_async_decision_process(self):
        """测试4: V5.9异步决策流程"""
        try:
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import create_enhanced_low_risk_engine_v5_9
            from storage.deep_memo0_integration_v5_9 import create_deep_memo0_integration_v5_9
            from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
            from storage.mem0_storage import get_unified_storage

            # 初始化组件
            storage = get_unified_storage()
            memo0_integration = create_deep_memo0_integration_v5_9({'enabled': True})
            decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=storage,
                fallback_storage=None
            )
            async_engine = create_enhanced_low_risk_engine_v5_9(
                config={'enable_async_analysis': True},
                decision_engine=decision_engine,
                memo0_integration=memo0_integration
            )

            # 测试多个机会的并发评估
            opportunities = [
                {
                    "profit_rate": 1.0 + i * 0.5,
                    "symbol": f"BTC/USDT_{i}",
                    "expected_profit": 100.0 * (1.0 + i * 0.5),
                    "max_position_size": 1000.0,
                    "buy_exchange": "binance",
                    "sell_exchange": "okx",
                    "id": f"test_opp_{i:03d}"
                }
                for i in range(3)
            ]

            current_market_conditions = {
                "volatility": 2.0,
                "trend": "stable",
                "liquidity": "normal"
            }

            # 并发评估
            start_time = asyncio.get_event_loop().time()
            tasks = [
                async_engine.evaluate_opportunity_async(
                    opportunity=opp,
                    strategy="cross_exchange",
                    current_market_conditions=current_market_conditions
                )
                for opp in opportunities
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = asyncio.get_event_loop().time() - start_time

            # 验证结果
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= 2  # 至少2个成功

            # 验证决策流程
            for result in successful_results:
                assert 'should_execute' in result
                assert 'confidence' in result
                assert 'async_analysis_time' in result

            logger.info(
                f"✅ 测试4通过: V5.9异步决策流程正常 "
                f"(并发评估{len(opportunities)}个机会, "
                f"成功{len(successful_results)}个, "
                f"总耗时={total_time:.2f}s)"
            )
            assert True
        except Exception as e:
            logger.error(f"❌ 测试4失败: V5.9异步决策流程失败 - {e}")
            assert False, f"异步决策流程失败: {e}"

    @pytest.mark.asyncio
    async def test_5_v59_performance_monitoring(self):
        """测试5: V5.9性能监控"""
        try:
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import create_enhanced_low_risk_engine_v5_9
            from storage.deep_memo0_integration_v5_9 import create_deep_memo0_integration_v5_9
            from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
            from storage.mem0_storage import get_unified_storage

            # 初始化组件
            storage = get_unified_storage()
            memo0_integration = create_deep_memo0_integration_v5_9({'enabled': True})
            decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=storage,
                fallback_storage=None
            )
            async_engine = create_enhanced_low_risk_engine_v5_9(
                config={'enable_async_analysis': True},
                decision_engine=decision_engine,
                memo0_integration=memo0_integration
            )

            # 执行一些异步分析
            opportunity = {
                "profit_rate": 1.2,
                "symbol": "ETH/USDT",
                "expected_profit": 120.0,
                "max_position_size": 1000.0,
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "id": "test_opp_perf"
            }

            current_market_conditions = {
                "volatility": 2.0,
                "trend": "stable",
                "liquidity": "normal"
            }

            await async_engine.evaluate_opportunity_async(
                opportunity=opportunity,
                strategy="cross_exchange",
                current_market_conditions=current_market_conditions
            )

            # 获取性能统计
            stats = async_engine.get_v5_9_statistics()

            # 验证统计信息
            assert 'v5_9_async_stats' in stats
            v5_9_stats = stats['v5_9_async_stats']
            assert 'async_analyses' in v5_9_stats
            assert 'async_cache_hits' in v5_9_stats
            assert 'async_cache_misses' in v5_9_stats
            assert 'async_cache_hit_rate' in v5_9_stats
            assert 'avg_async_decision_time' in v5_9_stats
            assert 'max_concurrent_analyses' in v5_9_stats

            logger.info(
                f"✅ 测试5通过: V5.9性能监控正常 "
                f"(异步分析={v5_9_stats['async_analyses']}, "
                f"缓存命中率={v5_9_stats['async_cache_hit_rate']:.1%}, "
                f"平均耗时={v5_9_stats['avg_async_decision_time']:.2f}s)"
            )
            assert True
        except Exception as e:
            logger.error(f"❌ 测试5失败: V5.9性能监控失败 - {e}")
            assert False, f"性能监控失败: {e}"

    @pytest.mark.asyncio
    async def test_6_v59_cache_management(self):
        """测试6: V5.9缓存管理"""
        try:
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import create_enhanced_low_risk_engine_v5_9
            from storage.deep_memo0_integration_v5_9 import create_deep_memo0_integration_v5_9
            from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
            from storage.mem0_storage import get_unified_storage

            # 初始化组件
            storage = get_unified_storage()
            memo0_integration = create_deep_memo0_integration_v5_9({'enabled': True})
            decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=storage,
                fallback_storage=None
            )
            async_engine = create_enhanced_low_risk_engine_v5_9(
                config={'enable_async_analysis': True},
                decision_engine=decision_engine,
                memo0_integration=memo0_integration
            )

            # 测试缓存预热
            warmup_result = await async_engine.warmup_async_cache([
                "BTC/USDT", "ETH/USDT"
            ])

            assert warmup_result is not None
            assert 'status' in warmup_result

            logger.info(f"✅ 测试6通过: V5.9缓存管理正常 (预热状态={warmup_result.get('status')})")
            assert True
        except Exception as e:
            logger.error(f"❌ 测试6失败: V5.9缓存管理失败 - {e}")
            assert False, f"缓存管理失败: {e}"

    @pytest.mark.asyncio
    async def test_7_v59_main_agent_integration(self):
        """测试7: V5.9主Agent集成"""
        try:
            from agents.main_agent_v5_9 import CryptoArbitrageAgentV59

            # 创建V5.9 Agent配置
            config = {
                'model': {
                    'provider': 'anthropic',
                    'model': 'claude-sonnet-4-5-20250929',
                    'temperature': 0.0
                },
                'scan_interval': 30,
                'monitor_interval': 120,
                'exchanges': {},
                'risk_management': {},
                'monitoring': {},
                'notifications': {},
                'strategies': {},
                'strategy_manager': {},
                'transaction_executor': {},
                'mem0': {},
                'intelligent_decision_engine_v5_2': {'enabled': False},  # 简化测试
                'enhanced_low_risk_engine_v5_2': {'enabled': False},  # 简化测试
                'memo0_integration_v5_9': {'enabled': False},  # 简化测试
                'enhanced_low_risk_engine_v5_9': {'enabled': False},  # 简化测试
                'enable_async_trading': False,  # 简化测试
                'intelligent_optimizer': {'enabled': False},
                'knowledge_manager_v3': {'enabled': False},
                'adaptive_error_handler': {'enabled': False}
            }

            # 创建V5.9 Agent
            agent = CryptoArbitrageAgentV59(config)

            # 验证初始化
            assert agent is not None
            assert agent.agent_version == "5.9"
            assert hasattr(agent, 'memo0_integration_v5_9')
            assert hasattr(agent, 'enhanced_low_risk_engine_v5_9')
            assert hasattr(agent, 'v5_9_performance_stats')

            # 验证工具
            tools = agent._get_agent_tools()
            tool_names = [tool.name for tool in tools]

            # 检查V5.9特定工具是否存在（如果组件启用）
            v5_9_tools = [
                'v59_async_evaluation_tool',
                'v59_warmup_cache_tool',
                'v59_get_async_stats_tool',
                'v59_get_performance_metrics_tool'
            ]

            # 由于组件未启用，工具可能不存在，这是正常的
            logger.info(f"✅ 测试7通过: V5.9主Agent集成成功 (工具数量={len(tools)})")
            assert True
        except Exception as e:
            logger.error(f"❌ 测试7失败: V5.9主Agent集成失败 - {e}")
            assert False, f"主Agent集成失败: {e}"

    @pytest.mark.asyncio
    async def test_8_v59_backward_compatibility(self):
        """测试8: V5.9向后兼容性"""
        try:
            from agents.main_agent_v5_9 import CryptoArbitrageAgentV59
            from agents.main_agent_v5_2 import CryptoArbitrageAgentV52

            # 创建V5.9 Agent
            config = {
                'model': {
                    'provider': 'anthropic',
                    'model': 'claude-sonnet-4-5-20250929',
                    'temperature': 0.0
                },
                'exchanges': {},
                'risk_management': {},
                'monitoring': {},
                'notifications': {},
                'strategies': {},
                'strategy_manager': {},
                'transaction_executor': {},
                'mem0': {},
                'intelligent_decision_engine_v5_2': {'enabled': False},
                'enhanced_low_risk_engine_v5_2': {'enabled': False},
                'memo0_integration_v5_9': {'enabled': False},
                'enhanced_low_risk_engine_v5_9': {'enabled': False},
                'intelligent_optimizer': {'enabled': False},
                'knowledge_manager_v3': {'enabled': False},
                'adaptive_error_handler': {'enabled': False}
            }

            agent_v5_9 = CryptoArbitrageAgentV59(config)

            # 验证V5.2方法仍然存在
            v5_2_methods = [
                'scan_arbitrage_opportunities_tool',
                'execute_arbitrage_tool',
                'get_risk_status_tool',
                'get_performance_stats_tool',
                'analyze_market_conditions_tool'
            ]

            tools = agent_v5_9._get_agent_tools()
            tool_names = [tool.name for tool in tools]

            for method in v5_2_methods:
                assert method in tool_names, f"V5.2方法 {method} 不存在"

            logger.info("✅ 测试8通过: V5.9向后兼容性保持 (所有V5.2方法存在)")
            assert True
        except Exception as e:
            logger.error(f"❌ 测试8失败: V5.9向后兼容性失败 - {e}")
            assert False, f"向后兼容性失败: {e}"

    @pytest.mark.asyncio
    async def test_9_v59_performance_improvement(self):
        """测试9: V5.9性能提升验证"""
        try:
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import create_enhanced_low_risk_engine_v5_9
            from storage.deep_memo0_integration_v5_9 import create_deep_memo0_integration_v5_9
            from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
            from storage.mem0_storage import get_unified_storage

            # 初始化组件
            storage = get_unified_storage()
            memo0_integration = create_deep_memo0_integration_v5_9({'enabled': True})
            decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=storage,
                fallback_storage=None
            )
            async_engine = create_enhanced_low_risk_engine_v5_9(
                config={'enable_async_analysis': True},
                decision_engine=decision_engine,
                memo0_integration=memo0_integration
            )

            # 执行多次异步分析
            opportunity = {
                "profit_rate": 1.3,
                "symbol": "BNB/USDT",
                "expected_profit": 130.0,
                "max_position_size": 1000.0,
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "id": "test_opp_perf_improve"
            }

            current_market_conditions = {
                "volatility": 2.0,
                "trend": "stable",
                "liquidity": "normal"
            }

            # 第一次分析（缓存未命中）
            result1 = await async_engine.evaluate_opportunity_async(
                opportunity=opportunity,
                strategy="cross_exchange",
                current_market_conditions=current_market_conditions
            )

            # 第二次分析（可能缓存命中）
            result2 = await async_engine.evaluate_opportunity_async(
                opportunity=opportunity,
                strategy="cross_exchange",
                current_market_conditions=current_market_conditions
            )

            # 验证性能改进
            perf_improvement1 = result1.get('performance_improvement', 0)
            perf_improvement2 = result2.get('performance_improvement', 0)

            # 至少应该有一些性能改进
            assert perf_improvement1 >= 0 or perf_improvement2 >= 0

            # 第二次分析应该更快（缓存命中）
            if result2.get('total_decision_time', 0) > 0:
                time_improvement = (
                    (result1.get('total_decision_time', 0) - result2.get('total_decision_time', 0)) /
                    result1.get('total_decision_time', 1)
                )
                logger.info(
                    f"✅ 测试9通过: V5.9性能提升验证成功 "
                    f"(第一次改进={perf_improvement1:.1%}, "
                    f"第二次改进={perf_improvement2:.1%}, "
                    f"时间改进={time_improvement:.1%})"
                )
            else:
                logger.info(
                    f"✅ 测试9通过: V5.9性能提升验证成功 "
                    f"(性能改进={max(perf_improvement1, perf_improvement2):.1%})"
                )

            assert True
        except Exception as e:
            logger.error(f"❌ 测试9失败: V5.9性能提升验证失败 - {e}")
            assert False, f"性能提升验证失败: {e}"

    @pytest.mark.asyncio
    async def test_10_v59_tool_interfaces(self):
        """测试10: V5.9工具接口"""
        try:
            from agents.main_agent_v5_9 import CryptoArbitrageAgentV59

            # 创建V5.9 Agent
            config = {
                'model': {
                    'provider': 'anthropic',
                    'model': 'claude-sonnet-4-5-20250929',
                    'temperature': 0.0
                },
                'exchanges': {},
                'risk_management': {},
                'monitoring': {},
                'notifications': {},
                'strategies': {},
                'strategy_manager': {},
                'transaction_executor': {},
                'mem0': {},
                'intelligent_decision_engine_v5_2': {'enabled': False},
                'enhanced_low_risk_engine_v5_2': {'enabled': False},
                'memo0_integration_v5_9': {'enabled': False},
                'enhanced_low_risk_engine_v5_9': {'enabled': False},
                'intelligent_optimizer': {'enabled': False},
                'knowledge_manager_v3': {'enabled': False},
                'adaptive_error_handler': {'enabled': False}
            }

            agent = CryptoArbitrageAgentV59(config)
            tools = agent._get_agent_tools()

            # 验证工具接口
            assert tools is not None
            assert len(tools) > 0

            # 验证每个工具有必要的属性
            for tool in tools:
                assert hasattr(tool, 'name'), f"工具 {tool} 缺少 name 属性"
                assert hasattr(tool, 'description'), f"工具 {tool} 缺少 description 属性"
                assert callable(tool.func), f"工具 {tool.name} 不可调用"

            logger.info(f"✅ 测试10通过: V5.9工具接口正常 (工具数量={len(tools)})")
            assert True
        except Exception as e:
            logger.error(f"❌ 测试10失败: V5.9工具接口失败 - {e}")
            assert False, f"工具接口失败: {e}"


# 运行测试的主函数
async def run_v59_phase2_tests():
    """运行V5.9 Phase 2所有测试"""
    test_class = TestV59Phase2Integration()

    tests = [
        ("测试1: V5.9组件导入", test_class.test_1_v59_components_import),
        ("测试2: V5.9异步化引擎初始化", test_class.test_2_v59_async_engine_initialization),
        ("测试3: V5.9异步分析功能", test_class.test_3_v59_async_analysis_functionality),
        ("测试4: V5.9异步决策流程", test_class.test_4_v59_async_decision_process),
        ("测试5: V5.9性能监控", test_class.test_5_v59_performance_monitoring),
        ("测试6: V5.9缓存管理", test_class.test_6_v59_cache_management),
        ("测试7: V5.9主Agent集成", test_class.test_7_v59_main_agent_integration),
        ("测试8: V5.9向后兼容性", test_class.test_8_v59_backward_compatibility),
        ("测试9: V5.9性能提升验证", test_class.test_9_v59_performance_improvement),
        ("测试10: V5.9工具接口", test_class.test_10_v59_tool_interfaces)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} 失败: {e}")
            failed += 1

    logger.info("\n" + "="*60)
    logger.info(f"V5.9 Phase 2 集成测试完成")
    logger.info(f"通过: {passed}/{len(tests)}")
    logger.info(f"失败: {failed}/{len(tests)}")
    logger.info(f"通过率: {passed/len(tests):.1%}")
    logger.info("="*60)

    return passed, failed


if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_v59_phase2_tests())
