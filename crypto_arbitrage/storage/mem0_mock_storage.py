"""Memo0模拟存储 V16.2

在无真实Memo0 API Key的情况下，使用本地SQLite模拟Memo0接口，
使系统能够完整运行并实现100%模块连接。

主要功能：
1. 模拟Memo0的核心API（add_memory, search_memories, get_all_memories）
2. 使用本地SQLite持久化存储
3. 提供简单的语义搜索（基于文本匹配和评分）
4. 线程安全设计
5. 与真实Memo0Storage接口兼容
"""

import hashlib
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MockMemo0Storage:
    """Memo0模拟存储

    使用本地SQLite模拟Memo0 Platform API，
    提供兼容的接口用于系统完整运行。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化Memo0模拟存储

        Args:
            config: 配置字典（包含user_id, agent_id等）
        """
        self._config = config
        self._user_id = config.get("user_id", "crypto-arbitrage-user")
        self._agent_id = config.get("agent_id", "crypto-arbitrage")

        # SQLite数据库路径
        self._db_path = "mock_mem0_storage.db"

        # 线程安全锁
        self._db_lock = threading.Lock()

        # 预取缓存
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()

        # 初始化数据库
        self._init_database()

        logger.info(
            f"[OK] Memo0模拟存储初始化: "
            f"user_id={self._user_id}, agent_id={self._agent_id}"
        )

    def _init_database(self) -> None:
        """初始化SQLite数据库"""
        with self._db_lock:
            db_path = Path(self._db_path)
            if not db_path.exists():
                logger.info(f"创建Mock Memo0数据库: {self._db_path}")

            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row

            # 创建memories表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_agent
                ON memories(user_id, agent_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON memories(created_at DESC)
            """)

            conn.commit()
            conn.close()

            logger.info("[OK] Mock Memo0数据库初始化完成")

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def is_available(self) -> bool:
        """检查是否可用

        Mock存储始终可用
        """
        return True

    def add_memory(self, content: str, infer: bool = True) -> bool:
        """添加记忆

        Args:
            content: 记忆内容
            infer: 是否使用LLM自动提取事实（Mock中忽略此参数）

        Returns:
            是否成功
        """
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO memories (memory, user_id, agent_id)
                    VALUES (?, ?, ?)
                """, (content, self._user_id, self._agent_id))

                conn.commit()
                conn.close()

                logger.debug(f"Mock记忆添加成功: {content[:50]}...")
                return True

        except Exception as e:
            logger.error(f"Mock添加记忆失败: {e}")
            return False

    def add_memory_async(self, content: str, infer: bool = True) -> None:
        """异步添加记忆（非阻塞）

        Args:
            content: 记忆内容
            infer: 是否使用LLM自动提取事实
        """
        # Mock版本直接同步添加（简单实现）
        self.add_memory(content, infer)

    def search_memories(
        self,
        query: str,
        rerank: bool = False,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索记忆

        Args:
            query: 查询内容
            rerank: 是否启用重排序（Mock中基于简单匹配）
            top_k: 返回结果数量

        Returns:
            记忆列表
        """
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                # 使用LIKE进行简单文本匹配
                cursor.execute("""
                    SELECT memory, created_at, id
                    FROM memories
                    WHERE user_id = ? AND agent_id = ?
                    AND memory LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (self._user_id, self._agent_id, f"%{query}%", top_k * 2))

                rows = cursor.fetchall()
                conn.close()

                # 计算匹配分数
                results = []
                for row in rows:
                    score = self._calculate_match_score(query, row["memory"])
                    results.append({
                        "memory": row["memory"],
                        "created_at": row["created_at"],
                        "id": row["id"],
                        "score": score
                    })

                # 如果启用重排序，按分数排序
                if rerank:
                    results.sort(key=lambda x: x["score"], reverse=True)

                # 返回top_k结果
                return results[:top_k]

        except Exception as e:
            logger.error(f"Mock搜索记忆失败: {e}")
            return []

    def _calculate_match_score(self, query: str, memory: str) -> float:
        """计算匹配分数

        Args:
            query: 查询内容
            memory: 记忆内容

        Returns:
            匹配分数（0-1）
        """
        query_lower = query.lower()
        memory_lower = memory.lower()

        # 完全匹配
        if query_lower in memory_lower:
            # 基于位置和长度计算分数
            position = memory_lower.find(query_lower)
            length_ratio = len(query) / len(memory)
            position_score = 1.0 - (position / len(memory))
            return position_score * 0.7 + length_ratio * 0.3

        # 部分匹配（基于词汇重叠）
        query_words = set(query_lower.split())
        memory_words = set(memory_lower.split())

        if not query_words:
            return 0.0

        overlap = len(query_words & memory_words)
        overlap_ratio = overlap / len(query_words)

        return overlap_ratio * 0.5

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """获取所有记忆

        Returns:
            记忆列表
        """
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT memory, created_at, id
                    FROM memories
                    WHERE user_id = ? AND agent_id = ?
                    ORDER BY created_at DESC
                """, (self._user_id, self._agent_id))

                rows = cursor.fetchall()
                conn.close()

                results = []
                for row in rows:
                    results.append({
                        "memory": row["memory"],
                        "created_at": row["created_at"],
                        "id": row["id"]
                    })

                return results

        except Exception as e:
            logger.error(f"Mock获取所有记忆失败: {e}")
            return []

    def get_profile(self) -> str:
        """获取用户profile（所有记忆的摘要）

        Returns:
            格式化的记忆摘要
        """
        memories = self.get_all_memories()
        if not memories:
            return "暂无记忆"

        lines = [m.get("memory", "") for m in memories if m.get("memory")]
        return "\n".join(f"- {line}" for line in lines)

    def queue_prefetch(self, query: str) -> None:
        """预取相关记忆（非阻塞）

        Args:
            query: 查询内容
        """
        # Mock版本直接同步预取
        results = self.search_memories(query, top_k=5)
        if results:
            lines = [r.get("memory", "") for r in results if r.get("memory")]
            with self._prefetch_lock:
                self._prefetch_result = "\n".join(f"- {l}" for l in lines)

    def prefetch(self, query: str) -> str:
        """获取预取的记忆

        Args:
            query: 查询内容

        Returns:
            格式化后的记忆
        """
        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""

        if not result:
            return ""
        return f"## Mock Memo0 记忆\n{result}"

    def sync_conversation(
        self,
        user_content: str,
        assistant_content: str
    ) -> None:
        """同步对话（非阻塞）

        Args:
            user_content: 用户消息
            assistant_content: 助手回复
        """
        # Mock版本直接同步添加
        memory_content = f"用户: {user_content}\n助手: {assistant_content}"
        self.add_memory(memory_content, infer=False)

    def shutdown(self) -> None:
        """关闭并清理资源"""
        logger.info("Mock Memo0存储已关闭")

    # ==== 兼容方法别名 ====

    def search(
        self,
        query: str,
        rerank: bool = False,
        top_k: int = 10,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索方法 - search_memories的别名 (Memo0 API兼容方法)

        Args:
            query: 查询内容
            rerank: 是否启用重排序
            top_k: 返回结果数量
            limit: 限制结果数量（别名）
            **kwargs: 其他参数

        Returns:
            记忆列表
        """
        n = limit if limit is not None else top_k
        return self.search_memories(query, rerank, n)

    def add(
        self,
        content: str,
        infer: bool = True,
        memory: Optional[str] = None,
        **kwargs
    ) -> bool:
        """添加方法 - add_memory的别名 (Memo0 API兼容方法)

        Args:
            content: 记忆内容
            infer: 是否启用推理
            memory: 记忆内容（别名）
            **kwargs: 其他参数

        Returns:
            是否成功
        """
        mem = memory if memory is not None else content
        return self.add_memory(mem, infer)

    def add_knowledge(
        self,
        category: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加知识（兼容UnifiedStorage接口）

        Args:
            category: 知识类别
            content: 知识内容
            metadata: 元数据

        Returns:
            是否成功
        """
        full_content = f"[{category}] {content}"
        if metadata:
            full_content += f" | metadata: {json.dumps(metadata, ensure_ascii=False)}"
        return self.add_memory(full_content)

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索知识（兼容UnifiedStorage接口）

        Args:
            query: 查询内容
            category: 知识类别过滤
            top_k: 返回数量

        Returns:
            知识列表
        """
        results = self.search_memories(query, top_k=top_k)
        filtered = []
        for r in results:
            memory = r.get("memory", "")
            if category and not memory.startswith(f"[{category}]"):
                continue
            # 解析类别
            cat = ""
            content = memory
            if memory.startswith("["):
                cat_end = memory.find("]")
                if cat_end > 0:
                    cat = memory[1:cat_end]
                    content = memory[cat_end+1:].strip()
            filtered.append({
                "category": cat,
                "content": content,
                "score": r.get("score", 0),
                "created_at": r.get("created_at", "")
            })
        return filtered[:top_k]


def create_mock_mem0_storage(config: Dict[str, Any]) -> MockMemo0Storage:
    """创建Mock Memo0存储实例

    Args:
        config: 配置字典

    Returns:
        MockMemo0Storage实例
    """
    return MockMemo0Storage(config)
