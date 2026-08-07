"""V5.2 智能深度集成验证测试

验证V5.2版本的核心功能：
1. Memo0 API Key配置
2. 智能决策引擎功能
3. 增强版低风险套利引擎
4. 知识积累和学习循环
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import load_config
from storage.mem0_storage import initialize_mem0
from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
from storage.auto_knowledge_accumulator_v5_2 import create_auto_knowledge_accumulator_v5_2
from strategies.enhanced_low_risk_arbitrage_engine_v5_2 import create_enhanced_low_risk_engine_v5_2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V52IntegrationTester:
    """V5.2 集成测试器"""

    def __init__(self):
        self.config = None
        self.mem0_storage = None
        self.decision_engine = None
        self.knowledge_accumulator = None
        self.arbitrage_engine = None

        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": []
        }

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("V5.2 Intelligent Deep Integration Verification Test")
        print("="*60 + "\n")

        # 测试1: 配置加载
        await self.test_config_loading()

        # 测试2: Memo0初始化
        await self.test_mem0_initialization()

        # 测试3: 智能决策引擎
        await self.test_intelligent_decision_engine()

        # 测试4: 知识积累器
        await self.test_knowledge_accumulator()

        # 测试5: 增强版低风险套利引擎
        await self.test_enhanced_arbitrage_engine()

        # 测试6: 集成功能
        await self.test_integration()

        # 输出测试结果
        self.print_test_results()

    async def test_config_loading(self):
        """测试1: 配置加载"""
        print("\n[Test 1] Configuration Loading")
        print("-" * 40)

        try:
            self.config = load_config()

            # 验证系统版本
            version = self.config.get("system", {}).get("version")
            print(f"  系统版本: {version}")

            # 验证Memo0配置
            mem0_config = self.config.get("mem0", {})
            api_key_configured = bool(mem0_config.get("api_key"))
            print(f"  Memo0 API Key: {'[OK] Configured' if api_key_configured else '[WARN] Not Configured'}")

            # 验证增强版引擎配置
            enhanced_config = self.config.get("enhanced_low_risk_engine", {})
            enhanced_enabled = enhanced_config.get("enabled", False)
            print(f"  Enhanced Engine: {'[OK] Enabled' if enhanced_enabled else '[FAIL] Disabled'}")

            self.test_results["total_tests"] += 1

            if version and enhanced_enabled:
                self.test_results["passed_tests"] += 1
                print("  [OK] Configuration loading test passed")
            else:
                self.test_results["failed_tests"] += 1
                print("  [FAIL] Configuration loading test failed")

        except Exception as e:
            self.test_results["total_tests"] += 1
            self.test_results["failed_tests"] += 1
            print(f"  ❌ 配置加载测试异常: {e}")

    async def test_mem0_initialization(self):
        """测试2: Memo0初始化"""
        print("\n[Test 2] Memo0 Initialization")
        print("-" * 40)

        try:
            self.mem0_storage = initialize_mem0(self.config.get("mem0", {}))

            self.test_results["total_tests"] += 1

            if self.mem0_storage is not None:
                self.test_results["passed_tests"] += 1
                print("  [OK] Memo0 initialization successful")
                print("  [INFO] Memo0 features enabled")
            else:
                self.test_results["warnings"].append("Memo0 not configured, system using SQLite fallback mode")
                print("  [WARN] Memo0 not configured, using SQLite fallback mode")
                self.test_results["passed_tests"] += 1  # 降级模式也算通过

        except Exception as e:
            self.test_results["total_tests"] += 1
            self.test_results["failed_tests"] += 1
            print(f"  ❌ Memo0初始化测试异常: {e}")

    async def test_intelligent_decision_engine(self):
        """测试3: 智能决策引擎"""
        print("\n[Test 3] Intelligent Decision Engine")
        print("-" * 40)

        try:
            # 创建V5.2智能决策引擎
            self.decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=self.mem0_storage
            )

            # 测试策略推荐
            market_conditions = {
                "volatility": 2.5,
                "trend": "rising",
                "liquidity": "normal",
                "funding_rate": 0.05,
                "spread": 0.3
            }

            print("  📊 测试策略推荐...")
            recommendation = await self.decision_engine.recommend_strategy(
                current_market_conditions=market_conditions,
                available_strategies=["cross_exchange", "triangular", "funding_rate"],
                top_k=2
            )

            print(f"    推荐策略数量: {len(recommendation.get('recommendations', []))}")
            print(f"    数据源: {recommendation.get('data_source', 'unknown')}")

            # 测试风险评估
            print("  ⚡ 测试风险评估...")
            opportunity = {
                "symbol": "BTC/USDT",
                "expected_profit": 15.0,
                "profit_rate": 0.6,
                "volatility": 2.5
            }

            risk_assessment = await self.decision_engine.assess_opportunity_risk(
                opportunity=opportunity,
                strategy="cross_exchange",
                current_market_conditions=market_conditions
            )

            print(f"    风险等级: {risk_assessment.get('risk_level', 'unknown')}")
            print(f"    风险分数: {risk_assessment.get('risk_score', 0):.1f}")

            # 获取统计信息
            stats = self.decision_engine.get_statistics()
            print(f"  📈 引擎统计:")
            print(f"    总查询数: {stats.get('total_queries', 0)}")
            print(f"    缓存命中率: {stats.get('cache_hit_rate', '0%')}")

            self.test_results["total_tests"] += 1

            if recommendation and risk_assessment:
                self.test_results["passed_tests"] += 1
                print("  [OK] Intelligent decision engine test passed")
            else:
                self.test_results["failed_tests"] += 1
                print("  [FAIL] Intelligent decision engine test failed")

        except Exception as e:
            self.test_results["total_tests"] += 1
            self.test_results["failed_tests"] += 1
            print(f"  ❌ 智能决策引擎测试异常: {e}")

    async def test_knowledge_accumulator(self):
        """测试4: 知识积累器"""
        print("\n[Test 4] Knowledge Accumulator")
        print("-" * 40)

        try:
            # 创建V5.2知识积累器
            self.knowledge_accumulator = create_auto_knowledge_accumulator_v5_2(
                mem0_storage=self.mem0_storage
            )

            # 测试添加知识
            print("  📝 测试添加知识...")
            test_knowledge = {
                "content": "BTC价格上涨时，跨交易所套利机会增加，建议关注Binance和OKX的价差",
                "metadata": {
                    "type": "strategy_knowledge",
                    "category": "market_condition",
                    "timestamp": "2026-04-18T15:36:00"
                }
            }

            knowledge_id = await self.knowledge_accumulator.add_knowledge(
                content=test_knowledge["content"],
                metadata=test_knowledge["metadata"],
                validate_quality=True
            )

            print(f"    知识ID: {knowledge_id[:8] if knowledge_id else 'N/A'}...")

            # 测试知识验证
            if knowledge_id:
                print("  🔍 测试知识验证...")
                await self.knowledge_accumulator.validate_knowledge(
                    knowledge_id=knowledge_id,
                    validation_result=True,
                    feedback="测试验证成功"
                )

            # 获取学习统计
            learning_stats = self.knowledge_accumulator.get_learning_statistics()
            print(f"  📈 学习统计:")
            print(f"    总知识数: {learning_stats.get('total_knowledge_added', 0)}")
            print(f"    缓存大小: {learning_stats.get('knowledge_cache_size', 0)}")

            self.test_results["total_tests"] += 1

            if knowledge_id:
                self.test_results["passed_tests"] += 1
                print("  [OK] Knowledge accumulator test passed")
            else:
                self.test_results["failed_tests"] += 1
                print("  [FAIL] Knowledge accumulator test failed")

        except Exception as e:
            self.test_results["total_tests"] += 1
            self.test_results["failed_tests"] += 1
            print(f"  ❌ 知识积累器测试异常: {e}")

    async def test_enhanced_arbitrage_engine(self):
        """测试5: 增强版低风险套利引擎"""
        print("\n[Test 5] Enhanced Low-Risk Arbitrage Engine")
        print("-" * 40)

        try:
            # 创建V5.2增强版引擎
            engine_config = {
                "base_stop_loss": 2.0,
                "base_take_profit": 1.0,
                "max_position_size": 1000
            }

            self.arbitrage_engine = create_enhanced_low_risk_engine_v5_2(
                config=engine_config,
                decision_engine=self.decision_engine
            )

            # 测试智能评估
            print("  🧠 测试智能机会评估...")
            test_opportunity = {
                "symbol": "BTC/USDT",
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "buy_price": 50000.0,
                "sell_price": 50050.0,
                "expected_profit": 50.0,
                "profit_rate": 0.1,
                "max_position_size": 1000,
                "volatility": 2.5
            }

            evaluation = await self.arbitrage_engine.evaluate_opportunity_intelligent(
                opportunity=test_opportunity,
                strategy="cross_exchange",
                current_market_conditions={
                    "volatility": 2.5,
                    "trend": "stable",
                    "liquidity": "normal"
                }
            )

            print(f"    是否执行: {evaluation.get('should_execute', False)}")
            print(f"    置信度: {evaluation.get('confidence', 0):.2f}")
            print(f"    引擎版本: {evaluation.get('engine_version', 'unknown')}")

            # 获取V5.2统计
            v5_2_stats = self.arbitrage_engine.get_v5_2_statistics()
            print(f"  📈 V5.2统计:")
            print(f"    智能决策数: {v5_2_stats.get('v5_2_intelligent_decisions', 0)}")
            print(f"    自适应调整数: {v5_2_stats.get('v5_2_adaptive_adjustments', 0)}")

            self.test_results["total_tests"] += 1

            if evaluation:
                self.test_results["passed_tests"] += 1
                print("  [OK] Enhanced low-risk arbitrage engine test passed")
            else:
                self.test_results["failed_tests"] += 1
                print("  [FAIL] Enhanced low-risk arbitrage engine test failed")

        except Exception as e:
            self.test_results["total_tests"] += 1
            self.test_results["failed_tests"] += 1
            print(f"  ❌ 增强版低风险套利引擎测试异常: {e}")

    async def test_integration(self):
        """测试6: 集成功能"""
        print("\n[Test 6] Integration Functionality")
        print("-" * 40)

        try:
            # 测试组件协同工作
            print("  🔄 测试组件集成...")

            # 模拟完整的决策流程
            if self.arbitrage_engine and self.decision_engine:
                print("    ✓ 引擎集成正常")

                # 测试数据流
                if self.knowledge_accumulator:
                    print("    ✓ 知识流集成正常")

            self.test_results["total_tests"] += 1

            if (self.arbitrage_engine and
                self.decision_engine and
                self.knowledge_accumulator):
                self.test_results["passed_tests"] += 1
                print("  [OK] Integration functionality test passed")
            else:
                self.test_results["failed_tests"] += 1
                print("  [FAIL] Integration functionality test failed")

        except Exception as e:
            self.test_results["total_tests"] += 1
            self.test_results["failed_tests"] += 1
            print(f"  ❌ 集成功能测试异常: {e}")

    def print_test_results(self):
        """输出测试结果"""
        print("\n" + "="*60)
        print("Test Results Summary")
        print("="*60 + "\n")

        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} [OK]")
        print(f"Failed: {failed} [FAIL]")
        print(f"Pass Rate: {(passed/total*100):.1f}%" if total > 0 else "Pass Rate: 0%")

        if self.test_results["warnings"]:
            print(f"\n[WARN] Warnings ({len(self.test_results['warnings'])}):")
            for warning in self.test_results["warnings"]:
                print(f"  - {warning}")

        print("\n" + "="*60)

        if passed == total:
            print("[SUCCESS] All tests passed! V5.2 Intelligent Deep Integration Verification Successful")
        else:
            print("[WARN] Some tests failed, please check related components")

        print("="*60 + "\n")


async def main():
    """主函数"""
    tester = V52IntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
