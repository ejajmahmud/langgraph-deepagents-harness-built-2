"""智能知识管理系统 V3.0

升级知识管理能力，实现智能知识提炼、分类、推荐和应用。

核心特性：
1. 智能知识提炼 - 从交易数据中自动提取有价值知识
2. 自动知识分类 - 基于内容的智能分类和标签
3. 知识推荐系统 - 基于上下文的知识推荐
4. 知识质量评估 - 自动评估知识的价值和可靠性
5. 知识图谱构建 - 构建知识之间的关联关系

V3.0新增：AI驱动的知识理解和应用
"""

import json
import logging
import re
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher
import hashlib

logger = logging.getLogger(__name__)


class IntelligentKnowledgeManager:
    """智能知识管理系统 V3.0

    自动管理和应用交易知识，提升系统智能化水平。
    """

    def __init__(self, storage_backend, config: Optional[Dict] = None):
        """初始化智能知识管理器

        Args:
            storage_backend: 存储后端（Memo0或SQLite）
            config: 配置字典
        """
        self.storage = storage_backend
        self.config = config or {}

        # 知识分类
        self.knowledge_categories = {
            "strategy": "策略相关",
            "risk": "风险管理",
            "market": "市场分析",
            "execution": "交易执行",
            "optimization": "系统优化",
            "error": "错误处理",
            "insight": "交易洞察",
            "pattern": "市场模式"
        }

        # 知识质量评分
        self.quality_factors = {
            "relevance": 0.3,      # 相关性
            "freshness": 0.2,      # 新鲜度
            "accuracy": 0.25,     # 准确性
            "uniqueness": 0.15,   # 独特性
            "applicability": 0.1   # 适用性
        }

        # 知识图谱
        self.knowledge_graph: Dict[str, Set[str]] = defaultdict(set)
        self.graph_lock = threading.Lock()

        # 知识缓存
        self.knowledge_cache: Dict[str, Tuple[float, Dict]] = {}
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5分钟

        # 知识统计
        self.knowledge_stats: Dict[str, Any] = defaultdict(int)

        # 后台处理线程
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        logger.info("IntelligentKnowledgeManager V3.0 initialized")

    def add_knowledge(
        self,
        content: str,
        category: str = "insight",
        metadata: Optional[Dict] = None,
        auto_classify: bool = True
    ) -> str:
        """添加知识条目

        Args:
            content: 知识内容
            category: 知识类别
            metadata: 元数据
            auto_classify: 是否自动分类

        Returns:
            知识ID
        """
        # 自动分类
        if auto_classify:
            category = self._classify_knowledge(content, category)

        # 计算知识指纹
        content_hash = self._compute_content_hash(content)

        # 检查重复
        if self._is_duplicate(content_hash):
            logger.debug(f"Duplicate knowledge detected: {content[:50]}...")
            return "duplicate"

        # 构建完整知识对象
        knowledge = {
            "content": content,
            "category": category,
            "metadata": metadata or {},
            "content_hash": content_hash,
            "created_at": datetime.now().isoformat(),
            "quality_score": 0.0,
            "tags": self._extract_tags(content),
            "references": []
        }

        # 计算质量评分
        knowledge["quality_score"] = self._calculate_quality_score(knowledge)

        # 存储知识
        knowledge_id = f"{category}_{content_hash[:8]}"
        try:
            # 存储到后端
            full_content = self._format_knowledge_for_storage(knowledge)
            self.storage.add_knowledge(category, full_content, metadata)

            # 更新知识图谱
            self._update_knowledge_graph(knowledge_id, knowledge)

            # 更新统计
            self.knowledge_stats["total_knowledge"] += 1
            self.knowledge_stats[f"category_{category}"] += 1

            logger.info(f"Knowledge added: {knowledge_id} (category={category}, quality={knowledge['quality_score']:.2f})")
            return knowledge_id

        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return "error"

    def _classify_knowledge(self, content: str, default_category: str) -> str:
        """自动分类知识

        Args:
            content: 知识内容
            default_category: 默认类别

        Returns:
            分类结果
        """
        content_lower = content.lower()

        # 关键词匹配
        category_keywords = {
            "strategy": ["策略", "strategy", "套利", "arbitrage", "交易", "trading"],
            "risk": ["风险", "risk", "止损", "stop loss", "回撤", "drawdown"],
            "market": ["市场", "market", "价格", "price", "趋势", "trend"],
            "execution": ["执行", "execution", "订单", "order", "交易所", "exchange"],
            "optimization": ["优化", "optimization", "性能", "performance", "参数", "parameter"],
            "error": ["错误", "error", "失败", "failed", "异常", "exception"],
            "pattern": ["模式", "pattern", "规律", "regularity", "周期", "cycle"]
        }

        # 计算每个类别的匹配分数
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            scores[category] = score

        # 返回得分最高的类别
        best_category = max(scores, key=scores.get) if scores else default_category
        return best_category if scores[best_category] > 0 else default_category

    def _compute_content_hash(self, content: str) -> str:
        """计算内容哈希

        Args:
            content: 内容

        Returns:
            哈希值
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _is_duplicate(self, content_hash: str) -> bool:
        """检查是否重复

        Args:
            content_hash: 内容哈希

        Returns:
            是否重复
        """
        # 这里应该检查存储中是否已存在相同哈希的知识
        # 简化实现：检查缓存
        cache_key = f"hash_{content_hash}"
        if cache_key in self.knowledge_cache:
            return True
        return False

    def _extract_tags(self, content: str) -> List[str]:
        """提取标签

        Args:
            content: 内容

        Returns:
            标签列表
        """
        tags = []

        # 提取数字和百分比
        numbers = re.findall(r'\d+\.?\d*%?', content)
        tags.extend([f"value:{num}" for num in numbers[:3]])  # 最多3个数值标签

        # 提取大写单词（可能是缩写）
        words = re.findall(r'\b[A-Z]{2,}\b', content)
        tags.extend([f"acronym:{word}" for word in set(words)])

        # 提取常见术语
        terms = ["BTC", "ETH", "USDT", "Binance", "OKX", "买入", "卖出", "做多", "做空"]
        for term in terms:
            if term in content:
                tags.append(f"term:{term}")

        return tags[:10]  # 最多10个标签

    def _calculate_quality_score(self, knowledge: Dict) -> float:
        """计算知识质量评分

        Args:
            knowledge: 知识对象

        Returns:
            质量评分 (0-1)
        """
        scores = {}

        # 相关性（基于类别匹配）
        category = knowledge["category"]
        scores["relevance"] = 1.0 if category in self.knowledge_categories else 0.5

        # 新鲜度（基于时间）
        created_at = datetime.fromisoformat(knowledge["created_at"])
        days_old = (datetime.now() - created_at).days
        scores["freshness"] = max(0.0, 1.0 - days_old / 30.0)  # 30天后降为0

        # 准确性（基于内容长度和结构）
        content_length = len(knowledge["content"])
        scores["accuracy"] = min(1.0, content_length / 100.0)  # 至少100字符

        # 独特性（基于标签数量）
        tag_count = len(knowledge.get("tags", []))
        scores["uniqueness"] = min(1.0, tag_count / 5.0)  # 至少5个标签

        # 适用性（基于元数据）
        metadata = knowledge.get("metadata", {})
        scores["applicability"] = 1.0 if metadata else 0.5

        # 加权平均
        total_score = sum(
            scores[factor] * weight
            for factor, weight in self.quality_factors.items()
        )

        return round(total_score, 3)

    def _format_knowledge_for_storage(self, knowledge: Dict) -> str:
        """格式化知识用于存储

        Args:
            knowledge: 知识对象

        Returns:
            格式化后的字符串
        """
        parts = [
            f"[{knowledge['category']}]",
            knowledge['content'],
            f"质量: {knowledge['quality_score']:.2f}",
            f"标签: {', '.join(knowledge['tags'])}"
        ]

        if knowledge['metadata']:
            parts.append(f"元数据: {json.dumps(knowledge['metadata'], ensure_ascii=False)}")

        return " | ".join(parts)

    def _update_knowledge_graph(self, knowledge_id: str, knowledge: Dict) -> None:
        """更新知识图谱

        Args:
            knowledge_id: 知识ID
            knowledge: 知识对象
        """
        with self.graph_lock:
            # 添加节点
            self.knowledge_graph[knowledge_id] = set()

            # 基于标签建立关联
            tags = knowledge.get("tags", [])
            for existing_id, existing_tags in self.knowledge_graph.items():
                if existing_id == knowledge_id:
                    continue

                # 计算标签相似度
                existing_tag_set = set(existing_tags)
                current_tag_set = set(tags)

                if existing_tag_set & current_tag_set:  # 有共同标签
                    self.knowledge_graph[knowledge_id].add(existing_id)
                    self.knowledge_graph[existing_id].add(knowledge_id)

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 10,
        min_quality: float = 0.0
    ) -> List[Dict[str, Any]]:
        """搜索知识

        Args:
            query: 查询内容
            category: 类别过滤
            top_k: 返回数量
            min_quality: 最低质量分数

        Returns:
            知识列表
        """
        # 检查缓存
        cache_key = f"search_{hash(query)}_{category}_{top_k}_{min_quality}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        # 从存储搜索
        try:
            results = self.storage.search_knowledge(query, category, top_k * 2)  # 搜索更多结果

            # 过滤和质量评分
            filtered_results = []
            for result in results:
                # 解析质量分数
                quality = self._extract_quality_from_result(result)
                if quality >= min_quality:
                    result["quality_score"] = quality
                    filtered_results.append(result)

            # 按质量排序
            filtered_results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

            # 应用知识图谱重排序
            filtered_results = self._rerank_with_knowledge_graph(query, filtered_results)

            # 限制返回数量
            final_results = filtered_results[:top_k]

            # 缓存结果
            self._add_to_cache(cache_key, final_results)

            return final_results

        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []

    def _extract_quality_from_result(self, result: Dict) -> float:
        """从结果中提取质量分数

        Args:
            result: 搜索结果

        Returns:
            质量分数
        """
        content = result.get("content", "")

        # 尝试从内容中解析质量分数
        match = re.search(r'质量:\s*([\d.]+)', content)
        if match:
            return float(match.group(1))

        # 默认质量分数
        return 0.5

    def _rerank_with_knowledge_graph(
        self,
        query: str,
        results: List[Dict]
    ) -> List[Dict]:
        """使用知识图谱重排序结果

        Args:
            query: 查询内容
            results: 搜索结果

        Returns:
            重排序后的结果
        """
        # 简化实现：基于相关性提升相关知识的权重
        query_lower = query.lower()

        for result in results:
            content = result.get("content", "").lower()
            # 计算查询与内容的相关性
            similarity = SequenceMatcher(None, query_lower, content).ratio()
            result["graph_boost"] = similarity

        # 混合质量分数和图谱提升
        for result in results:
            quality = result.get("quality_score", 0.5)
            boost = result.get("graph_boost", 0.0)
            result["final_score"] = quality * 0.7 + boost * 0.3

        # 按最终分数重排序
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        return results

    def recommend_knowledge(
        self,
        context: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """基于上下文推荐知识

        Args:
            context: 上下文信息
            top_k: 推荐数量

        Returns:
            推荐的知识列表
        """
        # 构建查询
        query_parts = []

        # 从上下文中提取关键信息
        if "strategy" in context:
            query_parts.append(f"策略 {context['strategy']}")
        if "symbol" in context:
            query_parts.append(f"交易对 {context['symbol']}")
        if "action" in context:
            query_parts.append(f"操作 {context['action']}")
        if "error" in context:
            query_parts.append(f"错误 {context['error']}")

        if not query_parts:
            return []

        query = " ".join(query_parts)

        # 搜索相关知识
        results = self.search_knowledge(query, top_k=top_k * 2)

        # 基于上下文相关性过滤
        context_keywords = set(query.lower().split())
        recommended = []

        for result in results:
            content = result.get("content", "").lower()
            content_keywords = set(content.split())

            # 计算关键词重叠度
            overlap = len(context_keywords & content_keywords) / len(context_keywords)

            if overlap > 0.2:  # 至少20%关键词重叠
                result["context_relevance"] = overlap
                recommended.append(result)

        # 按相关性排序
        recommended.sort(key=lambda x: x.get("context_relevance", 0), reverse=True)

        return recommended[:top_k]

    def extract_knowledge_from_trade(
        self,
        trade_result: Dict[str, Any]
    ) -> List[str]:
        """从交易结果中提取知识

        Args:
            trade_result: 交易结果

        Returns:
            提取的知识ID列表
        """
        extracted_knowledge = []

        try:
            # 1. 成功交易知识
            if trade_result.get("status") == "completed":
                profit = trade_result.get("actual_profit", 0)
                profit_rate = trade_result.get("profit_rate", 0)

                if profit > 0:
                    knowledge = (
                        f"成功套利交易：利润${profit:.2f}，利润率{profit_rate:.2f}%。"
                        f"策略：{trade_result.get('strategy', 'unknown')}，"
                        f"交易对：{trade_result.get('symbol', 'unknown')}。"
                    )
                    knowledge_id = self.add_knowledge(
                        knowledge,
                        category="strategy",
                        metadata={
                            "profit": profit,
                            "profit_rate": profit_rate,
                            "strategy": trade_result.get("strategy"),
                            "symbol": trade_result.get("symbol")
                        }
                    )
                    extracted_knowledge.append(knowledge_id)

            # 2. 失败交易知识
            elif trade_result.get("status") == "failed":
                error = trade_result.get("error", "unknown")
                knowledge = (
                    f"交易失败：{error}。"
                    f"策略：{trade_result.get('strategy', 'unknown')}，"
                    f"交易对：{trade_result.get('symbol', 'unknown')}。"
                )
                knowledge_id = self.add_knowledge(
                    knowledge,
                    category="error",
                    metadata={
                        "error": error,
                        "strategy": trade_result.get("strategy"),
                        "symbol": trade_result.get("symbol")
                    }
                )
                extracted_knowledge.append(knowledge_id)

            # 3. 性能知识
            execution_time = trade_result.get("execution_time", 0)
            if execution_time > 10:  # 执行时间超过10秒
                knowledge = (
                    f"交易执行较慢：{execution_time:.2f}秒。"
                    f"策略：{trade_result.get('strategy', 'unknown')}，"
                    f"建议优化执行流程。"
                )
                knowledge_id = self.add_knowledge(
                    knowledge,
                    category="optimization",
                    metadata={
                        "execution_time": execution_time,
                        "strategy": trade_result.get("strategy")
                    }
                )
                extracted_knowledge.append(knowledge_id)

        except Exception as e:
            logger.error(f"Failed to extract knowledge from trade: {e}")

        return extracted_knowledge

    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """获取知识统计信息

        Returns:
            统计信息字典
        """
        # 更新统计
        self.knowledge_stats["total_cached"] = len(self.knowledge_cache)
        self.knowledge_stats["graph_nodes"] = len(self.knowledge_graph)
        self.knowledge_stats["graph_edges"] = sum(len(edges) for edges in self.knowledge_graph.values()) // 2

        return dict(self.knowledge_stats)

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        if key in self.knowledge_cache:
            timestamp, value = self.knowledge_cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return value
            else:
                del self.knowledge_cache[key]
        return None

    def _add_to_cache(self, key: str, value: Any) -> None:
        """添加到缓存

        Args:
            key: 缓存键
            value: 缓存值
        """
        self.knowledge_cache[key] = (time.time(), value)

        # 限制缓存大小
        if len(self.knowledge_cache) > 1000:
            # 删除最旧的10%
            sorted_items = sorted(
                self.knowledge_cache.items(),
                key=lambda x: x[1][0]
            )
            for i in range(len(sorted_items) // 10):
                del self.knowledge_cache[sorted_items[i][0]]

    def clear_cache(self) -> None:
        """清除缓存"""
        self.knowledge_cache.clear()
        logger.info("Knowledge cache cleared")

    def export_knowledge_graph(self, filepath: Optional[str] = None) -> str:
        """导出知识图谱

        Args:
            filepath: 文件路径

        Returns:
            文件路径
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"knowledge_graph_{timestamp}.json"

        graph_data = {
            "nodes": list(self.knowledge_graph.keys()),
            "edges": [
                {"source": source, "target": target}
                for source, targets in self.knowledge_graph.items()
                for target in targets
            ],
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "total_nodes": len(self.knowledge_graph),
                "total_edges": sum(len(edges) for edges in self.knowledge_graph.values()) // 2
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Knowledge graph exported to {filepath}")
        return filepath


# ---------------------- 全局单例 ----------------------

_global_knowledge_manager: Optional[IntelligentKnowledgeManager] = None


def get_knowledge_manager(
    storage_backend,
    config: Optional[Dict] = None
) -> IntelligentKnowledgeManager:
    """获取全局知识管理器实例

    Args:
        storage_backend: 存储后端
        config: 配置字典

    Returns:
        IntelligentKnowledgeManager实例
    """
    global _global_knowledge_manager

    if _global_knowledge_manager is None:
        _global_knowledge_manager = IntelligentKnowledgeManager(
            storage_backend=storage_backend,
            config=config
        )

    return _global_knowledge_manager


def initialize_knowledge_manager(
    storage_backend,
    config: Optional[Dict] = None
) -> IntelligentKnowledgeManager:
    """初始化知识管理器

    Args:
        storage_backend: 存储后端
        config: 配置字典

    Returns:
        IntelligentKnowledgeManager实例
    """
    manager = get_knowledge_manager(storage_backend, config)
    logger.info("Knowledge manager initialized")
    return manager
