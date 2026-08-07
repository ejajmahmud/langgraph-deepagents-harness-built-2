"""混合Memo0存储系统 V14.0

实现云存储 + 本地缓存的混合存储策略，优化性能和可靠性。
核心特性：
1. 混合存储策略 - 云端Memo0 + 本地向量存储
2. 智能路由 - 根据操作类型自动选择最优存储
3. 故障切换 - 云端故障时自动切换到本地
4. 数据同步 - 本地与云端数据自动同步
5. 性能优化 - 批量操作、异步索引、数据压缩
"""

import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from concurrent.futures import ThreadPoolExecutor
import gzip
import pickle

logger = logging.getLogger(__name__)


class StorageTier(Enum):
    """存储层级"""
    HOT_CACHE = "hot_cache"       # 热缓存（内存）
    LOCAL_FAST = "local_fast"     # 本地快速存储（SQLite）
    CLOUD_PRIMARY = "cloud_primary"  # 云端主存储（Memo0）
    CLOUD_BACKUP = "cloud_backup"    # 云端备份存储


class OperationType(Enum):
    """操作类型"""
    READ = "read"                 # 读取
    WRITE = "write"               # 写入
    SEARCH = "search"             # 搜索
    DELETE = "delete"             # 删除


@dataclass
class StorageStats:
    """存储统计"""
    total_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cloud_operations: int = 0
    local_operations: int = 0
    average_latency: float = 0.0
    error_count: int = 0
    last_sync_time: Optional[datetime] = None

    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def cloud_usage_rate(self) -> float:
        """云端使用率"""
        if self.total_operations == 0:
            return 0.0
        return self.cloud_operations / self.total_operations


@dataclass
class CachedItem:
    """缓存项"""
    key: str
    value: Any
    timestamp: float
    tier: StorageTier = StorageTier.LOCAL_FAST
    access_count: int = 0
    size_bytes: int = 0
    compressed: bool = False

    def is_expired(self, ttl: int) -> bool:
        """检查是否过期"""
        return (time.time() - self.timestamp) > ttl

    def increment_access(self) -> None:
        """增加访问计数"""
        self.access_count += 1
        self.timestamp = time.time()


