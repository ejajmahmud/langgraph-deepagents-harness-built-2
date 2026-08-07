"""快速开始示例 - 演示如何使用套利交易系统"""

import asyncio
import logging
from agents.main_agent import CryptoArbitrageAgent, get_example_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def basic_usage_example():
    """基本使用示例"""
    print("=" * 60)
    print("数字货币套利交易系统 - 基本使用示例")
    print("=" * 60)

    # 获取示例配置
    config = get_example_config()

    # 创建 Agent
    print("\n1. 创建套利交易 Agent...")
    agent = CryptoArbitrageAgent(config)
    print("   ✅ Agent 创建成功")

    # 检查风险状态
    print("\n2. 检查当前风险状态...")
    risk_status = agent.get_risk_status_tool()
    print(risk_status)

    # 获取性能统计
    print("\n3. 获取性能统计...")
    perf_stats = agent.get_performance_stats_tool()
    print(perf_stats)

    # 分析市场条件
    print("\n4. 分析市场条件...")
    market_analysis = await agent.analyze_market_conditions_tool("BTC/USDT")
    print(market_analysis)

    # 记录知识
    print("\n5. 记录知识到知识库...")
    knowledge_result = agent.record_knowledge_tool(
        "strategy",
        "测试策略: 在低波动率市场环境下，跨交易所套利效果最佳"
    )
    print(knowledge_result)

    print("\n" + "=" * 60)
    print("基本使用示例完成")
    print("=" * 60)


async def opportunity_scanning_example():
    """机会扫描示例"""
    print("\n" + "=" * 60)
    print("套利机会扫描示例")
    print("=" * 60)

    # 获取示例配置
    config = get_example_config()

    # 创建 Agent
    agent = CryptoArbitrageAgent(config)

    # 扫描套利机会
    print("\n正在扫描套利机会...")
    opportunities = await agent.scan_arbitrage_opportunities_tool("cross_exchange")

    print("\n扫描结果:")
    print(opportunities)


async def risk_management_example():
    """风险管理示例"""
    print("\n" + "=" * 60)
    print("风险管理示例")
    print("=" * 60)

    from tools.risk_management import RiskManager

    # 创建风险管理器
    risk_manager = RiskManager({
        'max_daily_loss': 500,
        'max_position_size': 1000,
        'max_total_exposure': 5000,
        'max_drawdown': 10.0
    })

    # 检查仓位风险
    print("\n1. 检查仓位风险...")
    position = {
        'amount': 800,
        'symbol': 'BTC/USDT',
        'strategy': 'cross_exchange'
    }

    is_safe = risk_manager.check_position_risk(position)
    print(f"   仓位安全性: {'✅ 通过' if is_safe else '❌ 未通过'}")

    # 记录交易结果
    print("\n2. 记录交易结果...")
    risk_manager.record_trade_result({
        'profit': 15.5,
        'expected_profit': 15.0,
        'strategy': 'cross_exchange'
    })
    print("   ✅ 交易结果已记录")

    # 获取风险摘要
    print("\n3. 获取风险摘要...")
    summary = risk_manager.get_risk_summary()
    print(f"   当前敞口: ${summary['current_exposure']:.2f}")
    print(f"   今日盈亏: ${summary['daily_pnl']:.2f}")
    print(f"   今日交易: {summary['daily_trades']} 笔")
    print(f"   当前余额: ${summary['current_balance']:.2f}")


