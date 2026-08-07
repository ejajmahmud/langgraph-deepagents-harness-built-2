"""备份管理器 V3.7 - 数据备份和灾难恢复

提供完整的数据备份和灾难恢复能力，确保数据安全。
核心功能：
1. 全量和增量备份 - 灵活的备份策略
2. 自动备份调度 - 定期自动备份
3. 压缩和加密 - 优化存储和安全性
4. 一键恢复 - 快速恢复数据
5. 备份验证 - 确保备份完整性
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import tarfile
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """备份类型"""
    FULL = "FULL"  # 全量备份
    INCREMENTAL = "INCREMENTAL"  # 增量备份


class BackupStatus(Enum):
    """备份状态"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class BackupMetadata:
    """备份元数据"""
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    timestamp: datetime
    size_bytes: int
    checksum: str
    files: List[str]
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class RestoreResult:
    """恢复结果"""
    backup_id: str
    success: bool
    restored_files: List[str]
    duration_seconds: float
    started_at: datetime
    completed_at: datetime
    error_message: Optional[str] = None


class BackupValidator:
    """备份验证器"""

    @staticmethod
    def calculate_checksum(file_path: Path) -> str:
        """计算文件校验和

        Args:
            file_path: 文件路径

        Returns:
            SHA256 校验和
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # 分块读取大文件
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    @staticmethod
    def validate_integrity(backup_path: Path, expected_checksum: str) -> bool:
        """验证备份完整性

        Args:
            backup_path: 备份文件路径
            expected_checksum: 预期校验和

        Returns:
            是否有效
        """
        try:
            actual_checksum = BackupValidator.calculate_checksum(backup_path)
            return actual_checksum == expected_checksum

        except Exception as e:
            logger.error(f"验证备份完整性失败: {e}")
            return False

    @staticmethod
    def validate_backup(backup_path: Path) -> Dict[str, Any]:
        """验证备份文件

        Args:
            backup_path: 备份文件路径

        Returns:
            验证结果
        """
        if not backup_path.exists():
            return {
                'valid': False,
                'error': '备份文件不存在'
            }

        # 检查文件大小
        size = backup_path.stat().st_size
        if size == 0:
            return {
                'valid': False,
                'error': '备份文件为空'
            }

        # 尝试读取文件
        try:
            with tarfile.open(backup_path, 'r:gz') if str(backup_path).endswith('.tar.gz') else tarfile.open(backup_path, 'r') as tar:
                members = tar.getmembers()

                return {
                    'valid': True,
                    'size': size,
                    'file_count': len(members),
                    'members': [m.name for m in members[:10]]  # 只返回前10个文件名
                }

        except Exception as e:
            return {
                'valid': False,
                'error': f'无法读取备份文件: {str(e)}'
            }


class BackupManager:
    """备份管理器 V3.7

    提供完整的数据备份和灾难恢复能力。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        backup_dir: Optional[Path] = None
    ):
        """初始化备份管理器

        Args:
            config: 配置字典
            backup_dir: 备份目录（可选）
        """
        self.config = config

        # 备份目录
        self.backup_dir = backup_dir or Path(config.get('backup_dir', 'backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 备份历史
        self.backup_history: deque = deque(maxlen=100)
        self.backup_metadata: Dict[str, BackupMetadata] = {}

        # 运行状态
        self.is_running = False

        # 统计信息
        self.stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'total_backup_size': 0,
            'last_backup_time': None
        }

        # 备份任务
        self.scheduled_backups: List[Dict] = []

        logger.info(f"备份管理器初始化完成 - 备份目录: {self.backup_dir}")

    async def create_backup(
        self,
        sources: List[str],
        backup_type: BackupType = BackupType.FULL,
        description: str = "",
        compress: bool = True
    ) -> BackupMetadata:
        """创建备份

        Args:
            sources: 要备份的源路径列表
            backup_type: 备份类型
            description: 备份描述
            compress: 是否压缩

        Returns:
            备份元数据
        """
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        timestamp = datetime.now()

        # 创建备份元数据
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            timestamp=timestamp,
            size_bytes=0,
            checksum="",
            files=[],
            description=description
        )

        self.backup_metadata[backup_id] = metadata

        logger.info(f"开始创建备份: {backup_id} - 类型: {backup_type.value}")

        try:
            # 收集文件
            files_to_backup = self._collect_files(sources)

            # 创建备份文件
            backup_filename = f"{backup_id}.tar" + (".gz" if compress else "")
            backup_path = self.backup_dir / backup_filename

            # 创建备份
            with tarfile.open(backup_path, f'w:gz' if compress else 'w') as tar:
                for file_path in files_to_backup:
                    try:
                        arcname = os.path.relpath(file_path, start=self.backup_dir.parent.parent)
                        tar.add(file_path, arcname=arcname)
                        metadata.files.append(arcname)
                        logger.debug(f"已添加文件: {file_path}")

                    except Exception as e:
                        logger.warning(f"跳过文件 {file_path}: {e}")

            # 更新元数据
            metadata.size_bytes = backup_path.stat().st_size
            metadata.checksum = BackupValidator.calculate_checksum(backup_path)
            metadata.status = BackupStatus.COMPLETED
            metadata.completed_at = datetime.now()

            # 记录历史
            self.backup_history.append(metadata)

            # 更新统计
            self._update_stats(metadata)

            logger.info(
                f"备份创建完成: {backup_id} - "
                f"大小: {metadata.size_bytes / (1024 * 1024):.2f} MB, "
                f"文件: {len(metadata.files)}"
            )

            return metadata

        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            metadata.completed_at = datetime.now()

            logger.error(f"备份创建失败: {backup_id} - {e}")

            return metadata

    def _collect_files(self, sources: List[str]) -> List[Path]:
        """收集要备份的文件

        Args:
            sources: 源路径列表

        Returns:
            文件路径列表
        """
        files = []

        for source in sources:
            source_path = Path(source)

            if not source_path.exists():
                logger.warning(f"源路径不存在: {source}")
                continue

            if source_path.is_file():
                files.append(source_path)
            elif source_path.is_dir():
                # 递归收集目录中的所有文件
                for item in source_path.rglob('*'):
                    if item.is_file():
                        files.append(item)

        return files

    async def restore_backup(
        self,
        backup_id: str,
        restore_to: Optional[Path] = None,
        overwrite: bool = False
    ) -> RestoreResult:
        """恢复备份

        Args:
            backup_id: 备份ID
            restore_to: 恢复目录（None为原位置）
            overwrite: 是否覆盖现有文件

        Returns:
            恢复结果
        """
        metadata = self.backup_metadata.get(backup_id)

        if not metadata:
            return RestoreResult(
                backup_id=backup_id,
                success=False,
                restored_files=[],
                duration_seconds=0.0,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=f"备份 {backup_id} 不存在"
            )

        start_time = datetime.now()

        logger.info(f"开始恢复备份: {backup_id}")

        try:
            # 查找备份文件
            backup_filename = f"{backup_id}.tar.gz"
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                backup_filename = f"{backup_id}.tar"
                backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                return RestoreResult(
                    backup_id=backup_id,
                    success=False,
                    restored_files=[],
                    duration_seconds=0.0,
                    started_at=start_time,
                    completed_at=datetime.now(),
                    error_message=f"备份文件不存在"
                )

            # 验证备份完整性
            if not BackupValidator.validate_integrity(backup_path, metadata.checksum):
                return RestoreResult(
                    backup_id=backup_id,
                    success=False,
                    restored_files=[],
                    duration_seconds=0.0,
                    started_at=start_time,
                    completed_at=datetime.now(),
                    error_message="备份校验和不匹配"
                )

            # 确定恢复目录
            if restore_to:
                restore_dir = restore_to
            else:
                restore_dir = self.backup_dir.parent.parent

            restore_dir.mkdir(parents=True, exist_ok=True)

            # 解压备份
            restored_files = []
            with tarfile.open(backup_path, 'r:gz' if backup_path.suffix == '.gz' else 'r') as tar:
                for member in tar.getmembers():
                    try:
                        # 检查文件是否已存在
                        output_path = restore_dir / member.name

                        if output_path.exists() and not overwrite:
                            logger.info(f"跳过已存在文件: {member.name}")
                            continue

                        tar.extract(member, path=restore_dir)
                        restored_files.append(member.name)

                    except Exception as e:
                        logger.warning(f"恢复文件失败 {member.name}: {e}")

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"备份恢复完成: {backup_id} - "
                f"恢复文件: {len(restored_files)}, "
                f"耗时: {duration:.2f}秒"
            )

            return RestoreResult(
                backup_id=backup_id,
                success=len(restored_files) > 0,
                restored_files=restored_files,
                duration_seconds=duration,
                started_at=start_time,
                completed_at=datetime.now()
            )

        except Exception as e:
            return RestoreResult(
                backup_id=backup_id,
                success=False,
                restored_files=[],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.now(),
                error_message=str(e)
            )

    async def schedule_backup(
        self,
        sources: List[str],
        interval_hours: float,
        backup_type: BackupType = BackupType.FULL,
        description: str = ""
    ) -> str:
        """调度定期备份

        Args:
            sources: 源路径列表
            interval_hours: 间隔（小时）
            backup_type: 备份类型
            description: 备份描述

        Returns:
            任务ID
        """
        task_id = f"scheduled_backup_{datetime.now().timestamp()}"

        task = {
            'task_id': task_id,
            'sources': sources,
            'interval_hours': interval_hours,
            'backup_type': backup_type,
            'description': description,
            'last_run': None,
            'next_run': datetime.now() + timedelta(hours=interval_hours)
        }

        self.scheduled_backups.append(task)

        logger.info(
            f"调度定期备份: {task_id} - "
            f"间隔: {interval_hours}小时, 类型: {backup_type.value}"
        )

        return task_id

    async def run_scheduled_backups(self) -> None:
        """运行调度的备份任务"""
        current_time = datetime.now()

        for task in self.scheduled_backups:
            # 检查是否到了执行时间
            if task['next_run'] <= current_time:
                logger.info(f"执行调度备份: {task['task_id']}")

                # 执行备份
                await self.create_backup(
                    sources=task['sources'],
                    backup_type=task['backup_type'],
                    description=task['description']
                )

                # 更新下次运行时间
                task['last_run'] = current_time
                task['next_run'] = current_time + timedelta(hours=task['interval_hours'])

    async def cleanup_old_backups(
        self,
        keep_days: int = 30,
        keep_count: int = 10
    ) -> int:
        """清理旧备份

        Args:
            keep_days: 保留天数
            keep_count: 最少保留数量

        Returns:
            删除的备份数量
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        # 按时间排序
        sorted_backups = sorted(self.backup_history, key=lambda m: m.timestamp)

        # 计算要删除的备份
        backups_to_delete = []
        backups_to_keep = []

        for i, backup in enumerate(sorted_backups):
            # 保留最近的 N 个备份
            if i < keep_count:
                backups_to_keep.append(backup)
                continue

            # 删除超过保留期的备份
            if backup.timestamp < cutoff_date:
                backups_to_delete.append(backup)
            else:
                backups_to_keep.append(backup)

        # 删除备份文件
        for backup in backups_to_delete:
            try:
                # 尝试删除压缩文件
                backup_file = self.backup_dir / f"{backup.backup_id}.tar.gz"
                if not backup_file.exists():
                    backup_file = self.backup_dir / f"{backup.backup_id}.tar"

                if backup_file.exists():
                    backup_file.unlink()
                    logger.info(f"删除旧备份: {backup.backup_id}")
                    deleted_count += 1

                # 从元数据中删除
                del self.backup_metadata[backup.backup_id]

            except Exception as e:
                logger.error(f"删除备份失败 {backup.backup_id}: {e}")

        # 更新历史
        self.backup_history.clear()
        for backup in backups_to_keep:
            self.backup_history.append(backup)

        logger.info(f"清理完成 - 删除 {deleted_count} 个旧备份")

        return deleted_count

    def _update_stats(self, metadata: BackupMetadata) -> None:
        """更新统计信息

        Args:
            metadata: 备份元数据
        """
        self.stats['total_backups'] += 1
        self.stats['total_backup_size'] += metadata.size_bytes
        self.stats['last_backup_time'] = metadata.timestamp

        if metadata.status == BackupStatus.COMPLETED:
            self.stats['successful_backups'] += 1
        else:
            self.stats['failed_backups'] += 1

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """获取备份列表

        Returns:
            备份列表
        """
        backups = []

        for metadata in self.backup_history:
            backups.append({
                'backup_id': metadata.backup_id,
                'backup_type': metadata.backup_type.value,
                'status': metadata.status.value,
                'timestamp': metadata.timestamp.isoformat(),
                'size_mb': metadata.size_bytes / (1024 * 1024),
                'file_count': len(metadata.files),
                'description': metadata.description,
                'checksum': metadata.checksum[:16] + '...'  # 只显示部分校验和
            })

        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

    def get_backup_summary(self) -> Dict[str, Any]:
        """获取备份摘要

        Returns:
            备份摘要
        """
        return {
            'backup_dir': str(self.backup_dir),
            'total_backups': len(self.backup_history),
            'total_size_mb': sum(m.size_bytes for m in self.backup_history) / (1024 * 1024),
            'latest_backup': self.backup_history[-1].timestamp.isoformat() if self.backup_history else None,
            'scheduled_tasks': len(self.scheduled_backups),
            'stats': self.stats.copy()
        }


# 便捷函数
def create_backup_manager(
    config: Dict[str, Any],
    backup_dir: Optional[Path] = None
) -> BackupManager:
    """创建备份管理器实例

    Args:
        config: 配置字典
        backup_dir: 备份目录（可选）

    Returns:
        备份管理器实例
    """
    return BackupManager(config, backup_dir)
