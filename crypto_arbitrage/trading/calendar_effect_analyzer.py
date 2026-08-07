"""Calendar Effect Analyzer - V28.0 日历效应分析器

分析时间相关的市场效应，包括节假日效应、月度效应、周末效应等。
用于优化交易时间和仓位调整。

核心功能：
1. 节假日效应 - Holiday Effect Analysis
2. 月度效应 - Month-of-Year Effect
3. 周效应 - Day-of-Week Effect
4. 时刻效应 - Time-of-Day Effect
5. 季度效应 - Quarter Effect
6. 收益日历 - Profit Calendar

创建时间：2026-05-07 14:25
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class CalendarEffectType(Enum):
    """日历效应类型"""
    HOLIDAY = "holiday"  # 节假日效应
    MONTH = "month"  # 月度效应
    WEEK = "week"  # 周效应
    TIME = "time"  # 时刻效应
    QUARTER = "quarter"  # 季度效应


@dataclass
class CalendarEffect:
    """日历效应数据"""
    effect_type: str
    period: str  # e.g., "01", "Monday", "CNY"
    win_rate: float = 0.0  # 胜率
    avg_return: float = 0.0  # 平均收益
    volatility: float = 0.0  # 波动率
    sample_count: int = 0  # 样本数量
    confidence: float = 0.0  # 置信度 0-1
    recommendation: str = "neutral"  # increase/neutral/decrease


@dataclass
class HolidayCalendar:
    """节假日日历"""
    name: str  # e.g., "CNY", "THANKSGIVING"
    date: str  # "2026-01-29"
    effect_days_before: int = 0  # 节前效应天数
    effect_days_after: int = 0  # 节后效应天数
    historical_win_rate: float = 0.0
    historical_return: float = 0.0


@dataclass
class CalendarAnalysis:
    """日历分析结果"""
    effects: List[CalendarEffect] = field(default_factory=list)
    best_trading_days: List[str] = field(default_factory=list)
    worst_trading_days: List[str] = field(default_factory=list)
    best_months: List[str] = field(default_factory=list)
    worst_months: List[str] = field(default_factory=list)
    best_time_hours: List[int] = field(default_factory=list)
    active_holidays: List[HolidayCalendar] = field(default_factory=list)
    timestamp: float = 0.0


class CalendarEffectAnalyzer:
    """日历效应分析器 V28.0

    分析时间相关的市场效应，辅助交易决策。
    """

    # 中国主要节假日
    CHINESE_HOLIDAYS = [
        ("CNY", "01-01", 7, 3),  # 春节
        ("QINGMING", "04-04", 1, 1),  # 清明
        ("LABOR", "05-01", 3, 1),  # 劳动节
        ("DRAGON", "06-06", 3, 1),  # 端午
        ("MID_AUTUMN", "09-09", 3, 1),  # 中秋
        ("NATIONAL", "10-01", 7, 3),  # 国庆
    ]

    # 美国主要节假日
    US_HOLIDAYS = [
        ("MLK", "01-20", 1, 1),
        ("PRESIDENTS", "02-17", 1, 1),
        ("MEMORIAL", "05-26", 1, 1),
        ("INDEPENDENCE", "07-04", 3, 1),
        ("LABOR", "09-01", 1, 1),
        ("THANKSGIVING", "11-27", 3, 2),
        ("CHRISTMAS", "12-25", 3, 1),
    ]

    # 英文月份
    MONTH_NAMES = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # 英文星期
    WEEKDAY_NAMES = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化日历效应分析器

        Args:
            config: 配置字典，包含:
                - min_samples: 最小样本数 (默认 5)
                - confidence_threshold: 置信度阈值 (默认 0.6)
                - holiday_region: 节假日区域 "CN" 或 "US" (默认 "CN")
        """
        self.config = config or {}
        self.min_samples = self.config.get("min_samples", 5)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.6)
        self.holiday_region = self.config.get("holiday_region", "CN")

        # 加载历史节假日
        self._holidays = self._load_holidays()

        # 存储的分析数据
        self._monthly_stats = {}
        self._weekly_stats = {}
        self._hourly_stats = {}

    def _load_holidays(self) -> List[HolidayCalendar]:
        """加载节假日日历"""
        if self.holiday_region == "CN":
            holiday_list = self.CHINESE_HOLIDAYS
        else:
            holiday_list = self.US_HOLIDAYS

        holidays = []
        current_year = datetime.now().year

        for name, date_pattern, before, after in holiday_list:
            # 月-日格式
            month_day = date_pattern.split("-")
            month = int(month_day[0])
            day = int(month_day[1])

            holiday = HolidayCalendar(
                name=name,
                date=f"{current_year}-{month:02d}-{day:02d}",
                effect_days_before=before,
                effect_days_after=after,
                historical_win_rate=0.5,
                historical_return=0.0
            )
            holidays.append(holiday)

        return holidays

    def analyze(
        self,
        historical_trades: List[Dict[str, Any]]
    ) -> CalendarAnalysis:
        """分析日历效应

        Args:
            historical_trades: 历史交易列表，每笔包含:
                - timestamp: 交易时间戳
                - profit: 盈亏
                - win: 是否盈利

        Returns:
            CalendarAnalysis: 分析结果
        """
        if not historical_trades:
            logger.warning("无历史交易数据")
            return CalendarAnalysis()

        # 按月/周/小时分组
        self._analyze_monthly(historical_trades)
        self._analyze_weekly(historical_trades)
        self._analyze_hourly(historical_trades)

        # 构建效应列表
        effects = []
        effects.extend(self._get_month_effects())
        effects.extend(self._get_weekly_effects())
        effects.extend(self._get_hourly_effects())

        # 找出最佳/最差
        best_days, worst_days = self._get_best_worst_days()
        best_months, worst_months = self._get_best_worst_months()
        best_hours = self._get_best_hours()

        return CalendarAnalysis(
            effects=effects,
            best_trading_days=best_days,
            worst_trading_days=worst_days,
            best_months=best_months,
            worst_months=worst_months,
            best_time_hours=best_hours,
            active_holidays=self._holidays,
            timestamp=__import__("time").time()
        )

    def _analyze_monthly(self, trades: List[Dict[str, Any]]) -> None:
        """月度分析"""
        monthly: Dict[int, List[float]] = {m: [] for m in range(1, 13)}

        for trade in trades:
            ts = trade.get("timestamp", 0)
            if ts > 0:
                month = datetime.fromtimestamp(ts).month
                profit = trade.get("profit", 0)
                monthly[month].append(profit)

        # 计算统计
        for month, profits in monthly.items():
            if len(profits) >= self.min_samples:
                wins = [p for p in profits if p > 0]
                self._monthly_stats[month] = {
                    "win_rate": len(wins) / len(profits),
                    "avg_return": np.mean(profits),
                    "volatility": np.std(profits),
                    "sample_count": len(profits)
                }

    def _analyze_weekly(self, trades: List[Dict[str, Any]]) -> None:
        """周分析"""
        weekly: Dict[int, List[float]] = {d: [] for d in range(7)}

        for trade in trades:
            ts = trade.get("timestamp", 0)
            if ts > 0:
                weekday = datetime.fromtimestamp(ts).weekday()
                profit = trade.get("profit", 0)
                weekly[weekday].append(profit)

        # 计算统计
        for day, profits in weekly.items():
            if len(profits) >= self.min_samples:
                wins = [p for p in profits if p > 0]
                self._weekly_stats[day] = {
                    "win_rate": len(wins) / len(profits),
                    "avg_return": np.mean(profits),
                    "volatility": np.std(profits),
                    "sample_count": len(profits)
                }

    def _analyze_hourly(self, trades: List[Dict[str, Any]]) -> None:
        """小时分析"""
        hourly: Dict[int, List[float]] = {h: [] for h in range(24)}

        for trade in trades:
            ts = trade.get("timestamp", 0)
            if ts > 0:
                hour = datetime.fromtimestamp(ts).hour
                profit = trade.get("profit", 0)
                hourly[hour].append(profit)

        # 计算统计
        for hour, profits in hourly.items():
            if len(profits) >= self.min_samples:
                wins = [p for p in profits if p > 0]
                self._hourly_stats[hour] = {
                    "win_rate": len(wins) / len(profits),
                    "avg_return": np.mean(profits),
                    "volatility": np.std(profits),
                    "sample_count": len(profits)
                }

    def _get_month_effects(self) -> List[CalendarEffect]:
        """获取月度效应"""
        effects = []
        for month, stats in self._monthly_stats.items():
            rec = "neutral"
            if stats["win_rate"] > 0.6:
                rec = "increase"
            elif stats["win_rate"] < 0.4:
                rec = "decrease"

            effect = CalendarEffect(
                effect_type="month",
                period=f"{month:02d}",
                win_rate=stats["win_rate"],
                avg_return=stats["avg_return"],
                volatility=stats["volatility"],
                sample_count=stats["sample_count"],
                confidence=min(1.0, stats["sample_count"] / 20),
                recommendation=rec
            )
            effects.append(effect)

        return effects

    def _get_weekly_effects(self) -> List[CalendarEffect]:
        """获取周效应"""
        effects = []
        for day, stats in self._weekly_stats.items():
            rec = "neutral"
            if stats["win_rate"] > 0.6:
                rec = "increase"
            elif stats["win_rate"] < 0.4:
                rec = "decrease"

            effect = CalendarEffect(
                effect_type="week",
                period=self.WEEKDAY_NAMES[day],
                win_rate=stats["win_rate"],
                avg_return=stats["avg_return"],
                volatility=stats["volatility"],
                sample_count=stats["sample_count"],
                confidence=min(1.0, stats["sample_count"] / 20),
                recommendation=rec
            )
            effects.append(effect)

        return effects

    def _get_hourly_effects(self) -> List[CalendarEffect]:
        """获取小时效应"""
        effects = []
        for hour, stats in self._hourly_stats.items():
            rec = "neutral"
            if stats["win_rate"] > 0.6:
                rec = "increase"
            elif stats["win_rate"] < 0.4:
                rec = "decrease"

            effect = CalendarEffect(
                effect_type="time",
                period=f"{hour:02d}:00",
                win_rate=stats["win_rate"],
                avg_return=stats["avg_return"],
                volatility=stats["volatility"],
                sample_count=stats["sample_count"],
                confidence=min(1.0, stats["sample_count"] / 20),
                recommendation=rec
            )
            effects.append(effect)

        return effects

    def _get_best_worst_days(self) -> Tuple[List[str], List[str]]:
        """获取最佳/最差交易日"""
        if not self._weekly_stats:
            return [], []

        sorted_days = sorted(
            self._weekly_stats.items(),
            key=lambda x: x[1]["win_rate"],
            reverse=True
        )

        best = [self.WEEKDAY_NAMES[d] for d, _ in sorted_days[:2]]
        worst = [self.WEEKDAY_NAMES[d] for d, _ in sorted_days[-2:]]

        return best, worst

    def _get_best_worst_months(self) -> Tuple[List[str], List[str]]:
        """获取最佳/最差月份"""
        if not self._monthly_stats:
            return [], []

        sorted_months = sorted(
            self._monthly_stats.items(),
            key=lambda x: x[1]["win_rate"],
            reverse=True
        )

        best = [f"{m:02d}" for m, _ in sorted_months[:2]]
        worst = [f"{m:02d}" for m, _ in sorted_months[-2:]]

        return best, worst

    def _get_best_hours(self) -> List[int]:
        """获取最佳交易小时"""
        if not self._hourly_stats:
            return []

        sorted_hours = sorted(
            self._hourly_stats.items(),
            key=lambda x: x[1]["win_rate"],
            reverse=True
        )

        return [h for h, _ in sorted_hours[:3]]

    def get_recommendation(self) -> Dict[str, Any]:
        """获取当前交易建议

        Returns:
            建议字典，包含仓位调整建议和最佳交易时间
        """
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        month = now.month

        # 检查周效应
        week_rec = "neutral"
        if weekday in self._weekly_stats:
            wr = self._weekly_stats[weekday]["win_rate"]
            if wr > 0.6:
                week_rec = "increase"
            elif wr < 0.4:
                week_rec = "decrease"

        # 检查小时效应
        hour_rec = "neutral"
        if hour in self._hourly_stats:
            hr = self._hourly_stats[hour]["win_rate"]
            if hr > 0.6:
                hour_rec = "increase"
            elif hr < 0.4:
                hour_rec = "decrease"

        # 检查月度效应
        month_rec = "neutral"
        if month in self._monthly_stats:
            mr = self._monthly_stats[month]["win_rate"]
            if mr > 0.6:
                month_rec = "increase"
            elif mr < 0.4:
                month_rec = "decrease"

        # 综合建议
        increase_count = sum([
            week_rec == "increase",
            hour_rec == "increase",
            month_rec == "increase"
        ])

        if increase_count >= 2:
            position_adj = 1.2  # 增仓
        elif increase_count == 0:
            position_adj = 0.7  # 减仓
        else:
            position_adj = 1.0  # 正常

        return {
            "position_adjustment": position_adj,
            "weekday_effect": week_rec,
            "hourly_effect": hour_rec,
            "monthly_effect": month_rec,
            "current_weekday": self.WEEKDAY_NAMES[weekday],
            "current_hour": hour,
            "current_month": f"{month:02d}"
        }


def create_analyzer(config: Optional[Dict[str, Any]] = None) -> CalendarEffectAnalyzer:
    """创建日历效应分析器"""
    return CalendarEffectAnalyzer(config)