async def knowledge_base_example():
    """知识库使用示例"""
    print("\n" + "=" * 60)
    print("知识库使用示例")
    print("=" * 60)

    from storage.knowledge_base import KnowledgeBase

    # 创建知识库
    knowledge_base = KnowledgeBase(":memory:")  # 使用内存数据库

    # 添加策略
    print("\n1. 添加策略知识...")
    strategy_id = knowledge_base.add_strategy(
        name="跨交易所套利 V1",
        description="利用不同交易所间价格差异进行套利",
        parameters={
            'min_profit_rate': 0.5,
            'max_position_size': 1000,
            'symbols': ['BTC/USDT', 'ETH/USDT']
        },
        performance_metrics={
            'total_profit': 1250.5,
            'win_rate': 0.75,
            'sharpe_ratio': 2.3
        }
    )
    print(f"   ✅ 策略已添加 (ID: {strategy_id})")

    # 添加交易记录
    print("\n2. 添加交易记录...")
    trade_id = knowledge_base.add_trade_record(
        strategy="跨交易所套利 V1",
        symbol="BTC/USDT",
        exchange="binance->okx",
        entry_price=50000.0,
        exit_price=50250.0,
        quantity=0.1,
        profit=25.0,
        profit_rate=0.5,
        status="completed",
        execution_time=5.5,
        notes="成功执行套利交易"
    )
    print(f"   ✅ 交易记录已添加 (ID: {trade_id})")

    # 添加市场模式
    print("\n3. 添加市场模式...")
    pattern_id = knowledge_base.add_market_pattern(
        pattern_name="低波动率套利机会",
        pattern_type="volatility",
        description="在低波动率市场环境下，跨交易所套利机会更多",
        indicators={
            'volatility': '< 1%',
            'market_condition': 'stable'
        },
        success_rate=0.85,
        sample_size=100
    )
    print(f"   ✅ 市场模式已添加 (ID: {pattern_id})")

    # 获取统计信息
    print("\n4. 获取统计信息...")
    stats = knowledge_base.get_statistics()
    print(f"   策略数量: {stats['strategies_count']}")
    print(f"   交易数量: {stats['trades_count']}")
    print(f"   总利润: ${stats['total_profit']:.2f}")
    print(f"   胜率: {stats['win_rate']:.1%}")


async def project_tracking_example():
    """项目追踪示例"""
    print("\n" + "=" * 60)
    print("项目追踪示例")
    print("=" * 60)

    from storage.project_tracker import ProjectTracker

    # 创建项目追踪器
    project_tracker = ProjectTracker("CryptoArbitrageDemo")

    # 记录迭代
    print("\n1. 记录项目迭代...")
    project_tracker.record_iteration(
        version="1.0.0",
        completed_tasks=[
            "设计系统架构",
            "实现核心策略",
            "建立风险管理"
        ],
        in_progress_tasks=[
            "系统测试",
            "参数优化"
        ],
        planned_tasks=[
            "实盘部署",
            "性能监控"
        ],
        summary="V1.0.0 版本完成核心功能开发",
        achievements=[
            "成功构建完整交易系统",
            "实现两种套利策略",
            "建立完善风控体系"
        ],
        challenges=[
            "交易所API限流",
            "参数调优复杂"
        ],
        next_steps=[
            "配置真实API密钥",
            "进行模拟测试",
            "逐步实盘"
        ]
    )
    print("   ✅ 迭代已记录")

    # 生成进度报告
    print("\n2. 生成进度报告...")
    report = project_tracker.generate_progress_report()
    print(report)

    # 分析进度
    print("\n3. 分析项目进度...")
    analysis = project_tracker.analyze_progress()
    print(f"   总迭代次数: {analysis['total_iterations']}")
    print(f"   完成任务数: {analysis['total_completed_tasks']}")
    print(f"   完成率: {analysis['completion_rate']:.1%}")
    print(f"   平均每迭代任务数: {analysis['average_tasks_per_iteration']:.1f}")


async def main():
    """主函数 - 运行所有示例"""
    try:
        # 基本使用示例
        await basic_usage_example()

        # 机会扫描示例
        await opportunity_scanning_example()

        # 风险管理示例
        await risk_management_example()

        # 知识库示例
        await knowledge_base_example()

        # 项目追踪示例
        await project_tracking_example()

        print("\n" + "=" * 60)
        print("所有示例执行完成！")
        print("=" * 60)

    except Exception as e:
        logger.error(f"示例执行出错: {e}", exc_info=True)


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        数字货币套利交易系统 - 快速开始示例                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

    本示例演示了系统的核心功能：
    1. 基本使用 - Agent 的创建和基本操作
    2. 机会扫描 - 套利机会的识别和评估
    3. 风险管理 - 风险控制和监控
    4. 知识库 - 数据存储和知识积累
    5. 项目追踪 - 进度管理和迭代记录

    注意: 本示例使用模拟数据，不会连接真实交易所
    """)

    asyncio.run(main())
