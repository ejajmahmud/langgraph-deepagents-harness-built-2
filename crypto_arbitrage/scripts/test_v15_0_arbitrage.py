#!/usr/bin/env python3
"""
V15.0 模拟套利测试脚本
测试完整的套利流程：市场数据获取、机会识别、风险评估、交易执行
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from decimal import Decimal

sys.path.insert(0, '.')
sys.path.insert(0, 'crypto_arbitrage')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/test_v15_0_arbitrage.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def test_market_data_fetching() -> Dict[str, Any]:
    """测试市场数据获取"""
    logger.info("[TEST] 测试市场数据获取...")

    try:
        from storage.hybrid_memo0_storage import create_hybrid_storage
        import os

        # 获取配置
        config = {
            'hot_cache_size': 1000,
            'compression': True,
            'local_db_path': 'crypto_arbitrage_data.db',
            'mem0': {
                'api_key': os.getenv('MEM0_API_KEY', ''),
                'user_id': os.getenv('MEM0_USER_ID', 'crypto-arbitrage-v15-user'),
                'agent_id': os.getenv('MEM0_AGENT_ID', 'trading-bot-v15')
            }
        }

        storage = await create_hybrid_storage(config)

        # 模拟市场数据
        market_data = {
            "BTC/USDT": {
                "price": 67500.50,
                "volume": 245.67,
                "timestamp": datetime.now().isoformat()
            },
            "ETH/USDT": {
                "price": 3450.25,
                "volume": 1234.56,
                "timestamp": datetime.now().isoformat()
            },
            "BNB/USDT": {
                "price": 580.75,
                "volume": 567.89,
                "timestamp": datetime.now().isoformat()
            }
        }

        # 存储市场数据
        for symbol, data in market_data.items():
            await storage.store_data('market_data', symbol, data)
            logger.info(f"  [SUCCESS] 存储市场数据: {symbol}")

        # 检索市场数据
        for symbol in market_data.keys():
            data = await storage.retrieve_data('market_data', symbol)
            logger.info(f"  [SUCCESS] 检索市场数据: {symbol} = ${data.get('price', 0):.2f}")

        return {
            "status": "success",
            "data_points": len(market_data),
            "symbols": list(market_data.keys())
        }

    except Exception as e:
        logger.error(f"  [FAILED] 市场数据获取测试失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def test_opportunity_identification() -> Dict[str, Any]:
    """测试套利机会识别"""
    logger.info("[TEST] 测试套利机会识别...")

    try:
        from strategies.low_risk_arbitrage_engine import LowRiskArbitrageEngine, initialize_low_risk_arbitrage_engine, get_low_risk_arbitrage_engine

        initialize_low_risk_arbitrage_engine()
        engine = get_low_risk_arbitrage_engine()

        # 模拟套利机会
        opportunities = [
            {
                "pair": "BTC/USDT",
                "exchange1": "binance",
                "exchange2": "bybit",
                "price1": 67500.50,
                "price2": 67650.75,
                "spread": 150.25,
                "spread_pct": 0.22,
                "timestamp": datetime.now().isoformat()
            },
            {
                "pair": "ETH/USDT",
                "exchange1": "binance",
                "exchange2": "okx",
                "price1": 3450.25,
                "price2": 3460.50,
                "spread": 10.25,
                "spread_pct": 0.30,
                "timestamp": datetime.now().isoformat()
            }
        ]

        # 评估机会
        results = []
        for opp in opportunities:
            score = await engine.evaluate_opportunity(opp)
            results.append({
                "pair": opp["pair"],
                "spread": opp["spread"],
                "spread_pct": opp["spread_pct"],
                "score": score,
                "actionable": score > 0.7
            })
            logger.info(f"  [SUCCESS] 评估机会: {opp['pair']} - 得分: {score:.2f}")

        actionable_count = sum(1 for r in results if r["actionable"])

        return {
            "status": "success",
            "total_opportunities": len(opportunities),
            "actionable_opportunities": actionable_count,
            "details": results
        }

    except Exception as e:
        logger.error(f"  [FAILED] 套利机会识别测试失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def test_risk_assessment() -> Dict[str, Any]:
    """测试风险评估"""
    logger.info("[TEST] 测试风险评估...")

    try:
        from risk.deep_risk_manager import DeepRiskManager, initialize_deep_risk_manager, get_deep_risk_manager

        initialize_deep_risk_manager()
        risk_manager = get_deep_risk_manager()

        if risk_manager is None:
            raise Exception("风险管理器未初始化")

        # 模拟交易提案
        trade_proposals = [
            {
                "pair": "BTC/USDT",
                "action": "BUY",
                "amount": 0.01,
                "price": 67500.50,
                "expected_profit": 150.25,
                "risk_level": "LOW"
            },
            {
                "pair": "ETH/USDT",
                "action": "SELL",
                "amount": 0.5,
                "price": 3450.25,
                "expected_profit": 10.25,
                "risk_level": "MEDIUM"
            }
        ]

        # 风险评估
        results = []
        for proposal in trade_proposals:
            risk_assessment = await risk_manager.assess_risk(proposal)
            approved = await risk_manager.approve_trade(proposal)

            results.append({
                "pair": proposal["pair"],
                "action": proposal["action"],
                "expected_profit": proposal["expected_profit"],
                "risk_level": risk_assessment.get("risk_level", "UNKNOWN"),
                "risk_score": risk_assessment.get("risk_score", 0),
                "approved": approved
            })
            logger.info(f"  [SUCCESS] 风险评估: {proposal['pair']} - 批准: {approved}")

        approved_count = sum(1 for r in results if r["approved"])

        return {
            "status": "success",
            "total_proposals": len(trade_proposals),
            "approved_proposals": approved_count,
            "details": results
        }

    except Exception as e:
        logger.error(f"  [FAILED] 风险评估测试失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def test_trade_execution() -> Dict[str, Any]:
    """测试交易执行"""
    logger.info("[TEST] 测试交易执行...")

    try:
        from strategies.low_risk_arbitrage_engine import LowRiskArbitrageEngine, initialize_low_risk_arbitrage_engine, get_low_risk_arbitrage_engine
        from storage.hybrid_memo0_storage import create_hybrid_storage
        from storage.knowledge_base import initialize_knowledge_base, get_knowledge_base
        import os

        # 初始化引擎
        initialize_low_risk_arbitrage_engine()
        engine = get_low_risk_arbitrage_engine()

        # 创建存储
        config = {
            'hot_cache_size': 1000,
            'compression': True,
            'local_db_path': 'crypto_arbitrage_data.db',
            'mem0': {
                'api_key': os.getenv('MEM0_API_KEY', ''),
                'user_id': os.getenv('MEM0_USER_ID', 'crypto-arbitrage-v15-user'),
                'agent_id': os.getenv('MEM0_AGENT_ID', 'trading-bot-v15')
            }
        }
        storage = await create_hybrid_storage(config)

        # 初始化知识库
        kb = initialize_knowledge_base()

        # 模拟交易请求
        trade_request = {
            "pair": "BTC/USDT",
            "exchange1": "binance",
            "exchange2": "bybit",
            "action": "ARBITRAGE",
            "amount": 0.01,
            "price1": 67500.50,
            "price2": 67650.75,
            "expected_profit": 150.25,
            "timestamp": datetime.now().isoformat()
        }

        # 执行交易（模拟模式）
        execution_result = await engine.execute_arbitrage(trade_request)

        logger.info(f"  [SUCCESS] 交易执行状态: {execution_result.get('status', 'UNKNOWN')}")
        logger.info(f"  [SUCCESS] 实际利润: ${execution_result.get('profit', 0):.2f}")
        logger.info(f"  [SUCCESS] 执行时间: {execution_result.get('execution_time', 0):.3f}秒")

        # 记录交易到知识库
        if execution_result.get('status') == 'completed':
            trade_record = {
                "pair": trade_request["pair"],
                "action": "ARBITRAGE",
                "amount": trade_request["amount"],
                "entry_price": trade_request["price1"],
                "exit_price": trade_request["price2"],
                "profit": execution_result.get("profit", 0),
                "profit_pct": (execution_result.get("profit", 0) / trade_request["price1"]) * 100,
                "timestamp": datetime.now().isoformat(),
                "strategy": "low_risk_arbitrage",
                "risk_level": "LOW",
                "duration": execution_result.get("execution_time", 0)
            }

            await kb.add_transaction(trade_record)
            logger.info(f"  [SUCCESS] 交易已记录到知识库")

        return {
            "status": "success",
            "trade_status": execution_result.get('status', 'UNKNOWN'),
            "profit": execution_result.get('profit', 0),
            "execution_time": execution_result.get('execution_time', 0),
            "details": execution_result
        }

    except Exception as e:
        logger.error(f"  [FAILED] 交易执行测试失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def test_knowledge_base_integration() -> Dict[str, Any]:
    """测试知识库集成"""
    logger.info("[TEST] 测试知识库集成...")

    try:
        from storage.knowledge_base import initialize_knowledge_base, get_knowledge_base

        kb = initialize_knowledge_base()

        # 获取策略列表
        strategies = kb.get_all_knowledge('strategy')
        logger.info(f"  [SUCCESS] 策略数量: {len(strategies)}")

        # 获取最新交易记录
        transactions = kb.get_recent_trades(limit=5)
        logger.info(f"  [SUCCESS] 交易记录数: {len(transactions)}")

        # 计算统计数据
        if transactions:
            total_profit = sum(t.get('profit', 0) for t in transactions)
            win_rate = sum(1 for t in transactions if t.get('profit', 0) > 0) / len(transactions) * 100

            logger.info(f"  [SUCCESS] 总利润: ${total_profit:.2f}")
            logger.info(f"  [SUCCESS] 胜率: {win_rate:.2f}%")

            return {
                "status": "success",
                "strategies_count": len(strategies),
                "transactions_count": len(transactions),
                "total_profit": float(total_profit),
                "win_rate": float(win_rate)
            }

        return {
            "status": "success",
            "strategies_count": len(strategies),
            "transactions_count": 0,
            "total_profit": 0.0,
            "win_rate": 0.0
        }

    except Exception as e:
        logger.error(f"  [FAILED] 知识库集成测试失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def generate_test_report(results: Dict[str, Any]) -> str:
    """生成测试报告"""
    report = f"""
