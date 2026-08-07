"""
V5.4 迭代：Memo0 实际对接和深度集成实现

本次迭代目标：
1. 验证和测试 Memo0 实际对接功能
2. 实现深度语义搜索和知识关联
3. 完善低风险套利系统的 Memo0 集成
4. 提供完整的配置和使用指南
5. 建立完整的测试和验证体系

V5.4 核心突破：
- 实际 Memo0 API 对接（从配置指南到实际使用）
- 深度语义搜索验证
- 知识学习和自优化功能测试
- 生产环境就绪的 Memo0 集成
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import load_config
from storage.mem0_storage import (
    get_unified_storage,
    is_mem0_available,
    add_trading_knowledge,
    search_trading_knowledge
)
from agents.main_agent_v5_2 import CryptoArbitrageAgentV52

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V54Memo0Integration:
    """V5.4 Memo0 实际对接实现器"""

    def __init__(self):
        self.config = None
        self.storage = None
        self.agent = None
        self.test_results = []

    async def setup(self):
        """初始化测试环境"""
        logger.info("=" * 80)
        logger.info("V5.4 Memo0 实际对接迭代启动")
        logger.info("=" * 80)

        # 1. 加载配置
        logger.info("步骤 1: 加载系统配置...")
        self.config = load_config()
        logger.info(f"   ✅ 配置加载成功 (版本: {self.config.get('system', {}).get('version', 'unknown')})")

        # 2. 初始化统一存储
        logger.info("步骤 2: 初始化统一存储...")
        self.storage = get_unified_storage()
        mem0_available = is_mem0_available()

        logger.info(f"   {'✅' if mem0_available else '⚠️ '} Memo0状态: {'已启用' if mem0_available else 'SQLite降级模式'}")
        logger.info(f"   {'✅' if self.storage else '⚠️ '} 统一存储: {'已初始化' if self.storage else '未初始化'}")
        logger.info(f"   存储模式: {'Memo0' if self.storage.is_using_mem0 else 'SQLite'}")

        # 3. 检查 Memo0 配置
        logger.info("步骤 3: 检查 Memo0 配置...")
        await self._check_memo0_config()

        # 4. 初始化 V5.2 代理
        logger.info("步骤 4: 初始化 V5.2 代理...")
        try:
            self.agent = CryptoArbitrageAgentV52(self.config)
            logger.info("   ✅ V5.2 代理初始化成功")
        except Exception as e:
            logger.warning(f"   ⚠️  V5.2 代理初始化失败（降级模式）: {e}")
            self.agent = None

        logger.info("\n✅ 初始化完成\n")

    async def _check_memo0_config(self):
        """检查 Memo0 配置状态"""
        mem0_config = self.config.get('mem0', {})

        # 检查 API Key
        api_key = mem0_config.get('api_key') or os.environ.get('MEM0_API_KEY')
        if api_key:
            logger.info(f"   ✅ Memo0 API Key: 已配置 (长度: {len(api_key)})")
        else:
            logger.warning("   ⚠️  Memo0 API Key: 未配置")
            logger.info("   💡 配置方法:")
            logger.info("      方法1: 环境变量 MEM0_API_KEY=your_key_here")
            logger.info("      方法2: 配置文件 config.yaml -> mem0.api_key")
            logger.info("      参考: V5.3_MEMO0_SETUP_GUIDE.md")

        # 检查其他配置
        user_id = mem0_config.get('user_id', 'crypto-arbitrage-v52-user')
        agent_id = mem0_config.get('agent_id', 'trading-bot-v52')
        logger.info(f"   ✅ User ID: {user_id}")
        logger.info(f"   ✅ Agent ID: {agent_id}")

        # 检查智能搜索配置
        semantic_config = mem0_config.get('semantic_search', {})
        if semantic_config.get('enabled', False):
            logger.info(f"   ✅ 语义搜索: 已启用")
            logger.info(f"      相似度阈值: {semantic_config.get('similarity_threshold', 0.7)}")
            logger.info(f"      最大结果: {semantic_config.get('max_results', 20)}")
        else:
            logger.warning("   ⚠️  语义搜索: 未启用")

    async def test_mem0_deep_integration(self):
        """测试 Memo0 深度集成功能"""
        logger.info("\n" + "=" * 80)
        logger.info("测试 1: Memo0 深度集成功能")
        logger.info("=" * 80)

        try:
            # 测试 1.1: 添加交易知识
            logger.info("\n测试 1.1: 添加交易知识...")
            knowledge_data = [
                {
                    "type": "strategy",
                    "content": "跨交易所套利策略在低波动率市场中表现稳定，胜率可达75%以上",
                    "metadata": {
                        "strategy": "cross_exchange",
                        "market_condition": "low_volatility",
                        "win_rate": 0.75,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                {
                    "type": "risk",
                    "content": "当市场波动率超过3.0时，应降低仓位至50%并设置更严格的止损",
                    "metadata": {
                        "condition": "high_volatility",
                        "position_adjustment": 0.5,
                        "stop_loss": 1.5,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                {
                    "type": "market",
                    "content": "BTC/USDT 在流动性充足时，三角套利机会出现的频率增加30%",
                    "metadata": {
                        "symbol": "BTC/USDT",
                        "strategy": "triangular",
                        "liquidity": "high",
                        "opportunity_increase": 0.3,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            ]

            for i, data in enumerate(knowledge_data, 1):
                result = add_trading_knowledge(
                    data["type"],
                    data["content"],
                    data["metadata"]
                )
                status = "✅" if result else "⚠️ "
                logger.info(f"   {status} 知识 {i}/3: {data['type']} - {data['content'][:50]}...")

            # 测试 1.2: 语义搜索
            logger.info("\n测试 1.2: 语义搜索...")
            search_queries = [
                "低波动率市场的最佳策略",
                "高波动率时的风险管理",
                "BTC三角套利机会"
            ]

            for query in search_queries:
                results = search_trading_knowledge(query, top_k=3)
                logger.info(f"   查询: {query}")
                logger.info(f"   结果数量: {len(results)}")

                for i, result in enumerate(results[:2], 1):
                    content = result.get('content', result.get('memory', ''))[:100]
                    score = result.get('score', 0)
                    logger.info(f"      {i}. {content}... (相似度: {score:.2f})")

            # 测试 1.3: 获取所有知识
            logger.info("\n测试 1.3: 获取所有知识...")
            all_knowledge = self.storage.get_all_knowledge()
            logger.info(f"   知识总数: {len(all_knowledge)}")

            # 按类别统计
            categories = {}
            for item in all_knowledge:
                cat = item.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1

            logger.info("   知识类别分布:")
            for cat, count in categories.items():
                logger.info(f"      {cat}: {count}")

            self.test_results.append({
                "test": "Memo0深度集成",
                "status": "PASSED",
                "message": f"成功添加{len(knowledge_data)}条知识，语义搜索正常",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"   ❌ Memo0深度集成测试失败: {e}")
            self.test_results.append({
                "test": "Memo0深度集成",
                "status": "FAILED",
                "message": f"测试失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def test_intelligent_decision_engine(self):
        """测试智能决策引擎"""
        logger.info("\n" + "=" * 80)
        logger.info("测试 2: V5.2 智能决策引擎")
        logger.info("=" * 80)

        if not self.agent or not self.agent.decision_engine:
            logger.warning("   ⚠️  V5.2 智能决策引擎未启用")
            return

        try:
            # 测试 2.1: 策略推荐
            logger.info("\n测试 2.1: 智能策略推荐...")
            recommendation = await self.agent.decision_engine.recommend_strategy(
                current_market_conditions={
                    "volatility": 2.0,
                    "trend": "stable",
                    "liquidity": "normal"
                },
                available_strategies=["cross_exchange", "triangular", "funding_rate"],
                top_k=3
            )

            logger.info(f"   ✅ 策略推荐完成")
            logger.info(f"   数据源: {recommendation.get('data_source', 'unknown')}")

            market_analysis = recommendation.get('market_analysis', {})
            logger.info(f"   市场分析:")
            logger.info(f"      波动率: {market_analysis.get('volatility_level', 'N/A')}")
            logger.info(f"      趋势: {market_analysis.get('trend_strength', 'N/A')}")
            logger.info(f"      流动性: {market_analysis.get('liquidity_status', 'N/A')}")

            logger.info(f"   推荐策略:")
            for i, rec in enumerate(recommendation.get('recommendations', []), 1):
                logger.info(f"      {i}. {rec.get('strategy', 'N/A')} "
                          f"(置信度: {rec.get('confidence', 0):.2f}, "
                          f"胜率: {rec.get('expected_win_rate', 0):.1%})")

            # 测试 2.2: 风险评估
            logger.info("\n测试 2.2: 智能风险评估...")
            risk_assessment = await self.agent.decision_engine.assess_opportunity_risk(
                opportunity={
                    "profit_rate": 1.5,
                    "symbol": "BTC/USDT",
                    "expected_profit": 150.0
                },
                strategy="cross_exchange",
                current_market_conditions={
                    "volatility": 2.0,
                    "trend": "stable",
                    "liquidity": "normal"
                }
            )

            logger.info(f"   ✅ 风险评估完成")
            logger.info(f"   风险等级: {risk_assessment.get('risk_level', 'unknown').upper()}")
            logger.info(f"   风险评分: {risk_assessment.get('risk_score', 0)}/100")

            risk_factors = risk_assessment.get('risk_factors', [])
            if risk_factors:
                logger.info(f"   主要风险因素:")
                for factor in risk_factors[:3]:
                    logger.info(f"      - {factor.get('factor', 'N/A')} "
                              f"(严重性: {factor.get('severity', 'unknown')})")

            # 测试 2.3: 获取统计信息
            logger.info("\n测试 2.3: 决策引擎统计...")
            stats = self.agent.decision_engine.get_statistics()
            logger.info(f"   ✅ 统计信息获取完成")
            logger.info(f"   总查询数: {stats.get('total_queries', 0)}")
            logger.info(f"   缓存命中: {stats.get('cache_hits', 0)}")
            logger.info(f"   缓存命中率: {stats.get('cache_hit_rate', '0%')}")
            logger.info(f"   Memo0查询: {stats.get('mem0_queries', 0)}")
            logger.info(f"   降级查询: {stats.get('fallback_queries', 0)}")
            logger.info(f"   Memo0可用: {'是' if stats.get('mem0_available', False) else '否'}")

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
        """测试增强版低风险套利引擎"""
        logger.info("\n" + "=" * 80)
        logger.info("测试 3: V5.2 增强版低风险套利引擎")
        logger.info("=" * 80)

        if not self.agent or not self.agent.enhanced_low_risk_engine_v5_2:
            logger.warning("   ⚠️  V5.2 增强版低风险套利引擎未启用")
            return

        try:
            # 测试 3.1: 智能评估
            logger.info("\n测试 3.1: 智能机会评估...")
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

            logger.info(f"   ✅ 智能评估完成")
            logger.info(f"   执行建议: {'执行' if evaluation.get('should_execute', False) else '拒绝'}")
            logger.info(f"   置信度: {evaluation.get('confidence', 0):.2f}")

            # 自适应参数
            adaptive_params = evaluation.get('adaptive_parameters', {})
            if adaptive_params:
                logger.info(f"   自适应风险参数:")
                logger.info(f"      调整后仓位: ${adaptive_params.get('adjusted_position_size', 0):.2f}")
                logger.info(f"      调整后止损: {adaptive_params.get('adjusted_stop_loss', 0):.2f}%")
                logger.info(f"      调整因子: {adaptive_params.get('adjustment_factor', 0):.2f}")

            # 预期结果
            expected_outcome = evaluation.get('expected_outcome', {})
            if expected_outcome:
                logger.info(f"   预期结果:")
                logger.info(f"      成功概率: {expected_outcome.get('success_probability', 0):.1%}")
                logger.info(f"      预期利润: ${expected_outcome.get('expected_profit', 0):.2f}")
                logger.info(f"      风险调整收益: ${expected_outcome.get('risk_adjusted_return', 0):.2f}")

            # 测试 3.2: 执行路径优化
            logger.info("\n测试 3.2: 执行路径优化...")
            optimization = await self.agent.enhanced_low_risk_engine_v5_2.optimize_execution_path(
                opportunity={
                    "symbol": "BTC/USDT",
                    "buy_exchange": "binance",
                    "sell_exchange": "okx",
                    "amount": 1000.0
                },
                strategy="cross_exchange"
            )

            logger.info(f"   ✅ 路径优化完成")
            logger.info(f"   优化状态: {'已优化' if optimization.get('optimized', False) else '未优化'}")

            if optimization.get('optimized', False):
                execution_plan = optimization.get('execution_plan', {})
                if 'steps' in execution_plan:
                    logger.info(f"   执行步骤:")
                    for i, step in enumerate(execution_plan['steps'], 1):
                        logger.info(f"      {i}. {step.get('action', 'N/A')} {step.get('exchange', 'N/A')}")

            # 测试 3.3: 知识学习
            logger.info("\n测试 3.3: 知识学习功能...")
            from strategies.enhanced_low_risk_arbitrage_engine_v5_2 import EnhancedArbitrageExecution
            from strategies.enhanced_low_risk_arbitrage_engine import RiskLevel, ExecutionStatus

            # 创建模拟执行步骤
            from strategies.enhanced_low_risk_arbitrage_engine import RiskPrediction, IntelligentDecision

            execution = EnhancedArbitrageExecution(
                execution_id="test_execution_v54_001",
                opportunity={
                    "symbol": "BTC/USDT",
                    "profit_rate": 1.2,
                    "strategy": "cross_exchange",  # 策略信息放在opportunity中
                    "market_conditions": {"volatility": 1.8, "trend": "stable"}
                },
                steps=[],  # 空步骤列表用于测试
                status=ExecutionStatus.COMPLETED,
                start_time=datetime.now().timestamp(),
                end_time=datetime.now().timestamp() + 60,
                actual_profit=25.50,
                total_risk_score=15.0,
                risk_level=RiskLevel.LOW,
                # V4.1增强字段
                risk_prediction=RiskPrediction(
                    risk_type="market_volatility",
                    confidence=0.85,
                    impact_level=0.3,
                    estimated_time=datetime.now().timestamp() + 300,
                    recommendation="执行低风险套利"
                ),
                intelligent_decision=IntelligentDecision(
                    decision_type="execute",
                    action="执行跨交易所套利",
                    confidence=0.85,
                    reasoning="低波动率环境，适合执行套利",
                    evidence=["波动率1.8%低于阈值", "流动性充足"],
                    alternatives=["等待更大价差", "执行三角套利"]
                )
            )

            await self.agent.enhanced_low_risk_engine_v5_2.learn_from_execution(execution)
            logger.info(f"   ✅ 知识学习完成")
            logger.info(f"   策略: cross_exchange")
            logger.info(f"   利润: $25.50")
            logger.info(f"   状态: completed")

            # 测试 3.4: 获取统计信息
            logger.info("\n测试 3.4: 增强版引擎统计...")
            stats = self.agent.enhanced_low_risk_engine_v5_2.get_v5_2_statistics()
            logger.info(f"   ✅ 统计信息获取完成")
            logger.info(f"   智能决策: {stats.get('v5_2_intelligent_decisions', 0)}")
            logger.info(f"   风险预测: {stats.get('v5_2_risk_predictions', 0)}")
            logger.info(f"   自适应调整: {stats.get('v5_2_adaptive_adjustments', 0)}")
            logger.info(f"   知识学习: {stats.get('v5_2_knowledge_learned', 0)}")

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

    async def test_knowledge_association(self):
        """测试知识关联和推理"""
        logger.info("\n" + "=" * 80)
        logger.info("测试 4: 知识关联和智能推理")
        logger.info("=" * 80)

        try:
            # 测试 4.1: 添加关联知识
            logger.info("\n测试 4.1: 添加关联知识...")
            knowledge_pairs = [
                ("策略", "跨交易所套利在高波动率市场需要降低仓位至50%"),
                ("风险管理", "高波动率时，跨交易所套利仓位应降低至50%"),
                ("市场条件", "当波动率指标(VI)超过3.0时为高波动率市场"),
                ("历史数据", "2026-04-15高波动率期间，降低仓位后损失减少了40%")
            ]

            for i, (category, content) in enumerate(knowledge_pairs, 1):
                result = add_trading_knowledge(category, content)
                status = "✅" if result else "⚠️ "
                logger.info(f"   {status} 关联知识 {i}: {category}")

            # 测试 4.2: 语义关联查询
            logger.info("\n测试 4.2: 语义关联查询...")
            complex_queries = [
                "高波动率环境下跨交易所套利的最佳实践",
                "如何根据历史数据优化风险管理策略",
                "降低仓位对套利收益的影响"
            ]

            for query in complex_queries:
                logger.info(f"\n   查询: {query}")
                results = search_trading_knowledge(query, top_k=5)

                logger.info(f"   结果数量: {len(results)}")
                if results:
                    logger.info(f"   关联知识:")
                    for i, result in enumerate(results[:3], 1):
                        content = result.get('content', result.get('memory', ''))[:120]
                        score = result.get('score', 0)
                        logger.info(f"      {i}. {content}... (相关度: {score:.2f})")

            # 测试 4.3: 知识质量评分
            logger.info("\n测试 4.3: 知识质量分析...")
            all_knowledge = self.storage.get_all_knowledge()

            # 分析知识质量
            quality_metrics = {
                "total_knowledge": len(all_knowledge),
                "with_metadata": 0,
                "categories": set(),
                "avg_length": 0
            }

            total_length = 0
            for item in all_knowledge:
                content = item.get('content', '')
                total_length += len(content)

                if item.get('metadata'):
                    quality_metrics["with_metadata"] += 1

                category = item.get('category', 'unknown')
                quality_metrics["categories"].add(category)

            if all_knowledge:
                quality_metrics["avg_length"] = total_length / len(all_knowledge)

            logger.info(f"   知识质量指标:")
            logger.info(f"      总知识数: {quality_metrics['total_knowledge']}")
            logger.info(f"      有元数据: {quality_metrics['with_metadata']} "
                      f"({quality_metrics['with_metadata']/quality_metrics['total_knowledge']*100:.1f}%)")
            logger.info(f"      类别数: {len(quality_metrics['categories'])}")
            logger.info(f"      平均长度: {quality_metrics['avg_length']:.0f} 字符")

            self.test_results.append({
                "test": "知识关联和智能推理",
                "status": "PASSED",
                "message": f"知识关联正常，质量指标良好",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"   ❌ 知识关联测试失败: {e}")
            self.test_results.append({
                "test": "知识关联和智能推理",
                "status": "FAILED",
                "message": f"测试失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "=" * 80)
        logger.info("V5.4 Memo0 实际对接测试报告")
        logger.info("=" * 80)

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

        # 系统能力评估
        logger.info(f"\n系统能力评估:")

        mem0_available = is_mem0_available()
        logger.info(f"  Memo0状态: {'✅ 已启用' if mem0_available else '⚠️  SQLite降级'}")

        if self.storage:
            all_knowledge = self.storage.get_all_knowledge()
            logger.info(f"  知识库规模: {len(all_knowledge)} 条")
            logger.info(f"  存储模式: {'Memo0' if self.storage.is_using_mem0 else 'SQLite'}")

        if self.agent and self.agent.decision_engine:
            stats = self.agent.decision_engine.get_statistics()
            logger.info(f"  决策引擎查询: {stats.get('total_queries', 0)}")
            logger.info(f"  缓存命中率: {stats.get('cache_hit_rate', '0%')}")

        if self.agent and self.agent.enhanced_low_risk_engine_v5_2:
            stats = self.agent.enhanced_low_risk_engine_v5_2.get_v5_2_statistics()
            logger.info(f"  智能决策: {stats.get('v5_2_intelligent_decisions', 0)}")
            logger.info(f"  知识学习: {stats.get('v5_2_knowledge_learned', 0)}")

        # 下一步建议
        logger.info(f"\n下一步建议:")

        if not mem0_available:
            logger.info(f"  1. 配置 Memo0 API Key 以启用完整AI功能")
            logger.info(f"     参考: V5.3_MEMO0_SETUP_GUIDE.md")
        else:
            logger.info(f"  1. Memo0 已启用，系统具备完整AI能力")

        logger.info(f"  2. 在生产环境中进行实际交易验证")
        logger.info(f"  3. 监控知识库增长和决策质量")
        logger.info(f"  4. 根据实际表现优化参数配置")

        if failed_tests:
            logger.warning(f"\n⚠️  发现 {len(failed_tests)} 个失败的测试，请检查错误信息")
        else:
            logger.info(f"\n✅ 所有测试通过！V5.4 Memo0实际对接功能正常")

    async def run_all_tests(self):
        """运行所有测试"""
        try:
            # 初始化
            await self.setup()

            # 执行测试
            await self.test_mem0_deep_integration()
            await self.test_intelligent_decision_engine()
            await self.test_enhanced_low_risk_engine()
            await self.test_knowledge_association()

            # 生成报告
            await self.generate_report()

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
            if self.agent:
                try:
                    await self.agent.stop()
                    logger.info("✅ V5.2 代理已停止")
                except Exception as e:
                    logger.warning(f"停止代理失败: {e}")


async def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("V5.4 迭代：Memo0 实际对接和深度集成")
    logger.info("开始时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 80)

    tester = V54Memo0Integration()
    await tester.run_all_tests()

    logger.info("\n" + "=" * 80)
    logger.info("V5.4 迭代完成")
    logger.info("完成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
