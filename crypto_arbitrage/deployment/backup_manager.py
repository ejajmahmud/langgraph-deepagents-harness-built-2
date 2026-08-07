"""
备份恢复管理器 - V15.9 Phase 1核心模块

实现自动化的备份恢复机制，支持数据、知识库、配置的备份和恢复。

核心功能：
1. 数据库备份 - 自动备份所有数据库
2. 知识库备份 - 备份知识图谱和推理历史
3. 配置备份 - 备份系统配置
4. 自动恢复 - 支持一键恢复
5. 备份策略 - 支持定时备份、增量备份

创建时间：2026-05-01 02:45
"""

import os
import shutil
import sqlite3
import gzip
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
import asyncio
import aiofiles

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """备份信息"""
    backup_id: str
    backup_type: str  # 'full', 'incremental', 'config'
    created_at: str
    size_mb: float
    checksum: str
    files_count: int
    description: str

    def to_dict(self) -> Dict:
        return asdict(self)


class BackupManager:
    """备份恢复管理器

    提供完整的备份和恢复功能。
    """

    # 备份类型
    BACKUP_TYPE_FULL = "full"
    BACKUP_TYPE_INCREMENTAL = "incremental"
    BACKUP_TYPE_CONFIG = "config"

    # 备份目录结构
    BACKUP_ROOT = "backups"
    BACKUP_DB = "backup_metadata.db"

    def __init__(self, base_dir: Optional[str] = None, config: Optional[Dict] = None):
        """初始化备份管理器

        Args:
            base_dir: 基础目录（默认：当前目录）
            config: 配置字典
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.config = config or {}
        self.backup_root = self.base_dir / self.BACKUP_ROOT

        # 创建备份目录
        self.backup_root.mkdir(exist_ok=True)

        # 备份策略
        self.auto_backup_enabled = self.config.get('auto_backup_enabled', True)
        self.backup_interval_hours = self.config.get('backup_interval_hours', 24)
        self.max_backups = self.config.get('max_backups', 7)

        # 初始化备份元数据库
        self.backup_db = self.backup_root / self.BACKUP_DB
        self._init_backup_db()

        logger.info(f"[OK] 备份管理器初始化完成，备份根目录: {self.backup_root}")

    def _init_backup_db(self):
        """初始化备份元数据库"""
        conn = sqlite3.connect(str(self.backup_db))
        cursor = conn.cursor()

        # 创建备份记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                backup_id TEXT PRIMARY KEY,
                backup_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                size_mb REAL NOT NULL,
                checksum TEXT NOT NULL,
                files_count INTEGER NOT NULL,
                description TEXT,
                backup_path TEXT NOT NULL,
                restore_available INTEGER DEFAULT 1
            )
        ''')

        # 创建备份文件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                original_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                compressed_size INTEGER,
                FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
            )
        ''')

        conn.commit()
        conn.close()

        logger.info("[OK] 备份元数据库初始化完成")

    def create_backup(
        self,
        backup_type: str = BACKUP_TYPE_FULL,
        description: str = "",
        components: Optional[List[str]] = None
    ) -> BackupInfo:
        """创建备份

        Args:
            backup_type: 备份类型
            description: 备份描述
            components: 要备份的组件列表（None表示全部）

        Returns:
            备份信息
        """
        backup_id = self._generate_backup_id(backup_type)
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(exist_ok=True)

        logger.info(f"开始创建备份: {backup_id} ({backup_type})")

        # 备份文件列表
        backed_files = []
        total_size = 0

        # 确定要备份的组件
        if components is None:
            components = self._get_all_backup_components()

        # 备份各个组件
        for component in components:
            if component == "database":
                files, size = self._backup_databases(backup_dir)
            elif component == "knowledge_base":
                files, size = self._backup_knowledge_base(backup_dir)
            elif component == "config":
                files, size = self._backup_config(backup_dir)
            elif component == "logs":
                files, size = self._backup_logs(backup_dir)
            else:
                logger.warning(f"未知的备份组件: {component}")
                continue

            backed_files.extend(files)
            total_size += size

        # 计算校验和
        checksum = self._calculate_backup_checksum(backup_dir)

        # 创建备份信息
        backup_info = BackupInfo(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=datetime.now().isoformat(),
            size_mb=total_size / (1024 * 1024),
            checksum=checksum,
            files_count=len(backed_files),
            description=description or f"{backup_type} backup of {', '.join(components)}"
        )

        # 记录到数据库
        self._record_backup(backup_info, backup_dir, backed_files)

        # 压缩备份
        compressed_file = self._compress_backup(backup_dir, backup_id)

        logger.info(f"[OK] 备份创建成功: {backup_id}, 文件数: {len(backed_files)}, 大小: {backup_info.size_mb:.2f}MB")
        logger.info(f"   压缩后: {compressed_file}")

        return backup_info

    def restore_backup(
        self,
        backup_id: str,
        components: Optional[List[str]] = None
    ) -> bool:
        """恢复备份

        Args:
            backup_id: 备份ID
            components: 要恢复的组件列表（None表示全部）

        Returns:
            是否成功
        """
        logger.info(f"开始恢复备份: {backup_id}")

        # 查找备份
        backup_info = self._get_backup_info(backup_id)
        if not backup_info:
            logger.error(f"备份不存在: {backup_id}")
            return False

        # 解压备份
        compressed_file = self.backup_root / f"{backup_id}.tar.gz"
        if not compressed_file.exists():
            logger.error(f"备份文件不存在: {compressed_file}")
            return False

        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(exist_ok=True)

        # 解压
        try:
            shutil.unpack_archive(str(compressed_file), str(self.backup_root))
            logger.info(f"备份解压成功: {backup_dir}")
        except Exception as e:
            logger.error(f"解压备份失败: {e}")
            return False

        # 恢复各个组件
        if components is None:
            components = self._get_all_backup_components()

        success = True
        for component in components:
            try:
                if component == "database":
                    self._restore_databases(backup_dir)
                elif component == "knowledge_base":
                    self._restore_knowledge_base(backup_dir)
                elif component == "config":
                    self._restore_config(backup_dir)
                elif component == "logs":
                    self._restore_logs(backup_dir)

                logger.info(f"[OK] {component} 恢复成功")
            except Exception as e:
                logger.error(f"[FAIL] {component} 恢复失败: {e}")
                success = False

        return success

    def list_backups(
        self,
        backup_type: Optional[str] = None,
        limit: int = 10
    ) -> List[BackupInfo]:
        """列出备份

        Args:
            backup_type: 备份类型过滤
            limit: 返回数量限制

        Returns:
            备份信息列表
        """
        conn = sqlite3.connect(str(self.backup_db))
        cursor = conn.cursor()

        query = "SELECT * FROM backups WHERE restore_available = 1"
        if backup_type:
            query += f" AND backup_type = '{backup_type}'"
        query += " ORDER BY created_at DESC LIMIT ?"

        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        conn.close()

        backups = []
        for row in rows:
            backup_info = BackupInfo(
                backup_id=row[0],
                backup_type=row[1],
                created_at=row[2],
                size_mb=row[3],
                checksum=row[4],
                files_count=row[5],
                description=row[6]
            )
            backups.append(backup_info)

        return backups

    def delete_old_backups(self, keep_days: int = 7) -> int:
        """删除旧备份

        Args:
            keep_days: 保留天数

        Returns:
            删除的备份数量
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        conn = sqlite3.connect(str(self.backup_db))
        cursor = conn.cursor()

        # 查找旧备份
        cursor.execute(
            "SELECT backup_id, backup_path FROM backups WHERE created_at < ?",
            (cutoff_date.isoformat(),)
        )
        old_backups = cursor.fetchall()

        deleted_count = 0
        for backup_id, backup_path in old_backups:
            try:
                # 删除压缩文件
                compressed_file = self.backup_root / f"{backup_id}.tar.gz"
                if compressed_file.exists():
                    compressed_file.unlink()

                # 标记为不可恢复
                cursor.execute(
                    "UPDATE backups SET restore_available = 0 WHERE backup_id = ?",
                    (backup_id,)
                )

                deleted_count += 1
                logger.info(f"[OK] 删除旧备份: {backup_id}")
            except Exception as e:
                logger.error(f"删除备份失败 {backup_id}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"[OK] 删除了 {deleted_count} 个旧备份")
        return deleted_count

    # ========== 私有方法 ==========

    def _generate_backup_id(self, backup_type: str) -> str:
        """生成备份ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{backup_type}_{timestamp}"

    def _get_all_backup_components(self) -> List[str]:
        """获取所有可备份的组件"""
        return ["database", "knowledge_base", "config", "logs"]

    def _backup_databases(self, backup_dir: Path) -> Tuple[List[str], int]:
        """备份数据库"""
        backed_files = []
        total_size = 0
        db_dir = backup_dir / "database"
        db_dir.mkdir(exist_ok=True)

        # 查找所有数据库文件
        for db_file in self.base_dir.rglob("*.db"):
            if "backup" in str(db_file) or ".tmp" in str(db_file):
                continue

            try:
                # 复制数据库文件
                dest_file = db_dir / db_file.name
                shutil.copy2(str(db_file), str(dest_file))

                file_size = dest_file.stat().st_size
                backed_files.append(str(dest_file))
                total_size += file_size

            except Exception as e:
                logger.warning(f"备份数据库失败 {db_file}: {e}")

        return backed_files, total_size

    def _backup_knowledge_base(self, backup_dir: Path) -> Tuple[List[str], int]:
        """备份知识库"""
        backed_files = []
        total_size = 0
        kb_dir = backup_dir / "knowledge_base"
        kb_dir.mkdir(exist_ok=True)

        # 备份知识库目录
        kb_base = self.base_dir / "knowledge_base"
        if kb_base.exists():
            for item in kb_base.rglob("*"):
                if item.is_file():
                    dest_file = kb_dir / item.relative_to(kb_base)
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(item), str(dest_file))

                    file_size = dest_file.stat().st_size
                    backed_files.append(str(dest_file))
                    total_size += file_size

        return backed_files, total_size

    def _backup_config(self, backup_dir: Path) -> Tuple[List[str], int]:
        """备份配置"""
        backed_files = []
        total_size = 0
        config_dir = backup_dir / "config"
        config_dir.mkdir(exist_ok=True)

        # 备份.env文件
        env_file = self.base_dir / ".env"
        if env_file.exists():
            dest_file = config_dir / ".env"
            shutil.copy2(str(env_file), str(dest_file))
            backed_files.append(str(dest_file))
            total_size += dest_file.stat().st_size

        # 备份config目录
        config_base = self.base_dir / "config"
        if config_base.exists():
            for item in config_base.rglob("*"):
                if item.is_file():
                    dest_file = config_dir / item.relative_to(config_base)
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(item), str(dest_file))

                    file_size = dest_file.stat().st_size
                    backed_files.append(str(dest_file))
                    total_size += file_size

        return backed_files, total_size

    def _backup_logs(self, backup_dir: Path) -> Tuple[List[str], int]:
        """备份日志"""
        backed_files = []
        total_size = 0
        logs_dir = backup_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        # 备份logs目录
        logs_base = self.base_dir / "logs"
        if logs_base.exists():
            for item in logs_base.rglob("*.log"):
                dest_file = logs_dir / item.name
                shutil.copy2(str(item), str(dest_file))

                file_size = dest_file.stat().st_size
                backed_files.append(str(dest_file))
                total_size += file_size

        return backed_files, total_size

    def _calculate_backup_checksum(self, backup_dir: Path) -> str:
        """计算备份校验和"""
        checksum = hashlib.md5()
        for file in backup_dir.rglob("*"):
            if file.is_file():
                with open(file, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        checksum.update(chunk)
        return checksum.hexdigest()

    def _compress_backup(self, backup_dir: Path, backup_id: str) -> str:
        """压缩备份"""
        compressed_file = self.backup_root / f"{backup_id}.tar.gz"

        # 创建tar.gz压缩包
        shutil.make_archive(
            str(compressed_file.with_suffix('')),
            'gztar',
            str(backup_dir.parent),
            backup_dir.name
        )

        # 删除原始备份目录
        shutil.rmtree(str(backup_dir))

        return str(compressed_file)

    def _record_backup(
        self,
        backup_info: BackupInfo,
        backup_dir: Path,
        files: List[str]
    ):
        """记录备份信息到数据库"""
        conn = sqlite3.connect(str(self.backup_db))
        cursor = conn.cursor()

        # 插入备份记录
        cursor.execute('''
            INSERT INTO backups
            (backup_id, backup_type, created_at, size_mb, checksum, files_count, description, backup_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            backup_info.backup_id,
            backup_info.backup_type,
            backup_info.created_at,
            backup_info.size_mb,
            backup_info.checksum,
            backup_info.files_count,
            backup_info.description,
            str(backup_dir)
        ))

        # 插入文件记录
        for file_path in files:
            file_type = self._get_file_type(file_path)
            original_path = str(Path(file_path).relative_to(backup_dir))

            try:
                file_size = Path(file_path).stat().st_size
            except:
                file_size = 0

            cursor.execute('''
                INSERT INTO backup_files
                (backup_id, file_path, file_type, original_path, file_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (backup_info.backup_id, file_path, file_type, original_path, file_size))

        conn.commit()
        conn.close()

    def _get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """获取备份信息"""
        conn = sqlite3.connect(str(self.backup_db))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM backups WHERE backup_id = ?",
            (backup_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return BackupInfo(
                backup_id=row[0],
                backup_type=row[1],
                created_at=row[2],
                size_mb=row[3],
                checksum=row[4],
                files_count=row[5],
                description=row[6]
            )
        return None

    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == '.db':
            return 'database'
        elif ext == '.log':
            return 'log'
        elif ext in ['.yml', '.yaml', '.json', '.env']:
            return 'config'
        else:
            return 'unknown'

    def _restore_databases(self, backup_dir: Path):
        """恢复数据库"""
        db_backup_dir = backup_dir / "database"
        if not db_backup_dir.exists():
            return

        for db_file in db_backup_dir.rglob("*.db"):
            dest_file = self.base_dir / db_file.name
            shutil.copy2(str(db_file), str(dest_file))
            logger.info(f"恢复数据库: {db_file.name}")

    def _restore_knowledge_base(self, backup_dir: Path):
        """恢复知识库"""
        kb_backup_dir = backup_dir / "knowledge_base"
        if not kb_backup_dir.exists():
            return

        kb_base = self.base_dir / "knowledge_base"
        kb_base.mkdir(exist_ok=True)

        for item in kb_backup_dir.rglob("*"):
            if item.is_file():
                dest_file = kb_base / item.relative_to(kb_backup_dir)
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(dest_file))

        logger.info("恢复知识库")

    def _restore_config(self, backup_dir: Path):
        """恢复配置"""
        config_backup_dir = backup_dir / "config"
        if not config_backup_dir.exists():
            return

        for item in config_backup_dir.rglob("*"):
            if item.is_file():
                dest_file = self.base_dir / item.name
                shutil.copy2(str(item), str(dest_file))

        logger.info("恢复配置")

    def _restore_logs(self, backup_dir: Path):
        """恢复日志"""
        logs_backup_dir = backup_dir / "logs"
        if not logs_backup_dir.exists():
            return

        logs_base = self.base_dir / "logs"
        logs_base.mkdir(exist_ok=True)

        for item in logs_backup_dir.rglob("*.log"):
            dest_file = logs_base / item.name
            shutil.copy2(str(item), str(dest_file))

        logger.info("恢复日志")


# ========== 测试和便捷函数 ==========

def test_backup_manager():
    """测试备份管理器"""
    print("=" * 80)
    print("备份管理器测试")
    print("=" * 80)

    try:
        # 创建备份管理器
        manager = BackupManager()

        # 创建测试备份
        print("\n[1] 创建测试备份...")
        backup_info = manager.create_backup(
            backup_type=BackupManager.BACKUP_TYPE_CONFIG,
            description="测试配置备份"
        )
        print(f"   备份ID: {backup_info.backup_id}")
        print(f"   备份大小: {backup_info.size_mb:.2f}MB")
        print(f"   文件数: {backup_info.files_count}")

        # 列出备份
        print("\n[2] 列出所有备份...")
        backups = manager.list_backups()
        for i, backup in enumerate(backups, 1):
            print(f"   {i}. {backup.backup_id} - {backup.description} ({backup.size_mb:.2f}MB)")

        # 清理旧备份
        print("\n[3] 清理旧备份...")
        deleted = manager.delete_old_backups(keep_days=30)
        print(f"   删除了 {deleted} 个旧备份")

        print("\n" + "=" * 80)
        print("[OK] 备份管理器测试完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_backup_manager()
