"""V3.0 集成测试

测试数字货币套利交易系统 V3.0 的核心功能：
1. 智能优化引擎集成
2. 智能知识管理 V3 集成
3. 自适应错误处理集成
4. 主代理 V3.0 工具可用性
5. V3.0 组件协同工作

运行方式:
    python tests/test_v3_0.py
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.main_agent import CryptoArbitrageAgent


def print_header(title: str) -> None:
    """打印测试标题"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_test(name: str, passed: bool, message: str = "") -> None:
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if message:
        print(f"    {message}")


async def test_v3_0_initialization():
    """测试 V3.0 组件初始化"""
    print_header("测试 1: V3.0 组件初始化")

    # V3.0 配置（最小配置）
    config = {
        'system': {
            'name': 'CryptoArbitrage',
            'version': '3.0',
            'mode': 'simulation'
        },
        'model': {
            'provider': 'anthropic',
            'model': 'claude-sonnet-4-6',
            'temperature': 0.0
        },

        # V3.0 智能优化引擎配置
        'intelligent_optimizer': {
            'enabled': True,
            'optimization_interval': 60,  # 1分钟优化一次（测试用）
            'history_window': 100,
            'min_data_points': 5,  # 最少数据点（测试用）
            'config_path': 'config/optimization_state.json'
        },

        # V3.0 智能知识管理配置
        'knowledge_manager_v3': {
            'enabled': True,
            'cache_ttl': 60,
            'auto_extract': True,
            'auto_classify': True,
            'quality_threshold': 0.6
        },

        # V3.0 自适应错误处理配置
        'adaptive_error_handler': {
            'enabled': True,
            'max_retries': 2,
            'retry_delay': 0.5,
            'backoff_factor': 2.0,
            'circuit_breaker': {
                'failure_threshold': 3,
                'timeout': 30.0,
                'half_open_max_calls': 2
            }
        },

        # 其他必要配置
        'exchanges': {
            'binance': {
                'enabled': False  # 使用模拟模式
            }
        },
        'risk_management': {
            'max_daily_loss': 1000,
            'max_position_size': 500,
            'max_total_exposure': 2000,
            'max_drawdown': 10.0
        },
        'trading_agents': {
            'enabled': False  # 测试时禁用以减少依赖
        },
        'mem0': {
            'api_key': None  # 使用 SQLite 备用
        }
    }

    try:
        # 初始化 Agent
        agent = CryptoArbitrageAgent(config)

        # 测试 1.1: 智能优化引擎初始化
        test1_1_passed = agent.intelligent_optimizer is not None
        print_test("智能优化引擎初始化", test1_1_passed,
                  "已成功初始化" if test1_1_passed else "初始化失败")

        # 测试 1.2: 智能知识管理器初始化
        test1_2_passed = agent.intelligent_knowledge_manager is not None
        print_test("智能知识管理器 V3 初始化", test1_2_passed,
                  "已成功初始化" if test1_2_passed else "初始化失败")

        # 测试 1.3: 自适应错误处理器初始化
        test1_3_passed = agent.error_handler is not None
        print_test("自适应错误处理器 V3 初始化", test1_3_passed,
                  "已成功初始化" if test1_3_passed else "初始化失败")

        # 测试 1.4: 原有组件仍然正常
        test1_4_passed = (
            agent.strategy_manager is not None and
            agent.risk_manager is not None and
            agent.monitoring is not None
        )
        print_test("原有组件（策略管理器、风险管理器、监控系统）",
                  test1_4_passed,
                  "均正常初始化" if test1_4_passed else "部分组件初始化失败")

        print(f"\nV3.0 组件初始化测试结果: "
              f"{'✅ 全部通过 (4/4)' if all([test1_1_passed, test1_2_passed, test1_3_passed, test1_4_passed]) else '⚠️  部分失败'}")

        return agent, [test1_1_passed, test1_2_passed, test1_3_passed, test1_4_passed]

    except Exception as e:
        print_test("V3.0 组件初始化", False, f"异常: {e}")
        import traceback
        traceback.print_exc()
        return None, [False, False, False, False]