# V15.0 模拟套利测试报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试概况

- **总测试数**: 5
- **成功测试数**: {sum(1 for r in results.values() if r.get('status') == 'success')}
- **失败测试数**: {sum(1 for r in results.values() if r.get('status') == 'failed')}
- **成功率**: {sum(1 for r in results.values() if r.get('status') == 'success') / len(results) * 100:.1f}%

## 测试详情

### 1. 市场数据获取
- **状态**: {results.get('market_data', {}).get('status', 'UNKNOWN').upper()}
- **数据点数**: {results.get('market_data', {}).get('data_points', 0)}
- **交易对**: {results.get('market_data', {}).get('symbols', [])}

### 2. 套利机会识别
- **状态**: {results.get('opportunity_identification', {}).get('status', 'UNKNOWN').upper()}
- **总机会数**: {results.get('opportunity_identification', {}).get('total_opportunities', 0)}
- **可执行机会数**: {results.get('opportunity_identification', {}).get('actionable_opportunities', 0)}

### 3. 风险评估
- **状态**: {results.get('risk_assessment', {}).get('status', 'UNKNOWN').upper()}
- **总提案数**: {results.get('risk_assessment', {}).get('total_proposals', 0)}
- **批准提案数**: {results.get('risk_assessment', {}).get('approved_proposals', 0)}

