"""V5.0 性能测试

测试优化后的 Agent 初始化性能
"""

import sys
import os
import time
import asyncio
import logging

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_v5_performance():
    """测试 V5.0 性能"""

    print("="*60)
    print("[V5.0] 性能测试开始")
    print("="*60)

    config = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']},
        'enhanced_low_risk_engine': {
            'enabled': True,
            'enable_risk_prediction': True,
            'enable_health_monitoring': True,
            'enable_intelligent_decision': True
        },
        'trading_agents': {'enabled': False}
    }

    print(f"\n[配置]")
    print(f"  增强版低风险引擎: 启用")
    print(f"  TradingAgents: 禁用 (性能测试)")
    print(f"  监控系统: 启用")

    print(f"\n[测试 1: V5.0 优化版]")
    start = time.time()

    try:
        from agents.main_agent_v5 import create_crypto_arbitrage_agent_v5
        agent_v5 = create_crypto_arbitrage_agent_v5(config)

        elapsed = time.time() - start

        print(f"  初始化时间: {elapsed:.3f}秒 ({elapsed*1000:.2f}ms)")
        print(f"  组件状态:")

        components = {
            '交易所管理器': agent_v5.exchange_manager is not None,
            '风险管理器': agent_v5.risk_manager is not None,
            '监控系统': agent_v5.monitoring is not None,
            '策略管理器': agent_v5.strategy_manager is not None,
            '增强版引擎': agent_v5.enhanced_low_risk_engine is not None,
        }

        for name, status in components.items():
            status_icon = "[OK]" if status else "[MISSING]"
            print(f"    {status_icon} {name}")

        # 计算性能提升
        baseline_time = 5.942  # 原版基线时间
        improvement = ((baseline_time - elapsed) / baseline_time) * 100

        print(f"\n  [性能对比]")
        print(f"    原版 V3.5: {baseline_time:.3f}秒")
        print(f"    优化版 V5.0: {elapsed:.3f}秒")
        print(f"    性能提升: {improvement:.1f}%")

        print(f"\n  [评级]")
        if elapsed < 3.0:
            print(f"    评级: EXCELLENT (< 3秒)")
            print(f"    状态: 达到目标")
        elif elapsed < 5.0:
            print(f"    评级: GOOD (3-5秒)")
            print(f"    状态: 显著改善")
        else:
            print(f"    评级: 需优化 (> 5秒)")
            print(f"    状态: 未达目标")

        return elapsed

    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_import_overhead():
    """测试导入开销"""

    print(f"\n[测试 2: 导入开销分析]")

    # 测试单独导入各个模块的时间
    imports = [
        ("基础模块", "from agents.main_agent_v5 import CryptoArbitrageAgentV5"),
        ("策略模块", "from strategies.cross_exchange import CrossExchangeArbitrageStrategy"),
        ("风险管理", "from tools.risk_management import initialize_risk_manager"),
        ("监控系统", "from tools.monitoring import initialize_monitoring"),
    ]

    for name, import_stmt in imports:
        start = time.time()
        try:
            exec(import_stmt)
            elapsed = time.time() - start
            print(f"  {name}: {elapsed*1000:.2f}ms")
        except Exception as e:
            print(f"  {name}: 错误 - {e}")


async def main():
    """主函数"""

    # 测试 V5.0 性能
    v5_time = await test_v5_performance()

    # 测试导入开销
    await test_import_overhead()

    # 总结
    print(f"\n" + "="*60)
    print("[V5.0] 性能测试总结")
    print("="*60)

    if v5_time:
        if v5_time < 3.0:
            print("状态: 成功达到性能目标 (< 3秒)")
            print("建议: 可以部署到生产环境")
        elif v5_time < 5.0:
            print("状态: 显著性能改善，接近目标")
            print("建议: 可以继续微调优化")
        else:
            print("状态: 需要进一步优化")
            print("建议: 深入分析剩余瓶颈")

    print(f"\n优化建议:")
    print(f"  1. 继续优化导入依赖")
    print(f"  2. 考虑使用缓存机制")
    print(f"  3. 异步化更多初始化流程")
    print(f"  4. 优化数据库连接")
    print("="*60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    import logging
    asyncio.run(main())
