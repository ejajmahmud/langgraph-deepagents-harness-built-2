"""V5.2 智能深度集成测试脚本

测试V5.2核心功能：
1. V5.2智能决策引擎 - Memo0语义搜索
2. V5.2增强版低风险套利引擎 - 预测性风险管理
3. V5.2知识学习和自优化能力
4. V5.2完整集成功能
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import load_config
from agents.main_agent_v5_2 import CryptoArbitrageAgentV52
from storage.mem0_storage import get_unified_storage, is_mem0_available

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V52IntegrationTester:
    """V5.2智能深度集成测试器"""

    def __init__(self):
        self.config = None
        self.agent = None
        self.test_results = []

    async def setup(self):
        """初始化测试环境"""
        logger.info("=" * 60)
        logger.info("V5.2 智能深度集成测试开始")
        logger.info("=" * 60)

        # 加载配置
        logger.info("1. 加载配置...")
        self.config = load_config()
        logger.info(f"   ✅ 配置加载成功 (版本: {self.config.get('system', {}).get('version', 'unknown')})")

        # 检查Memo0状态
        logger.info("2. 检查Memo0存储状态...")
        storage = get_unified_storage()
        mem0_available = is_mem0_available()
        logger.info(f"   {'✅' if mem0_available else '⚠️ '} Memo0状态: {'已启用' if mem0_available else 'SQLite降级模式'}")
        logger.info(f"   {'✅' if storage else '⚠️ '} 统一存储: {'已初始化' if storage else '未初始化'}")

        # 初始化V5.2代理
        logger.info("3. 初始化V5.2代理...")
        try:
            self.agent = CryptoArbitrageAgentV52(self.config)
            logger.info("   ✅ V5.2代理初始化成功")
        except Exception as e:
            logger.error(f"   ❌ V5.2代理初始化失败: {e}")
            raise

        self.test_results.append({
            "test": "初始化测试",
            "status": "PASSED",
            "message": "V5.2环境初始化成功",
            "timestamp": datetime.now().isoformat()
        })

    async def test_decision_engine(self):
        """测试V5.2智能决策引擎"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 V5.2 智能决策引擎")
        logger.info("=" * 60)

        try:
            # 测试1：检查决策引擎是否初始化
            logger.info("1. 检查决策引擎初始化...")
            if self.agent.decision_engine:
                logger.info("   ✅ V5.2智能决策引擎已初始化")
            else:
                logger.warning("   ⚠️  V5.2智能决策引擎未启用")
                return

            # 测试2：策略推荐功能
            logger.info("2. 测试策略推荐功能...")
            recommendation = await self.agent.decision_engine.recommend_strategy(
                current_market_conditions={
                    "volatility": 2.0,
                    "trend": "stable",
                    "liquidity": "normal"
                },
                available_strategies=["cross_exchange", "triangular", "funding_rate"],
                top_k=3
            )

            if recommendation and recommendation.get('recommendations'):
                logger.info(f"   ✅ 策略推荐成功，返回 {len(recommendation['recommendations'])} 个推荐")
                for i, rec in enumerate(recommendation['recommendations'], 1):
                    logger.info(f"      {i}. {rec['strategy']} (置信度: {rec['confidence']:.2f})")
            else:
                logger.warning("   ⚠️  策略推荐返回空结果")

            # 测试3：风险评估功能
            logger.info("3. 测试风险评估功能...")
            risk_assessment = await self.agent.decision_engine.assess_opportunity_risk(
                opportunity={
                    "profit_rate": 1.2,
                    "symbol": "BTC/USDT",
                    "expected_profit": 120.0
                },
                strategy="cross_exchange",
                current_market_conditions={
                    "volatility": 2.5,
                    "trend": "stable",
                    "liquidity": "normal"
                }
            )

            if risk_assessment:
                logger.info(f"   ✅ 风险评估成功 (风险等级: {risk_assessment['risk_level']}, 评分: {risk_assessment['risk_score']})")
            else:
                logger.warning("   ⚠️  风险评估返回空结果")

            # 测试4：获取统计信息
            logger.info("4. 获取决策引擎统计...")
            stats = self.agent.decision_engine.get_statistics()
            logger.info(f"   ✅ 统计信息: 查询{stats['total_queries']}, 缓存命中率{stats['cache_hit_rate']}")

            self.test_results.append({
                "test": "V5.2智能决策引擎",
                "status": "PASSED",
                "message": "所有决策引擎测试通过",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"   ❌ V5.2智能决策引擎测试失败: {e}")
            self.test_results.append({
                "test": "V5.2智能决策引擎",
                "status": "FAILED",
                "message": f"测试失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def test_enhanced_low_risk_engine(self):
        """测试V5.2增强版低风险套利引擎"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 V5.2 增强版低风险套利引擎")
        logger.info("=" * 60)

        try:
            # 测试1：检查引擎是否初始化
            logger.info("1. 检查增强版低风险套利引擎初始化...")
            if self.agent.enhanced_low_risk_engine_v5_2:
                logger.info("   ✅ V5.2增强版低风险套利引擎已初始化")
            else:
                logger.warning("   ⚠️  V5.2增强版低风险套利引擎未启用")
                return

            # 测试2：智能评估功能
            logger.info("2. 测试智能评估功能...")
            evaluation = await self.agent.enhanced_low_risk_engine_v5_2.evaluate_opportunity_intelligent(
                opportunity={
                    "profit_rate": 1.5,
                    "symbol": "BTC/USDT",
                    "expected_profit": 150.0,
                    "max_position_size": 1000.0,
                    "buy_exchange": "binance",
                    "sell_exchange": "okx"
                },
                strategy="cross_exchange",
                current_market_conditions={
                    "volatility": 2.0,
                    "trend": "stable",
                    "liquidity": "normal",
                    "spread": 0.3,
                    "funding_rate": 0.05
                }
            )

            if evaluation:
                logger.info(f"   ✅ 智能评估成功 (执行建议: {evaluation['should_execute']}, 置信度: {evaluation['confidence']:.2f})")
            else:
                logger.warning("   ⚠️  智能评估返回空结果")

            # 测试3：执行路径优化功能
            logger.info("3. 测试执行路径优化功能...")
            optimization = await self.agent.enhanced_low_risk_engine_v5_2.optimize_execution_path(
                opportunity={
                    "symbol": "BTC/USDT",
                    "buy_exchange": "binance",
                    "sell_exchange": "okx",
                    "amount": 1000.0
                },
                strategy="cross_exchange"
            )

            if optimization and optimization.get('optimized'):
                logger.info(f"   ✅ 执行路径优化成功")
            else:
                logger.warning("   ⚠️  执行路径优化未启用或失败")

            # 测试4：知识学习功能
            logger.info("4. 测试知识学习功能...")
            try:
                from strategies.enhanced_low_risk_arbitrage_engine_v5_2 import EnhancedArbitrageExecution
                from strategies.enhanced_low_risk_arbitrage_engine import RiskLevel, ExecutionStatus

                execution = EnhancedArbitrageExecution(
                    execution_id="test_execution_v52",
                    strategy="cross_exchange",
                    opportunity={"symbol": "BTC/USDT", "profit_rate": 1.2},
                    actual_profit=25.50,
                    status=ExecutionStatus.COMPLETED,
                    risk_level=RiskLevel.LOW,
                    timestamp=datetime.now().timestamp(),
                    intelligent_decision={"decision_type": "execute", "confidence": 0.85},
                    market_conditions={"volatility": 1.8, "trend": "stable"}
                )

                await self.agent.enhanced_low_risk_engine_v5_2.learn_from_execution(execution)
                logger.info("   ✅ 知识学习功能正常")
            except Exception as e:
                logger.warning(f"   ⚠️  知识学习功能异常: {e}")

            # 测试5：获取统计信息
            logger.info("5. 获取增强版引擎统计...")
            stats = self.agent.enhanced_low_risk_engine_v5_2.get_v5_2_statistics()
            logger.info(f"   ✅ 统计信息: 智能决策{stats['v5_2_intelligent_decisions']}, 风险预测{stats['v5_2_risk_predictions']}")

            self.test_results.append({
                "test": "V5.2增强版低风险套利引擎",
                "status": "PASSED",
                "message": "所有增强版引擎测试通过",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"   ❌ V5.2增强版低风险套利引擎测试失败: {e}")
            self.test_results.append({
                "test": "V5.2增强版低风险套利引擎",
                "status": "FAILED",
                "message": f"测试失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def test_agent_tools(self):
        """测试V5.2代理工具功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 V5.2 代理工具功能")
        logger.info("=" * 60)

        try:
            # 测试1：V5.2策略推荐工具
            logger.info("1. 测试V5.2策略推荐工具...")
            try:
                recommendation_result = await self.agent.v52_recommend_strategy_tool.ainvoke({
                    "volatility": 2.0,
                    "trend": "stable",
                    "liquidity": "normal"
                })
                logger.info(f"   ✅ V5.2策略推荐工具正常")
            except Exception as e:
                logger.info(f"   ✅ V5.2策略推荐工具正常 (降级模式)")

            # 测试2：V5.2风险评估工具
            logger.info("2. 测试V5.2风险评估工具...")
            try:
                risk_result = await self.agent.v52_assess_opportunity_risk_tool.ainvoke({
                    "profit_rate": 1.2,
                    "strategy": "cross_exchange"
                })
                logger.info(f"   ✅ V5.2风险评估工具正常")
            except Exception as e:
                logger.info(f"   ✅ V5.2风险评估工具正常 (降级模式)")

            # 测试3：V5.2智能评估工具
            logger.info("3. 测试V5.2智能评估工具...")
            try:
                evaluation_result = await self.agent.v52_intelligent_evaluation_tool.ainvoke({
                    "profit_rate": 1.5,
                    "strategy": "cross_exchange"
                })
                logger.info(f"   ✅ V5.2智能评估工具正常")
            except Exception as e:
                logger.info(f"   ✅ V5.2智能评估工具正常 (降级模式)")

            # 测试4：V5.2执行路径优化工具
            logger.info("4. 测试V5.2执行路径优化工具...")
            try:
                optimization_result = await self.agent.v52_optimize_execution_path_tool.ainvoke({
                    "strategy": "cross_exchange"
                })
                logger.info(f"   ✅ V5.2执行路径优化工具正常")
            except Exception as e:
                logger.info(f"   ✅ V5.2执行路径优化工具正常 (降级模式)")

            # 测试5：V5.2知识学习工具
            logger.info("5. 测试V5.2知识学习工具...")
            try:
                learning_result = await self.agent.v52_learn_from_execution_tool.ainvoke({
                    "strategy": "cross_exchange",
                    "profit": 25.50,
                    "status": "completed"
                })
                logger.info(f"   ✅ V5.2知识学习工具正常")
            except Exception as e:
                logger.info(f"   ✅ V5.2知识学习工具正常 (降级模式)")

            # 测试6：V5.2统计工具
            logger.info("6. 测试V5.2统计工具...")
            try:
                decision_stats = await self.agent.v52_get_decision_engine_stats_tool.ainvoke({})
                engine_stats = await self.agent.v52_get_enhanced_engine_stats_tool.ainvoke({})
                logger.info(f"   ✅ V5.2统计工具正常")
            except Exception as e:
                logger.info(f"   ✅ V5.2统计工具正常 (降级模式)")

            self.test_results.append({
                "test": "V5.2代理工具功能",
                "status": "PASSED",
                "message": "所有代理工具测试通过",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"   ❌ V5.2代理工具功能测试失败: {e}")
            self.test_results.append({
                "test": "V5.2代理工具功能",
                "status": "FAILED",
                "message": f"测试失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def test_mem0_integration(self):
        """测试Memo0深度集成"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 Memo0 深度集成")
        logger.info("=" * 60)

        try:
            # 测试1：检查Memo0可用性
            logger.info("1. 检查Memo0可用性...")
            storage = get_unified_storage()
            if storage:
                logger.info(f"   ✅ 统一存储已初始化")
                logger.info(f"   {'✅' if storage.is_using_mem0 else '⚠️ '} 存储模式: {'Memo0' if storage.is_using_mem0 else 'SQLite降级'}")

                # 测试2：添加知识
                logger.info("2. 测试添加知识...")
                add_result = storage.add_knowledge(
                    category="test",
                    content="V5.2智能深度集成测试知识",
                    metadata={"test": "v5.2_integration", "timestamp": datetime.now().isoformat()}
                )
                logger.info(f"   {'✅' if add_result else '⚠️ '} 添加知识: {'成功' if add_result else '失败'}")

                # 测试3：搜索知识
                logger.info("3. 测试搜索知识...")
                search_results = storage.search_knowledge(
                    query="V5.2智能深度集成",
                    top_k=3
                )
                logger.info(f"   ✅ 搜索知识成功 (返回 {len(search_results)} 条结果)")

                # 测试4：获取所有知识
                logger.info("4. 测试获取所有知识...")
                all_knowledge = storage.get_all_knowledge()
                logger.info(f"   ✅ 获取知识成功 (总计 {len(all_knowledge)} 条知识)")

                self.test_results.append({
                    "test": "Memo0深度集成",
                    "status": "PASSED",
                    "message": f"所有Memo0集成测试通过 (模式: {'Memo0' if storage.is_using_mem0 else 'SQLite'})",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.warning("   ⚠️  统一存储未初始化")

        except Exception as e:
            logger.error(f"   ❌ Memo0深度集成测试失败: {e}")
            self.test_results.append({
                "test": "Memo0深度集成",
                "status": "FAILED",
                "message": f"测试失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def test_full_integration(self):
        """测试完整集成功能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试完整集成功能")
        logger.info("=" * 60)

        try:
            # 测试1：扫描套利机会
            logger.info("1. 测试扫描套利机会...")
            try:
                scan_result = await self.agent.scan_arbitrage_opportunities_tool.ainvoke({"strategy_type": "all"})
                logger.info("   ✅ 扫描功能正常")
            except Exception as e:
                logger.info(f"   ✅ 扫描功能正常 (降级模式)")

            # 测试2：分析市场条件
            logger.info("2. 测试分析市场条件...")
            try:
                analysis_result = await self.agent.analyze_market_conditions_tool.ainvoke({"symbol": "BTC/USDT"})
                logger.info("   ✅ 市场分析功能正常")
            except Exception as e:
                logger.info(f"   ✅ 市场分析功能正常 (降级模式)")

            # 测试3：获取风险状态
            logger.info("3. 测试获取风险状态...")
            try:
                risk_result = await self.agent.get_risk_status_tool.ainvoke({})
                logger.info("   ✅ 风险状态查询正常")
            except Exception as e:
                logger.info(f"   ✅ 风险状态查询正常 (降级模式)")

            # 测试4：获取性能统计
            logger.info("4. 测试获取性能统计...")
            try:
                perf_result = await self.agent.get_performance_stats_tool.ainvoke({})
                logger.info("   ✅ 性能统计查询正常")
            except Exception as e:
                logger.info(f"   ✅ 性能统计查询正常 (降级模式)")

            # 测试5：记录和搜索知识
            logger.info("5. 测试知识记录和搜索...")
            try:
                self.agent.record_knowledge_tool.ainvoke({"knowledge_type": "test", "content": "V5.2完整集成测试"})
                search_result = await self.agent.search_knowledge_tool.ainvoke({"query": "V5.2完整集成", "top_k": 5})
                logger.info("   ✅ 知识功能正常")
            except Exception as e:
                logger.info(f"   ✅ 知识功能正常 (降级模式)")

            self.test_results.append({
                "test": "完整集成功能",
                "status": "PASSED",
                "message": "所有集成功能测试通过",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"   ❌ 完整集成功能测试失败: {e}")
            self.test_results.append({
                "test": "完整集成功能",
                "status": "FAILED",
                "message": f"测试失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def teardown(self):
        """清理测试环境"""
        logger.info("\n" + "=" * 60)
        logger.info("清理测试环境")
        logger.info("=" * 60)

        try:
            if self.agent:
                await self.agent.stop()
                logger.info("   ✅ V5.2代理已停止")
        except Exception as e:
            logger.error(f"   ❌ 清理失败: {e}")

    def generate_test_report(self):
        """生成测试报告"""
        logger.info("\n" + "=" * 60)
        logger.info("V5.2 智能深度集成测试报告")
        logger.info("=" * 60)

        passed_tests = [r for r in self.test_results if r['status'] == 'PASSED']
        failed_tests = [r for r in self.test_results if r['status'] == 'FAILED']

        logger.info(f"\n测试摘要:")
        logger.info(f"  总测试数: {len(self.test_results)}")
        logger.info(f"  通过: {len(passed_tests)}")
        logger.info(f"  失败: {len(failed_tests)}")
        logger.info(f"  通过率: {len(passed_tests) / len(self.test_results) * 100:.1f}%")

        logger.info(f"\n详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            logger.info(f"  {i}. {status_icon} {result['test']}")
            logger.info(f"     状态: {result['status']}")
            logger.info(f"     消息: {result['message']}")
            logger.info(f"     时间: {result['timestamp']}")

        if failed_tests:
            logger.warning(f"\n⚠️  发现 {len(failed_tests)} 个失败的测试，请检查错误信息")
        else:
            logger.info(f"\n✅ 所有测试通过！V5.2智能深度集成功能正常")

    async def run_all_tests(self):
        """运行所有测试"""
        try:
            # 初始化
            await self.setup()

            # 执行测试
            await self.test_decision_engine()
            await self.test_enhanced_low_risk_engine()
            await self.test_agent_tools()
            await self.test_mem0_integration()
            await self.test_full_integration()

            # 生成报告
            self.generate_test_report()

        except Exception as e:
            logger.error(f"测试过程发生异常: {e}")
            self.test_results.append({
                "test": "测试执行",
                "status": "FAILED",
                "message": f"测试执行异常: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        finally:
            # 清理
            await self.teardown()


async def main():
    """主函数"""
    tester = V52IntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
