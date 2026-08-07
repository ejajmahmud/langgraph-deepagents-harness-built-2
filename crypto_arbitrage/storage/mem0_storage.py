"""
Memo0 存储集成层 - 对接 Mem0 AI Memory

将 Memo0 智能语义存储与现有知识库系统集成，
实现更智能的记忆和检索功能。

基于 hermes-agent 的 mem0 插件实现
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 全局单例
_mem0_provider: Optional['Memo0Storage'] = None
_mem0_config: Dict[str, Any] = {}

# 线程安全锁（V5.3添加）
_unified_storage_lock = threading.Lock()


def load_mem0_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载 Memo0 配置

    支持从环境变量和配置文件加载配置:
    - MEM0_API_KEY: Memo0 平台 API 密钥
    - MEM0_USER_ID: 用户标识符
    - MEM0_AGENT_ID: Agent 标识符

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    config = {
        "api_key": os.environ.get("MEM0_API_KEY", ""),
        "user_id": os.environ.get("MEM0_USER_ID", "crypto-arbitrage-user"),
        "agent_id": os.environ.get("MEM0_AGENT_ID", "crypto-arbitrage"),
        "rerank": True,
        "keyword_search": False,
    }

    # 如果没有提供 config_path，使用默认路径
    if config_path is None:
        config_path = os.environ.get("MEM0_CONFIG_PATH",
            str(Path.cwd() / "config" / "mem0.json"))

    # 从配置文件加载
    config_file = Path(config_path)
    if config_file.exists():
        try:
            file_cfg = json.loads(config_file.read_text(encoding="utf-8"))
            config.update({k: v for k, v in file_cfg.items()
                         if v is not None and v != ""})
        except Exception as e:
            logger.warning(f"加载 mem0 配置文件失败: {e}")

    return config


def initialize_mem0(config: Optional[Dict[str, Any]] = None) -> 'Memo0Storage':
    """初始化 Memo0 存储

    V16.2升级：无API Key时使用Mock存储，确保系统完整运行。

    Args:
        config: 配置字典，如果为 None 则从环境变量加载

    Returns:
        Memo0Storage 实例或Mock实例
    """
    global _mem0_provider, _mem0_config

    if config is None:
        config = load_mem0_config()

    _mem0_config = config

    if config.get("api_key"):
        _mem0_provider = Memo0Storage(config)
        logger.info("Memo0 存储初始化成功（真实API）")
    else:
        # V16.2：使用Mock存储，确保系统完整运行
        try:
            try:
                from storage.mem0_mock_storage import MockMemo0Storage
            except ImportError:
                from mem0_mock_storage import MockMemo0Storage
            _mem0_provider = MockMemo0Storage(config)
            logger.info("Memo0 存储初始化成功（Mock模式 - 本地存储）")
        except Exception as e:
            logger.warning(f"Memo0 Mock初始化失败: {e}")
            logger.warning("将使用本地 SQLite 知识库存储")
            _mem0_provider = None

    return _mem0_provider


def get_mem0_storage() -> Optional['Memo0Storage']:
    """获取 Memo0 存储实例（V16.2 自动初始化）

    首次调用时自动初始化，确保系统模块100%连接。

    Returns:
        Memo0Storage 实例或Mock实例
    """
    global _mem0_provider

    if _mem0_provider is None:
        # V16.2：自动初始化（使用Mock或真实API）
        _mem0_provider = initialize_mem0()

    return _mem0_provider


def is_mem0_available() -> bool:
    """检查 Memo0 是否可用

    Returns:
        是否可用
    """
    return _mem0_provider is not None and _mem0_provider.is_available()


class Memo0Storage:
    """Memo0 智能存储提供者

    实现语义搜索、自动去重、LLM辅助事实提取等高级功能。
    基于 Mem0 Platform API。
    """

    # 熔断器配置
    _BREAKER_THRESHOLD = 5
    _BREAKER_COOLDOWN_SECS = 120

    def __init__(self, config: Dict[str, Any]):
        """初始化 Memo0 存储

        Args:
            config: 配置字典
        """
        self._config = config
        self._client = None
        self._client_lock = threading.Lock()

        self._api_key = config.get("api_key", "")
        self._user_id = config.get("user_id", "crypto-arbitrage-user")
        self._agent_id = config.get("agent_id", "crypto-arbitrage")
        self._rerank = config.get("rerank", True)

        # 预取缓存
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()
        self._prefetch_thread = None

        # 异步同步线程
        self._sync_thread = None

        # 熔断器状态
        self._consecutive_failures = 0
        self._breaker_open_until = 0.0

        logger.info(f"Memo0 存储初始化: user_id={self._user_id}, agent_id={self._agent_id}")

    def is_available(self) -> bool:
        """检查是否可用

        Returns:
            API Key 是否配置
        """
        return bool(self._api_key)

    def _get_client(self):
        """获取 Memo0 客户端（线程安全）"""
        with self._client_lock:
            if self._client is not None:
                return self._client

            try:
                from mem0 import MemoryClient
                self._client = MemoryClient(api_key=self._api_key)
                return self._client
            except ImportError:
                raise RuntimeError(
                    "mem0ai 包未安装。运行: pip install mem0ai"
                )

    def _is_breaker_open(self) -> bool:
        """检查熔断器是否触发"""
        if self._consecutive_failures < self._BREAKER_THRESHOLD:
            return False
        if time.monotonic() >= self._breaker_open_until:
            self._consecutive_failures = 0
            return False
        return True

    def _record_success(self):
        """记录成功"""
        self._consecutive_failures = 0

    def _record_failure(self):
        """记录失败"""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._BREAKER_THRESHOLD:
            self._breaker_open_until = time.monotonic() + self._BREAKER_COOLDOWN_SECS
            logger.warning(
                f"Memo0 熔断器触发，连续 {self._consecutive_failures} 次失败."
                f"暂停 API 调用 {self._BREAKER_COOLDOWN_SECS} 秒"
            )

    def _read_filters(self) -> Dict[str, Any]:
        """获取读取过滤器"""
        return {"user_id": self._user_id}

    def _write_filters(self) -> Dict[str, Any]:
        """获取写入过滤器"""
        return {"user_id": self._user_id, "agent_id": self._agent_id}

    @staticmethod
    def _unwrap_results(response: Any) -> list:
        """规范化 Mem0 API 响应"""
        if isinstance(response, dict):
            return response.get("results", [])
        if isinstance(response, list):
            return response
        return []

    # ---------------------- 核心 API ----------------------

    def add_memory(self, content: str, infer: bool = True) -> bool:
        """添加记忆

        Args:
            content: 记忆内容
            infer: 是否使用 LLM 自动提取事实

        Returns:
            是否成功
        """
        if self._is_breaker_open():
            logger.warning("Memo0 熔断器触发中，跳过添加记忆")
            return False

        try:
            client = self._get_client()
            messages = [{"role": "user", "content": content}]
            client.add(messages, infer=infer, **self._write_filters())
            self._record_success()
            logger.debug(f"记忆添加成功: {content[:50]}...")
            return True
        except Exception as e:
            self._record_failure()
            logger.error(f"添加记忆失败: {e}")
            return False

    def add_memory_async(self, content: str, infer: bool = True) -> None:
        """异步添加记忆（非阻塞）

        Args:
            content: 记忆内容
            infer: 是否使用 LLM 自动提取事实
        """
        if self._is_breaker_open():
            return

        def _run():
            try:
                client = self._get_client()
                messages = [{"role": "user", "content": content}]
                client.add(messages, infer=infer, **self._write_filters())
                self._record_success()
            except Exception as e:
                self._record_failure()
                logger.debug(f"异步添加记忆失败: {e}")

        self._sync_thread = threading.Thread(
            target=_run, daemon=True, name="mem0-async-add"
        )
        self._sync_thread.start()

    def search_memories(
        self,
        query: str,
        rerank: bool = False,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索记忆

        Args:
            query: 查询内容
            rerank: 是否启用重排序
            top_k: 返回结果数量

        Returns:
            记忆列表
        """
        if self._is_breaker_open():
            logger.warning("Memo0 熔断器触发中，跳过搜索")
            return []

        try:
            client = self._get_client()
            results = self._unwrap_results(client.search(
                query=query,
                filters=self._read_filters(),
                rerank=rerank,
                top_k=min(top_k, 50),
            ))
            self._record_success()
            return results
        except Exception as e:
            self._record_failure()
            logger.error(f"搜索记忆失败: {e}")
            return []

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """获取所有记忆

        Returns:
            记忆列表
        """
        if self._is_breaker_open():
            return []

        try:
            client = self._get_client()
            memories = self._unwrap_results(client.get_all(
                filters=self._read_filters()
            ))
            self._record_success()
            return memories
        except Exception as e:
            self._record_failure()
            logger.error(f"获取所有记忆失败: {e}")
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
        if self._is_breaker_open():
            return

        def _run():
            try:
                client = self._get_client()
                results = self._unwrap_results(client.search(
                    query=query,
                    filters=self._read_filters(),
                    rerank=self._rerank,
                    top_k=5,
                ))
                if results:
                    lines = [
                        r.get("memory", "")
                        for r in results
                        if r.get("memory")
                    ]
                    with self._prefetch_lock:
                        self._prefetch_result = "\n".join(
                            f"- {l}" for l in lines
                        )
                self._record_success()
            except Exception as e:
                self._record_failure()
                logger.debug(f"Memo0 预取失败: {e}")

        self._prefetch_thread = threading.Thread(
            target=_run, daemon=True, name="mem0-prefetch"
        )
        self._prefetch_thread.start()

    def prefetch(self, query: str) -> str:
        """获取预取的记忆

        Args:
            query: 查询内容

        Returns:
            格式化后的记忆
        """
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=3.0)

        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""

        if not result:
            return ""
        return f"## Mem0 记忆\n{result}"

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
        if self._is_breaker_open():
            return

        def _sync():
            try:
                client = self._get_client()
                messages = [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content},
                ]
                client.add(messages, **self._write_filters())
                self._record_success()
            except Exception as e:
                self._record_failure()
                logger.debug(f"Memo0 对话同步失败: {e}")

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)

        self._sync_thread = threading.Thread(
            target=_sync, daemon=True, name="mem0-sync"
        )
        self._sync_thread.start()

    def shutdown(self) -> None:
        """关闭并清理资源"""
        for t in (self._prefetch_thread, self._sync_thread):
            if t and t.is_alive():
                t.join(timeout=5.0)

        with self._client_lock:
            self._client = None

        logger.info("Memo0 存储已关闭")


