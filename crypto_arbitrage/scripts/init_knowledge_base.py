"""初始化知识库 - V2.9

确保所有表结构正确创建，验证知识库可用性。
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.knowledge_base import initialize_knowledge_base, get_knowledge_base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def init_knowledge_base():
    """初始化并验证知识库"""
    logger.info("=" * 70)
    logger.info("开始初始化知识库")
    logger.info("=" * 70)

    try:
        # 初始化知识库
        kb = initialize_knowledge_base("crypto_arbitrage_knowledge.db")

        # 验证表结构
        import sqlite3
        conn = sqlite3.connect("crypto_arbitrage_knowledge.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        expected_tables = [
            'strategies',
            'market_patterns',
            'risk_events',
            'trades',
            'performance_metrics',
            'project_progress',
            'knowledge_entries'
        ]

        table_names = [t[0] for t in tables]

        logger.info("\n✅ 知识库表检查：")
        for table in expected_tables:
            if table in table_names:
                # 统计记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"  ✓ {table:25} - {count} 条记录")
            else:
                logger.warning(f"  ✗ {table:25} - 表不存在")

        # 添加初始知识条目
        logger.info("\n📝 添加初始知识条目...")

        # 添加V2.8迭代记录
        kb.add_project_progress(
            version="2.8",
            date="2026-04-17",
            completed_tasks=[
                "环境变量配置系统 - 支持环境变量优先级加载",
                ".env 配置模板 - 完整的环境变量配置示例",
                "配置验证增强 - 自动检测 Memo0 API Key 和交易所配置",
                "AutoKnowledgeAccumulator 初始化 - 在 StrategyManager 中集成",
                "知识记录集成 - 交易决策、结果、模式自动记录",
                "智能决策引擎激活 - 策略选择时查询历史经验",
                "版本号统一 - 统一到 V2.8"
            ],
            in_progress_tasks=[
                "系统完整测试和验证",
                "配置 Memo0 API Key 以启用完整 AI 功能",
                "知识积累效果验证",
                "智能决策质量评估"
            ],
            planned_tasks=[
                "TradingAgents 深度集成",
                "高级可视化功能",
                "移动端支持",
                "多语言支持"
            ],
            notes="V2.8 完成了完整的知识循环激活"
        )

        # 添加策略知识
        kb.add_strategy(
            name="跨交易所套利",
            description="利用不同交易所之间的价格差异进行低风险套利",
            parameters={
                "min_profit_rate": 0.5,
                "max_position_size": 1000,
                "max_volatility": 5.0,
                "min_liquidity": 10000,
                "max_slippage": 0.1
            },
            performance_metrics={
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_profit_rate": 0.0
            }
        )

        kb.add_strategy(
            name="三角套利",
            description="利用三种货币之间的汇率差异进行套利",
            parameters={
                "min_profit_rate": 0.3,
                "max_position_size": 500,
                "scan_interval": 30
            },
            performance_metrics={
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_profit_rate": 0.0
            }
        )

        kb.add_strategy(
            name="统计套利",
            description="基于统计相关性进行配对交易套利",
            parameters={
                "min_profit_rate": 0.4,
                "max_position_size": 800,
                "lookback_period": 100,
                "z_score_threshold": 2.0
            },
            performance_metrics={
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_profit_rate": 0.0
            }
        )

        # 添加市场模式
        kb.add_market_pattern(
            pattern_name="高波动率市场",
            pattern_type="volatility",
            description="市场波动率显著高于平均水平，适合策略性持仓",
            indicators={
                "volatility_threshold": 3.0,
                "volume_increase": True
            },
            success_rate=0.65,
            sample_size=0
        )

        kb.add_market_pattern(
            pattern_name="低流动性市场",
            pattern_type="liquidity",
            description="市场流动性不足，可能导致交易延迟和滑点",
            indicators={
                "liquidity_threshold": 10000,
                "spread_widen": True
            },
            success_rate=0.40,
            sample_size=0
        )

        # 添加通用知识
        kb.add_knowledge_entry(
            category="风险管理",
            title="止损设置原则",
            content="止损应设置在技术支撑位以下，通常为入场价格的2-3%。高波动市场应适当扩大止损幅度。",
            tags=["止损", "风险管理", "仓位控制"],
            importance=5
        )

        kb.add_knowledge_entry(
            category="套利策略",
            title="跨交易所套利时机",
            content="当两个交易所的价差超过最小收益率阈值且流动性充足时执行套利。注意交易手续费和转账时间成本。",
            tags=["跨交易所", "套利时机", "交易成本"],
            importance=5
        )

        kb.add_knowledge_entry(
            category="技术分析",
            title="资金费率套利",
            content="当永续合约资金费率显著偏离零时，通过同时持有现货和合约仓位获取资金费率收益。注意合约强平风险。",
            tags=["资金费率", "永续合约", "无风险套利"],
            importance=4
        )

        # 获取统计信息
        stats = kb.get_statistics()

        logger.info("\n📊 知识库统计：")
        logger.info(f"  策略数量:         {stats['strategies_count']}")
        logger.info(f"  市场模式:         {stats['patterns_count']}")
        logger.info(f"  风险事件:         {stats['risk_events_count']}")
        logger.info(f"  交易记录:         {stats['trades_count']}")
        logger.info(f"  性能记录:         {stats['performance_records_count']}")
        logger.info(f"  知识条目:         {stats['knowledge_entries_count']}")
        logger.info(f"  总盈亏:           ${stats['total_profit']:.2f}")
        logger.info(f"  胜率:             {stats['win_rate']:.1%}")

        conn.close()

        logger.info("\n" + "=" * 70)
        logger.info("✅ 知识库初始化完成！")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"❌ 知识库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_knowledge_base()
    sys.exit(0 if success else 1)
