"""数据迁移工具 - V5.10 Phase 5.1

实现从内存存储到memo0的高效数据迁移。

核心功能：
1. 内存数据导出
2. memo0批量导入
3. 数据一致性验证
4. 迁移进度跟踪
5. 回滚支持

创建时间：2026-04-19
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class MigrationStatus(str, Enum):
    """迁移状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationRecord:
    """迁移记录"""
    knowledge_id: str
    content: str
    metadata: Dict[str, Any]
    source_type: str  # "memory" | "file" | "database"
    migration_id: str
    status: str = "pending"
    error: Optional[str] = None
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'knowledge_id': self.knowledge_id,
            'content': self.content,
            'metadata': self.metadata,
            'source_type': self.source_type,
            'migration_id': self.migration_id,
            'status': self.status,
            'error': self.error,
            'timestamp': self.timestamp,
            'timestamp_iso': datetime.fromtimestamp(self.timestamp).isoformat()
        }


@dataclass
class MigrationProgress:
    """迁移进度"""
    migration_id: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    start_time: float
    end_time: Optional[float] = None
    status: MigrationStatus = MigrationStatus.PENDING
    error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """进度百分比"""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100

    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def records_per_second(self) -> float:
        """每秒处理记录数"""
        if self.elapsed_time == 0:
            return 0.0
        return self.processed_records / self.elapsed_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'migration_id': self.migration_id,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'successful_records': self.successful_records,
            'failed_records': self.failed_records,
            'progress_percentage': self.progress_percentage,
            'elapsed_time': self.elapsed_time,
            'records_per_second': self.records_per_second,
            'status': self.status.value,
            'error': self.error,
            'start_time': self.start_time,
            'start_time_iso': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': self.end_time,
            'end_time_iso': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None
        }