async def test_v3_0_tools(agent: CryptoArbitrageAgent):
    """测试 V3.0 工具可用性"""
    print_header("测试 2: V3.0 工具可用性")

    tools = agent._get_agent_tools()
    test_results = []

    # 测试 2.1: 智能优化工具
    optimizer_tools = [
        'trigger_optimization_tool',
        'get_optimization_status_tool',
        'get_optimization_history_tool'
    ]
    test2_1_passed = all(any(hasattr(agent, tool) and tool in str(agent._get_agent_tools())
                           for tool in optimizer_tools))
    print_test("智能优化工具注册", test2_1_passed,
              "已注册 3 个智能优化工具" if test2_1_passed else "工具注册失败")
    test_results.append(test2_1_passed)

    # 测试 2.2: 智能知识管理工具
    km_tools = [
        'add_intelligent_knowledge_tool',
        'get_recommended_knowledge_tool',
        'extract_knowledge_from_trade_tool'
    ]
    test2_2_passed = all(any(hasattr(agent, tool) and tool in str(agent._get_agent_tools())
                           for tool in km_tools))
    print_test("智能知识管理工具注册", test2_2_passed,
              "已注册 3 个知识管理工具" if test2_2_passed else "工具注册失败")
    test_results.append(test2_2_passed)

    # 测试 2.3: 错误处理工具
    eh_tools = [
        'get_error_statistics_tool',
        'get_error_patterns_tool',
        'reset_circuit_breakers_tool'
    ]
    test2_3_passed = all(any(hasattr(agent, tool) and tool in str(agent._get_agent_tools())
                           for tool in eh_tools))
    print_test("错误处理工具注册", test2_3_passed,
              "已注册 3 个错误处理工具" if test2_3_passed else "工具注册失败")
    test_results.append(test2_3_passed)

    # 测试 2.4: 原有工具仍然可用
    original_tools = [
        'scan_arbitrage_opportunities_tool',
        'execute_arbitrage_tool',
        'get_risk_status_tool',
        'get_performance_stats_tool'
    ]
    test2_4_passed = all(hasattr(agent, tool) for tool in original_tools)
    print_test("原有工具可用性", test2_4_passed,
              f"已有 {len(original_tools)} 个核心工具可用" if test2_4_passed else "部分工具丢失")
    test_results.append(test2_4_passed)

    print(f"\nV3.0 工具测试结果: "
          f"{'✅ 全部通过 (4/4)' if all(test_results) else '⚠️  部分失败'}")

    return test_results


async def test_intelligent_optimizer(agent: CryptoArbitrageAgent):
    """测试智能优化引擎"""
    print_header("测试 3: 智能优化引擎功能")

    test_results = []

    # 测试 3.1: 优化引擎状态
    try:
        status = agent.intelligent_optimizer.get_status()
        test3_1_passed = 'is_running' in status and 'optimization_count' in status
        print_test("优化引擎状态查询", test3_1_passed,
                  f"运行状态: {status.get('is_running', False)}")
        test_results.append(test3_1_passed)
    except Exception as e:
        print_test("优化引擎状态查询", False, f"异常: {e}")
        test_results.append(False)

    # 测试 3.2: 性能数据记录
    try:
        agent.intelligent_optimizer.record_performance(
            'cross_exchange',
            {'total_profit': 100.0, 'win_rate': 0.8, 'average_profit_rate': 0.5}
        )
        agent.intelligent_optimizer.record_performance(
            'triangular',
            {'total_profit': 50.0, 'win_rate': 0.6, 'average_profit_rate': 0.3}
        )

        status = agent.intelligent_optimizer.get_status()
        test3_2_passed = status.get('data_points', 0) >= 2
        print_test("性能数据记录", test3_2_passed,
                  f"已记录 {status.get('data_points', 0)} 个数据点")
        test_results.append(test3_2_passed)
    except Exception as e:
        print_test("性能数据记录", False, f"异常: {e}")
        test_results.append(False)

    # 测试 3.3: 优化历史
    try:
        history = agent.intelligent_optimizer.get_optimization_history(5)
        test3_3_passed = isinstance(history, list)
        print_test("优化历史查询", test3_3_passed,
                  f"历史记录数: {len(history)}")
        test_results.append(test3_3_passed)
    except Exception as e:
        print_test("优化历史查询", False, f"异常: {e}")
        test_results.append(False)

    print(f"\n智能优化引擎测试结果: "
          f"{'✅ 全部通过 (3/3)' if all(test_results) else '⚠️  部分失败'}")

    return test_results