### 4. 交易执行
- **状态**: {results.get('trade_execution', {}).get('status', 'UNKNOWN').upper()}
- **交易状态**: {results.get('trade_execution', {}).get('trade_status', 'UNKNOWN').upper()}
- **实际利润**: ${results.get('trade_execution', {}).get('profit', 0):.2f}
- **执行时间**: {results.get('trade_execution', {}).get('execution_time', 0):.3f}秒

### 5. 知识库集成
- **状态**: {results.get('knowledge_base', {}).get('status', 'UNKNOWN').upper()}
- **策略数量**: {results.get('knowledge_base', {}).get('strategies_count', 0)}
- **交易记录数**: {results.get('knowledge_base', {}).get('transactions_count', 0)}
- **总利润**: ${results.get('knowledge_base', {}).get('total_profit', 0):.2f}
- **胜率**: {results.get('knowledge_base', {}).get('win_rate', 0):.2f}%

## 结论

V15.0 系统模拟套利测试{'成功完成' if all(r.get('status') == 'success' for r in results.values()) else '存在问题'}

{'✅ 所有核心功能正常，可以进行下一步开发' if all(r.get('status') == 'success' for r in results.values()) else '❌ 部分功能需要修复'}

## 下一步

1. 修复失败的测试
2. 优化交易执行逻辑
3. 增加更多测试用例
4. 准备V15.1迭代

---

**报告生成**: V15.0 测试套件
"""

    return report


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("[START] V15.0 模拟套利测试开始")
    print("="*60 + "\n")

    results = {}

    # 运行测试
    try:
        # 1. 市场数据获取测试
        results['market_data'] = await test_market_data_fetching()
        print()

        # 2. 套利机会识别测试
        results['opportunity_identification'] = await test_opportunity_identification()
        print()

        # 3. 风险评估测试
        results['risk_assessment'] = await test_risk_assessment()
        print()

        # 4. 交易执行测试
        results['trade_execution'] = await test_trade_execution()
        print()

        # 5. 知识库集成测试
        results['knowledge_base'] = await test_knowledge_base_integration()
        print()

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        print(f"\n❌ 测试失败: {e}\n")
        return

    # 生成测试报告
    report = await generate_test_report(results)

    # 保存报告
    report_path = 'reports/test_v15_0_arbitrage_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[REPORT] 测试报告已保存到: {report_path}")

    # 保存测试结果JSON
    results_path = 'reports/test_v15_0_results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"[RESULTS] 测试结果已保存到: {results_path}")

    print("\n" + "="*60)
    print("[COMPLETE] V15.0 模拟套利测试完成")
    print("="*60 + "\n")

    # 显示摘要
    print(f"总测试数: {len(results)}")
    print(f"成功测试: {sum(1 for r in results.values() if r.get('status') == 'success')}")
    print(f"失败测试: {sum(1 for r in results.values() if r.get('status') == 'failed')}")
    print(f"成功率: {sum(1 for r in results.values() if r.get('status') == 'success') / len(results) * 100:.1f}%")
    print()


if __name__ == "__main__":
    asyncio.run(main())
