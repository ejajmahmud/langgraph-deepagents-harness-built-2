"""Real-Time Risk Dashboard - V28.0 实时风控仪表板

实时显示系统风险状态，提供直观的风险监控界面。

核心功能：
1. 实时风险指标 - Real-Time Risk Metrics
2. 风险热力图 - Risk Heatmap
3. 暴露度监控 - Exposure Monitoring
4. 杠杆仪表 - Leverage Gauge
5. 风险告警 - Risk Alerts
6. 趋势分析 - Trend Analysis

创建时间：2026-05-07 14:30
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """风险指标"""
    total_exposure: float = 0.0  # 总暴露
    max_exposure: float = 0.0  # 最大暴露
    utilization: float = 0.0  # 资金利用率
    leverage: float = 1.0  # 杠杆率
    position_count: int = 0  # 持仓数量
    daily_pnl: float = 0.0  # 今日盈亏
    max_drawdown: float = 0.0  # 最大回撤
    win_rate: float = 0.5  # 胜率
    risk_score: float = 50.0  # 风险评分 0-100


@dataclass
class SymbolExposure:
    """币种暴露"""
    symbol: str
    position_size: float = 0.0
    position_value: float = 0.0
    exposure_pct: float = 0.0  # 占比
    side: str = "neutral"
    unrealized_pnl: float = 0.0
    liquidation_distance: float = 0.0  # 距离爆仓百分比


@dataclass
class RiskAlert:
    """风险告警"""
    alert_id: str
    level: str  # low/medium/high/critical
    message: str
    symbol: Optional[str] = None
    timestamp: float = 0.0
    acknowledged: bool = False


@dataclass
class DashboardState:
    """仪表板状态"""
    status: str = "normal"  # normal/warning/critical
    risk_level: str = "low"
    last_update: float = 0.0
    uptime_seconds: float = 0.0
    metrics: RiskMetrics = field(default_factory=RiskMetrics)
    exposures: List[SymbolExposure] = field(default_factory=list)
    alerts: List[RiskAlert] = field(default_factory=list)
    trends: Dict[str, float] = field(default_factory=dict)


class RealTimeRiskDashboard:
    """实时风控仪表板 V28.0

    实时监控和显示系统风险状态。
    """

    # 风险阈值配置
    THRESHOLDS = {
        "max_exposure": 10000.0,  # 最大暴露
        "max_leverage": 3.0,  # 最大杠杆
        "max_position_count": 10,  # 最大持仓数
        "max_drawdown": 0.15,  # 最大回撤15%
        "min_liquidation_distance": 0.20,  # 最小距离爆仓20%
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化仪表板

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._thresholds = {**self.THRESHOLDS, **self.config}

        # 状态
        self._state = DashboardState()
        self._start_time = time.time()
        self._lock = threading.Lock()

        # 历史数据 (用于趋势)
        self._history: List[RiskMetrics] = []
        self._max_history = 100  # 保留100条历史

    def update(
        self,
        total_exposure: float,
        max_exposure: float,
        utilization: float,
        leverage: float,
        position_count: int,
        daily_pnl: float,
        max_drawdown: float,
        win_rate: float,
        positions: Optional[List[Dict[str, Any]]] = None
    ) -> DashboardState:
        """更新仪表板状态

        Args:
            total_exposure: 总暴露
            max_exposure: 最大暴露
            utilization: 资金利用率
            leverage: 杠杆率
            position_count: 持仓数
            daily_pnl: 今日盈亏
            max_drawdown: 最大回撤
            win_rate: 胜率
            positions: 持仓列表 (可选)

        Returns:
            DashboardState: 更新后的状态
        """
        with self._lock:
            # 更新指标
            metrics = RiskMetrics(
                total_exposure=total_exposure,
                max_exposure=max_exposure,
                utilization=utilization,
                leverage=leverage,
                position_count=position_count,
                daily_pnl=daily_pnl,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                risk_score=self._calculate_risk_score(
                    total_exposure, leverage, max_drawdown, position_count
                )
            )

            # 更新暴露
            exposures = []
            if positions:
                for pos in positions:
                    sym = SymbolExposure(
                        symbol=pos.get("symbol", ""),
                        position_size=pos.get("size", 0),
                        position_value=pos.get("value", 0),
                        exposure_pct=pos.get("exposure_pct", 0),
                        side=pos.get("side", "neutral"),
                        unrealized_pnl=pos.get("pnl", 0),
                        liquidation_distance=pos.get("liq_dist", 1.0)
                    )
                    exposures.append(sym)

            # 检查告警
            alerts = self._check_alerts(metrics, exposures)

            # 风险等级
            risk_level = self._get_risk_level(metrics)

            # 状态
            status = "critical" if risk_level == "critical" else \
                     "warning" if risk_level in ["high", "medium"] else "normal"

            # 更新趋势
            trends = self._update_trends(metrics)

            self._state = DashboardState(
                status=status,
                risk_level=risk_level,
                last_update=time.time(),
                uptime_seconds=time.time() - self._start_time,
                metrics=metrics,
                exposures=exposures,
                alerts=alerts,
                trends=trends
            )

            # 保存历史
            self._history.append(metrics)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        return self._state

    def _calculate_risk_score(
        self,
        exposure: float,
        leverage: float,
        drawdown: float,
        position_count: int
    ) -> float:
        """计算风险评分 (0-100)"""
        score = 0.0

        # 暴露评分 (0-30)
        exposure_ratio = exposure / self._thresholds["max_exposure"]
        score += min(30, exposure_ratio * 30)

        # 杠杆评分 (0-30)
        leverage_ratio = leverage / self._thresholds["max_leverage"]
        score += min(30, leverage_ratio * 30)

        # 回撤评分 (0-20)
        drawdown_ratio = drawdown / self._thresholds["max_drawdown"]
        score += min(20, drawdown_ratio * 20)

        # 持仓评分 (0-10)
        position_ratio = position_count / self._thresholds["max_position_count"]
        score += min(10, position_ratio * 10)

        return min(100, score)

    def _get_risk_level(self, metrics: RiskMetrics) -> str:
        """获取风险等级"""
        if metrics.risk_score >= 80:
            return "critical"
        elif metrics.risk_score >= 60:
            return "high"
        elif metrics.risk_score >= 40:
            return "medium"
        else:
            return "low"

    def _check_alerts(
        self,
        metrics: RiskMetrics,
        exposures: List[SymbolExposure]
    ) -> List[RiskAlert]:
        """检查告警"""
        alerts = []
        now = time.time()

        # 高暴露告警
        if metrics.total_exposure > self._thresholds["max_exposure"] * 0.8:
            alerts.append(RiskAlert(
                alert_id=f"alert_{now}",
                level="high",
                message=f"高暴露: {metrics.total_exposure:.2f}",
                timestamp=now
            ))

        # 高杠杆告警
        if metrics.leverage > self._thresholds["max_leverage"]:
            alerts.append(RiskAlert(
                alert_id=f"alert_{now}",
                level="critical",
                message=f"高杠杆: {metrics.leverage:.2f}x",
                timestamp=now
            ))

        # 大回撤告警
        if metrics.max_drawdown > self._thresholds["max_drawdown"]:
            alerts.append(RiskAlert(
                alert_id=f"alert_{now}",
                level="critical",
                message=f"大回撤: {metrics.max_drawdown*100:.1f}%",
                timestamp=now
            ))

        # 接近爆仓告警
        for exp in exposures:
            if exp.liquidation_distance < self._thresholds["min_liquidation_distance"]:
                alerts.append(RiskAlert(
                    alert_id=f"alert_{now}",
                    level="critical",
                    message=f"{exp.symbol} 接近爆仓",
                    symbol=exp.symbol,
                    timestamp=now
                ))

        return alerts

    def _update_trends(self, metrics: RiskMetrics) -> Dict[str, float]:
        """更新趋势分析"""
        if len(self._history) < 2:
            return {}

        prev = self._history[-2]

        return {
            "exposure_change": metrics.total_exposure - prev.total_exposure,
            "leverage_change": metrics.leverage - prev.leverage,
            "pnl_change": metrics.daily_pnl - prev.daily_pnl,
            "drawdown_change": metrics.max_drawdown - prev.max_drawdown
        }

    def get_state(self) -> DashboardState:
        """获取当前状态"""
        with self._lock:
            return self._state

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        state = self.get_state()

        return {
            "status": state.status,
            "risk_level": state.risk_level,
            "risk_score": state.metrics.risk_score,
            "exposure": state.metrics.total_exposure,
            "leverage": state.metrics.leverage,
            "daily_pnl": state.metrics.daily_pnl,
            "positions": state.metrics.position_count,
            "alerts_count": len(state.alerts),
            "uptime": int(state.uptime_seconds),
            "last_update": state.last_update
        }

    def get_risk_gauge(self) -> Dict[str, float]:
        """获取风险仪表数据"""
        state = self.get_state()
        m = state.metrics

        return {
            "value": m.risk_score,
            "max": 100,
            "zones": [
                {"max": 40, "color": "green", "label": "LOW"},
                {"max": 60, "color": "yellow", "label": "MEDIUM"},
                {"max": 80, "color": "orange", "label": "HIGH"},
                {"max": 100, "color": "red", "label": "CRITICAL"}
            ]
        }


def create_dashboard(config: Optional[Dict[str, Any]] = None) -> RealTimeRiskDashboard:
    """创建仪表板"""
    return RealTimeRiskDashboard(config)