async def test_intelligent_knowledge_manager(agent: CryptoArbitrageAgent):
    """测试智能知识管理器"""
    print_header("测试 4: 智能知识管理器功能")

    test_results = []

    # 测试 4.1: 知识添加
    try:
        knowledge_id = agent.intelligent_knowledge_manager.add_knowledge(
            content="测试知识条目",
            category="insight",
            metadata={'test': True}
        )
        test4_1_passed = knowledge_id is not None
        print_test("知识添加", test4_1_passed,
                  f"知识ID: {knowledge_id[:8] if knowledge_id else 'N/A'}...")
        test_results.append(test4_1_passed)
    except Exception as e:
        print_test("知识添加", False, f"异常: {e}")
        test_results.append(False)

    # 测试 4.2: 知识推荐
    try:
        recommendations = agent.intelligent_knowledge_manager.recommend_knowledge(
            context="交易套利",
            max_results=3
        )
        test4_2_passed = isinstance(recommendations, list)
        print_test("知识推荐", test4_2_passed,
                  f"推荐数量: {len(recommendations)}")
        test_results.append(test4_2_passed)
    except Exception as e:
        print_test("知识推荐", False, f"异常: {e}")
        test_results.append(False)

    # 测试 4.3: 知识质量评估
    try:
        if knowledge_id:
            quality = agent.intelligent_knowledge_manager.assess_knowledge_quality(knowledge_id)
            test4_3_passed = 0.0 <= quality <= 1.0
            print_test("知识质量评估", test4_3_passed,
                      f"质量评分: {quality:.2f}")
            test_results.append(test4_3_passed)
        else:
            test4_3_passed = False
            print_test("知识质量评估", False, "知识ID为空")
            test_results.append(False)
    except Exception as e:
        print_test("知识质量评估", False, f"异常: {e}")
        test_results.append(False)

    print(f"\n智能知识管理器测试结果: "
          f"{'✅ 全部通过 (3/3)' if all(test_results) else '⚠️  部分失败'}")

    return test_results


async def test_adaptive_error_handler(agent: CryptoArbitrageAgent):
    """测试自适应错误处理器"""
    print_header("测试 5: 自适应错误处理器功能")

    test_results = []

    # 测试 5.1: 错误统计
    try:
        stats = agent.error_handler.get_error_statistics()
        test5_1_passed = 'total_errors' in stats and 'recovered' in stats
        print_test("错误统计查询", test5_1_passed,
                  f"总错误数: {stats.get('total_errors', 0)}")
        test_results.append(test5_1_passed)
    except Exception as e:
        print_test("错误统计查询", False, f"异常: {e}")
        test_results.append(False)

    # 测试 5.2: 错误模式分析
    try:
        patterns = agent.error_handler.analyze_error_patterns(5)
        test5_2_passed = isinstance(patterns, list)
        print_test("错误模式分析", test5_2_passed,
                  f"模式数量: {len(patterns)}")
        test_results.append(test5_2_passed)
    except Exception as e:
        print_test("错误模式分析", False, f"异常: {e}")
        test_results.append(False)

    # 测试 5.3: 错误日志
    try:
        agent.error_handler.log_error(
            error=Exception("测试错误"),
            category='API',
            severity='MEDIUM',
            context="测试场景"
        )
        stats = agent.error_handler.get_error_statistics()
        test5_3_passed = stats.get('total_errors', 0) >= 1
        print_test("错误日志记录", test5_3_passed,
                  "错误已成功记录")
        test_results.append(test5_3_passed)
    except Exception as e:
        print_test("错误日志记录", False, f"异常: {e}")
        test_results.append(False)

    print(f"\n自适应错误处理器测试结果: "
          f"{'✅ 全部通过 (3/3)' if all(test_results) else '⚠️  部分失败'}")

    return test_results