# ---------------------- 统一存储接口 ----------------------

class UnifiedStorage:
    """统一存储 - 智能选择 Memo0 或本地存储

    自动优先使用 Memo0（如果可用），否则降级到本地 SQLite。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化统一存储

        Args:
            config: 配置字典
        """
        self._mem0 = None
        self._sqlite_path = "crypto_arbitrage_knowledge.db"
        self._sqlite_conn = None
        self._use_mem0 = False

        # 尝试初始化 Memo0
        if config is not None:
            self._mem0 = initialize_mem0(config)
        else:
            self._mem0 = get_mem0_storage()

        self._use_mem0 = is_mem0_available()

        # 如果Memo0不可用，初始化SQLite持久化存储
        if not self._use_mem0:
            self._init_sqlite()

        logger.info(
            f"统一存储初始化: 使用 {'Memo0' if self._use_mem0 else 'SQLite持久化存储'}"
        )

    def _init_sqlite(self) -> None:
        """初始化SQLite持久化存储"""
        import sqlite3
        from pathlib import Path

        db_path = Path(self._sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._sqlite_conn = sqlite3.connect(self._sqlite_path, check_same_thread=False)
        self._sqlite_conn.row_factory = sqlite3.Row

        # 创建表结构
        cursor = self._sqlite_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_category
            ON knowledge(category)
        """)

        self._sqlite_conn.commit()
        logger.info(f"[OK] SQLite持久化存储初始化完成: {self._sqlite_path}")

    @property
    def is_using_mem0(self) -> bool:
        """是否使用 Memo0"""
        return self._use_mem0

    def add_knowledge(
        self,
        category: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加知识

        Args:
            category: 知识类别
            content: 知识内容
            metadata: 元数据

        Returns:
            是否成功
        """
        full_content = f"[{category}] {content}"
        if metadata:
            full_content += f" | 元数据: {json.dumps(metadata)}"

        if self._use_mem0 and self._mem0:
            return self._mem0.add_memory(full_content)

        # 降级到 SQLite持久化存储
        if self._sqlite_conn:
            try:
                cursor = self._sqlite_conn.cursor()
                cursor.execute("""
                    INSERT INTO knowledge (category, content, metadata, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    category,
                    content,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat()
                ))
                self._sqlite_conn.commit()
                return True
            except Exception as e:
                logger.error(f"SQLite存储失败: {e}")
                return False

        return False

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索知识

        Args:
            query: 查询内容
            category: 知识类别过滤
            top_k: 返回数量

        Returns:
            知识列表
        """
        if self._use_mem0 and self._mem0:
            results = self._mem0.search_memories(query, top_k=top_k)
            return [
                {"content": r.get("memory", ""), "score": r.get("score", 0)}
                for r in results
            ]

        # SQLite持久化存储搜索
        if self._sqlite_conn:
            try:
                cursor = self._sqlite_conn.cursor()

                # 构建查询条件
                params = []
                where_clauses = []
                if category:
                    where_clauses.append("category = ?")
                    params.append(category)

                where_clauses.append("(content LIKE ? OR metadata LIKE ?)")
                query_like = f"%{query}%"
                params.extend([query_like, query_like])

                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

                cursor.execute(f"""
                    SELECT category, content, metadata, timestamp, id
                    FROM knowledge
                    WHERE {where_sql}
                    ORDER BY id DESC
                    LIMIT ?
                """, params + [top_k])

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "category": row["category"],
                        "content": row["content"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "timestamp": row["timestamp"],
                        "id": row["id"],
                        "score": 0.8  # 简单匹配给一个固定分数
                    })

                return results[:top_k]

            except Exception as e:
                logger.error(f"SQLite搜索失败: {e}")
                return []

        return []

    def get_all_knowledge(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取所有知识

        Args:
            category: 知识类别过滤

        Returns:
            知识列表
        """
        if self._use_mem0 and self._mem0:
            memories = self._mem0.get_all_memories()
            results = []
            for m in memories:
                content = m.get("memory", "")
                # 解析类别
                if content.startswith("["):
                    cat_end = content.find("]")
                    if cat_end > 0:
                        cat = content[1:cat_end]
                        rest = content[cat_end+1:].strip()
                        if category is None or cat == category:
                            results.append({
                                "category": cat,
                                "content": rest,
                                "timestamp": m.get("created_at", "")
                            })
            return results

        # SQLite持久化存储查询
        if self._sqlite_conn:
            try:
                cursor = self._sqlite_conn.cursor()

                if category:
                    cursor.execute("""
                        SELECT category, content, metadata, timestamp
                        FROM knowledge
                        WHERE category = ?
                        ORDER BY id DESC
                    """, (category,))
                else:
                    cursor.execute("""
                        SELECT category, content, metadata, timestamp
                        FROM knowledge
                        ORDER BY id DESC
                    """)

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "category": row["category"],
                        "content": row["content"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "timestamp": row["timestamp"]
                    })

                return results

            except Exception as e:
                logger.error(f"SQLite查询失败: {e}")
                return []

        return []

    def prefetch_knowledge(self, query: str) -> str:
        """预取知识

        Args:
            query: 查询内容

        Returns:
            格式化的知识
        """
        if self._use_mem0 and self._mem0:
            return self._mem0.prefetch(query)
        return ""

    def queue_prefetch(self, query: str) -> None:
        """队列预取知识

        Args:
            query: 查询内容
        """
        if self._use_mem0 and self._mem0:
            self._mem0.queue_prefetch(query)

    def close(self) -> None:
        """关闭存储连接"""
        if self._use_mem0 and self._mem0:
            self._mem0.shutdown()

        # 关闭SQLite连接
        if self._sqlite_conn:
            self._sqlite_conn.close()
            self._sqlite_conn = None
            logger.info("SQLite连接已关闭")

        logger.info("统一存储已关闭")


# ---------------------- 便捷函数 ----------------------

_unified_storage: Optional[UnifiedStorage] = None


def get_unified_storage(config: Optional[Dict] = None) -> UnifiedStorage:
    """获取统一存储实例（V5.3线程安全版）

    Args:
        config: 配置字典

    Returns:
        统一存储实例
    """
    global _unified_storage

    # 双重检查锁定模式（线程安全）
    if _unified_storage is None:
        with _unified_storage_lock:
            # 再次检查，防止其他线程已经初始化
            if _unified_storage is None:
                _unified_storage = UnifiedStorage(config)
                logger.debug("统一存储初始化完成（线程安全）")

    return _unified_storage


def add_trading_knowledge(
    knowledge_type: str,
    content: str,
    metadata: Optional[Dict] = None
) -> bool:
    """添加交易知识（便捷函数）

    Args:
        knowledge_type: 知识类型 (strategy, risk, market, etc.)
        content: 知识内容
        metadata: 元数据

    Returns:
        是否成功
    """
    storage = get_unified_storage()
    return storage.add_knowledge(knowledge_type, content, metadata)


def search_trading_knowledge(
    query: str,
    knowledge_type: Optional[str] = None,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """搜索交易知识（便捷函数）

    Args:
        query: 查询内容
        knowledge_type: 知识类型过滤
        top_k: 返回数量

    Returns:
        知识列表
    """
    storage = get_unified_storage()
    return storage.search_knowledge(query, knowledge_type, top_k)
