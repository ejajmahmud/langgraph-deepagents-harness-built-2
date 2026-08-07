"""深度Memo0集成模块 V3.1 - 高级知识应用

核心功能:
1. 语义搜索增强 - 多维度检索交易知识
2. 智能知识融合 - 合并多源知识形成洞察
3. 预测性分析 - 基于历史模式预测市场行为
4. 实时知识更新 - 智能知识去重和优化
"""

import logging
import time
from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class DeepMemo0Integration:
    """深度Memo0集成 - 高级知识应用"""

    def __init__(self, config: Dict[str, Any]):
        """初始化深度Memo0集成

        Args:
            config: 配置字典
        """
        self.config = config
        self.enable_semantic_search = config.get('enable_semantic_search', True)
        self.enable_knowledge_fusion = config.get('enable_knowledge_fusion', True)
        self.enable_predictive_analysis = config.get('enable_predictive_analysis', True)

        # 知识缓存
        self._knowledge_cache: Dict[str, Dict] = {}
        self._cache_ttl = config.get('cache_ttl', 300)  # 5分钟

        # 搜索历史
        self._search_history: List[Dict] = []
        self._max_history = 100

        logger.info("✅ 深度Memo0集成 V3.1 初始化完成")

    async def semantic_search(
        self,
        query: str,
        dimensions: List[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """语义搜索 - 多维度知识检索

        Args:
            query: 查询内容
            dimensions: 搜索维度 [strategy, risk, market, execution]
            top_k: 返回数量

        Returns:
            知识结果列表
        """
        if not self.enable_semantic_search:
            return await self._basic_search(query, top_k)

        dimensions = dimensions or ['strategy', 'risk', 'market', 'execution']
        all_results = []

        # 多维度搜索
        for dimension in dimensions:
            dimension_query = f"{dimension} {query}"
            results = await self._search_with_cache(dimension_query, top_k)
            all_results.extend(results)

        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, query)

        logger.debug(f"语义搜索: {query} -> {len(ranked_results)} 结果")
        return ranked_results[:top_k]

    async def _search_with_cache(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """带缓存的搜索

        Args:
            query: 查询内容
            top_k: 返回数量

        Returns:
            知识结果列表
        """
        cache_key = f"{query}:{top_k}"

        # 检查缓存
        cached = self._knowledge_cache.get(cache_key)
        if cached and (time.time() - cached['timestamp']) < self._cache_ttl:
            logger.debug(f"缓存命中: {query}")
            return cached['results']

        # 执行搜索
        try:
            from storage.mem0_storage import search_trading_knowledge
            results = search_trading_knowledge(query, top_k=top_k)

            # 更新缓存
            self._knowledge_cache[cache_key] = {
                'results': results,
                'timestamp': time.time()
            }

            # 记录搜索历史
            self._record_search(query, results)

            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def _basic_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """基础搜索

        Args:
            query: 查询内容
            top_k: 返回数量

        Returns:
            知识结果列表
        """
        try:
            from storage.mem0_storage import search_trading_knowledge
            return search_trading_knowledge(query, top_k=top_k)
        except Exception as e:
            logger.error(f"基础搜索失败: {e}")
            return []

    def _deduplicate_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重知识结果

        Args:
            results: 原始结果列表

        Returns:
            去重后的结果列表
        """
        seen_contents = set()
        unique_results = []

        for result in results:
            content = result.get('content', '')
            if content and content not in seen_contents:
                seen_contents.add(content)
                unique_results.append(result)

        return unique_results

    def _rank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """排序知识结果

        Args:
            results: 知识结果列表
            query: 原始查询

        Returns:
            排序后的结果列表
        """
        # 简单按分数排序
        return sorted(
            results,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

    def _record_search(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> None:
        """记录搜索历史

        Args:
            query: 查询内容
            results: 搜索结果
        """
        record = {
            'query': query,
            'result_count': len(results),
            'timestamp': time.time()
        }

        self._search_history.append(record)

        # 限制历史大小
        if len(self._search_history) > self._max_history:
            self._search_history = self._search_history[-self._max_history:]

    async def knowledge_fusion(
        self,
        topics: List[str],
        fusion_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """知识融合 - 合并多源知识

        Args:
            topics: 知识主题列表
            fusion_type: 融合类型 [comprehensive, focused, risk_assessment]

        Returns:
            融合后的知识字典
        """
        if not self.enable_knowledge_fusion:
            return {
                'enabled': False,
                'message': '知识融合未启用'
            }

        # 收集多源知识
        all_knowledge = []
        for topic in topics:
            results = await self.semantic_search(topic, top_k=5)
            all_knowledge.extend(results)

        # 按融合类型处理
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

    async def _comprehensive_fusion(
        self,
        knowledge: List[Dict[str, Any]],
        topics: List[str]
    ) -> Dict[str, Any]:
        """综合融合

        Args:
            knowledge: 知识列表
            topics: 主题列表

        Returns:
            融合结果
        """
        # 按类别分组
        categories = defaultdict(list)
        for item in knowledge:
            content = item.get('content', '')
            # 简单分类
            if '风险' in content or '失败' in content:
                categories['risk'].append(item)
            elif '成功' in content or '利润' in content:
                categories['success'].append(item)
            elif '策略' in content or '优化' in content:
                categories['strategy'].append(item)
            else:
                categories['general'].append(item)

        # 生成综合报告
        return {
            'fusion_type': 'comprehensive',
            'topics': topics,
            'total_knowledge': len(knowledge),
            'categories': dict(categories),
            'summary': self._generate_summary(categories),
            'recommendations': self._generate_recommendations(categories)
        }

    async def _focused_fusion(
        self,
        knowledge: List[Dict[str, Any]],
        topics: List[str]
    ) -> Dict[str, Any]:
        """聚焦融合

        Args:
            knowledge: 知识列表
            topics: 主题列表

        Returns:
            融合结果
        """
        # 筛选高相关性知识
        high_relevance = [
            item for item in knowledge
            if item.get('score', 0) > 0.7
        ]

        return {
            'fusion_type': 'focused',
            'topics': topics,
            'high_relevance_count': len(high_relevance),
            'high_relevance_knowledge': high_relevance
        }

    async def _risk_assessment_fusion(
        self,
        knowledge: List[Dict[str, Any]],
        topics: List[str]
    ) -> Dict[str, Any]:
        """风险评估融合

        Args:
            knowledge: 知识列表
            topics: 主题列表

        Returns:
            融合结果
        """
        # 提取风险知识
        risk_knowledge = [
            item for item in knowledge
            if '风险' in item.get('content', '') or
               '失败' in item.get('content', '') or
               '错误' in item.get('content', '')
        ]

        # 风险等级评估
        risk_level = self._assess_risk_level(risk_knowledge)

        return {
            'fusion_type': 'risk_assessment',
            'topics': topics,
            'risk_knowledge_count': len(risk_knowledge),
            'risk_level': risk_level,
            'risk_factors': risk_knowledge
        }

    def _generate_summary(
        self,
        categories: Dict[str, List]
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

        return " | ".join(parts) if parts else "无相关知识"

    def _generate_recommendations(
        self,
        categories: Dict[str, List]
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

        return recommendations[:3]

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

    async def predictive_analysis(
        self,
        symbol: str = "BTC/USDT",
        time_horizon: str = "short_term"
    ) -> Dict[str, Any]:
        """预测性分析 - 基于历史模式

        Args:
            symbol: 交易对
            time_horizon: 时间视野 [short_term, medium_term, long_term]

        Returns:
            预测分析字典
        """
        if not self.enable_predictive_analysis:
            return {
                'enabled': False,
                'message': '预测分析未启用'
            }

        try:
            # 搜索相关历史模式
            pattern_queries = [
                f"{symbol} 价格模式",
                f"{symbol} 波动规律",
                f"{symbol} 套利机会",
                "市场趋势预测"
            ]

            patterns = []
            for query in pattern_queries:
                results = await self.semantic_search(query, top_k=3)
                patterns.extend(results)

            # 分析模式
            analysis = self._analyze_patterns(patterns, symbol)

            return {
                'enabled': True,
                'symbol': symbol,
                'time_horizon': time_horizon,
                'pattern_count': len(patterns),
                'analysis': analysis,
                'confidence': self._calculate_confidence(patterns)
            }

        except Exception as e:
            logger.error(f"预测分析失败: {e}")
            return {
                'error': str(e)
            }

    def _analyze_patterns(
        self,
        patterns: List[Dict[str, Any]],
        symbol: str
    ) -> Dict[str, Any]:
        """分析模式

        Args:
            patterns: 模式列表
            symbol: 交易对

        Returns:
            分析结果字典
        """
        analysis = {
            'trend': 'neutral',
            'volatility': 'medium',
            'opportunity': 'normal',
            'signals': []
        }

        # 简单模式分析
        for pattern in patterns:
            content = pattern.get('content', '').lower()

            if '上涨' in content or 'bullish' in content:
                analysis['trend'] = 'bullish'
                analysis['signals'].append('上涨信号')
            elif '下跌' in content or 'bearish' in content:
                analysis['trend'] = 'bearish'
                analysis['signals'].append('下跌信号')

            if '高波动' in content or 'volatile' in content:
                analysis['volatility'] = 'high'

            if '机会' in content or 'arbitrage' in content:
                analysis['opportunity'] = 'high'

        return analysis

    def _calculate_confidence(
        self,
        patterns: List[Dict[str, Any]]
    ) -> float:
        """计算预测置信度

        Args:
            patterns: 模式列表

        Returns:
            置信度 (0-1)
        """
        if not patterns:
            return 0.0

        # 基于模式数量和相关性
        pattern_factor = min(1.0, len(patterns) / 10)

        # 基于平均相关性分数
        avg_score = sum(p.get('score', 0) for p in patterns) / len(patterns)

        return (pattern_factor + avg_score) / 2

    async def smart_knowledge_update(
        self,
        content: str,
        category: str = "insight",
        auto_deduplicate: bool = True
    ) -> bool:
        """智能知识更新 - 自动去重和优化

        Args:
            content: 知识内容
            category: 知识类别
            auto_deduplicate: 是否自动去重

        Returns:
            是否成功
        """
        if auto_deduplicate:
            # 检查重复
            existing = await self.semantic_search(content, top_k=3)
            for item in existing:
                existing_content = item.get('content', '')
                if self._is_duplicate(content, existing_content):
                    logger.debug("检测到重复知识，跳过添加")
                    return False

        # 添加知识
        try:
            from storage.mem0_storage import add_trading_knowledge

            # 增强知识内容
            enhanced_content = self._enhance_knowledge(content, category)

            success = add_trading_knowledge(category, enhanced_content)

            if success:
                # 清除相关缓存
                self._clear_related_cache(content)

            return success

        except Exception as e:
            logger.error(f"知识更新失败: {e}")
            return False

    def _is_duplicate(
        self,
        new_content: str,
        existing_content: str
    ) -> bool:
        """检查是否重复

        Args:
            new_content: 新内容
            existing_content: 已存在内容

        Returns:
            是否重复
        """
        # 简单的相似度检查
        if len(new_content) < 20 or len(existing_content) < 20:
            return new_content == existing_content

        # Jaccard相似度
        new_words = set(new_content.lower().split())
        existing_words = set(existing_content.lower().split())

        intersection = new_words & existing_words
        union = new_words | existing_words

        similarity = len(intersection) / len(union) if union else 0

        return similarity > 0.8

    def _enhance_knowledge(
        self,
        content: str,
        category: str
    ) -> str:
        """增强知识内容

        Args:
            content: 原始内容
            category: 知识类别

        Returns:
            增强后的内容
        """
        # 添加时间戳
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        enhanced = f"[{timestamp}] {content}"

        # 添加类别标签
        if category:
            enhanced = f"[{category}] {enhanced}"

        return enhanced

    def _clear_related_cache(self, content: str) -> None:
        """清除相关缓存

        Args:
            content: 知识内容
        """
        keys_to_remove = []

        for key in self._knowledge_cache:
            # 简单的关键词匹配
            if any(word in key for word in content.split()[:3]):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._knowledge_cache[key]

    def get_integration_stats(self) -> Dict[str, Any]:
        """获取集成统计

        Returns:
            统计数据字典
        """
        return {
            'cache_size': len(self._knowledge_cache),
            'search_history_size': len(self._search_history),
            'features_enabled': {
                'semantic_search': self.enable_semantic_search,
                'knowledge_fusion': self.enable_knowledge_fusion,
                'predictive_analysis': self.enable_predictive_analysis
            },
            'recent_searches': self._search_history[-10:]
        }

    def clear_cache(self) -> None:
        """清除缓存"""
        self._knowledge_cache.clear()
        logger.info("知识缓存已清除")

    def export_cache(self) -> Dict[str, Any]:
        """导出缓存

        Returns:
            缓存数据字典
        """
        return {
            'cache': dict(self._knowledge_cache),
            'search_history': self._search_history,
            'timestamp': time.time()
        }

    def import_cache(self, data: Dict[str, Any]) -> None:
        """导入缓存

        Args:
            data: 缓存数据字典
        """
        if 'cache' in data:
            self._knowledge_cache = data['cache']
        if 'search_history' in data:
            self._search_history = data['search_history']

        logger.info("缓存数据已导入")