"""管道状态持久化层 V16.6

将管道运行状态（持仓/NAV/熔断/统计）持久化到SQLite，
确保系统重启后能恢复到上次运行状态。

核心能力：
1. 持仓快照 — 开仓/平仓/结算状态保存与恢复
2. 风控状态 — NAV/峰值/回撤/熔断器状态持久化
3. 管道统计 — 累计交易/盈亏/信号计数跨重启保持
4. 结果历史 — 管道执行结果存档，支持查询和回溯

架构位置:
    ArbitragePipeline V16.6
           ↕ save/load
    PipelineStatePersistence V16.6
           ↕
    SQLite (pipeline_state.db)

创建时间：2026-05-05
"""

import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PersistedPosition:
    """持久化的持仓记录"""
    position_id: str
    strategy: str
    symbol: str
    exchange: str
    side: str
    quantity: float
    value_usd: float
    entry_price: float
    unrealized_pnl_usd: float
    opened_at: float
    extra_data: str = ""  # JSON格式的额外数据


@dataclass
class PersistedRiskState:
    """持久化的风控状态"""
    peak_nav: float
    total_realized_pnl: float
    circuit_breaker_active: bool
    circuit_breaker_reason: str
    circuit_breaker_since: float
    total_position_count: int
    timestamp: float = 0.0


@dataclass
class PersistedPipelineStats:
    """持久化的管道统计"""
    total_pipelines: int = 0
    total_opportunities_found: int = 0
    total_opportunities_executed: int = 0
    total_positions_opened: int = 0
    total_positions_closed: int = 0
    total_realized_pnl: float = 0.0
    total_stat_arb_pnl: float = 0.0
    total_funding_rate_pnl: float = 0.0
    total_portfolio_risk_rejections: int = 0
    timestamp: float = 0.0


