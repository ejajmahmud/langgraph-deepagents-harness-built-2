"""Enhanced Risk Monitor - V51.3 实时风控增强模块

实时风险监控功能：
1. Real-Time Risk Tracking - 实时风险追踪
2. Portfolio VaR - 投资组合VaR计算
3. Stress Testing - 压力测试
4. Anomaly Detection - 异常检测
5. Auto Risk Adjustment - 自动风险调整

作者：DeepAgents
创建时间：2026-05-08
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """警报等级"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RiskMetric(Enum):
    """风险指标"""
    VAR = "var"                  # VaR
    CVAR = "cvar"               # CVaR
    SHARPE = "sharpe"           # 夏普比率
    MAX_DRAWDOWN = "max_dd"     # 最大回撤
    VOLATILITY = "volatility"    # 波动率
    BETA = "beta"               # Beta


@dataclass
class RiskAlert:
    """风险警报"""
    level: AlertLevel
    metric: str
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioRisk:
    """投资组合风险"""
    total_value: float
    volatility: float
    var_95: float
    var_99: float
    cvar_95: float
    max_drawdown: float
    beta: float
    sharpe_ratio: float
    positions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario: str
    portfolio_value_initial: float
    portfolio_value_new: float
    loss: float
    loss_pct: float
    margin_required: float
    margin_call: bool


