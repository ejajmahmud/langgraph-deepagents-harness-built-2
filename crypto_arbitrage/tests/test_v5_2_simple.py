"""V5.2 Intelligent Deep Integration Simple Test

Simple test without special Unicode characters to avoid encoding issues.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import load_config
from storage.mem0_storage import initialize_mem0
from storage.intelligent_decision_engine_v5_2 import create_intelligent_decision_engine_v5_2
from storage.auto_knowledge_accumulator_v5_2 import create_auto_knowledge_accumulator_v5_2
from strategies.enhanced_low_risk_arbitrage_engine_v5_2 import create_enhanced_low_risk_engine_v5_2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V52SimpleTester:
    """V5.2 Simple Tester"""

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
        """Run all tests"""
        print("\n" + "="*60)
        print("V5.2 Intelligent Deep Integration Test")
        print("="*60 + "\n")

        # Test 1: Configuration Loading
        await self.test_config_loading()

        # Test 2: Memo0 Initialization
        await self.test_mem0_initialization()

        # Test 3: Intelligent Decision Engine
        await self.test_intelligent_decision_engine()

        # Test 4: Knowledge Accumulator
        await self.test_knowledge_accumulator()

        # Test 5: Enhanced Arbitrage Engine
        await self.test_enhanced_arbitrage_engine()

        # Test 6: Integration
        await self.test_integration()

        # Print test results
        self.print_test_results()

    async def test_config_loading(self):
        """Test 1: Configuration Loading"""
        print("\n[Test 1] Configuration Loading")
        print("-" * 40)

        try:
            self.config = load_config()

            # Verify system version
            version = self.config.get("system", {}).get("version")
            print(f"  System Version: {version}")

            # Verify Memo0 configuration
            mem0_config = self.config.get("mem0", {})
            api_key_configured = bool(mem0_config.get("api_key"))
            print(f"  Memo0 API Key: {'[OK] Configured' if api_key_configured else '[WARN] Not Configured'}")

            # Verify enhanced engine configuration
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
            print(f"  [FAIL] Configuration loading test error: {e}")

    async def test_mem0_initialization(self):
        """Test 2: Memo0 Initialization"""
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
                self.test_results["passed_tests"] += 1  # Fallback mode is acceptable

        except Exception as e:
            self.test_results["total_tests"] += 1
            self.test_results["failed_tests"] += 1
            print(f"  [FAIL] Memo0 initialization test error: {e}")

    async def test_intelligent_decision_engine(self):
        """Test 3: Intelligent Decision Engine"""
        print("\n[Test 3] Intelligent Decision Engine")
        print("-" * 40)

        try:
            # Create V5.2 intelligent decision engine
            self.decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=self.mem0_storage
            )

            # Test strategy recommendation
            market_conditions = {
                "volatility": 2.5,
                "trend": "rising",
                "liquidity": "normal",
                "funding_rate": 0.05,
                "spread": 0.3
            }

            print("  [TEST] Strategy recommendation...")
            recommendation = await self.decision_engine.recommend_strategy(
                current_market_conditions=market_conditions,
                available_strategies=["cross_exchange", "triangular", "funding_rate"],
                top_k=2
            )

            print(f"    Recommendations count: {len(recommendation.get('recommendations', []))}")
            print(f"    Data source: {recommendation.get('data_source', 'unknown')}")

            # Test risk assessment
            print("  [TEST] Risk assessment...")
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

            print(f"    Risk level: {risk_assessment.get('risk_level', 'unknown')}")
            print(f"    Risk score: {risk_assessment.get('risk_score', 0):.1f}")

            # Get statistics
            stats = self.decision_engine.get_statistics()
            print(f"  [STATS] Engine statistics:")
            print(f"    Total queries: {stats.get('total_queries', 0)}")
            print(f"    Cache hit rate: {stats.get('cache_hit_rate', '0%')}")

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
            print(f"  [FAIL] Intelligent decision engine test error: {e}")

    async def test_knowledge_accumulator(self):
        """Test 4: Knowledge Accumulator"""
        print("\n[Test 4] Knowledge Accumulator")
        print("-" * 40)

        try:
            # Create V5.2 knowledge accumulator
            self.knowledge_accumulator = create_auto_knowledge_accumulator_v5_2(
                mem0_storage=self.mem0_storage
            )

            # Test adding knowledge
            print("  [TEST] Adding knowledge...")
            test_knowledge = {
                "content": "BTC price increase leads to more cross-exchange arbitrage opportunities",
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

            print(f"    Knowledge ID: {knowledge_id[:8] if knowledge_id else 'N/A'}...")

            # Test knowledge validation
            if knowledge_id:
                print("  [TEST] Knowledge validation...")
                await self.knowledge_accumulator.validate_knowledge(
                    knowledge_id=knowledge_id,
                    validation_result=True,
                    feedback="Test validation successful"
                )

            # Get learning statistics
            learning_stats = self.knowledge_accumulator.get_learning_statistics()
            print(f"  [STATS] Learning statistics:")
            print(f"    Total knowledge: {learning_stats.get('total_knowledge_added', 0)}")
            print(f"    Cache size: {learning_stats.get('knowledge_cache_size', 0)}")

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
            print(f"  [FAIL] Knowledge accumulator test error: {e}")

    async def test_enhanced_arbitrage_engine(self):
        """Test 5: Enhanced Low-Risk Arbitrage Engine"""
        print("\n[Test 5] Enhanced Low-Risk Arbitrage Engine")
        print("-" * 40)

        try:
            # Create V5.2 enhanced engine
            engine_config = {
                "base_stop_loss": 2.0,
                "base_take_profit": 1.0,
                "max_position_size": 1000
            }

            self.arbitrage_engine = create_enhanced_low_risk_engine_v5_2(
                config=engine_config,
                decision_engine=self.decision_engine
            )

            # Test intelligent evaluation
            print("  [TEST] Intelligent opportunity evaluation...")
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

            print(f"    Should execute: {evaluation.get('should_execute', False)}")
            print(f"    Confidence: {evaluation.get('confidence', 0):.2f}")
            print(f"    Engine version: {evaluation.get('engine_version', 'unknown')}")

            # Get V5.2 statistics
            v5_2_stats = self.arbitrage_engine.get_v5_2_statistics()
            print(f"  [STATS] V5.2 statistics:")
            print(f"    Intelligent decisions: {v5_2_stats.get('v5_2_intelligent_decisions', 0)}")
            print(f"    Adaptive adjustments: {v5_2_stats.get('v5_2_adaptive_adjustments', 0)}")

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
            print(f"  [FAIL] Enhanced low-risk arbitrage engine test error: {e}")

    async def test_integration(self):
        """Test 6: Integration"""
        print("\n[Test 6] Integration Functionality")
        print("-" * 40)

        try:
            # Test component collaboration
            print("  [TEST] Component integration...")

            # Simulate complete decision flow
            if self.arbitrage_engine and self.decision_engine:
                print("    [OK] Engine integration normal")

                # Test data flow
                if self.knowledge_accumulator:
                    print("    [OK] Knowledge flow integration normal")

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
            print(f"  [FAIL] Integration functionality test error: {e}")

    def print_test_results(self):
        """Print test results"""
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
    """Main function"""
    tester = V52SimpleTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