class PipelineStatePersistence:
    """管道状态持久化 V16.6

    使用SQLite持久化管道运行状态，支持重启恢复。
    """

    SCHEMA_VERSION = "V16.6"

    def __init__(self, db_path: str = "pipeline_state.db", config: Optional[Dict[str, Any]] = None):
        """初始化持久化层

        Args:
            db_path: 数据库文件路径
            config: 配置字典
        """
        self._db_path = db_path
        self.config = config or {}
        self._lock = threading.RLock()  # 使用可重入锁避免嵌套锁死锁

        self._conn: Optional[sqlite3.Connection] = None
        self._init_database()

        logger.info(f"管道状态持久化 V16.6 初始化: {db_path}")

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 持仓表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                position_id TEXT PRIMARY KEY,
                strategy TEXT NOT NULL,
                symbol TEXT NOT NULL,
                exchange TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                value_usd REAL NOT NULL,
                entry_price REAL NOT NULL,
                unrealized_pnl_usd REAL DEFAULT 0,
                opened_at REAL NOT NULL,
                extra_data TEXT DEFAULT '{}',
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 风控状态表（单行）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                peak_nav REAL DEFAULT 0,
                total_realized_pnl REAL DEFAULT 0,
                circuit_breaker_active INTEGER DEFAULT 0,
                circuit_breaker_reason TEXT DEFAULT '',
                circuit_breaker_since REAL DEFAULT 0,
                total_position_count INTEGER DEFAULT 0,
                timestamp REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 管道统计表（单行）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_pipelines INTEGER DEFAULT 0,
                total_opportunities_found INTEGER DEFAULT 0,
                total_opportunities_executed INTEGER DEFAULT 0,
                total_positions_opened INTEGER DEFAULT 0,
                total_positions_closed INTEGER DEFAULT 0,
                total_realized_pnl REAL DEFAULT 0,
                total_stat_arb_pnl REAL DEFAULT 0,
                total_funding_rate_pnl REAL DEFAULT 0,
                total_portfolio_risk_rejections INTEGER DEFAULT 0,
                timestamp REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 管道结果历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                opportunities_scanned INTEGER DEFAULT 0,
                opportunities_executed INTEGER DEFAULT 0,
                positions_opened INTEGER DEFAULT 0,
                positions_closed INTEGER DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                execution_time_ms REAL DEFAULT 0,
                errors TEXT DEFAULT '[]',
                details TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_positions_strategy
            ON positions(strategy)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_positions_symbol
            ON positions(symbol)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_positions_status
            ON positions(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_pipeline_id
            ON pipeline_history(pipeline_id)
        """)

        conn.commit()
        logger.debug("管道状态数据库初始化完成")

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is not None:
            return self._conn

        db_path = Path(self._db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        return self._conn

    # ==================== 持仓操作 ====================

    def save_position(
        self,
        position_id: str,
        strategy: str,
        symbol: str,
        exchange: str,
        side: str,
        quantity: float,
        value_usd: float,
        entry_price: float,
        unrealized_pnl_usd: float = 0.0,
        opened_at: float = 0.0,
        extra_data: Optional[Dict] = None
    ) -> bool:
        """保存持仓

        Args:
            position_id: 持仓ID
            strategy: 策略
            symbol: 交易对
            exchange: 交易所
            side: 方向
            quantity: 数量
            value_usd: 价值
            entry_price: 入场价
            unrealized_pnl_usd: 未实现盈亏
            opened_at: 开仓时间
            extra_data: 额外数据

        Returns:
            是否成功
        """
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    INSERT OR REPLACE INTO positions
                    (position_id, strategy, symbol, exchange, side, quantity,
                     value_usd, entry_price, unrealized_pnl_usd, opened_at,
                     extra_data, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', CURRENT_TIMESTAMP)
                """, (
                    position_id, strategy, symbol, exchange, side, quantity,
                    value_usd, entry_price, unrealized_pnl_usd,
                    opened_at or time.time(),
                    json.dumps(extra_data or {}, ensure_ascii=False)
                ))
                conn.commit()
                logger.debug(f"持仓已保存: {position_id} {symbol}")
                return True
            except Exception as e:
                logger.error(f"保存持仓失败: {e}")
                return False

    def close_position(
        self,
        position_id: str,
        realized_pnl: float = 0.0
    ) -> bool:
        """关闭持仓

        Args:
            position_id: 持仓ID
            realized_pnl: 已实现盈亏

        Returns:
            是否成功
        """
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    UPDATE positions
                    SET status = 'closed',
                        unrealized_pnl_usd = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE position_id = ?
                """, (realized_pnl, position_id))
                conn.commit()
                logger.debug(f"持仓已关闭: {position_id}")
                return True
            except Exception as e:
                logger.error(f"关闭持仓失败: {e}")
                return False

    def load_open_positions(self) -> List[PersistedPosition]:
        """加载所有开仓持仓

        Returns:
            持仓列表
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("""
                    SELECT * FROM positions
                    WHERE status = 'open'
                    ORDER BY opened_at ASC
                """)
                rows = cursor.fetchall()

                positions = []
                for row in rows:
                    positions.append(PersistedPosition(
                        position_id=row["position_id"],
                        strategy=row["strategy"],
                        symbol=row["symbol"],
                        exchange=row["exchange"],
                        side=row["side"],
                        quantity=row["quantity"],
                        value_usd=row["value_usd"],
                        entry_price=row["entry_price"],
                        unrealized_pnl_usd=row["unrealized_pnl_usd"],
                        opened_at=row["opened_at"],
                        extra_data=row["extra_data"]
                    ))

                logger.info(f"加载开仓持仓: {len(positions)} 个")
                return positions

            except Exception as e:
                logger.error(f"加载持仓失败: {e}")
                return []

    # ==================== 风控状态操作 ====================

    def save_risk_state(
        self,
        peak_nav: float,
        total_realized_pnl: float,
        circuit_breaker_active: bool,
        circuit_breaker_reason: str,
        circuit_breaker_since: float,
        total_position_count: int
    ) -> bool:
        """保存风控状态

        Args:
            peak_nav: 峰值NAV
            total_realized_pnl: 累计已实现盈亏
            circuit_breaker_active: 熔断器是否激活
            circuit_breaker_reason: 熔断原因
            circuit_breaker_since: 熔断开始时间
            total_position_count: 总持仓数

        Returns:
            是否成功
        """
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    INSERT OR REPLACE INTO risk_state
                    (id, peak_nav, total_realized_pnl, circuit_breaker_active,
                     circuit_breaker_reason, circuit_breaker_since,
                     total_position_count, timestamp, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    peak_nav, total_realized_pnl,
                    int(circuit_breaker_active), circuit_breaker_reason,
                    circuit_breaker_since, total_position_count, time.time()
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存风控状态失败: {e}")
                return False

    def load_risk_state(self) -> Optional[PersistedRiskState]:
        """加载风控状态

        Returns:
            风控状态，无数据返回None
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("SELECT * FROM risk_state WHERE id = 1")
                row = cursor.fetchone()

                if row is None:
                    return None

                return PersistedRiskState(
                    peak_nav=row["peak_nav"],
                    total_realized_pnl=row["total_realized_pnl"],
                    circuit_breaker_active=bool(row["circuit_breaker_active"]),
                    circuit_breaker_reason=row["circuit_breaker_reason"],
                    circuit_breaker_since=row["circuit_breaker_since"],
                    total_position_count=row["total_position_count"],
                    timestamp=row["timestamp"]
                )

            except Exception as e:
                logger.error(f"加载风控状态失败: {e}")
                return None

    # ==================== 管道统计操作 ====================

    def save_pipeline_stats(self, stats: PersistedPipelineStats) -> bool:
        """保存管道统计

        Args:
            stats: 管道统计数据

        Returns:
            是否成功
        """
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    INSERT OR REPLACE INTO pipeline_stats
                    (id, total_pipelines, total_opportunities_found,
                     total_opportunities_executed, total_positions_opened,
                     total_positions_closed, total_realized_pnl,
                     total_stat_arb_pnl, total_funding_rate_pnl,
                     total_portfolio_risk_rejections, timestamp, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    stats.total_pipelines,
                    stats.total_opportunities_found,
                    stats.total_opportunities_executed,
                    stats.total_positions_opened,
                    stats.total_positions_closed,
                    stats.total_realized_pnl,
                    stats.total_stat_arb_pnl,
                    stats.total_funding_rate_pnl,
                    stats.total_portfolio_risk_rejections,
                    time.time()
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存管道统计失败: {e}")
                return False

    def load_pipeline_stats(self) -> Optional[PersistedPipelineStats]:
        """加载管道统计

        Returns:
            管道统计，无数据返回None
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("SELECT * FROM pipeline_stats WHERE id = 1")
                row = cursor.fetchone()

                if row is None:
                    return None

                return PersistedPipelineStats(
                    total_pipelines=row["total_pipelines"],
                    total_opportunities_found=row["total_opportunities_found"],
                    total_opportunities_executed=row["total_opportunities_executed"],
                    total_positions_opened=row["total_positions_opened"],
                    total_positions_closed=row["total_positions_closed"],
                    total_realized_pnl=row["total_realized_pnl"],
                    total_stat_arb_pnl=row["total_stat_arb_pnl"],
                    total_funding_rate_pnl=row["total_funding_rate_pnl"],
                    total_portfolio_risk_rejections=row["total_portfolio_risk_rejections"],
                    timestamp=row["timestamp"]
                )

            except Exception as e:
                logger.error(f"加载管道统计失败: {e}")
                return None

    # ==================== 管道历史操作 ====================

    def save_pipeline_result(
        self,
        pipeline_id: str,
        stage: str,
        opportunities_scanned: int = 0,
        opportunities_executed: int = 0,
        positions_opened: int = 0,
        positions_closed: int = 0,
        realized_pnl: float = 0.0,
        execution_time_ms: float = 0.0,
        errors: Optional[List[str]] = None,
        details: Optional[Dict] = None
    ) -> bool:
        """保存管道执行结果到历史

        Args:
            pipeline_id: 管道ID
            stage: 管道阶段
            opportunities_scanned: 扫描到的机会数
            opportunities_executed: 执行的机会数
            positions_opened: 开仓数
            positions_closed: 平仓数
            realized_pnl: 已实现盈亏
            execution_time_ms: 执行时间(ms)
            errors: 错误列表
            details: 详情

        Returns:
            是否成功
        """
        with self._lock:
            try:
                conn = self._get_connection()
                conn.execute("""
                    INSERT INTO pipeline_history
                    (pipeline_id, stage, opportunities_scanned, opportunities_executed,
                     positions_opened, positions_closed, realized_pnl,
                     execution_time_ms, errors, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pipeline_id, stage, opportunities_scanned, opportunities_executed,
                    positions_opened, positions_closed, realized_pnl,
                    execution_time_ms,
                    json.dumps(errors or [], ensure_ascii=False),
                    json.dumps(details or {}, ensure_ascii=False)
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存管道结果失败: {e}")
                return False

    def load_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """加载最近的管道执行历史

        Args:
            limit: 返回数量

        Returns:
            历史记录列表
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("""
                    SELECT * FROM pipeline_history
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    results.append({
                        "pipeline_id": row["pipeline_id"],
                        "stage": row["stage"],
                        "opportunities_scanned": row["opportunities_scanned"],
                        "opportunities_executed": row["opportunities_executed"],
                        "positions_opened": row["positions_opened"],
                        "positions_closed": row["positions_closed"],
                        "realized_pnl": row["realized_pnl"],
                        "execution_time_ms": row["execution_time_ms"],
                        "errors": json.loads(row["errors"]) if row["errors"] else [],
                        "details": json.loads(row["details"]) if row["details"] else {},
                        "created_at": row["created_at"],
                    })

                return results

            except Exception as e:
                logger.error(f"加载管道历史失败: {e}")
                return []

    # ==================== 统计与维护 ====================

    def get_persistence_stats(self) -> Dict[str, Any]:
        """获取持久化层统计

        Returns:
            统计字典
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
                open_positions = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'closed'")
                closed_positions = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM pipeline_history")
                history_count = cursor.fetchone()[0]

                risk_state = self.load_risk_state()
                pipeline_stats = self.load_pipeline_stats()

                return {
                    "version": self.SCHEMA_VERSION,
                    "db_path": self._db_path,
                    "open_positions": open_positions,
                    "closed_positions": closed_positions,
                    "history_count": history_count,
                    "has_risk_state": risk_state is not None,
                    "has_pipeline_stats": pipeline_stats is not None,
                }

            except Exception as e:
                return {"error": str(e)}

    def cleanup_old_history(self, max_age_days: int = 30) -> int:
        """清理旧历史记录

        Args:
            max_age_days: 保留天数

        Returns:
            删除的记录数
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("""
                    DELETE FROM pipeline_history
                    WHERE created_at < datetime('now', ?)
                """, (f"-{max_age_days} days",))
                deleted = cursor.rowcount
                conn.commit()

                if deleted > 0:
                    logger.info(f"清理旧历史: 删除 {deleted} 条记录")

                return deleted

            except Exception as e:
                logger.error(f"清理历史失败: {e}")
                return 0

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("管道状态持久化连接已关闭")


# 全局实例
_pipeline_persistence: Optional[PipelineStatePersistence] = None


def get_pipeline_persistence(
    db_path: str = "pipeline_state.db",
    config: Optional[Dict[str, Any]] = None
) -> PipelineStatePersistence:
    """获取全局管道持久化实例

    Args:
        db_path: 数据库路径
        config: 配置字典

    Returns:
        管道持久化实例
    """
    global _pipeline_persistence
    if _pipeline_persistence is None:
        _pipeline_persistence = PipelineStatePersistence(db_path, config)
    return _pipeline_persistence
