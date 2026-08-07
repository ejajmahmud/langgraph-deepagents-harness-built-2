"""知识融合模块 V5.8 - 专注多源知识合并与洞察生成

核心职责：
1. 多源知识收集 - 从不同主题收集相关知识
2. 智能知识融合 - 支持三种融合策略
3. 洞察生成 - 基于融合知识生成可操作洞察
4. 风险评估 - 专门的风险知识融合与分析

融合策略：
- comprehensive: 综合融合 - 全面分析所有相关知识
- focused: 聚焦融合 - 专注高相关性知识
- risk_assessment: 风险评估融合 - 专门提取和分析风险知识

设计原则：
- 单一职责：专注知识融合功能
- 高内聚性：所有方法都围绕融合展开
- 可扩展性：易于添加新的融合策略
- 智能化：自动分类和推荐

基于：V5.7 Graphify架构优化分析
内聚性目标：0.42+
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeFusionModule:
    """知识融合模块 - 专注多源知识合并与洞察生成

    提供智能的知识融合功能，支持多种融合策略，
    能够从分散的知识中提取有价值的洞察和推荐。
    """

    def __init__(self, config: Dict[str, Any], semantic_search_module):
        """初始化知识融合模块

        Args:
            config: 配置字典，包含：
                - enable_knowledge_fusion: 是否启用知识融合
                - fusion_strategies: 支持的融合策略列表
                - min_relevance_score: 最小相关性分数
                - max_knowledge_per_topic: 每个主题最大知识条数
            semantic_search_module: 语义搜索模块实例
        """
        self.config = config
        self.enable_knowledge_fusion = config.get('enable_knowledge_fusion', True)
        self.semantic_search_module = semantic_search_module

        # 融合策略配置
        self._fusion_strategies = config.get('fusion_strategies', [
            'comprehensive',
            'focused',
            'risk_assessment'
        ])

        # 融合参数
        self._min_relevance_score = config.get('min_relevance_score', 0.7)
        self._max_knowledge_per_topic = config.get('max_knowledge_per_topic', 5)

        # 性能统计
        self._stats = {
            'total_fusions': 0,
            'fusion_by_type': defaultdict(int),
            'avg_knowledge_per_fusion': 0,
            'total_insights_generated': 0
        }

        logger.info("[OK] 知识融合模块 V5.8 初始化完成")

    async def knowledge_fusion(
        self,
        topics: List[str],
        fusion_type: str = "comprehensive",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """知识融合 - 合并多源知识

        Args:
            topics: 知识主题列表
            fusion_type: 融合类型 [comprehensive, focused, risk_assessment]
            top_k: 每个主题返回的知识数量

        Returns:
            融合后的知识字典
        """
        if not self.enable_knowledge_fusion:
            return {
                'enabled': False,
                'message': '知识融合未启用'
            }

        # 验证融合策略
        if fusion_type not in self._fusion_strategies:
            logger.warning(f"不支持的融合策略: {fusion_type}")
            return {
                'error': f'不支持的融合策略: {fusion_type}',
                'supported_strategies': self._fusion_strategies
            }

        # 更新统计
        self._stats['total_fusions'] += 1
        self._stats['fusion_by_type'][fusion_type] += 1

        # 执行融合
        try:
            result = await self._execute_fusion(topics, fusion_type, top_k)
            self._update_fusion_stats(result)
            return result
        except Exception as e:
            logger.error(f"知识融合失败: {e}")
            return {
                'error': str(e),
                'fusion_type': fusion_type,
                'topics': topics
            }

    async def _execute_fusion(
        self,
        topics: List[str],
        fusion_type: str,
        top_k: int
    ) -> Dict[str, Any]:
        """执行知识融合

        Args:
            topics: 知识主题列表
            fusion_type: 融合类型
            top_k: 每个主题返回的知识数量

        Returns:
            融合结果
        """
        # 收集多源知识
        all_knowledge = await self._collect_knowledge(topics, top_k)

        # 根据融合类型处理
        if fusion_type == "comprehensive":
            return await self._comprehensive_fusion(all_knowledge, topics)
        elif fusion_type == "focused":
            return await self._focused_fusion(all_knowledge, topics)
        elif fusion_type == "risk_assessment":
            return await self._risk_assessment_fusion(all_knowledge, topics)
        else:
            return {
                'fusion_type': fusion_type,
                'knowledge_count': len(all_knowledge),
                'knowledge': all_knowledge
            }

    async def _collect_knowledge(
        self,
        topics: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """收集多源知识

        Args:
            topics: 知识主题列表
            top_k: 每个主题返回的知识数量

        Returns:
            知识列表
        """
        all_knowledge = []

        # 并行搜索多个主题
        search_tasks = []
        for topic in topics:
            task = self.semantic_search_module.semantic_search(topic, top_k=top_k)
            search_tasks.append(task)

        # 等待所有搜索完成
        topic_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 收集有效结果
        for results in topic_results:
            if isinstance(results, list):
                all_knowledge.extend(results)
            elif isinstance(results, Exception):
                logger.error(f"主题搜索失败: {results}")

        return all_knowledge

    async def _comprehensive_fusion(
        self,
        knowledge: List[Dict[str, Any]],
        topics: List[str]
    ) -> Dict[str, Any]:
        """综合融合 - 全面分析所有相关知识

        Args:
            knowledge: 知识列表
            topics: 主题列表

        Returns:
            综合融合结果
        """
        # 按类别分组
        categories = self._categorize_knowledge(knowledge)

        # 生成综合报告
        result = {
            'fusion_type': 'comprehensive',
            'topics': topics,
            'total_knowledge': len(knowledge),
            'categories': dict(categories),
            'summary': self._generate_summary(categories),
            'recommendations': self._generate_recommendations(categories),
            'insights': self._generate_insights(categories),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    async def _focused_fusion(
        self,
        knowledge: List[Dict[str, Any]],
        topics: List[str]
    ) -> Dict[str, Any]:
        """聚焦融合 - 专注高相关性知识

        Args:
            knowledge: 知识列表
            topics: 主题列表

        Returns:
            聚焦融合结果
        """
        # 筛选高相关性知识
        high_relevance = [
            item for item in knowledge
            if item.get('score', 0) > self._min_relevance_score
        ]

        # 分析高相关性知识
        categories = self._categorize_knowledge(high_relevance)

        result = {
            'fusion_type': 'focused',
            'topics': topics,
            'total_knowledge': len(knowledge),
            'high_relevance_count': len(high_relevance),
            'high_relevance_knowledge': high_relevance,
            'relevance_threshold': self._min_relevance_score,
            'categories': dict(categories),
            'key_insights': self._extract_key_insights(high_relevance),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    async def _risk_assessment_fusion(
        self,
        knowledge: List[Dict[str, Any]],
        topics: List[str]
    ) -> Dict[str, Any]:
        """风险评估融合 - 专门提取和分析风险知识

        Args:
            knowledge: 知识列表
            topics: 主题列表

        Returns:
            风险评估融合结果
        """
        # 提取风险知识
        risk_knowledge = self._extract_risk_knowledge(knowledge)

        # 风险等级评估
        risk_level = self._assess_risk_level(risk_knowledge)

        # 风险因素分析
        risk_factors = self._analyze_risk_factors(risk_knowledge)

        result = {
            'fusion_type': 'risk_assessment',
            'topics': topics,
            'total_knowledge': len(knowledge),
            'risk_knowledge_count': len(risk_knowledge),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'risk_mitigation': self._generate_risk_mitigation(risk_factors),
            'risk_score': self._calculate_risk_score(risk_knowledge),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    def _categorize_knowledge(
        self,
        knowledge: List[Dict[str, Any]]
    ) -> defaultdict:
        """分类知识

        Args:
            knowledge: 知识列表

        Returns:
            分类后的知识字典
        """
        categories = defaultdict(list)

        for item in knowledge:
            content = item.get('content', '').lower()

            # 风险类
            if any(keyword in content for keyword in ['风险', '失败', '错误', '损失', '下跌']):
                categories['risk'].append(item)

            # 成功类
            elif any(keyword in content for keyword in ['成功', '利润', '盈利', '上涨', '收益']):
                categories['success'].append(item)

            # 策略类
            elif any(keyword in content for keyword in ['策略', '优化', '方法', '技巧', '方案']):
                categories['strategy'].append(item)

            # 市场类
            elif any(keyword in content for keyword in ['市场', '趋势', '波动', '行情', '价格']):
                categories['market'].append(item)

            # 执行类
            elif any(keyword in content for keyword in ['执行', '交易', '下单', '操作', '实施']):
                categories['execution'].append(item)

            # 通用类
            else:
                categories['general'].append(item)

        return categories

    def _generate_summary(
        self,
        categories: defaultdict
    ) -> str:
        """生成摘要

        Args:
            categories: 分类知识字典

        Returns:
            摘要文本
        """
        parts = []

        if 'success' in categories:
            parts.append(f"成功案例 {len(categories['success'])} 条")
        if 'risk' in categories:
            parts.append(f"风险记录 {len(categories['risk'])} 条")
        if 'strategy' in categories:
            parts.append(f"策略知识 {len(categories['strategy'])} 条")
        if 'market' in categories:
            parts.append(f"市场分析 {len(categories['market'])} 条")
        if 'execution' in categories:
            parts.append(f"执行经验 {len(categories['execution'])} 条")

        return " | ".join(parts) if parts else "无相关知识"

    def _generate_recommendations(
        self,
        categories: defaultdict
    ) -> List[str]:
        """生成推荐

        Args:
            categories: 分类知识字典

        Returns:
            推荐列表
        """
        recommendations = []

        # 风险推荐
        if 'risk' in categories and len(categories['risk']) > 3:
            recommendations.append("检测到较多风险记录，建议加强风险控制")

        # 成功推荐
        if 'success' in categories and len(categories['success']) > 5:
            recommendations.append("成功模式良好，可考虑加大仓位")

        # 策略推荐
        if 'strategy' in categories:
            recommendations.append(f"有 {len(categories['strategy'])} 条策略知识可供参考")

        # 市场推荐
        if 'market' in categories and len(categories['market']) > 3:
            recommendations.append("市场分析充足，可优化入场时机")

        return recommendations[:5]

    def _generate_insights(
        self,
        categories: defaultdict
    ) -> List[str]:
        """生成洞察

        Args:
            categories: 分类知识字典

        Returns:
            洞察列表
        """
        insights = []

        # 成功与风险比例
        success_count = len(categories.get('success', []))
        risk_count = len(categories.get('risk', []))

        if success_count > 0 and risk_count > 0:
            ratio = success_count / risk_count
            if ratio > 2:
                insights.append(f"成功率较高 ({success_count}:{risk_count})，当前策略有效")
            elif ratio < 0.5:
                insights.append(f"风险较高 ({success_count}:{risk_count})，需要调整策略")
            else:
                insights.append(f"风险收益平衡 ({success_count}:{risk_count})，保持当前策略")

        # 策略丰富度
        strategy_count = len(categories.get('strategy', []))
        if strategy_count > 5:
            insights.append(f"策略知识丰富 ({strategy_count} 条)，可尝试多策略组合")

        # 市场洞察
        market_count = len(categories.get('market', []))
        if market_count > 3:
            insights.append(f"市场分析充分 ({market_count} 条)，对市场理解较深")

        return insights

    def _extract_risk_knowledge(
        self,
        knowledge: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取风险知识

        Args:
            knowledge: 知识列表

        Returns:
            风险知识列表
        """
        risk_keywords = ['风险', '失败', '错误', '损失', '下跌', '亏损', '暴跌']

        return [
            item for item in knowledge
            if any(keyword in item.get('content', '') for keyword in risk_keywords)
        ]

    def _assess_risk_level(
        self,
        risk_knowledge: List[Dict[str, Any]]
    ) -> str:
        """评估风险等级

        Args:
            risk_knowledge: 风险知识列表

        Returns:
            风险等级 [LOW, MEDIUM, HIGH, CRITICAL]
        """
        risk_count = len(risk_knowledge)

        if risk_count == 0:
            return "LOW"
        elif risk_count < 3:
            return "MEDIUM"
        elif risk_count < 6:
            return "HIGH"
        else:
            return "CRITICAL"

    def _analyze_risk_factors(
        self,
        risk_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析风险因素

        Args:
            risk_knowledge: 风险知识列表

        Returns:
            风险因素分析
        """
        risk_factors = defaultdict(list)

        for item in risk_knowledge:
            content = item.get('content', '').lower()

            # 市场风险
            if any(keyword in content for keyword in ['市场', '波动', '趋势', '行情']):
                risk_factors['market'].append(item)

            # 执行风险
            elif any(keyword in content for keyword in ['执行', '下单', '滑点', '延迟']):
                risk_factors['execution'].append(item)

            # 策略风险
            elif any(keyword in content for keyword in ['策略', '参数', '设置']):
                risk_factors['strategy'].append(item)

            # 外部风险
            elif any(keyword in content for keyword in ['外部', '政策', '监管']):
                risk_factors['external'].append(item)

            return {
                'total_factors': len(risk_factors),
                'factors': dict(risk_factors),
                'most_common': max(risk_factors.items(), key=lambda x: len(x[1]))[0] if risk_factors else None
            }

    def _generate_risk_mitigation(
        self,
        risk_factors: Dict[str, Any]
    ) -> List[str]:
        """生成风险缓解建议

        Args:
            risk_factors: 风险因素分析

        Returns:
            风险缓解建议列表
        """
        mitigations = []

        factors = risk_factors.get('factors', {})

        if 'market' in factors and len(factors['market']) > 2:
            mitigations.append("建议加强市场监控，设置更严格的止损")

        if 'execution' in factors and len(factors['execution']) > 2:
            mitigations.append("建议优化执行策略，减少滑点和延迟影响")

        if 'strategy' in factors and len(factors['strategy']) > 2:
            mitigations.append("建议重新评估策略参数，降低风险敞口")

        if 'external' in factors:
            mitigations.append("建议关注外部环境变化，制定应急预案")

        return mitigations

    def _calculate_risk_score(
        self,
        risk_knowledge: List[Dict[str, Any]]
    ) -> float:
        """计算风险分数

        Args:
            risk_knowledge: 风险知识列表

        Returns:
            风险分数 (0-1)
        """
        if not risk_knowledge:
            return 0.0

        # 基于风险知识数量
        count_factor = min(1.0, len(risk_knowledge) / 10)

        # 基于平均相关性
        avg_score = sum(item.get('score', 0) for item in risk_knowledge) / len(risk_knowledge)

        # 综合计算
        return (count_factor + avg_score) / 2

    def _extract_key_insights(
        self,
        high_relevance: List[Dict[str, Any]]
    ) -> List[str]:
        """提取关键洞察

        Args:
            high_relevance: 高相关性知识列表

        Returns:
            关键洞察列表
        """
        insights = []

        # 提取前3个最高相关性的知识内容
        top_items = sorted(high_relevance, key=lambda x: x.get('score', 0), reverse=True)[:3]

        for item in top_items:
            content = item.get('content', '')
            if content:
                # 截取前100个字符作为洞察
                insight = content[:100] + "..." if len(content) > 100 else content
                insights.append({
                    'insight': insight,
                    'score': item.get('score', 0),
                    'category': self._classify_content(content)
                })

        return insights

    def _classify_content(self, content: str) -> str:
        """分类内容

        Args:
            content: 内容文本

        Returns:
            分类标签
        """
        content_lower = content.lower()

        if any(keyword in content_lower for keyword in ['风险', '失败', '错误']):
            return 'risk'
        elif any(keyword in content_lower for keyword in ['成功', '利润', '盈利']):
            return 'success'
        elif any(keyword in content_lower for keyword in ['策略', '优化', '方法']):
            return 'strategy'
        else:
            return 'general'

    def _update_fusion_stats(self, result: Dict[str, Any]) -> None:
        """更新融合统计

        Args:
            result: 融合结果
        """
        knowledge_count = result.get('total_knowledge', 0)

        # 更新平均知识数
        total_fusions = self._stats['total_fusions']
        current_avg = self._stats['avg_knowledge_per_fusion']
        self._stats['avg_knowledge_per_fusion'] = (
            (current_avg * (total_fusions - 1) + knowledge_count) / total_fusions
        )

        # 更新洞察生成数
        if 'insights' in result:
            self._stats['total_insights_generated'] += len(result['insights'])

    def get_fusion_stats(self) -> Dict[str, Any]:
        """获取融合统计

        Returns:
            融合统计数据
        """
        return {
            'total_fusions': self._stats['total_fusions'],
            'fusion_by_type': dict(self._stats['fusion_by_type']),
            'avg_knowledge_per_fusion': self._stats['avg_knowledge_per_fusion'],
            'total_insights_generated': self._stats['total_insights_generated']
        }

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            'total_fusions': 0,
            'fusion_by_type': defaultdict(int),
            'avg_knowledge_per_fusion': 0,
            'total_insights_generated': 0
        }
        logger.info("知识融合统计已重置")


def create_knowledge_fusion_module(
    config: Dict[str, Any],
    semantic_search_module
) -> KnowledgeFusionModule:
    """创建知识融合模块

    Args:
        config: 配置字典
        semantic_search_module: 语义搜索模块实例

    Returns:
        知识融合模块实例
    """
    return KnowledgeFusionModule(config, semantic_search_module)
