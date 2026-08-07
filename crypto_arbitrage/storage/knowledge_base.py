"""知识库存储系统 - 基于 DeepAgents 存储机制"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """知识库 - 存储和管理交易知识"""

    def __init__(self, db_path: str = "crypto_arbitrage_knowledge.db"):
        """初始化知识库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._initialize_database()

        logger.info(f"知识库初始化完成: {db_path}")

    def _initialize_database(self) -> None:
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 策略知识表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    parameters TEXT,
                    performance_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 市场模式表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_name TEXT NOT NULL,
                    pattern_type TEXT,
                    description TEXT,
                    indicators TEXT,
                    success_rate REAL,
                    sample_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 风险事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT,
                    description TEXT,
                    impact TEXT,
                    lessons_learned TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 交易记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT NOT NULL,
                    symbol TEXT,
                    exchange TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    quantity REAL,
                    profit REAL,
                    profit_rate REAL,
                    status TEXT,
                    execution_time REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 性能指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT NOT NULL,
                    date DATE NOT NULL,
                    total_trades INTEGER,
                    profitable_trades INTEGER,
                    total_profit REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL,
                    win_rate REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(strategy, date)
                )
            """)

            # 项目进度表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    date DATE NOT NULL,
                    completed_tasks TEXT,
                    in_progress_tasks TEXT,
                    planned_tasks TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 知识条目表 (通用知识存储)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    tags TEXT,
                    importance INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def add_strategy(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> int:
        """添加策略到知识库

        Args:
            name: 策略名称
            description: 策略描述
            parameters: 策略参数
            performance_metrics: 性能指标

        Returns:
            策略ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO strategies (name, description, parameters, performance_metrics)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                description,
                json.dumps(parameters),
                json.dumps(performance_metrics) if performance_metrics else None
            ))

            conn.commit()
            strategy_id = cursor.lastrowid

        logger.info(f"策略已添加到知识库: {name} (ID: {strategy_id})")
        return strategy_id

    def add_market_pattern(
        self,
        pattern_name: str,
        pattern_type: str,
        description: str,
        indicators: Dict[str, Any],
        success_rate: float,
        sample_size: int
    ) -> int:
        """添加市场模式到知识库

        Args:
            pattern_name: 模式名称
            pattern_type: 模式类型
            description: 模式描述
            indicators: 技术指标
            success_rate: 成功率
            sample_size: 样本数量

        Returns:
            模式ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO market_patterns
                (pattern_name, pattern_type, description, indicators, success_rate, sample_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pattern_name,
                pattern_type,
                description,
                json.dumps(indicators),
                success_rate,
                sample_size
            ))

            conn.commit()
            pattern_id = cursor.lastrowid

        logger.info(f"市场模式已添加: {pattern_name} (成功率: {success_rate:.1%})")
        return pattern_id

    def add_risk_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        impact: str,
        lessons_learned: str
    ) -> int:
        """添加风险事件到知识库

        Args:
            event_type: 事件类型
            severity: 严重程度
            description: 事件描述
            impact: 事件影响
            lessons_learned: 经验教训

        Returns:
            事件ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO risk_events
                (event_type, severity, description, impact, lessons_learned)
                VALUES (?, ?, ?, ?, ?)
            """, (event_type, severity, description, impact, lessons_learned))

            conn.commit()
            event_id = cursor.lastrowid

        logger.warning(f"风险事件已记录: {event_type} (严重程度: {severity})")
        return event_id

    def add_trade_record(
        self,
        strategy: str,
        symbol: str,
        exchange: str,
        entry_price: float,
        exit_price: Optional[float],
        quantity: float,
        profit: Optional[float],
        profit_rate: Optional[float],
        status: str,
        execution_time: float,
        notes: Optional[str] = None
    ) -> int:
        """添加交易记录到知识库

        Args:
            strategy: 策略名称
            symbol: 交易对
            exchange: 交易所
            entry_price: 入场价格
            exit_price: 出场价格
            quantity: 数量
            profit: 利润
            profit_rate: 收益率
            status: 交易状态
            execution_time: 执行时间
            notes: 备注

        Returns:
            交易记录ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO trades
                (strategy, symbol, exchange, entry_price, exit_price, quantity,
                 profit, profit_rate, status, execution_time, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                strategy, symbol, exchange, entry_price, exit_price, quantity,
                profit, profit_rate, status, execution_time, notes
            ))

            conn.commit()
            trade_id = cursor.lastrowid

        logger.info(f"交易记录已添加: {strategy} {symbol} (状态: {status})")
        return trade_id

    def add_performance_metrics(
        self,
        strategy: str,
        date: str,
        total_trades: int,
        profitable_trades: int,
        total_profit: float,
        max_drawdown: float,
        sharpe_ratio: Optional[float],
        win_rate: float
    ) -> int:
        """添加性能指标到知识库

        Args:
            strategy: 策略名称
            date: 日期 (YYYY-MM-DD)
            total_trades: 总交易数
            profitable_trades: 盈利交易数
            total_profit: 总利润
            max_drawdown: 最大回撤
            sharpe_ratio: 夏普比率
            win_rate: 胜率

        Returns:
            记录ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO performance_metrics
                (strategy, date, total_trades, profitable_trades, total_profit,
                 max_drawdown, sharpe_ratio, win_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(strategy, date) DO UPDATE SET
                    total_trades=excluded.total_trades,
                    profitable_trades=excluded.profitable_trades,
                    total_profit=excluded.total_profit,
                    max_drawdown=excluded.max_drawdown,
                    sharpe_ratio=excluded.sharpe_ratio,
                    win_rate=excluded.win_rate
            """, (
                strategy, date, total_trades, profitable_trades, total_profit,
                max_drawdown, sharpe_ratio, win_rate
            ))

            conn.commit()
            record_id = cursor.lastrowid

        logger.info(f"性能指标已更新: {strategy} {date}")
        return record_id

    def add_project_progress(
        self,
        version: str,
        date: str,
        completed_tasks: List[str],
        in_progress_tasks: List[str],
        planned_tasks: List[str],
        notes: Optional[str] = None
    ) -> int:
        """添加项目进度记录

        Args:
            version: 版本号
            date: 日期 (YYYY-MM-DD)
            completed_tasks: 已完成任务列表
            in_progress_tasks: 进行中任务列表
            planned_tasks: 计划任务列表
            notes: 备注说明

        Returns:
            记录ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO project_progress
                (version, date, completed_tasks, in_progress_tasks, planned_tasks, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                version,
                date,
                json.dumps(completed_tasks, ensure_ascii=False),
                json.dumps(in_progress_tasks, ensure_ascii=False),
                json.dumps(planned_tasks, ensure_ascii=False),
                notes
            ))

            conn.commit()
            record_id = cursor.lastrowid

        logger.info(f"项目进度已记录: 版本 {version}, 日期 {date}")
        return record_id

    def add_knowledge_entry(
        self,
        category: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        importance: int = 3
    ) -> int:
        """添加通用知识条目

        Args:
            category: 知识类别
            title: 标题
            content: 内容
            tags: 标签列表
            importance: 重要性 (1-5)

        Returns:
            知识条目ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO knowledge_entries
                (category, title, content, tags, importance)
                VALUES (?, ?, ?, ?, ?)
            """, (
                category,
                title,
                content,
                json.dumps(tags) if tags else None,
                importance
            ))

            conn.commit()
            entry_id = cursor.lastrowid

        logger.info(f"知识条目已添加: {title} (类别: {category})")
        return entry_id

    def add_knowledge(
        self,
        title: str,
        content: str,
        category: str,
        importance: str = "MEDIUM",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """添加知识条目（兼容方法，用于迭代记录）

        Args:
            title: 知识标题
            content: 知识内容
            category: 知识类别
            importance: 重要性 (LOW/MEDIUM/HIGH)
            metadata: 额外的元数据

        Returns:
            知识条目ID
        """
        # 将字符串重要性转换为数字
        importance_map = {
            "LOW": 1,
            "MEDIUM": 3,
            "HIGH": 5
        }
        importance_value = importance_map.get(importance, 3)

        # 从元数据中提取标签
        tags = []
        if metadata:
            tags = [f"{k}:{v}" for k, v in metadata.items() if k != 'added_date']

        # 使用现有的 add_knowledge_entry 方法
        return self.add_knowledge_entry(
            category=category,
            title=title,
            content=content,
            tags=tags if tags else None,
            importance=importance_value
        )

    def get_strategy(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略信息

        Args:
            strategy_name: 策略名称

        Returns:
            策略信息字典
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM strategies WHERE name = ?
            """, (strategy_name,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_recent_trades(
        self,
        limit: int = 100,
        strategy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取最近的交易记录

        Args:
            limit: 返回数量限制
            strategy: 策略名称过滤

        Returns:
            交易记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM trades"
            params = []

            if strategy:
                query += " WHERE strategy = ?"
                params.append(strategy)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_performance_history(
        self,
        strategy: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取性能历史数据

        Args:
            strategy: 策略名称过滤
            days: 查询天数

        Returns:
            性能数据列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT * FROM performance_metrics
                WHERE date >= date('now', ?)
            """
            params = [f'-{days} days']

            if strategy:
                query += " AND strategy = ?"
                params.append(strategy)

            query += " ORDER BY date ASC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_project_progress_history(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取项目进度历史

        Args:
            limit: 返回数量限制

        Returns:
            项目进度记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM project_progress
                ORDER BY date DESC, created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def search_knowledge(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索知识库

        Args:
            keyword: 搜索关键词
            category: 知识类别过滤
            limit: 返回数量限制

        Returns:
            匹配的知识条目列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT * FROM knowledge_entries
                WHERE (title LIKE ? OR content LIKE ?)
            """
            params = [f'%{keyword}%', f'%{keyword}%']

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY importance DESC, created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息

        Returns:
            统计信息字典
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # 统计各表的记录数
            cursor.execute("SELECT COUNT(*) FROM strategies")
            stats['strategies_count'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM market_patterns")
            stats['patterns_count'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM risk_events")
            stats['risk_events_count'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trades")
            stats['trades_count'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM performance_metrics")
            stats['performance_records_count'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
            stats['knowledge_entries_count'] = cursor.fetchone()[0]

            # 计算总盈亏
            cursor.execute("SELECT SUM(profit) FROM trades WHERE profit IS NOT NULL")
            total_profit = cursor.fetchone()[0]
            stats['total_profit'] = total_profit if total_profit else 0.0

            # 计算胜率
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as profitable
                FROM trades WHERE profit IS NOT NULL
            """)
            row = cursor.fetchone()
            if row[0] > 0:
                stats['win_rate'] = row[1] / row[0]
            else:
                stats['win_rate'] = 0.0

            return stats

    def export_knowledge_to_markdown(self, output_path: str) -> None:
        """导出知识库到 Markdown 文件

        Args:
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 数字货币套利交易系统知识库\n\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 导出策略知识
            f.write("## 策略知识\n\n")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM strategies ORDER BY name")
                for row in cursor.fetchall():
                    strategy = dict(row)
                    f.write(f"### {strategy['name']}\n\n")
                    f.write(f"**描述**: {strategy['description']}\n\n")

                    if strategy['parameters']:
                        params = json.loads(strategy['parameters'])
                        f.write("**参数**:\n\n")
                        for key, value in params.items():
                            f.write(f"- {key}: {value}\n")
                        f.write("\n")

                    if strategy['performance_metrics']:
                        metrics = json.loads(strategy['performance_metrics'])
                        f.write("**性能指标**:\n\n")
                        for key, value in metrics.items():
                            f.write(f"- {key}: {value}\n")
                        f.write("\n")

                    f.write(f"*创建时间: {strategy['created_at']}*\n\n")

            # 导出市场模式
            f.write("## 市场模式\n\n")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM market_patterns ORDER BY success_rate DESC")
                for row in cursor.fetchall():
                    pattern = dict(row)
                    f.write(f"### {pattern['pattern_name']}\n\n")
                    f.write(f"**类型**: {pattern['pattern_type']}\n\n")
                    f.write(f"**描述**: {pattern['description']}\n\n")
                    f.write(f"**成功率**: {pattern['success_rate']:.1%}\n\n")
                    f.write(f"**样本数**: {pattern['sample_size']}\n\n")
                    f.write(f"*记录时间: {pattern['created_at']}*\n\n")

            # 导出风险事件
            f.write("## 风险事件\n\n")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM risk_events ORDER BY created_at DESC LIMIT 50")
                for row in cursor.fetchall():
                    event = dict(row)
                    f.write(f"### {event['event_type']} ({event['severity']})\n\n")
                    f.write(f"**描述**: {event['description']}\n\n")
                    f.write(f"**影响**: {event['impact']}\n\n")
                    f.write(f"**经验教训**: {event['lessons_learned']}\n\n")
                    f.write(f"*发生时间: {event['created_at']}*\n\n")

        logger.info(f"知识库已导出到: {output_path}")


# 创建全局知识库实例
knowledge_base: Optional[KnowledgeBase] = None


def initialize_knowledge_base(db_path: str = "crypto_arbitrage_knowledge.db") -> KnowledgeBase:
    """初始化全局知识库

    Args:
        db_path: 数据库文件路径

    Returns:
        知识库实例
    """
    global knowledge_base
    knowledge_base = KnowledgeBase(db_path)
    return knowledge_base


def get_knowledge_base() -> Optional[KnowledgeBase]:
    """获取全局知识库实例

    Returns:
        知识库实例，如果未初始化则返回 None
    """
    return knowledge_base
