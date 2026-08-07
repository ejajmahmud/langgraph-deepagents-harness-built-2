"""
日志聚合系统 - V15.9 Phase 1核心模块

实现统一的日志收集、聚合、分析和存储系统。

核心功能：
1. 日志收集 - 收集所有组件的日志
2. 日志解析 - 结构化解析日志内容
3. 日志聚合 - 按类型、级别、组件聚合
4. 日志分析 - 日志统计和异常检测
5. 日志存储 - 高效的日志存储和检索

创建时间：2026-05-01 03:15
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
import sqlite3
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    log_file: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'LogEntry':
        """从字典创建"""
        return cls(**data)

    @property
    def severity_score(self) -> int:
        """严重程度评分"""
        severity_map = {
            'DEBUG': 1,
            'INFO': 2,
            'WARNING': 3,
            'ERROR': 4,
            'CRITICAL': 5
        }
        return severity_map.get(self.level, 2)


class LogAggregator:
    """日志聚合器

    提供完整的日志收集、聚合、分析和存储功能。
    """

    # 日志级别
    LEVEL_DEBUG = "DEBUG"
    LEVEL_INFO = "INFO"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"
    LEVEL_CRITICAL = "CRITICAL"

    # 日志模式
    LOG_PATTERN = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[^,]*)'
        r'[,\s]*(?P<level>\w+)'
        r'[\s:-]*(?P<message>.*)',
        re.IGNORECASE
    )

    def __init__(self, base_dir: Optional[str] = None, config: Optional[Dict] = None):
        """初始化日志聚合器

        Args:
            base_dir: 基础目录
            config: 配置字典
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.config = config or {}

        # 日志目录
        self.logs_root = self.base_dir / "logs"
        self.logs_root.mkdir(exist_ok=True)

        # 聚合数据目录
        self.aggregated_root = self.base_dir / "logs_aggregated"
        self.aggregated_root.mkdir(exist_ok=True)

        # 数据库
        self.db_path = self.aggregated_root / "logs.db"
        self._init_db()

        # 日志源配置
        self.log_sources = self.config.get('log_sources', [
            {'path': 'logs', 'component': 'main'},
            {'path': 'logs/knowledge', 'component': 'knowledge-graph'},
            {'path': 'logs/trading', 'component': 'trading-engine'},
            {'path': 'logs/risk', 'component': 'risk-management'}
        ])

        # 聚合策略
        self.aggregate_interval_minutes = self.config.get('aggregate_interval_minutes', 5)
        self.max_log_age_days = self.config.get('max_log_age_days', 30)

        logger.info(f"[OK] 日志聚合器初始化完成，日志根目录: {self.logs_root}")

    def _init_db(self):
        """初始化日志数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 创建日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                log_file TEXT,
                line_number INTEGER,
                severity_score INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs(level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_component ON logs(component)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_severity ON logs(severity_score)')

        # 创建统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                component TEXT NOT NULL,
                level TEXT NOT NULL,
                count INTEGER NOT NULL,
                UNIQUE(date, component, level)
            )
        ''')

        # 创建异常表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_type TEXT NOT NULL,
                component TEXT NOT NULL,
                description TEXT,
                count INTEGER NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                severity INTEGER NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

        logger.info("[OK] 日志数据库初始化完成")

    def collect_logs(
        self,
        since: Optional[datetime] = None,
        components: Optional[List[str]] = None
    ) -> List[LogEntry]:
        """收集日志

        Args:
            since: 收集起始时间
            components: 要收集的组件列表

        Returns:
            日志条目列表
        """
        logger.info("开始收集日志...")

        all_logs = []

        for source in self.log_sources:
            component = source['component']
            if components and component not in components:
                continue

            log_path = self.logs_root / source['path']
            if not log_path.exists():
                continue

            logs = self._collect_logs_from_path(log_path, component, since)
            all_logs.extend(logs)

            logger.info(f"收集了 {len(logs)} 条日志，组件: {component}")

        logger.info(f"[OK] 总共收集了 {len(all_logs)} 条日志")
        return all_logs

    def aggregate_logs(self, logs: List[LogEntry]) -> bool:
        """聚合日志

        Args:
            logs: 日志条目列表

        Returns:
            是否成功
        """
        if not logs:
            logger.warning("没有日志需要聚合")
            return False

        logger.info(f"开始聚合 {len(logs)} 条日志...")

        # 插入到数据库
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            # 批量插入
            for log_entry in logs:
                cursor.execute('''
                    INSERT INTO logs
                    (timestamp, level, component, message, details, log_file, line_number, severity_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log_entry.timestamp,
                    log_entry.level,
                    log_entry.component,
                    log_entry.message,
                    json.dumps(log_entry.details),
                    log_entry.log_file,
                    log_entry.line_number,
                    log_entry.severity_score
                ))

            conn.commit()
            logger.info("[OK] 日志聚合完成")

            # 生成统计
            self._generate_statistics(conn)

            # 检测异常
            self._detect_anomalies(conn)

            return True

        except Exception as e:
            logger.error(f"日志聚合失败: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def query_logs(
        self,
        level: Optional[str] = None,
        component: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        message_filter: Optional[str] = None
    ) -> List[LogEntry]:
        """查询日志

        Args:
            level: 日志级别过滤
            component: 组件过滤
            since: 起始时间
            until: 结束时间
            limit: 返回数量限制
            message_filter: 消息过滤（支持正则）

        Returns:
            日志条目列表
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 构建查询
        query = "SELECT * FROM logs WHERE 1=1"
        params = []

        if level:
            query += " AND level = ?"
            params.append(level)

        if component:
            query += " AND component = ?"
            params.append(component)

        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())

        if until:
            query += " AND timestamp <= ?"
            params.append(until.isoformat())

        if message_filter:
            query += " AND message LIKE ?"
            params.append(f"%{message_filter}%")

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # 转换为LogEntry对象
        logs = []
        for row in rows:
            log_entry = LogEntry(
                timestamp=row[1],
                level=row[2],
                component=row[3],
                message=row[4],
                details=json.loads(row[5]) if row[5] else {},
                log_file=row[6],
                line_number=row[7]
            )
            logs.append(log_entry)

        return logs

    def get_statistics(
        self,
        component: Optional[str] = None,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取统计信息

        Args:
            component: 组件过滤
            date: 日期过滤

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 基础统计
        query = "SELECT level, COUNT(*) FROM logs WHERE 1=1"
        params = []

        if component:
            query += " AND component = ?"
            params.append(component)

        if date:
            date_str = date.strftime("%Y-%m-%d")
            query += " AND DATE(timestamp) = ?"
            params.append(date_str)

        query += " GROUP BY level"

        cursor.execute(query, params)
        level_counts = dict(cursor.fetchall())

        # 总数统计
        cursor.execute("SELECT COUNT(*) FROM logs")
        total_logs = cursor.fetchone()[0]

        # 组件统计
        cursor.execute("SELECT component, COUNT(*) FROM logs GROUP BY component")
        component_counts = dict(cursor.fetchall())

        conn.close()

        return {
            'total_logs': total_logs,
            'level_counts': level_counts,
            'component_counts': component_counts,
            'error_rate': (level_counts.get('ERROR', 0) + level_counts.get('CRITICAL', 0)) / max(total_logs, 1) * 100
        }

    def cleanup_old_logs(self, days: Optional[int] = None) -> int:
        """清理旧日志

        Args:
            days: 保留天数

        Returns:
            删除的日志数量
        """
        keep_days = days or self.max_log_age_days
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 删除旧日志
        cursor.execute(
            "DELETE FROM logs WHERE timestamp < ?",
            (cutoff_date.isoformat(),)
        )

        deleted_count = cursor.rowcount

        # 更新统计表
        cursor.execute(
            "DELETE FROM log_statistics WHERE date < ?",
            (cutoff_date.strftime("%Y-%m-%d"),)
        )

        conn.commit()
        conn.close()

        logger.info(f"[OK] 清理了 {deleted_count} 条旧日志")
        return deleted_count

    # ========== 私有方法 ==========

    def _collect_logs_from_path(
        self,
        log_path: Path,
        component: str,
        since: Optional[datetime]
    ) -> List[LogEntry]:
        """从路径收集日志"""
        logs = []

        for log_file in log_path.rglob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue

                        log_entry = self._parse_log_line(line, component, log_file, line_num)
                        if log_entry:
                            # 检查时间过滤
                            if since:
                                try:
                                    log_time = datetime.fromisoformat(log_entry.timestamp.replace('[', '').replace(']', ''))
                                    if log_time < since:
                                        continue
                                except:
                                    pass

                            logs.append(log_entry)

            except Exception as e:
                logger.warning(f"读取日志文件失败 {log_file}: {e}")

        return logs

    def _parse_log_line(
        self,
        line: str,
        component: str,
        log_file: Path,
        line_num: int
    ) -> Optional[LogEntry]:
        """解析日志行"""
        # 尝试匹配标准日志格式
        match = self.LOG_PATTERN.search(line)
        if match:
            return LogEntry(
                timestamp=match.group('timestamp').strip(),
                level=match.group('level').upper(),
                component=component,
                message=match.group('message').strip(),
                log_file=str(log_file),
                line_number=line_num
            )

        # 如果不匹配标准格式，使用默认解析
        # 简单提取日志级别
        for level in [self.LEVEL_CRITICAL, self.LEVEL_ERROR, self.LEVEL_WARNING, self.LEVEL_INFO, self.LEVEL_DEBUG]:
            if level in line.upper():
                return LogEntry(
                    timestamp=datetime.now().isoformat(),
                    level=level,
                    component=component,
                    message=line,
                    log_file=str(log_file),
                    line_number=line_num
                )

        # 默认为INFO级别
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            level=self.LEVEL_INFO,
            component=component,
            message=line,
            log_file=str(log_file),
            line_number=line_num
        )

    def _generate_statistics(self, conn: sqlite3.Connection):
        """生成日志统计"""
        # 按日期、组件、级别统计
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO log_statistics (date, component, level, count)
            SELECT
                DATE(timestamp) as date,
                component,
                level,
                COUNT(*) as count
            FROM logs
            WHERE DATE(timestamp) = DATE('now')
            GROUP BY DATE(timestamp), component, level
        ''')

        conn.commit()

    def _detect_anomalies(self, conn: sqlite3.Connection):
        """检测日志异常"""
        cursor = conn.cursor()

        # 检测错误激增
        cursor.execute('''
            SELECT component, COUNT(*) as error_count
            FROM logs
            WHERE level IN ('ERROR', 'CRITICAL')
            AND timestamp >= datetime('now', '-1 hour')
            GROUP BY component
            HAVING error_count > 10
        ''')

        for row in cursor.fetchall():
            component, error_count = row
            logger.warning(f"检测到异常: 组件 {component} 错误激增 ({error_count}/小时)")

        # 检测重复错误
        cursor.execute('''
            INSERT OR REPLACE INTO log_anomalies
            (anomaly_type, component, description, count, first_seen, last_seen, severity)
            SELECT
                'repeated_error',
                component,
                message,
                COUNT(*) as count,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen,
                4 as severity
            FROM logs
            WHERE level = 'ERROR'
            AND timestamp >= datetime('now', '-1 hour')
            GROUP BY component, message
            HAVING count > 5
        ''')


# ========== 测试和便捷函数 ==========

def test_log_aggregator():
    """测试日志聚合器"""
    print("=" * 80)
    print("日志聚合器测试")
    print("=" * 80)

    try:
        # 创建日志聚合器
        aggregator = LogAggregator()

        # 创建测试日志文件
        test_logs_path = aggregator.logs_root / "test.log"
        test_logs_path.write_text("""2026-05-01 03:00:00,000 - INFO - Starting system
2026-05-01 03:00:01,000 - INFO - Component initialized
2026-05-01 03:00:02,000 - WARNING - Low memory detected
2026-05-01 03:00:03,000 - ERROR - Connection failed
2026-05-01 03:00:04,000 - CRITICAL - System crash imminent
""")

        # 收集日志
        print("\n[1] 收集日志...")
        logs = aggregator.collect_logs()
        print(f"   收集了 {len(logs)} 条日志")

        # 聚合日志
        print("\n[2] 聚合日志...")
        success = aggregator.aggregate_logs(logs)
        print(f"   聚合{'成功' if success else '失败'}")

        # 查询日志
        print("\n[3] 查询ERROR级别日志...")
        error_logs = aggregator.query_logs(level="ERROR")
        print(f"   找到 {len(error_logs)} 条ERROR日志")
        for log in error_logs:
            print(f"   - [{log.level}] {log.message}")

        # 获取统计
        print("\n[4] 获取统计信息...")
        stats = aggregator.get_statistics()
        print(f"   总日志数: {stats['total_logs']}")
        print(f"   错误率: {stats['error_rate']:.2f}%")
        print(f"   级别分布: {stats['level_counts']}")

        print("\n" + "=" * 80)
        print("[OK] 日志聚合器测试完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_log_aggregator()