class EnhancedRiskMonitor:
    """增强型实时风险监控器

    核心功能：
    - 实时风险追踪
    - VaR/CVaR计算
    - 压力测试
    - 异常检测
    - 自动风险调整
    """

    # 风险阈值配置
    RISK_THRESHOLDS = {
        'var_95': 0.05,          # 5%
        'var_99': 0.10,         # 10%
        'max_drawdown': 0.20,   # 20%
        'volatility': 0.30,     # 30%
        'concentration': 0.30,   # 30%
        'leverage': 3.0,        # 3x
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化风险监控器

        Args:
            config: 配置
        """
        self.config = config or {}
        self._alerts: List[RiskAlert] = []
        self._positions: List[Dict[str, Any]] = []
        self._pnl_history: List[float] = []
        self._price_history: Dict[str, List[float]] = {}

        logger.info("增强风险监控器初始化")

    # -------------------- 核心风险计算 --------------------

    def calculate_var(
        self,
        returns: List[float],
        confidence: float = 0.95,
    ) -> float:
        """计算VaR (Value at Risk)

        Args:
            returns: 收益列表
            confidence: 置信度

        Returns:
            float: VaR值
        """
        if not returns:
            return 0.0

        # 使用历史法
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))

        return abs(sorted_returns[index]) if index < len(sorted_returns) else 0.0

    def calculate_cvar(
        self,
        returns: List[float],
        confidence: float = 0.95,
    ) -> float:
        """计算CVaR (Conditional VaR)

        Args:
            returns: 收益列表
            confidence: 置信度

        Returns:
            float: CVaR值
        """
        if not returns:
            return 0.0

        var = self.calculate_var(returns, confidence)

        # 计算VaR条件下的平均损失
        tail_losses = [r for r in returns if abs(r) > var]

        return np.mean(tail_losses) if tail_losses else 0.0

    def calculate_volatility(
        self,
        returns: List[float],
        annualize: bool = True,
    ) -> float:
        """计算波动率

        Args:
            returns: 收益列表
            annualize: 是否年化

        Returns:
            float: 波动率
        """
        if not returns:
            return 0.0

        vol = np.std(returns)

        if annualize:
            # 年化 (假设每日数据)
            vol = vol * math.sqrt(365)

        return vol

    def calculate_max_drawdown(
        self,
        values: List[float],
    ) -> float:
        """计算最大回撤

        Args:
            values: 组合价值列表

        Returns:
            float: 最大回撤
        """
        if not values:
            return 0.0

        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value

            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02,
    ) -> float:
        """计算夏普比率

        Args:
            returns: 收益列表
            risk_free_rate: 无风险利率

        Returns:
            float: 夏普比率
        """
        if not returns:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        return (mean_return - risk_free_rate / 365) / std_return

    def calculate_portfolio_risk(
        self,
        positions: Dict[str, Any],
        prices: Dict[str, float],
    ) -> PortfolioRisk:
        """计算投资组合风险

        Args:
            positions: 持仓
            prices: 价格

        Returns:
            PortfolioRisk: 组合风险
        """
        # 计算总价值
        total_value = sum(
            pos.get('quantity', 0) * prices.get(pos.get('symbol', ''), 0)
            for pos in positions
        )

        # 模拟收益
        if len(self._pnl_history) > 1:
            returns = self._pnl_history[-30:]
        else:
            returns = [0.0] * 30

        # 计算风险指标
        var_95 = self.calculate_var(returns, 0.95)
        var_99 = self.calculate_var(returns, 0.99)
        cvar_95 = self.calculate_cvar(returns, 0.95)

        volatility = self.calculate_volatility(returns)
        max_dd = 0.0  # 需要历史数据
        sharpe = self.calculate_sharpe_ratio(returns)

        return PortfolioRisk(
            total_value=total_value,
            volatility=volatility,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown=max_dd,
            beta=1.0,  # 简化
            sharpe_ratio=sharpe,
            positions=list(positions.values()),
        )

    # -------------------- 压力测试 --------------------

    def run_stress_test(
        self,
        portfolio_value: float,
        scenario: str = "market_crash",
    ) -> StressTestResult:
        """运行压力测试

        Args:
            portfolio_value: 组合价值
            scenario: 场景

        Returns:
            StressTestResult: 压力测试结果
        """
        scenarios = {
            'market_crash': -0.30,       # 30%下跌
            'flash_crash': -0.15,        # 15%闪崩
            'liquidity_crisis': -0.20,     # 流动性危机
            'volatility_spike': -0.15,    # 波动率飙升
            'correlation_break': -0.10,   # 相关性破裂
        }

        shock = scenarios.get(scenario, -0.20)

        new_value = portfolio_value * (1 + shock)
        loss = portfolio_value - new_value
        loss_pct = shock

        # 检查是否需要追加保证金
        margin_required = new_value * 0.25  # 简化
        margin_call = new_value < margin_required * 2

        return StressTestResult(
            scenario=scenario,
            portfolio_value_initial=portfolio_value,
            portfolio_value_new=new_value,
            loss=loss,
            loss_pct=loss_pct,
            margin_required=margin_required,
            margin_call=margin_call,
        )

    def run_scenario_analysis(
        self,
        portfolio_value: float,
    ) -> Dict[str, StressTestResult]:
        """运行场景分析

        Args:
            portfolio_value: 组合价值

        Returns:
            Dict: 所有场景结果
        """
        scenarios = ['market_crash', 'flash_crash', 'liquidity_crisis',
                    'volatility_spike', 'correlation_break']

        return {
            scenario: self.run_stress_test(portfolio_value, scenario)
            for scenario in scenarios
        }

    # -------------------- 异常检测 --------------------

    def detect_price_anomaly(
        self,
        symbol: str,
        current_price: float,
        window: int = 30,
    ) -> bool:
        """检测价格异常

        Args:
            symbol: 交易对
            current_price: 当前价格
            window: 窗口大小

        Returns:
            bool: 是否异常
        """
        history = self._price_history.get(symbol, [])

        if len(history) < window:
            return False

        recent = history[-window:]
        mean = np.mean(recent)
        std = np.std(recent)

        if std == 0:
            return False

        # Z-score检测
        z_score = abs(current_price - mean) / std

        return z_score > 3.0  # 3标准差外

    def detect_volume_anomaly(
        self,
        symbol: str,
        current_volume: float,
        window: int = 30,
    ) -> bool:
        """检测交易量异常

        Args:
            symbol: 交易对
            current_volume: 当前交易量
            window: 窗口大小

        Returns:
            bool: 是否异常
        """
        # 简化处理
        return current_volume > 1000000  # 简化阈值

    def detect_position_concentration(
        self,
        positions: List[Dict[str, Any]],
    ) -> bool:
        """检测仓位集中度

        Args:
            positions: 持仓列表

        Returns:
            bool: 是否集中
        """
        if not positions:
            return False

        values = [pos.get('value', 0) for pos in positions]
        total = sum(values)

        if total == 0:
            return False

        # 单一仓位超过30%
        max_concentration = max(values) / total

        return max_concentration > self.RISK_THRESHOLDS['concentration']

    # -------------------- 风控操作 --------------------

    def check_risk_limits(
        self,
        portfolio_risk: PortfolioRisk,
    ) -> List[RiskAlert]:
        """检查风险限制

        Args:
            portfolio_risk: 组合风险

        Returns:
            List[RiskAlert]: 警报列表
        """
        alerts = []

        # VaR检查
        if portfolio_risk.var_95 > self.RISK_THRESHOLDS['var_95']:
            alerts.append(RiskAlert(
                level=AlertLevel.WARNING,
                metric='var_95',
                message=f"VaR超过阈值: {portfolio_risk.var_95:.1%}",
                value=portfolio_risk.var_95,
                threshold=self.RISK_THRESHOLDS['var_95'],
            ))

        # 最大回撤检查
        if portfolio_risk.max_drawdown > self.RISK_THRESHOLDS['max_drawdown']:
            alerts.append(RiskAlert(
                level=AlertLevel.CRITICAL,
                metric='max_drawdown',
                message=f"最大回撤超过阈值: {portfolio_risk.max_drawdown:.1%}",
                value=portfolio_risk.max_drawdown,
                threshold=self.RISK_THRESHOLDS['max_drawdown'],
            ))

        # 波动率检查
        if portfolio_risk.volatility > self.RISK_THRESHOLDS['volatility']:
            alerts.append(RiskAlert(
                level=AlertLevel.WARNING,
                metric='volatility',
                message=f"波动率过高: {portfolio_risk.volatility:.1%}",
                value=portfolio_risk.volatility,
                threshold=self.RISK_THRESHOLDS['volatility'],
            ))

        # 存储警报
        self._alerts.extend(alerts)

        return alerts

    def suggest_position_adjustment(
        self,
        portfolio_risk: PortfolioRisk,
        target_risk: float = 0.05,
    ) -> Dict[str, Any]:
        """建议仓位调整

        Args:
            portfolio_risk: 组合风险
            target_risk: 目标风险

        Returns:
            Dict: 调整建议
        """
        current_var = portfolio_risk.var_95

        if current_var <= target_risk:
            return {
                'action': 'hold',
                'reason': 'Risk within limits',
                'adjustment': 0.0,
            }

        # 计算需要降低的仓位
        adjustment = (current_var - target_risk) / current_var

        return {
            'action': 'reduce_position',
            'reason': f"Reduce to meet target risk {target_risk:.1%}",
            'adjustment': adjustment,
            'target_var': target_risk,
            'current_var': current_var,
        }

    def emergency_liquidation(
        self,
        positions: List[Dict[str, Any]],
        portfolio_value: float,
    ) -> Dict[str, Any]:
        """紧急清算

        Args:
            positions: 持仓
            portfolio_value: 组合价值

        Returns:
            Dict: 清算结果
        """
        # 触发条件：回撤超过30%
        max_dd = self.calculate_max_drawdown(
            [portfolio_value] + self._pnl_history
        )

        if max_dd < 0.30:
            return {
                'triggered': False,
                'reason': 'Drawdown within limits',
            }

        return {
            'triggered': True,
            'reason': f"Emergency liquidation triggered: {max_dd:.1%} drawdown",
            'positions_to_close': positions,
            'estimated_loss': portfolio_value * max_dd,
        }

    # -------------------- 数据更新 --------------------

    def update_position(
        self,
        symbol: str,
        quantity: float,
        value: float,
        pnl: float,
    ) -> None:
        """更新持仓数据

        Args:
            symbol: 交易对
            quantity: 数量
            value: 价值
            pnl: 盈亏
        """
        # 更新持仓
        existing = None
        for pos in self._positions:
            if pos.get('symbol') == symbol:
                existing = pos
                break

        if existing:
            existing.update({
                'quantity': quantity,
                'value': value,
                'pnl': pnl,
            })
        else:
            self._positions.append({
                'symbol': symbol,
                'quantity': quantity,
                'value': value,
                'pnl': pnl,
            })

        # 更新PnL历史
        self._pnl_history.append(pnl)
        if len(self._pnl_history) > 1000:
            self._pnl_history = self._pnl_history[-1000:]

    def update_price(
        self,
        symbol: str,
        price: float,
    ) -> None:
        """更新价格数据

        Args:
            symbol: 交易对
            price: 价格
        """
        if symbol not in self._price_history:
            self._price_history[symbol] = []

        self._price_history[symbol].append(price)

        # 保持历史长度
        if len(self._price_history[symbol]) > 1000:
            self._price_history[symbol] = self._price_history[symbol][-1000:]

    # -------------------- 统计 --------------------

    def get_risk_statistics(self) -> Dict[str, Any]:
        """获取风险统计

        Returns:
            Dict: 统计信息
        """
        if not self._pnl_history:
            return {'total_updates': 0}

        return {
            'total_updates': len(self._pnl_history),
            'avg_pnl': np.mean(self._pnl_history),
            'total_pnl': sum(self._pnl_history),
            'volatility': self.calculate_volatility(self._pnl_history),
            'max_drawdown': self.calculate_max_drawdown(
                [sum(self._pnl_history[:i+1]) for i in range(len(self._pnl_history))]
            ),
            'active_alerts': len([a for a in self._alerts if a.level in [AlertLevel.WARNING, AlertLevel.CRITICAL]]),
        }

    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        limit: int = 10,
    ) -> List[RiskAlert]:
        """获取警报

        Args:
            level: 警报等级
            limit: 数量限制

        Returns:
            List[RiskAlert]: 警报列表
        """
        alerts = self._alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        return alerts[-limit:]

    def clear_alerts(self) -> None:
        """清除警报"""
        self._alerts.clear()
        logger.info("警报已清除")