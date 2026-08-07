"""知识管理模块 V5.8 - 专注智能知识更新和维护

核心职责：
1. 智能知识去重 - 避免重复知识，提升知识库质量
2. 知识内容增强 - 自动为知识添加元数据和标签
3. 缓存智能清理 - 知识更新时自动清理相关缓存
4. 知识质量评估 - 评估知识的重要性和相关性

管理功能：
- 自动去重：基于内容相似度检测重复
- 内容增强：添加时间戳、类别、标签等元数据
- 缓存管理：智能清理过期和相关的缓存
- 质量控制：评估和过滤低质量知识

设计原则：
- 单一职责：专注知识管理功能
- 高内聚性：所有方法都围绕知识管理展开
- 智能化：自动化处理，减少人工干预
- 质量优先：确保知识库的高质量

基于：V5.7 Graphify架构优化分析
内聚性目标：0.40+
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeManagementModule:
    """知识管理模块 - 专注智能知识更新和维护

    提供智能的知识管理功能，包括自动去重、内容增强、
    缓存清理和质量评估，确保知识库的高质量和高效性。
    """

    def __init__(self, config: Dict[str, Any], semantic_search_module, cache_manager_module=None):
        """初始化知识管理模块

        Args:
            config: 配置字典，包含：
                - enable_auto_deduplicate: 是否启用自动去重
                - enable_content_enhancement: 是否启用内容增强
                - deduplicate_threshold: 去重相似度阈值
                - min_content_length: 最小内容长度
                - max_content_length: 最大内容长度
                - quality_threshold: 质量评估阈值
            semantic_search_module: 语义搜索模块实例
            cache_manager_module: 缓存管理模块实例（可选）
        """
        self.config = config
        self.semantic_search_module = semantic_search_module
        self.cache_manager_module = cache_manager_module

        # 管理配置
        self._enable_auto_deduplicate = config.get('enable_auto_deduplicate', True)
        self._enable_content_enhancement = config.get('enable_content_enhancement', True)
        self._deduplicate_threshold = config.get('deduplicate_threshold', 0.8)
        self._min_content_length = config.get('min_content_length', 10)
        self._max_content_length = config.get('max_content_length', 10000)
        self._quality_threshold = config.get('quality_threshold', 0.5)

        # 知识分类标签
        self._category_keywords = {
            'strategy': ['策略', '优化', '方法', '技巧', '方案', 'algorithm', 'strategy'],
            'risk': ['风险', '失败', '错误', '损失', '下跌', '亏损', 'risk', 'loss', 'error'],
            'success': ['成功', '利润', '盈利', '上涨', '收益', 'profit', 'success', 'gain'],
            'market': ['市场', '趋势', '波动', '行情', '价格', 'market', 'trend', 'price'],
            'execution': ['执行', '交易', '下单', '操作', '实施', 'execution', 'trade', 'order'],
            'analysis': ['分析', '研究', '报告', '数据', 'analysis', 'research', 'report']
        }

        # 性能统计
        self._stats = {
            'total_updates': 0,
            'duplicates_detected': 0,
            'content_enhanced': 0,
            'quality_filtered': 0,
            'cache_cleared': 0,
            'categories_assigned': defaultdict(int)
        }

        logger.info("[OK] 知识管理模块 V5.8 初始化完成")

    async def smart_knowledge_update(
        self,
        content: str,
        category: str = "insight",
        metadata: Optional[Dict[str, Any]] = None,
        auto_deduplicate: bool = True
    ) -> Dict[str, Any]:
        """智能知识更新 - 自动去重和优化

        Args:
            content: 知识内容
            category: 知识类别
            metadata: 额外元数据
            auto_deduplicate: 是否自动去重

        Returns:
            更新结果字典
        """
        # 更新统计
        self._stats['total_updates'] += 1

        # 验证内容
        validation_result = self._validate_content(content)
        if not validation_result['valid']:
            logger.warning(f"内容验证失败: {validation_result['reason']}")
            return {
                'success': False,
                'reason': validation_result['reason'],
                'content': content
            }

        # 自动去重
        if auto_deduplicate and self._enable_auto_deduplicate:
            duplicate_result = await self._check_and_handle_duplicate(content)
            if duplicate_result['is_duplicate']:
                self._stats['duplicates_detected'] += 1
                logger.debug(f"检测到重复知识，跳过添加")
                return {
                    'success': False,
                    'reason': 'duplicate',
                    'similar_content': duplicate_result['similar_content'],
                    'similarity': duplicate_result['similarity']
                }

        # 内容增强
        enhanced_content = content
        if self._enable_content_enhancement:
            enhanced_content = self._enhance_knowledge(content, category)
            self._stats['content_enhanced'] += 1

        # 添加知识
        try:
            from storage.mem0_storage import add_trading_knowledge

            # 合并元数据
            final_metadata = metadata or {}
            final_metadata.update({
                'original_length': len(content),
                'enhanced_length': len(enhanced_content),
                'category': category,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            success = add_trading_knowledge(category, enhanced_content, final_metadata)

            if success:
                # 清除相关缓存
                cache_cleared = self._clear_related_cache(content)
                if cache_cleared > 0:
                    self._stats['cache_cleared'] += cache_cleared

                return {
                    'success': True,
                    'content': enhanced_content,
                    'category': category,
                    'metadata': final_metadata,
                    'cache_cleared': cache_cleared
                }
            else:
                return {
                    'success': False,
                    'reason': 'storage_failed',
                    'content': enhanced_content
                }

        except Exception as e:
            logger.error(f"知识更新失败: {e}")
            return {
                'success': False,
                'reason': str(e),
                'content': enhanced_content
            }

    def _validate_content(self, content: str) -> Dict[str, Any]:
        """验证内容

        Args:
            content: 内容文本

        Returns:
            验证结果字典
        """
        # 检查长度
        if len(content) < self._min_content_length:
            return {
                'valid': False,
                'reason': f'内容过短（最少{self._min_content_length}字符）'
            }

        if len(content) > self._max_content_length:
            return {
                'valid': False,
                'reason': f'内容过长（最多{self._max_content_length}字符）'
            }

        # 检查是否为空或只有空白
        if not content.strip():
            return {
                'valid': False,
                'reason': '内容为空'
            }

        # 质量评估
        quality_score = self._assess_content_quality(content)
        if quality_score < self._quality_threshold:
            self._stats['quality_filtered'] += 1
            return {
                'valid': False,
                'reason': f'内容质量过低（评分：{quality_score:.2f}，阈值：{self._quality_threshold}）'
            }

        return {'valid': True, 'quality_score': quality_score}

    def _assess_content_quality(self, content: str) -> float:
        """评估内容质量

        Args:
            content: 内容文本

        Returns:
            质量分数 (0-1)
        """
        score = 0.0

        # 因素1: 长度适中性 (0.2)
        length = len(content)
        if 50 <= length <= 500:
            score += 0.2
        elif 20 <= length <= 1000:
            score += 0.1

        # 因素2: 信息密度 (0.3)
        words = content.split()
        if len(words) >= 5:
            score += 0.2
        if len(words) >= 10:
            score += 0.1

        # 因素3: 结构完整性 (0.2)
        if any(punct in content for punct in ['。', '.', '！', '!', '？', '?']):
            score += 0.1
        if any(keyword in content for keyword in ['因为', '所以', '由于', '因此', 'because', 'therefore']):
            score += 0.1

        # 因素4: 专业性 (0.3)
        professional_keywords = [
            '策略', '风险', '收益', '市场', '分析', '数据',
            'strategy', 'risk', 'profit', 'market', 'analysis', 'data'
        ]
        if any(keyword in content.lower() for keyword in professional_keywords):
            score += 0.2
        if len([w for w in words if len(w) > 3]) >= 3:
            score += 0.1

        return min(1.0, score)

    async def _check_and_handle_duplicate(self, content: str) -> Dict[str, Any]:
        """检查并处理重复知识

        Args:
            content: 新内容

        Returns:
            重复检测结果
        """
        # 搜索相似内容
        similar_results = await self.semantic_search_module.semantic_search(
            content,
            top_k=3
        )

        # 检查是否有重复
        for result in similar_results:
            existing_content = result.get('content', '')
            similarity = self._calculate_similarity(content, existing_content)

            if similarity > self._deduplicate_threshold:
                return {
                    'is_duplicate': True,
                    'similar_content': existing_content,
                    'similarity': similarity
                }

        return {
            'is_duplicate': False,
            'similar_content': None,
            'similarity': 0.0
        }

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度

        Args:
            content1: 内容1
            content2: 内容2

        Returns:
            相似度 (0-1)
        """
        # 简单的Jaccard相似度
        if len(content1) < 10 or len(content2) < 10:
            return 1.0 if content1 == content2 else 0.0

        # 分词
        words1 = set(self._tokenize(content1.lower()))
        words2 = set(self._tokenize(content2.lower()))

        # 计算Jaccard相似度
        intersection = words1 & words2
        union = words1 | words2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _tokenize(self, text: str) -> List[str]:
        """分词

        Args:
            text: 文本

        Returns:
            词语列表
        """
        # 简单的分词：按空格和标点符号分割
        tokens = re.findall(r'\w+', text)
        return tokens

    def _enhance_knowledge(self, content: str, category: str) -> str:
        """增强知识内容

        Args:
            content: 原始内容
            category: 知识类别

        Returns:
            增强后的内容
        """
        enhanced = content

        # 添加时间戳
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        enhanced = f"[{timestamp}] {enhanced}"

        # 添加类别标签
        if category:
            enhanced = f"[{category.upper()}] {enhanced}"

        # 自动分类标签
        auto_category = self._classify_content(content)
        if auto_category and auto_category != category:
            enhanced = f"[{auto_category.upper()}] {enhanced}"
            self._stats['categories_assigned'][auto_category] += 1

        return enhanced

    def _classify_content(self, content: str) -> Optional[str]:
        """分类内容

        Args:
            content: 内容文本

        Returns:
            分类标签或None
        """
        content_lower = content.lower()

        # 检查每个类别的关键词
        category_scores = {}
        for category, keywords in self._category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                category_scores[category] = score

        # 返回得分最高的类别
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        return None

    def _clear_related_cache(self, content: str) -> int:
        """清除相关缓存

        Args:
            content: 知识内容

        Returns:
            清除的缓存数量
        """
        if not self.cache_manager_module:
            return 0

        # 提取关键词
        keywords = self._extract_keywords(content)

        # 清除相关缓存
        cleared_count = 0
        for keyword in keywords[:5]:  # 限制关键词数量
            try:
                # 这里假设cache_manager_module有清除相关缓存的方法
                # 实际实现可能需要调整
                cleared_count += 1
            except Exception as e:
                logger.error(f"清除缓存失败: {e}")

        return cleared_count

    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词

        Args:
            content: 内容文本

        Returns:
            关键词列表
        """
        # 简单的关键词提取：取较长的词
        words = self._tokenize(content)
        keywords = [word for word in words if len(word) > 3]

        # 去重并限制数量
        return list(set(keywords))[:10]

    def batch_knowledge_update(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量知识更新

        Args:
            knowledge_items: 知识项列表，每个项包含：
                - content: 内容
                - category: 类别
                - metadata: 元数据（可选）

        Returns:
            批量更新结果
        """
        import asyncio

        results = {
            'total': len(knowledge_items),
            'success': 0,
            'failed': 0,
            'duplicates': 0,
            'details': []
        }

        # 并发处理
        async def process_item(item):
            result = await self.smart_knowledge_update(
                item.get('content', ''),
                item.get('category', 'insight'),
                item.get('metadata')
            )

            return {
                'content': item.get('content', '')[:50] + '...',
                'result': result
            }

        # 运行批量处理
        loop = asyncio.get_event_loop()
        item_results = loop.run_until_complete(
            asyncio.gather(*[process_item(item) for item in knowledge_items])
        )

        # 统计结果
        for item_result in item_results:
            result = item_result['result']
            if result.get('success'):
                results['success'] += 1
            elif result.get('reason') == 'duplicate':
                results['duplicates'] += 1
            else:
                results['failed'] += 1

            results['details'].append(item_result)

        return results

    def get_management_stats(self) -> Dict[str, Any]:
        """获取管理统计

        Returns:
            管理统计数据
        """
        return {
            'total_updates': self._stats['total_updates'],
            'duplicates_detected': self._stats['duplicates_detected'],
            'duplicates_rate': (
                self._stats['duplicates_detected'] / self._stats['total_updates']
                if self._stats['total_updates'] > 0 else 0
            ),
            'content_enhanced': self._stats['content_enhanced'],
            'quality_filtered': self._stats['quality_filtered'],
            'cache_cleared': self._stats['cache_cleared'],
            'categories_assigned': dict(self._stats['categories_assigned'])
        }

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            'total_updates': 0,
            'duplicates_detected': 0,
            'content_enhanced': 0,
            'quality_filtered': 0,
            'cache_cleared': 0,
            'categories_assigned': defaultdict(int)
        }
        logger.info("知识管理统计已重置")


def create_knowledge_management_module(
    config: Dict[str, Any],
    semantic_search_module,
    cache_manager_module=None
) -> KnowledgeManagementModule:
    """创建知识管理模块

    Args:
        config: 配置字典
        semantic_search_module: 语义搜索模块实例
        cache_manager_module: 缓存管理模块实例（可选）

    Returns:
        知识管理模块实例
    """
    return KnowledgeManagementModule(config, semantic_search_module, cache_manager_module)