class HybridMemo0Storage:
    """混合Memo0存储系统 V14.0

    实现智能的多层存储策略，优化性能和可靠性。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        local_storage_path: str = "./data/hybrid_storage.db",
        hot_cache_size: int = 1000,
        enable_compression: bool = True,
        enable_async_operations: bool = True,
        sync_interval: int = 300  # 同步间隔（秒）
    ):
        """初始化混合存储系统

        Args:
            config: Memo0配置（云存储）
            local_storage_path: 本地存储路径
            hot_cache_size: 热缓存大小
            enable_compression: 是否启用压缩
            enable_async_operations: 是否启用异步操作
            sync_interval: 数据同步间隔（秒）
        """
        self.config = config
        self.local_storage_path = local_storage_path
        self.hot_cache_size = hot_cache_size
        self.enable_compression = enable_compression
        self.enable_async_operations = enable_async_operations
        self.sync_interval = sync_interval

        # 存储层实例
        self._cloud_storage = None  # Memo0云存储
        self._local_storage = None   # 本地SQLite存储
        self._hot_cache = {}         # 热内存缓存

        # 缓存管理
        self._cache_lock = threading.Lock()
        self._cache_ttl = config.get('cache_ttl', 300)
        self._cache_stats = StorageStats()

        # 同步状态
        self._sync_lock = threading.Lock()
        self._last_sync_time: Optional[datetime] = None
        self._pending_sync_items: List[Dict] = []

        # 性能优化
        self._executor = ThreadPoolExecutor(max_workers=4) if enable_async_operations else None
        self._operation_history: List[Dict] = []
        self._max_history_size = 1000

        # 初始化存储层
        self._initialize_storage_layers()

        # 启动后台同步任务
        if self.enable_async_operations:
            self._start_background_sync()

        logger.info(
            f"✅ 混合Memo0存储系统 V14.0 初始化完成 "
            f"(hot_cache={hot_cache_size}, compression={enable_compression})"
        )

    def _initialize_storage_layers(self) -> None:
        """初始化所有存储层"""
        try:
            # 初始化云存储
            self._initialize_cloud_storage()

            # 初始化本地存储
            self._initialize_local_storage()

            # 预加载热缓存
            self._preload_hot_cache()

        except Exception as e:
            logger.error(f"存储层初始化失败: {e}")

    def _initialize_cloud_storage(self) -> None:
        """初始化云端Memo0存储"""
        try:
            from storage.mem0_storage import get_mem0_storage

            self._cloud_storage = get_mem0_storage()

            if self._cloud_storage:
                logger.info("✅ 云端Memo0存储初始化成功")
            else:
                logger.warning("⚠️ 云端Memo0存储不可用，将使用本地存储")

        except Exception as e:
            logger.warning(f"云端存储初始化失败: {e}")
            self._cloud_storage = None

    def _initialize_local_storage(self) -> None:
        """初始化本地存储"""
        try:
            import sqlite3
            from pathlib import Path

            # 确保目录存在
            Path(self.local_storage_path).parent.mkdir(parents=True, exist_ok=True)

            # 创建SQLite连接
            self._local_conn = sqlite3.connect(self.local_storage_path, check_same_thread=False)
            self._local_conn.row_factory = sqlite3.Row

            # 创建表结构
            self._create_local_tables()

            # 创建索引
            self._create_local_indexes()

            logger.info("✅ 本地存储初始化成功")

        except Exception as e:
            logger.error(f"本地存储初始化失败: {e}")
            self._local_conn = None

    def _create_local_tables(self) -> None:
        """创建本地存储表"""
        if not self._local_conn:
            return

        cursor = self._local_conn.cursor()

        # 主存储表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                size_bytes INTEGER DEFAULT 0,
                compressed BOOLEAN DEFAULT 0,
                cloud_synced BOOLEAN DEFAULT 0,
                sync_pending BOOLEAN DEFAULT 0
            )
        """)

        # 搜索索引表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_index (
                knowledge_id TEXT NOT NULL,
                vector_key TEXT NOT NULL,
                similarity_score REAL,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
            )
        """)

        # 缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                knowledge_id TEXT,
                tier TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                expires_at TEXT,
                size_bytes INTEGER DEFAULT 0
            )
        """)

        self._local_conn.commit()

    def _create_local_indexes(self) -> None:
        """创建本地存储索引"""
        if not self._local_conn:
            return

        cursor = self._local_conn.cursor()

        # 知识表索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON knowledge(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON knowledge(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cloud_synced ON knowledge(cloud_synced)")

        # 搜索索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vector_key ON search_index(vector_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_similarity ON search_index(similarity_score)")

        # 缓存索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)")

        self._local_conn.commit()

    def _preload_hot_cache(self) -> None:
        """预加载热缓存"""
        if not self._local_conn:
            return

        try:
            cursor = self._local_conn.cursor()

            # 加载最近访问的知识
            cursor.execute("""
                SELECT id, category, content
                FROM knowledge
                ORDER BY access_count DESC, updated_at DESC
                LIMIT ?
            """, (self.hot_cache_size // 2,))

            for row in cursor.fetchall():
                cache_key = f"knowledge:{row['id']}"
                self._hot_cache[cache_key] = CachedItem(
                    key=cache_key,
                    value={
                        'id': row['id'],
                        'category': row['category'],
                        'content': row['content']
                    },
                    timestamp=time.time(),
                    tier=StorageTier.HOT_CACHE
                )

            logger.info(f"预加载了 {len(self._hot_cache)} 个热缓存项")

        except Exception as e:
            logger.debug(f"热缓存预加载失败: {e}")

    def _start_background_sync(self) -> None:
        """启动后台同步任务"""
        def sync_loop():
            while True:
                try:
                    time.sleep(self.sync_interval)
                    self._sync_to_cloud()
                except Exception as e:
                    logger.error(f"后台同步失败: {e}")

        import threading
        sync_thread = threading.Thread(target=sync_loop, daemon=True)
        sync_thread.start()
        logger.info(f"后台同步任务已启动 (间隔: {self.sync_interval}s)")

    def add_knowledge(
        self,
        category: str,
        content: str,
        metadata: Optional[Dict] = None,
        immediate_cloud_sync: bool = False
    ) -> bool:
        """添加知识到存储系统

        Args:
            category: 知识类别
            content: 知识内容
            metadata: 元数据
            immediate_cloud_sync: 是否立即同步到云端

        Returns:
            是否成功
        """
        start_time = time.time()
        operation_id = self._generate_operation_id()

        try:
            # 生成唯一ID
            knowledge_id = self._generate_knowledge_id(category, content)

            # 压缩内容
            processed_content, compressed = self._compress_content(content)

            # 存储到本地
            if self._local_conn:
                cursor = self._local_conn.cursor()
                timestamp = datetime.now().isoformat()

                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge
                    (id, category, content, metadata, created_at, updated_at,
                     access_count, size_bytes, compressed, cloud_synced, sync_pending)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    knowledge_id,
                    category,
                    processed_content,
                    json.dumps(metadata) if metadata else None,
                    timestamp,
                    timestamp,
                    0,
                    len(processed_content.encode('utf-8')),
                    compressed,
                    immediate_cloud_sync,
                    not immediate_cloud_sync
                ))

                self._local_conn.commit()

            # 异步同步到云端
            if self._cloud_storage and not immediate_cloud_sync:
                self._queue_for_cloud_sync(knowledge_id, category, processed_content, metadata)

            # 立即同步到云端
            elif self._cloud_storage and immediate_cloud_sync:
                self._sync_single_to_cloud(knowledge_id, category, content, metadata)

            # 更新热缓存
            cache_key = f"knowledge:{knowledge_id}"
            self._update_hot_cache(cache_key, {
                'id': knowledge_id,
                'category': category,
                'content': content
            })

            # 记录操作
            self._record_operation(operation_id, OperationType.WRITE, StorageTier.LOCAL_FAST,
                                time.time() - start_time, True)

            return True

        except Exception as e:
            logger.error(f"添加知识失败: {e}")
            self._record_operation(operation_id, OperationType.WRITE, StorageTier.LOCAL_FAST,
                                time.time() - start_time, False)
            self._cache_stats.error_count += 1
            return False

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 10,
        use_cloud: bool = True
    ) -> List[Dict[str, Any]]:
        """搜索知识

        Args:
            query: 搜索查询
            category: 过滤类别
            top_k: 返回数量
            use_cloud: 是否使用云端搜索

        Returns:
            搜索结果列表
        """
        start_time = time.time()
        operation_id = self._generate_operation_id()

        try:
            results = []

            # 1. 检查热缓存
            cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
            cached_results = self._get_from_hot_cache(cache_key)

            if cached_results:
                logger.debug(f"搜索缓存命中: {query}")
                self._cache_stats.cache_hits += 1
                self._record_operation(operation_id, OperationType.SEARCH, StorageTier.HOT_CACHE,
                                    time.time() - start_time, True)
                return cached_results[:top_k]

            self._cache_stats.cache_misses += 1

            # 2. 搜索本地存储
            local_results = self._search_local(query, category, top_k)
            results.extend(local_results)

            # 3. 搜索云端存储
            if use_cloud and self._cloud_storage and len(results) < top_k:
                remaining = top_k - len(results)
                try:
                    cloud_results = self._cloud_storage.search_knowledge(query, category, remaining)
                    results.extend(cloud_results)
                    self._cache_stats.cloud_operations += 1
                except Exception as e:
                    logger.warning(f"云端搜索失败: {e}")

            # 4. 去重和排序
            unique_results = self._deduplicate_results(results)
            ranked_results = self._rank_results(unique_results, query)

            # 5. 缓存结果
            self._store_in_hot_cache(cache_key, ranked_results[:top_k])

            # 记录操作
            self._record_operation(operation_id, OperationType.SEARCH, StorageTier.LOCAL_FAST,
                                time.time() - start_time, True)
            self._cache_stats.total_operations += 1

            return ranked_results[:top_k]

        except Exception as e:
            logger.error(f"搜索知识失败: {e}")
            self._record_operation(operation_id, OperationType.SEARCH, StorageTier.LOCAL_FAST,
                                time.time() - start_time, False)
            self._cache_stats.error_count += 1
            return []

    def get_all_knowledge(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有知识

        Args:
            category: 过滤类别

        Returns:
            知识列表
        """
        try:
            if not self._local_conn:
                return []

            cursor = self._local_conn.cursor()

            if category:
                cursor.execute("""
                    SELECT id, category, content, metadata, created_at, updated_at
                    FROM knowledge
                    WHERE category = ?
                    ORDER BY updated_at DESC
                """, (category,))
            else:
                cursor.execute("""
                    SELECT id, category, content, metadata, created_at, updated_at
                    FROM knowledge
                    ORDER BY updated_at DESC
                """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'category': row['category'],
                    'content': self._decompress_content(row['content'], row.get('compressed', False)),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })

            return results

        except Exception as e:
            logger.error(f"获取知识列表失败: {e}")
            return []

    def _compress_content(self, content: str) -> Tuple[str, bool]:
        """压缩内容

        Args:
            content: 原始内容

        Returns:
            (压缩后的内容, 是否压缩)
        """
        if not self.enable_compression or len(content) < 500:
            return content, False

        try:
            compressed = gzip.compress(content.encode('utf-8'))
            if len(compressed) < len(content.encode('utf-8')):
                return compressed.decode('latin1'), True
        except Exception as e:
            logger.debug(f"内容压缩失败: {e}")

        return content, False

    def _decompress_content(self, content: str, compressed: bool) -> str:
        """解压缩内容

        Args:
            content: 压缩或原始内容
            compressed: 是否压缩

        Returns:
            解压后的内容
        """
        if not compressed:
            return content

        try:
            decompressed = gzip.decompress(content.encode('latin1'))
            return decompressed.decode('utf-8')
        except Exception as e:
            logger.debug(f"内容解压缩失败: {e}")
            return content

    def _search_local(
        self,
        query: str,
        category: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """搜索本地存储

        Args:
            query: 搜索查询
            category: 过滤类别
            top_k: 返回数量

        Returns:
            搜索结果列表
        """
        if not self._local_conn:
            return []

        try:
            cursor = self._local_conn.cursor()

            # 简单的关键词搜索
            query_lower = query.lower()
            keywords = query_lower.split()

            base_query = """
                SELECT id, category, content, metadata, created_at, updated_at,
                       access_count, compressed
                FROM knowledge
                WHERE 1=1
            """
            params = []

            if category:
                base_query += " AND category = ?"
                params.append(category)

            # 关键词匹配
            for keyword in keywords[:5]:  # 最多5个关键词
                base_query += " AND LOWER(content) LIKE ?"
                params.append(f"%{keyword}%")

            base_query += " ORDER BY access_count DESC, updated_at DESC LIMIT ?"
            params.append(top_k)

            cursor.execute(base_query, params)

            results = []
            for row in cursor.fetchall():
                # 更新访问计数
                self._update_access_count(row['id'])

                results.append({
                    'id': row['id'],
                    'category': row['category'],
                    'content': self._decompress_content(row['content'], row['compressed']),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'score': 1.0 - (row['access_count'] * 0.01)  # 简单的评分
                })

            self._cache_stats.local_operations += 1
            return results

        except Exception as e:
            logger.error(f"本地搜索失败: {e}")
            return []

    def _update_access_count(self, knowledge_id: str) -> None:
        """更新访问计数"""
        if not self._local_conn:
            return

        try:
            cursor = self._local_conn.cursor()
            cursor.execute("""
                UPDATE knowledge
                SET access_count = access_count + 1,
                    updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), knowledge_id))
            self._local_conn.commit()
        except Exception as e:
            logger.debug(f"更新访问计数失败: {e}")

    def _get_from_hot_cache(self, key: str) -> Optional[List]:
        """从热缓存获取数据"""
        with self._cache_lock:
            if key in self._hot_cache:
                cached_item = self._hot_cache[key]
                if not cached_item.is_expired(self._cache_ttl):
                    cached_item.increment_access()
                    return cached_item.value
                else:
                    del self._hot_cache[key]
        return None

    def _store_in_hot_cache(self, key: str, value: Any) -> None:
        """存储到热缓存"""
        with self._cache_lock:
            # 计算大小
            size_bytes = len(str(value).encode('utf-8'))

            # 如果缓存满了，删除最久未使用的项
            if len(self._hot_cache) >= self.hot_cache_size:
                oldest_key = min(
                    self._hot_cache.keys(),
                    key=lambda k: (
                        1 if self._hot_cache[k].is_expired(self._cache_ttl) else 0,
                        self._hot_cache[k].timestamp
                    )
                )
                del self._hot_cache[oldest_key]

            self._hot_cache[key] = CachedItem(
                key=key,
                value=value,
                timestamp=time.time(),
                tier=StorageTier.HOT_CACHE,
                size_bytes=size_bytes
            )

    def _update_hot_cache(self, key: str, value: Any) -> None:
        """更新热缓存"""
        with self._cache_lock:
            self._hot_cache[key] = CachedItem(
                key=key,
                value=value,
                timestamp=time.time(),
                tier=StorageTier.HOT_CACHE
            )

    def _sync_to_cloud(self) -> None:
        """同步数据到云端"""
        if not self._cloud_storage:
            return

        with self._sync_lock:
            try:
                # 获取待同步的数据
                cursor = self._local_conn.cursor()
                cursor.execute("""
                    SELECT id, category, content, metadata
                    FROM knowledge
                    WHERE sync_pending = 1
                    LIMIT 100
                """)

                pending_items = cursor.fetchall()

                if not pending_items:
                    logger.debug("没有待同步的数据")
                    return

                logger.info(f"开始同步 {len(pending_items)} 个知识项到云端")

                # 批量同步
                for item in pending_items:
                    try:
                        metadata = json.loads(item['metadata']) if item['metadata'] else {}

                        # 添加到云端
                        self._cloud_storage.add_knowledge(
                            category=item['category'],
                            content=self._decompress_content(item['content'], False),
                            metadata=metadata
                        )

                        # 标记为已同步
                        cursor.execute("""
                            UPDATE knowledge
                            SET cloud_synced = 1, sync_pending = 0
                            WHERE id = ?
                        """, (item['id'],))

                    except Exception as e:
                        logger.warning(f"同步单个项目失败 {item['id']}: {e}")
                        continue

                self._local_conn.commit()
                self._last_sync_time = datetime.now()

                logger.info(f"✅ 云端同步完成: {len(pending_items)} 项")

            except Exception as e:
                logger.error(f"云端同步失败: {e}")

    def _sync_single_to_cloud(
        self,
        knowledge_id: str,
        category: str,
        content: str,
        metadata: Optional[Dict]
    ) -> None:
        """同步单个知识到云端"""
        if not self._cloud_storage:
            return

        try:
            self._cloud_storage.add_knowledge(
                category=category,
                content=content,
                metadata=metadata
            )

            # 更新本地状态
            if self._local_conn:
                cursor = self._local_conn.cursor()
                cursor.execute("""
                    UPDATE knowledge
                    SET cloud_synced = 1, sync_pending = 0
                    WHERE id = ?
                """, (knowledge_id,))
                self._local_conn.commit()

        except Exception as e:
            logger.warning(f"单项目云端同步失败: {e}")

    def _queue_for_cloud_sync(
        self,
        knowledge_id: str,
        category: str,
        content: str,
        metadata: Optional[Dict]
    ) -> None:
        """排队等待云端同步"""
        self._pending_sync_items.append({
            'knowledge_id': knowledge_id,
            'category': category,
            'content': content,
            'metadata': metadata,
            'timestamp': time.time()
        })

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重搜索结果"""
        seen_ids = set()
        unique_results = []

        for result in results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)

        return unique_results

    def _rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """排序搜索结果"""
        # 简单按分数排序
        return sorted(
            results,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

    def _generate_knowledge_id(self, category: str, content: str) -> str:
        """生成知识ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{category}_{content_hash}_{timestamp}"

    def _generate_operation_id(self) -> str:
        """生成操作ID"""
        return f"op_{int(time.time() * 1000)}"

    def _record_operation(
        self,
        operation_id: str,
        operation_type: OperationType,
        tier: StorageTier,
        latency: float,
        success: bool
    ) -> None:
        """记录操作"""
        record = {
            'operation_id': operation_id,
            'type': operation_type.value,
            'tier': tier.value,
            'latency': latency,
            'success': success,
            'timestamp': time.time()
        }

        self._operation_history.append(record)

        # 限制历史大小
        if len(self._operation_history) > self._max_history_size:
            self._operation_history = self._operation_history[-self._max_history_size:]

        # 更新统计
        if success:
            self._cache_stats.total_operations += 1
            # 更新平均延迟
            if self._cache_stats.average_latency == 0:
                self._cache_stats.average_latency = latency
            else:
                self._cache_stats.average_latency = (
                    self._cache_stats.average_latency * 0.9 + latency * 0.1
                )

    def get_statistics(self) -> StorageStats:
        """获取存储统计"""
        with self._cache_lock:
            return StorageStats(
                total_operations=self._cache_stats.total_operations,
                cache_hits=self._cache_stats.cache_hits,
                cache_misses=self._cache_stats.cache_misses,
                cloud_operations=self._cache_stats.cloud_operations,
                local_operations=self._cache_stats.local_operations,
                average_latency=self._cache_stats.average_latency,
                error_count=self._cache_stats.error_count,
                last_sync_time=self._last_sync_time
            )

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        stats = self.get_statistics()

        return {
            'cloud_available': self._cloud_storage is not None,
            'local_available': self._local_conn is not None,
            'hot_cache_size': len(self._hot_cache),
            'cache_hit_rate': stats.cache_hit_rate(),
            'cloud_usage_rate': stats.cloud_usage_rate(),
            'average_latency_ms': stats.average_latency * 1000,
            'error_rate': stats.error_count / stats.total_operations if stats.total_operations > 0 else 0,
            'pending_sync_items': len(self._pending_sync_items),
            'last_sync_time': stats.last_sync_time.isoformat() if stats.last_sync_time else None
        }

    def shutdown(self) -> None:
        """关闭存储系统"""
        logger.info("正在关闭混合存储系统...")

        # 停止线程池
        if self._executor:
            self._executor.shutdown(wait=True)

        # 关闭数据库连接
        if self._local_conn:
            self._local_conn.close()

        # 清空缓存
        with self._cache_lock:
            self._hot_cache.clear()

        logger.info("✅ 混合存储系统已关闭")


def create_hybrid_storage(config: Dict[str, Any]) -> Optional[HybridMemo0Storage]:
    """创建混合存储系统

    Args:
        config: 配置字典

    Returns:
        HybridMemo0Storage实例
    """
    try:
        storage = HybridMemo0Storage(
            config=config.get('mem0', {}),
            local_storage_path=config.get('local_storage_path', './data/hybrid_storage.db'),
            hot_cache_size=config.get('hot_cache_size', 1000),
            enable_compression=config.get('enable_compression', True),
            enable_async_operations=config.get('enable_async_operations', True),
            sync_interval=config.get('sync_interval', 300)
        )

        return storage

    except Exception as e:
        logger.error(f"创建混合存储失败: {e}")
        return None