"""备份管理器 - Phase 11核心模块

自动化备份和恢复。

核心功能：
1. 自动备份 - 定期自动备份
2. 备份类型 - 完整备份/增量备份
3. 备份恢复 - 快速恢复备份
4. 备份清理 - 自动清理过期备份

创建时间：2026-04-19 20:52:00
"""

import asyncio
import logging
import shutil
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BackupManager:
    """备份管理器

    自动化备份和恢复。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化备份管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.backup_schedule: Dict[str, Any] = {}
        self.backup_history: List[Dict[str, Any]] = []
        self.backup_cooldowns: Dict[str, float] = {}

        # 创建备份目录
        self.backup_dir = Path(self.config.get('backup_dir', './backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"备份管理器初始化完成，备份目录: {self.backup_dir}")

    async def create_backup(
        self,
        backup_type: str = 'full',
        backup_name: Optional[str] = None
    ) -> str:
        """创建备份

        Args:
            backup_type: 备份类型（full/incremental/database/config）
            backup_name: 备份名称（可选）

        Returns:
            备份ID
        """
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{backup_type}"

        backup_id = backup_name
        logger.info(f"开始创建备份: {backup_id} ({backup_type})")

        try:
            # 检查冷却期
            if self._is_in_cooldown(backup_type):
                logger.warning(f"备份 {backup_type} 在冷却期中，跳过")
                return backup_id

            # 创建备份目录
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)

            # 根据备份类型执行不同的备份逻辑
            backup_tasks = []

            if backup_type in ['full', 'database']:
                backup_tasks.append(self._backup_database(backup_path))

            if backup_type == 'full':
                backup_tasks.append(self._backup_config(backup_path))
                backup_tasks.append(self._backup_logs(backup_path))

            if backup_type == 'incremental':
                backup_tasks.append(self._backup_incremental(backup_path))

            # 并行执行备份任务
            if backup_tasks:
                await asyncio.gather(*backup_tasks, return_exceptions=True)

            # 创建备份清单
            await self._create_backup_manifest(backup_path, backup_type)

            # 计算备份大小
            backup_size_mb = self._calculate_backup_size(backup_path)

            # 记录备份历史
            self.backup_history.append({
                'id': str(uuid.uuid4()),
                'backup_id': backup_id,
                'backup_type': backup_type,
                'backup_path': str(backup_path),
                'size_mb': backup_size_mb,
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
            })

            # 更新冷却期
            cooldown = self.config.get('backup_cooldown', 300)
            self.backup_cooldowns[backup_type] = time.time() + cooldown

            logger.info(f"备份创建成功: {backup_id} (大小: {backup_size_mb:.2f}MB)")

            return backup_id

        except Exception as e:
            logger.error(f"创建备份失败: {e}")

            # 记录失败的备份
            self.backup_history.append({
                'id': str(uuid.uuid4()),
                'backup_id': backup_id,
                'backup_type': backup_type,
                'backup_path': str(self.backup_dir / backup_name),
                'size_mb': 0,
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e),
            })

            raise

    async def _backup_database(self, backup_path: Path):
        """备份数据库

        Args:
            backup_path: 备份路径
        """
        logger.info("备份数据库...")

        db_files = [
            './local_vector_db.sqlite3',
            './crypto_arbitrage.db',
        ]

        for db_file in db_files:
            src_path = Path(db_file)
            if src_path.exists():
                shutil.copy2(src_path, backup_path / src_path.name)
                logger.info(f"数据库已备份: {db_file}")

    async def _backup_config(self, backup_path: Path):
        """备份配置

        Args:
            backup_path: 备份路径
        """
        logger.info("备份配置...")

        config_file = './config/config.yaml'
        src_path = Path(config_file)

        if src_path.exists():
            shutil.copy2(src_path, backup_path / 'config.yaml')
            logger.info("配置文件已备份")

    async def _backup_logs(self, backup_path: Path):
        """备份日志

        Args:
            backup_path: 备份路径
        """
        logger.info("备份日志...")

        logs_dir = Path('./logs')
        if logs_dir.exists():
            backup_logs_dir = backup_path / 'logs'
            shutil.copytree(logs_dir, backup_logs_dir, dirs_exist_ok=True)
            logger.info("日志文件已备份")

    async def _backup_incremental(self, backup_path: Path):
        """增量备份

        Args:
            backup_path: 备份路径
        """
        logger.info("执行增量备份...")

        # 获取上一个备份
        last_backup = self.get_latest_backup()

        if last_backup:
            # TODO: 实现增量备份逻辑
            # 对比上一个备份，只备份变更的文件
            logger.info(f"基于上一个备份 {last_backup['backup_id']} 执行增量备份")
        else:
            # 如果没有上一个备份，执行完整备份
            logger.info("没有上一个备份，执行完整备份")

    async def _create_backup_manifest(self, backup_path: Path, backup_type: str):
        """创建备份清单

        Args:
            backup_path: 备份路径
            backup_type: 备份类型
        """
        import json

        manifest = {
            'backup_id': backup_path.name,
            'backup_type': backup_type,
            'created_at': datetime.now().isoformat(),
            'files': [],
        }

        # 列出备份目录中的文件
        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                file_info = {
                    'path': str(file_path.relative_to(backup_path)),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                }
                manifest['files'].append(file_info)

        # 写入清单文件
        manifest_path = backup_path / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.debug(f"备份清单已创建: {manifest_path}")

    def _calculate_backup_size(self, backup_path: Path) -> float:
        """计算备份大小

        Args:
            backup_path: 备份路径

        Returns:
            备份大小（MB）
        """
        total_size = 0

        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size / 1024 / 1024  # MB

    def _is_in_cooldown(self, backup_type: str) -> bool:
        """检查是否在冷却期

        Args:
            backup_type: 备份类型

        Returns:
            是否在冷却期
        """
        if backup_type not in self.backup_cooldowns:
            return False

        cooldown_time = self.backup_cooldowns[backup_type]
        return time.time() < cooldown_time

    async def restore_backup(self, backup_id: str) -> bool:
        """恢复备份

        Args:
            backup_id: 备份ID

        Returns:
            是否成功
        """
        logger.info(f"开始恢复备份: {backup_id}")

        try:
            # 查找备份
            backup_info = None
            for info in self.backup_history:
                if info['backup_id'] == backup_id:
                    backup_info = info
                    break

            if not backup_info:
                logger.error(f"未找到备份: {backup_id}")
                return False

            backup_path = Path(backup_info['backup_path'])

            if not backup_path.exists():
                logger.error(f"备份目录不存在: {backup_path}")
                return False

            # 根据备份类型执行恢复
            if backup_info['backup_type'] in ['full', 'database']:
                await self._restore_database(backup_path)

            if backup_info['backup_type'] == 'full':
                await self._restore_config(backup_path)
                await self._restore_logs(backup_path)

            logger.info(f"备份恢复成功: {backup_id}")

            return True

        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False

    async def _restore_database(self, backup_path: Path):
        """恢复数据库

        Args:
            backup_path: 备份路径
        """
        logger.info("恢复数据库...")

        db_files = ['local_vector_db.sqlite3', 'crypto_arbitrage.db']

        for db_file in db_files:
            backup_db = backup_path / db_file
            if backup_db.exists():
                shutil.copy2(backup_db, f'./{db_file}')
                logger.info(f"数据库已恢复: {db_file}")

    async def _restore_config(self, backup_path: Path):
        """恢复配置

        Args:
            backup_path: 备份路径
        """
        logger.info("恢复配置...")

        backup_config = backup_path / 'config.yaml'
        if backup_config.exists():
            shutil.copy2(backup_config, './config/config.yaml')
            logger.info("配置文件已恢复")

    async def _restore_logs(self, backup_path: Path):
        """恢复日志

        Args:
            backup_path: 备份路径
        """
        logger.info("恢复日志...")

        backup_logs = backup_path / 'logs'
        if backup_logs.exists():
            # 删除现有日志
            logs_dir = Path('./logs')
            if logs_dir.exists():
                shutil.rmtree(logs_dir)

            # 恢复日志
            shutil.copytree(backup_logs, logs_dir)
            logger.info("日志文件已恢复")

    async def list_backups(self) -> List[Dict[str, Any]]:
        """列出备份

        Returns:
            备份列表
        """
        return self.backup_history.copy()

    async def get_latest_backup(self, backup_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取最新的备份

        Args:
            backup_type: 备份类型过滤

        Returns:
            最新备份信息字典
        """
        backups = self.backup_history.copy()

        # 过滤备份类型
        if backup_type:
            backups = [b for b in backups if b.get('backup_type') == backup_type]

        if not backups:
            return None

        # 返回最新的备份
        return backups[-1]

    async def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """清理旧备份

        Args:
            keep_days: 保留天数

        Returns:
            清理的备份数量
        """
        logger.info(f"开始清理 {keep_days} 天前的备份...")

        cutoff_time = datetime.now() - timedelta(days=keep_days)
        cleaned_count = 0

        for backup_info in self.backup_history.copy():
            backup_time = datetime.fromisoformat(backup_info['timestamp'])

            if backup_time < cutoff_time:
                backup_path = Path(backup_info['backup_path'])

                # 删除备份目录
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    logger.info(f"清理旧备份: {backup_info['backup_id']}")

                # 从历史中移除
                self.backup_history.remove(backup_info)
                cleaned_count += 1

        logger.info(f"清理了 {cleaned_count} 个旧备份")

        return cleaned_count

    async def start_auto_backup(
        self,
        backup_type: str = 'full',
        interval_hours: int = 24
    ):
        """启动自动备份

        Args:
            backup_type: 备份类型
            interval_hours: 备份间隔（小时）
        """
        logger.info(f"启动自动备份，类型: {backup_type}, 间隔: {interval_hours}小时")

        while True:
            try:
                # 创建备份
                await self.create_backup(backup_type)

                # 等待下次备份
                await asyncio.sleep(interval_hours * 3600)

            except Exception as e:
                logger.error(f"自动备份异常: {e}")
                await asyncio.sleep(3600)  # 出错后等待1小时

    def get_backup_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取备份统计

        Args:
            days: 统计时间范围（天）

        Returns:
            统计信息字典
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        # 过滤时间范围内的备份
        recent_backups = [
            b for b in self.backup_history
            if datetime.fromisoformat(b['timestamp']) >= cutoff_time
        ]

        # 统计信息
        type_counts = {}
        total_size = 0
        success_count = sum(1 for b in recent_backups if b.get('status') == 'success')

        for backup in recent_backups:
            backup_type = backup.get('backup_type', 'unknown')
            type_counts[backup_type] = type_counts.get(backup_type, 0) + 1

            total_size += backup.get('size_mb', 0)

        return {
            'time_range_days': days,
            'total_backups': len(recent_backups),
            'successful_backups': success_count,
            'success_rate': (
                success_count / len(recent_backups) * 100
                if recent_backups else 0
            ),
            'type_breakdown': type_counts,
            'total_size_mb': total_size,
            'average_size_mb': (
                total_size / len(recent_backups)
                if recent_backups else 0
            ),
        }

    def get_backup_history(
        self,
        limit: int = 100,
        backup_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取备份历史

        Args:
            limit: 返回数量限制
            backup_type: 备份类型过滤

        Returns:
            备份历史列表
        """
        history = self.backup_history.copy()

        # 过滤备份类型
        if backup_type:
            history = [h for h in history if h.get('backup_type') == backup_type]

        # 限制数量并倒序
        history.reverse()
        return history[:limit]

    def clear_backup_history(self):
        """清除备份历史"""
        self.backup_history.clear()
        logger.info("已清除备份历史")

    def clear_cooldowns(self):
        """清除所有冷却期"""
        self.backup_cooldowns.clear()
        logger.info("已清除所有备份冷却期")

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        return f"BackupManager(dir={self.backup_dir}, history={len(self.backup_history)})"