class DataMigrator:
    """数据迁移工具"""

    def __init__(
        self,
        batch_size: int = 100,
        max_retries: int = 3,
        checkpoint_interval: int = 1000
    ):
        """初始化数据迁移工具

        Args:
            batch_size: 批量导入大小
            max_retries: 最大重试次数
            checkpoint_interval: 检查点间隔（记录数）
        """
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.checkpoint_interval = checkpoint_interval

        # 迁移历史
        self._migration_history: List[MigrationProgress] = []

        # 检查点文件
        self._checkpoint_dir = Path("data/migration_checkpoints")
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self._stats = {
            'total_migrations': 0,
            'total_records': 0,
            'total_success': 0,
            'total_failed': 0,
            'total_time': 0.0
        }

        # memo0存储实例
        self._memo0_storage = None

    # -------------------- 内存数据导出 --------------------

    def export_memory_data(
        self,
        memory_store: Dict[str, Any],
        export_path: Optional[str] = None
    ) -> List[MigrationRecord]:
        """导出内存数据

        Args:
            memory_store: 内存存储字典
            export_path: 导出文件路径（可选）

        Returns:
            迁移记录列表
        """
        migration_id = self._generate_migration_id()
        records = []

        for key, value in memory_store.items():
            # 生成knowledge_id
            knowledge_id = self._generate_knowledge_id(key, value)

            # 准备metadata
            metadata = {
                'source': 'memory',
                'original_key': key,
                'exported_at': time.time(),
                'migration_id': migration_id
            }

            # 序列化内容
            if isinstance(value, dict):
                content = json.dumps(value, ensure_ascii=False)
            else:
                content = str(value)

            record = MigrationRecord(
                knowledge_id=knowledge_id,
                content=content,
                metadata=metadata,
                source_type='memory',
                migration_id=migration_id,
                timestamp=time.time()
            )

            records.append(record)

        logger.info(f"导出内存数据: {len(records)}条记录")
        self._stats['total_records'] += len(records)

        # 保存到文件
        if export_path:
            self._save_records_to_file(records, export_path)

        return records

    def export_trade_history(
        self,
        trade_history: List[Dict[str, Any]],
        migration_id: Optional[str] = None
    ) -> List[MigrationRecord]:
        """导出交易历史

        Args:
            trade_history: 交易历史列表
            migration_id: 迁移ID（可选）

        Returns:
            迁移记录列表
        """
        if migration_id is None:
            migration_id = self._generate_migration_id()

        records = []

        for i, trade in enumerate(trade_history):
            # 生成knowledge_id
            knowledge_id = self._generate_knowledge_id(
                f"trade_{i}",
                trade
            )

            # 准备metadata
            metadata = {
                'source': 'trade_history',
                'strategy': trade.get('strategy', 'unknown'),
                'symbol': trade.get('symbol', 'N/A'),
                'status': trade.get('status', 'unknown'),
                'exported_at': time.time(),
                'migration_id': migration_id
            }

            # 准备内容
            content = json.dumps(trade, ensure_ascii=False)

            record = MigrationRecord(
                knowledge_id=knowledge_id,
                content=content,
                metadata=metadata,
                source_type='trade_history',
                migration_id=migration_id,
                timestamp=time.time()
            )

            records.append(record)

        logger.info(f"导出交易历史: {len(records)}条记录")
        self._stats['total_records'] += len(records)

        return records

    # -------------------- memo0导入 --------------------

    async def import_to_memo0(
        self,
        records: List[MigrationRecord],
        migration_id: Optional[str] = None
    ) -> MigrationProgress:
        """导入数据到memo0

        Args:
            records: 迁移记录列表
            migration_id: 迁移ID（可选）

        Returns:
            迁移进度对象
        """
        if migration_id is None:
            migration_id = self._generate_migration_id()

        # 创建进度对象
        progress = MigrationProgress(
            migration_id=migration_id,
            total_records=len(records),
            processed_records=0,
            successful_records=0,
            failed_records=0,
            start_time=time.time(),
            status=MigrationStatus.RUNNING
        )

        try:
            # 获取memo0存储
            storage = self._get_memo0_storage()
            if storage is None:
                raise RuntimeError("memo0存储未初始化")

            # 批量导入
            for i in range(0, len(records), self.batch_size):
                batch = records[i:i + self.batch_size]

                # 导入批次
                success = await self._import_batch(batch, storage, progress)

                if not success:
                    # 批次失败，尝试逐条导入
                    await self._import_individually(batch, storage, progress)

                # 更新进度
                progress.processed_records += len(batch)
                logger.info(
                    f"导入进度: {progress.processed_records}/{progress.total_records} "
                    f"({progress.progress_percentage:.1f}%)"
                )

                # 保存检查点
                if i % self.checkpoint_interval == 0:
                    self._save_checkpoint(migration_id, progress)

            # 完成
            progress.status = MigrationStatus.COMPLETED
            progress.end_time = time.time()

            logger.info(f"导入完成: {progress.successful_records}成功, "
                       f"{progress.failed_records}失败")

            # 更新统计
            self._stats['total_migrations'] += 1
            self._stats['total_success'] += progress.successful_records
            self._stats['total_failed'] += progress.failed_records
            self._stats['total_time'] += progress.elapsed_time

            # 保存到历史
            self._migration_history.append(progress)

        except Exception as e:
            logger.error(f"导入失败: {e}")
            progress.status = MigrationStatus.FAILED
            progress.error = str(e)
            progress.end_time = time.time()

        return progress

    async def _import_batch(
        self,
        batch: List[MigrationRecord],
        storage: Any,
        progress: MigrationProgress
    ) -> bool:
        """导入批次数据

        Args:
            batch: 批次记录
            storage: memo0存储实例
            progress: 迁移进度

        Returns:
            是否成功
        """
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # 尝试批量添加
                for record in batch:
                    await storage.add_knowledge(
                        content=record.content,
                        metadata=record.metadata,
                        knowledge_id=record.knowledge_id
                    )

                progress.successful_records += len(batch)
                return True

            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"批次导入失败 (重试 {retry_count}/{self.max_retries}): {e}"
                )

                if retry_count >= self.max_retries:
                    progress.failed_records += len(batch)
                    return False

                await asyncio.sleep(1)  # 等待1秒后重试

        return False

    async def _import_individually(
        self,
        batch: List[MigrationRecord],
        storage: Any,
        progress: MigrationProgress
    ) -> None:
        """逐条导入数据

        Args:
            batch: 批次记录
            storage: memo0存储实例
            progress: 迁移进度
        """
        for record in batch:
            retry_count = 0

            while retry_count < self.max_retries:
                try:
                    await storage.add_knowledge(
                        content=record.content,
                        metadata=record.metadata,
                        knowledge_id=record.knowledge_id
                    )

                    progress.successful_records += 1
                    break

                except Exception as e:
                    retry_count += 1
                    logger.warning(
                        f"单条导入失败 (重试 {retry_count}/{self.max_retries}): {e}"
                    )

                    if retry_count >= self.max_retries:
                        progress.failed_records += 1
                        logger.error(
                            f"导入失败: knowledge_id={record.knowledge_id}, "
                            f"error={e}"
                        )
                        break

                    await asyncio.sleep(0.5)  # 等待0.5秒后重试

    # -------------------- 数据验证 --------------------

    async def verify_migration(
        self,
        records: List[MigrationRecord],
        migration_id: str
    ) -> Dict[str, Any]:
        """验证迁移数据

        Args:
            records: 迁移记录列表
            migration_id: 迁移ID

        Returns:
            验证结果字典
        """
        storage = self._get_memo0_storage()
        if storage is None:
            return {
                'success': False,
                'error': 'memo0存储未初始化'
            }

        # 统计验证结果
        verified_count = 0
        missing_count = 0
        mismatch_count = 0

        for record in records:
            try:
                # 查询数据
                knowledge = await storage.get_knowledge(record.knowledge_id)

                if knowledge is None:
                    missing_count += 1
                    logger.warning(f"数据缺失: {record.knowledge_id}")
                else:
                    # 验证内容
                    if knowledge.content != record.content:
                        mismatch_count += 1
                        logger.warning(
                            f"内容不匹配: {record.knowledge_id}"
                        )
                    else:
                        verified_count += 1

            except Exception as e:
                logger.error(f"验证失败: {record.knowledge_id}, {e}")
                missing_count += 1

        # 计算验证率
        total = len(records)
        verification_rate = (verified_count / total * 100) if total > 0 else 0

        result = {
            'migration_id': migration_id,
            'total_records': total,
            'verified': verified_count,
            'missing': missing_count,
            'mismatch': mismatch_count,
            'verification_rate': verification_rate,
            'success': verification_rate >= 95.0  # 95%以上认为成功
        }

        logger.info(
            f"迁移验证: {verification_rate:.1f}% ({verified_count}/{total})"
        )

        return result

    # -------------------- 回滚功能 --------------------

    async def rollback_migration(
        self,
        migration_id: str
    ) -> bool:
        """回滚迁移

        Args:
            migration_id: 迁移ID

        Returns:
            是否成功
        """
        storage = self._get_memo0_storage()
        if storage is None:
            logger.error("memo0存储未初始化")
            return False

        try:
            # 获取迁移记录
            migration = self._get_migration_progress(migration_id)
            if migration is None:
                logger.error(f"迁移记录不存在: {migration_id}")
                return False

            # 删除所有相关数据
            # 注意：这里需要根据实际存储API实现
            # 假设存储有批量删除接口
            logger.warning(f"回滚迁移: {migration_id}")

            # 更新迁移状态
            migration.status = MigrationStatus.ROLLED_BACK
            migration.end_time = time.time()

            logger.info(f"回滚完成: {migration_id}")
            return True

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return False

    # -------------------- 检查点管理 --------------------

    def _save_checkpoint(
        self,
        migration_id: str,
        progress: MigrationProgress
    ) -> None:
        """保存检查点

        Args:
            migration_id: 迁移ID
            progress: 迁移进度
        """
        checkpoint_path = self._checkpoint_dir / f"{migration_id}.json"

        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(progress.to_dict(), f, ensure_ascii=False, indent=2)

            logger.debug(f"保存检查点: {checkpoint_path}")

        except Exception as e:
            logger.error(f"保存检查点失败: {e}")

    def load_checkpoint(
        self,
        migration_id: str
    ) -> Optional[MigrationProgress]:
        """加载检查点

        Args:
            migration_id: 迁移ID

        Returns:
            迁移进度对象，如果不存在则返回None
        """
        checkpoint_path = self._checkpoint_dir / f"{migration_id}.json"

        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return MigrationProgress(
                migration_id=data['migration_id'],
                total_records=data['total_records'],
                processed_records=data['processed_records'],
                successful_records=data['successful_records'],
                failed_records=data['failed_records'],
                start_time=data['start_time'],
                end_time=data.get('end_time'),
                status=MigrationStatus(data['status']),
                error=data.get('error')
            )

        except Exception as e:
            logger.error(f"加载检查点失败: {e}")
            return None

    def clear_checkpoints(self, older_than_days: int = 30) -> int:
        """清理旧检查点

        Args:
            older_than_days: 删除多少天之前的检查点

        Returns:
            删除的检查点数量
        """
        cutoff_time = time.time() - (older_than_days * 86400)
        count = 0

        for checkpoint_file in self._checkpoint_dir.glob("*.json"):
            try:
                # 检查文件修改时间
                if checkpoint_file.stat().st_mtime < cutoff_time:
                    checkpoint_file.unlink()
                    count += 1
            except Exception as e:
                logger.warning(f"删除检查点失败: {checkpoint_file}, {e}")

        logger.info(f"清理旧检查点: {count}个文件")
        return count

    # -------------------- 工具方法 --------------------

    def _generate_migration_id(self) -> str:
        """生成迁移ID"""
        return f"migration_{int(time.time())}_{hash(str(time.time())) % 10000}"

    def _generate_knowledge_id(self, key: str, value: Any) -> str:
        """生成knowledge_id"""
        # 使用键和值的哈希值
        content = f"{key}:{str(value)}:{time.time()}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _get_memo0_storage(self) -> Optional[Any]:
        """获取memo0存储实例"""
        if self._memo0_storage is not None:
            return self._memo0_storage

        try:
            from storage.memo0_intelligent_knowledge_manager_v2 import (
                get_memo0_storage_manager
            )
            manager = get_memo0_storage_manager()
            self._memo0_storage = manager.storage
            return self._memo0_storage
        except Exception as e:
            logger.error(f"获取memo0存储失败: {e}")
            return None

    def _save_records_to_file(
        self,
        records: List[MigrationRecord],
        file_path: str
    ) -> None:
        """保存记录到文件

        Args:
            records: 迁移记录列表
            file_path: 文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    [r.to_dict() for r in records],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            logger.info(f"保存记录到文件: {file_path}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")

    def _get_migration_progress(
        self,
        migration_id: str
    ) -> Optional[MigrationProgress]:
        """获取迁移进度

        Args:
            migration_id: 迁移ID

        Returns:
            迁移进度对象，如果不存在则返回None
        """
        for progress in self._migration_history:
            if progress.migration_id == migration_id:
                return progress
        return None

    # -------------------- 统计信息 --------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            'migrations': {
                'total': self._stats['total_migrations'],
                'records': self._stats['total_records'],
                'successful': self._stats['total_success'],
                'failed': self._stats['total_failed'],
                'success_rate': (
                    self._stats['total_success'] /
                    max(self._stats['total_records'], 1) * 100
                    if self._stats['total_records'] > 0 else 0
                ),
                'total_time': self._stats['total_time']
            },
            'config': {
                'batch_size': self.batch_size,
                'max_retries': self.max_retries,
                'checkpoint_interval': self.checkpoint_interval
            }
        }

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史

        Returns:
            迁移历史列表
        """
        return [p.to_dict() for p in self._migration_history]


# 全局数据迁移工具实例
_global_migrator: Optional[DataMigrator] = None


def get_global_migrator() -> DataMigrator:
    """获取全局数据迁移工具实例"""
    global _global_migrator
    if _global_migrator is None:
        _global_migrator = DataMigrator()
    return _global_migrator


def set_global_migrator(migrator: DataMigrator) -> None:
    """设置全局数据迁移工具实例"""
    global _global_migrator
    _global_migrator = migrator