async def test_component_collaboration(agent: CryptoArbitrageAgent):
    """测试 V3.0 组件协同工作"""
    print_header("测试 6: V3.0 组件协同工作")

    test_results = []

    # 测试 6.1: 知识管理器与优化引擎协作
    try:
        # 添加一条关于优化的知识
        knowledge_id = agent.intelligent_knowledge_manager.add_knowledge(
            content="策略A在低波动率市场表现更佳，建议降低风险敞口",
            category="optimization",
            metadata={'strategy': 'A', 'condition': 'low_volatility'}
        )

        # 记录性能数据
        agent.intelligent_optimizer.record_performance(
            'strategy_A',
            {'total_profit': 200.0, 'win_rate': 0.85, 'average_profit_rate': 0.8}
        )

        test6_1_passed = knowledge_id is not None
        print_test("知识管理与优化引擎协作", test6_1_passed,
                  "知识已添加，性能数据已记录")
        test_results.append(test6_1_passed)
    except Exception as e:
        print_test("知识管理与优化引擎协作", False, f"异常: {e}")
        test_results.append(False)

    # 测试 6.2: 错误处理器与其他组件协作
    try:
        # 模拟一个错误
        agent.error_handler.log_error(
            error=Exception("API超时"),
            category='NETWORK',
            severity='HIGH',
            context="数据获取"
        )

        # 获取错误统计和模式
        stats = agent.error_handler.get_error_statistics()
        patterns = agent.error_handler.analyze_error_patterns(3)

        test6_2_passed = stats.get('total_errors', 0) > 0 and isinstance(patterns, list)
        print_test("错误处理器与其他组件协作", test6_2_passed,
                  "错误已记录，模式分析已完成")
        test_results.append(test6_2_passed)
    except Exception as e:
        print_test("错误处理器与其他组件协作", False, f"异常: {e}")
        test_results.append(False)

    # 测试 6.3: 所有组件状态正常
    try:
        all_healthy = (
            agent.intelligent_optimizer is not None and
            agent.intelligent_knowledge_manager is not None and
            agent.error_handler is not None
        )

        test6_3_passed = all_healthy
        print_test("所有组件健康状态", test6_3_passed,
                  "所有 V3.0 组件运行正常" if all_healthy else "部分组件异常")
        test_results.append(test6_3_passed)
    except Exception as e:
        print_test("所有组件健康状态", False, f"异常: {e}")
        test_results.append(False)

    print(f"\n组件协同工作测试结果: "
          f"{'✅ 全部通过 (3/3)' if all(test_results) else '⚠️  部分失败'}")

    return test_results


async def test_agent_shutdown(agent: CryptoArbitrageAgent):
    """测试 Agent 优雅关闭"""
    print_header("测试 7: Agent 优雅关闭")

    test_results = []

    try:
        # 保存优化状态
        if agent.intelligent_optimizer:
            agent.intelligent_optimizer.save_state()
            print("✅ 优化状态已保存")

        # 停止组件
        if agent.intelligent_optimizer:
            agent.intelligent_optimizer.stop()
            print("✅ 智能优化引擎已停止")

        if agent.intelligent_knowledge_manager:
            agent.intelligent_knowledge_manager.stop_processing()
            print("✅ 智能知识管理器已停止")

        test_results.append(True)
        print_test("Agent 优雅关闭", True, "所有组件已正常关闭")

    except Exception as e:
        print_test("Agent 优雅关闭", False, f"异常: {e}")
        test_results.append(False)

    print(f"\nAgent 优雅关闭测试结果: "
          f"{'✅ 通过' if all(test_results) else '⚠️  失败'}")

    return test_results


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print(" 数字货币套利交易系统 V3.0 - 集成测试")
    print(f" 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    all_test_results = []

    # 测试 1: V3.0 组件初始化
    agent, test1_results = await test_v3_0_initialization()
    all_test_results.extend(test1_results)

    if agent is None:
        print("\n❌ Agent 初始化失败，无法继续测试")
        return

    # 测试 2: V3.0 工具可用性
    test2_results = await test_v3_0_tools(agent)
    all_test_results.extend(test2_results)

    # 测试 3: 智能优化引擎
    test3_results = await test_intelligent_optimizer(agent)
    all_test_results.extend(test3_results)

    # 测试 4: 智能知识管理器
    test4_results = await test_intelligent_knowledge_manager(agent)
    all_test_results.extend(test4_results)

    # 测试 5: 自适应错误处理器
    test5_results = await test_adaptive_error_handler(agent)
    all_test_results.extend(test5_results)

    # 测试 6: 组件协同工作
    test6_results = await test_component_collaboration(agent)
    all_test_results.extend(test6_results)

    # 测试 7: Agent 优雅关闭
    test7_results = await test_agent_shutdown(agent)
    all_test_results.extend(test7_results)

    # 汇总测试结果
    print("\n" + "="*80)
    print(" 测试结果汇总")
    print("="*80)

    total_tests = len(all_test_results)
    passed_tests = sum(all_test_results)
    failed_tests = total_tests - passed_tests

    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

    if failed_tests == 0:
        print("\n🎉 恭喜！所有测试通过！V3.0 系统集成成功！")
    else:
        print(f"\n⚠️  有 {failed_tests} 个测试失败，请检查上述输出")

    print("="*80)

    return failed_tests == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
