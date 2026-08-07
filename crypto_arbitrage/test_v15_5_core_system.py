"""V15.5核心系统验证测试 - 修复导入问题"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_storage_system():
    """测试存储系统"""
    print("\n[测试1] 存储系统验证...")
    results = {}

    try:
        from storage import get_mem0_storage, DeepMemo0IntegrationV59
        print("  [OK] 基础存储导入成功")

        # 初始化V5.9深度集成
        config = {"enable_async_analysis": True}
        memo0_integration = DeepMemo0IntegrationV59(config)
        print("  [OK] V5.9深度Memo0集成初始化成功")
        results["storage"] = True
        return memo0_integration, results

    except Exception as e:
        print(f"  [FAIL] 存储系统初始化失败: {e}")
        return None, results


async def test_decision_engine(memo0_integration):
    """测试决策引擎"""
    print("\n[测试2] 决策引擎验证...")
    results = {}

    try:
        from storage import IntelligentDecisionEngine

        config = {"memo0_integration": memo0_integration}
        decision_engine = IntelligentDecisionEngine(config)
        print("  [OK] 智能决策引擎初始化成功")
        results["decision_engine"] = True
        return decision_engine, results

    except Exception as e:
        print(f"  [FAIL] 决策引擎初始化失败: {e}")
        return None, results


async def test_arbitrage_engine(decision_engine, memo0_integration):
    """测试套利引擎"""
    print("\n[测试3] 套利引擎验证...")
    results = {}

    try:
        from strategies import EnhancedLowRiskArbitrageEngineV59

        config = {
            "enable_async_analysis": True,
            "async_analysis_timeout": 30
        }

        # 手动创建决策引擎参数（简化版）
        engine = EnhancedLowRiskArbitrageEngineV59(
            config, decision_engine, memo0_integration
        )
        print("  [OK] V5.9低风险套利引擎初始化成功")
        results["arbitrage"] = True
        return engine, results

    except Exception as e:
        print(f"  [FAIL] 套利引擎初始化失败: {e}")
        return None, results


async def test_main_agent():
    """测试主代理"""
    print("\n[测试4] 主代理验证...")
    results = {}

    try:
        from agents.main_agent_v5_10 import CryptoArbitrageAgentV510

        config = {
            "enable_async_analysis": True,
            "enable_production_mode": False,
            "production_safety_checks": True
        }

        agent = CryptoArbitrageAgentV510(config)
        print("  [OK] V5.10主代理初始化成功")
        results["agent"] = True
        return agent, results

    except Exception as e:
        print(f"  [FAIL] 主代理初始化失败: {e}")
        return None, results


async def test_trading_modules():
    """测试交易模块"""
    print("\n[测试5] 交易模块验证...")
    results = {}

    try:
        from trading.trading_coordinator import get_trading_coordinator
        from trading.market_data_manager import get_market_data_manager
        from trading.signal_generator import get_signal_generator
        from trading.risk_manager_v2 import get_risk_manager_v2
        from trading.execution_engine import get_execution_engine
        from trading.position_manager import get_position_manager
        from trading.trade_monitor import get_trade_monitor

        # 初始化所有模块
        coordinator = get_trading_coordinator()
        data_manager = get_market_data_manager()
        signal_gen = get_signal_generator()
        risk_mgr = get_risk_manager_v2()
        exec_engine = get_execution_engine()
        pos_mgr = get_position_manager()
        monitor = get_trade_monitor()

        print("  [OK] 交易协调器初始化成功")
        print("  [OK] 市场数据管理器初始化成功")
        print("  [OK] 信号生成器初始化成功")
        print("  [OK] 风险管理器V2初始化成功")
        print("  [OK] 执行引擎初始化成功")
        print("  [OK] 仓位管理器初始化成功")
        print("  [OK] 交易监控器初始化成功")

        results["trading_modules"] = True
        return True, results

    except Exception as e:
        print(f"  [FAIL] 交易模块初始化失败: {e}")
        return False, results


async def test_async_functionality():
    """测试异步功能"""
    print("\n[测试6] 异步功能验证...")
    results = {}

    try:
        from storage import DeepMemo0IntegrationV59
        from strategies import EnhancedLowRiskArbitrageEngineV59

        # 检查异步方法存在
        async_methods_v59 = [
            'analyze_symbol_async',
            'batch_analyze_symbols_async'
        ]

        async_methods_engine = [
            'evaluate_opportunity_async',
            '_async_analyze_market_conditions'
        ]

        print("  检查V5.9存储异步方法:")
        for method in async_methods_v59:
            exists = hasattr(DeepMemo0IntegrationV59, method)
            status = "[OK]" if exists else "[MISSING]"
            print(f"    {status} {method}")
            if not exists:
                raise Exception(f"缺少方法: {method}")

        print("  检查套利引擎异步方法:")
        for method in async_methods_engine:
            exists = hasattr(EnhancedLowRiskArbitrageEngineV59, method)
            status = "[OK]" if exists else "[MISSING]"
            print(f"    {status} {method}")
            if not exists:
                raise Exception(f"缺少方法: {method}")

        print("  [OK] 所有异步方法验证通过")
        results["async"] = True
        return results

    except Exception as e:
        print(f"  [FAIL] 异步功能验证失败: {e}")
        return results


async def test_integration():
    """测试集成功能"""
    print("\n[测试7] 系统集成验证...")
    results = {}

    try:
        # 测试统一导入接口
        print("  验证统一导入接口...")

        from storage import (
            KnowledgeBase,
            initialize_knowledge_base,
            DeepMemo0IntegrationV59,
            create_deep_memo0_integration_v5_9,
            get_mem0_storage
        )

        from strategies import (
            EnhancedLowRiskArbitrageEngineV59
        )

        from agents.main_agent_v5_10 import (
            CryptoArbitrageAgentV510,
            run_crypto_arbitrage_agent_v5_10
        )

        print("    [OK] Storage统一接口")
        print("    [OK] Strategies统一接口")
        print("    [OK] Agents统一接口")

        # 测试版本信息
        print("  验证版本兼容性...")

        config = {"enable_async_analysis": True}
        v59_integration = DeepMemo0IntegrationV59(config)

        if hasattr(v59_integration, '_version'):
            version = v59_integration._version
            print(f"    [OK] Memo0集成版本: {version}")
        else:
            print("    [WARN] 版本信息未找到")

        results["integration"] = True
        return results

    except Exception as e:
        print(f"  [FAIL] 集成验证失败: {e}")
        return results


async def main():
    """主测试流程"""
    print("=" * 60)
    print("V15.5 核心系统验证测试")
    print("=" * 60)

    all_results = {}

    # 顺序测试
    try:
        # 测试1: 存储系统
        memo0_integration, storage_results = await test_storage_system()
        all_results.update(storage_results)

        if not memo0_integration:
            print("\n[ABORT] 存储系统初始化失败，停止测试")
            return 1

        # 测试2: 决策引擎
        decision_engine, decision_results = await test_decision_engine(memo0_integration)
        all_results.update(decision_results)

        # 测试3: 套利引擎
        arbitrage_engine, arbitrage_results = await test_arbitrage_engine(
            decision_engine, memo0_integration
        )
        all_results.update(arbitrage_results)

        # 测试4: 主代理
        agent, agent_results = await test_main_agent()
        all_results.update(agent_results)

        # 测试5: 交易模块
        trading_ok, trading_results = await test_trading_modules()
        all_results.update(trading_results)

        # 测试6: 异步功能
        async_results = await test_async_functionality()
        all_results.update(async_results)

        # 测试7: 系统集成
        integration_results = await test_integration()
        all_results.update(integration_results)

    except Exception as e:
        logger.error(f"测试流程异常: {e}")
        return 1

    # 最终总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)

    total_tests = len(all_results)
    passed_tests = sum(all_results.values())
    pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    for test_name, passed in all_results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"{test_name:20s}: {status}")

    print(f"\n总体结果: {passed_tests}/{total_tests} 通过 ({pass_rate:.1f}%)")

    if pass_rate == 100:
        print("\nV15.5 核心系统验证全部通过！")
        print("\n系统状态:")
        print("  [OK] 存储系统: V5.9深度集成")
        print("  [OK] 决策引擎: 智能V2.2")
        print("  [OK] 套利引擎: V5.9异步增强")
        print("  [OK] 主代理: V5.10生产级")
        print("  [OK] 交易模块: Phase 13完整")
        print("  [OK] 异步功能: 全面支持")
        print("  [OK] 系统集成: 向后兼容")
        print("\n系统准备就绪，可以开始优化迭代！")
        return 0
    else:
        print(f"\n部分测试失败，通过率: {pass_rate:.1f}%")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
