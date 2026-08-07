"""V68.0 高级风险分析与投资组合管理

V68.0 新增功能:
1. RiskAnalytics - 高级风险分析器
2. PortfolioManager - 投资组合管理器
3. VaRCalculator - VaR计算器
4. StressTester - 压力测试器
5. RiskReport - 风险报告生成器

创建时间：2026-05-08
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# 风险类型
class RiskType(Enum):
    """风险类型"""
    MARKET = "market"          # 市场风险
    CREDIT = "credit"        # 信用风险
    LIQUIDITY = "liquidity"  # 流动性风险
    OPERATIONAL = "operational"  # 操作风险
    CORRELATION = "correlation"  # 相关性风险
    VOLATILITY = "volatility"  # 波动性风险


# 风险等级
class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# VaR方法
class VaRMethod(Enum):
    """VaR计算方法"""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


@dataclass
class RiskMetric:
    """风险指标"""
    name: str
    value: float
    threshold: float
    unit: str
    breached: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class PositionRisk:
    """持仓风险"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    volatility: float
    beta: float = 1.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0


@dataclass
class RiskReport:
    """风险报告"""
    report_id: str
    timestamp: float
    portfolio_value: float
    total_risk_score: float
    risk_level: RiskLevel
    metrics: List[RiskMetric]
    var_95: float = 0.0
    var_99: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "portfolio_value": self.portfolio_value,
            "total_risk_score": self.total_risk_score,
            "risk_level": self.risk_level.value,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "recommendations": self.recommendations
        }


@dataclass
class PortfolioAllocation:
    """投资组合配置"""
    symbol: str
    weight: float
    target_weight: float
    current_value: float
    target_value: float
    drift: float = 0.0
    rebalance_needed: float = 0.0


class VaRCalculator:
    """VaR计算器

    功能：
    - 历史VaR
    - 参数VaR
    - Monte Carlo VaR
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化VaR计算器

        Args:
            config: 配置字典
                - confidence_level: 置信水平
                - holding_period: 持有期
        """
        self.config = config or {}
        self.confidence_level = self.config.get("confidence_level", 0.95)
        self.holding_period = self.config.get("holding_period", 1)

        logger.info("VaR计算器 V68.0 初始化完成")

    def calculate_historical_var(
        self,
        returns: List[float],
        portfolio_value: float
    ) -> float:
        """计算历史VaR

        Args:
            returns: 收益序列
            portfolio_value: 组合价值

        Returns:
            VaR值
        """
        if not returns or len(returns) < 10:
            return portfolio_value * 0.1

        returns_arr = np.array(returns)

        # 计算百分位数
        percentile = (1 - self.confidence_level) * 100
        var_return = np.percentile(returns_arr, percentile)

        # 转换为金额
        var_value = abs(var_return) * portfolio_value

        return var_value

    def calculate_parametric_var(
        self,
        mean_return: float,
        std_return: float,
        portfolio_value: float
    ) -> float:
        """计算参数VaR

        Args:
            mean_return: 平均收益
            std_return: 收益标准差
            portfolio_value: 组合价值

        Returns:
            VaR值
        """
        from scipy import stats  # 简化计算

        # Z分数
        if self.confidence_level == 0.95:
            z_score = 1.645
        elif self.confidence_level == 0.99:
            z_score = 2.326
        else:
            z_score = 1.645

        # VaR = z * sigma * value
        var_value = z_score * std_return * portfolio_value

        return var_value

    def calculate_monte_carl(
        self,
        returns: List[float],
        portfolio_value: float,
        simulations: int = 1000
    ) -> float:
        """计算Monte Carlo VaR

        Args:
            returns: 历史收益
            portfolio_value: 组合价值
            simulations: 模拟次数

        Returns:
            VaR值
        """
        if not returns:
            return portfolio_value * 0.1

        # 计算统计量
        mean = np.mean(returns)
        std = np.std(returns)

        # 生成随机模拟
        np.random.seed(42)
        sim_returns = np.random.normal(mean, std, simulations)

        # 计算VaR
        percentile = (1 - self.confidence_level) * 100
        var_return = np.percentile(sim_returns, percentile)

        return abs(var_return) * portfolio_value


class RiskAnalytics:
    """风险分析器

    功能：
    - 风险指标计算
    - 风险评估
    - 风险报告生成
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化风险分析器"""
        self.config = config or {}

        # VaR计算器
        self.var_calculator = VaRCalculator(config)

        # 风险阈值
        self.max_var_pct = self.config.get("max_var_pct", 0.05)  # 5%最大VaR
        self.max_drawdown_pct = self.config.get("max_drawdown_pct", 0.20)  # 20%最大回撤
        self.max_leverage = self.config.get("max_leverage", 3)

        # 历史数据
        self.returns_history: List[float] = []
        self.equity_curve: List[float] = []

        logger.info("风险分析器 V68.0 初始化完成")

    def add_return(self, return_value: float) -> None:
        """添加收益"""
        self.returns_history.append(return_value)
        self.returns_history = self.returns_history[-252:]  # 保留1年数据

    def add_equity(self, value: float) -> None:
        """添加权益值"""
        self.equity_curve.append(value)
        self.equity_curve = self.equity_curve[-252:]

    def calculate_var(
        self,
        portfolio_value: float,
        method: VaRMethod = VaRMethod.HISTORICAL
    ) -> Dict[str, float]:
        """计算VaR

        Args:
            portfolio_value: 组合价值
            method: 计算方法

        Returns:
            VaR字典
        """
        if method == VaRMethod.HISTORICAL:
            var_95 = self.var_calculator.calculate_historical_var(
                self.returns_history, portfolio_value
            )
            var_99 = self.var_calculator.calculate_historical_var(
                self.returns_history, portfolio_value
            ) * 1.3  # 简化调整
        elif method == VaRMethod.PARAMETRIC:
            mean = np.mean(self.returns_history) if self.returns_history else 0
            std = np.std(self.returns_history) if self.returns_history else 0.1
            var_95 = self.var_calculator.calculate_parametric_var(
                mean, std, portfolio_value
            )
            var_99 = self.var_calculator.calculate_parametric_var(
                mean, std * 1.5, portfolio_value
            )
        else:
            var_95 = self.var_calculator.calculate_monte_carl(
                self.returns_history, portfolio_value
            )
            var_99 = self.var_calculator.calculate_monte_carl(
                self.returns_history, portfolio_value, 5000
            )

        return {
            "var_95": var_95,
            "var_99": var_99,
            "var_95_pct": var_95 / portfolio_value if portfolio_value > 0 else 0,
            "var_99_pct": var_99 / portfolio_value if portfolio_value > 0 else 0
        }

    def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.equity_curve:
            return 0.0

        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max

        return abs(min(drawdown))

    def calculate_sharpe_ratio(
        self,
        risk_free_rate: float = 0.02
    ) -> float:
        """计算夏普比率"""
        if not self.returns_history or len(self.returns_history) < 2:
            return 0.0

        returns = np.array(self.returns_history)
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        sharpe = (mean_return - risk_free_rate) / std_return * math.sqrt(252)

        return sharpe

    def assess_risk_level(self, total_risk_score: float) -> RiskLevel:
        """评估风险等级

        Args:
            total_risk_score: 总风险评分

        Returns:
            风险等级
        """
        if total_risk_score < 0.3:
            return RiskLevel.LOW
        elif total_risk_score < 0.6:
            return RiskLevel.MEDIUM
        elif total_risk_score < 0.8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def generate_report(
        self,
        portfolio_value: float
    ) -> RiskReport:
        """生成风险报告

        Args:
            portfolio_value: 组合价值

        Returns:
            风险报告
        """
        # 计算各项指标
        var_results = self.calculate_var(portfolio_value)
        max_dd = self.calculate_max_drawdown()
        sharpe = self.calculate_sharpe_ratio()

        # 计算总风险评分
        var_pct = var_results["var_95_pct"]
        risk_score = min(var_pct * 2 + max_dd * 0.5, 1.0)

        # 评估风险等级
        risk_level = self.assess_risk_level(risk_score)

        # 生成建议
        recommendations = []
        if var_pct > self.max_var_pct:
            recommendations.append(f"VaR超过阈值 {self.max_var_pct:.1%}，考虑降低仓位")
        if max_dd > self.max_drawdown_pct:
            recommendations.append(f"回撤超过阈值 {self.max_drawdown_pct:.1%}，建议止损")
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("风险等级过高，建议重新平衡组合")

        report = RiskReport(
            report_id=f"risk_{int(time.time() * 1000)}",
            timestamp=time.time(),
            portfolio_value=portfolio_value,
            total_risk_score=risk_score,
            risk_level=risk_level,
            metrics=[],
            var_95=var_results["var_95"],
            var_99=var_results["var_99"],
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            recommendations=recommendations
        )

        return report


class StressTester:
    """压力测试器

    功能：
    - 市场压力测试
    - 情景分析
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化压力测试器"""
        self.config = config or {}

        logger.info("压力测试器 V68.0 初始化完成")

    def stress_test(
        self,
        portfolio_value: float,
        positions: List[Dict[str, Any]],
        scenario: str = "market_crash"
    ) -> Dict[str, float]:
        """执行压力测试

        Args:
            portfolio_value: 组合价值
            positions: 持仓列表
            scenario: 场景

        Returns:
            结果字典
        """
        # 定义压力场景
        scenarios = {
            "market_crash": -0.30,  # 市场崩盘 -30%
            "crypto_winter": -0.50,  # 加密冬天 -50%
            "liquidity_crisis": -0.25,  # 流动性危机 -25%
            "high_volatility": 0.0,  # 高波动
            "black_swan": -0.40  # 黑天鹅 -40%
        }

        shock = scenarios.get(scenario, -0.20)

        # 计算影响
        total_exposure = sum(p.get("value", 0) for p in positions)
        loss = total_exposure * abs(shock)

        return {
            "scenario": scenario,
            "shock": shock,
            "portfolio_value": portfolio_value,
            "projected_value": portfolio_value + loss,
            "projected_loss": loss,
            "loss_pct": abs(shock)
        }

    def run_scenarios(
        self,
        portfolio_value: float,
        positions: List[Dict[str, Any]]
    ) -> List[Dict[str, float]]:
        """运行多个场景

        Args:
            portfolio_value: 组合价值
            positions: 持仓列表

        Returns:
            场景结果列表
        """
        scenarios = ["market_crash", "crypto_winter", "liquidity_crisis", "black_swan"]

        results = []
        for scenario in scenarios:
            result = self.stress_test(portfolio_value, positions, scenario)
            results.append(result)

        return results


class PortfolioManager:
    """投资组合管理器

    功能：
    - 组合配置管理
    - 再平衡执行
    - 配置分析
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化投资组合管理器"""
        self.config = config or {}

        # 投资组合配置
        self.allocations: Dict[str, PortfolioAllocation] = {}

        # 总价值
        self.total_value: float = 0.0

        # 目标配置
        self.target_allocations: Dict[str, float] = self.config.get(
            "target_allocations",
            {}
        )

        # 触发阈值
        self.rebalance_threshold = self.config.get(
            "rebalance_threshold",
            0.05
        )

        logger.info("投资组合管理器 V68.0 初始化完成")

    def add_allocation(
        self,
        symbol: str,
        weight: float,
        value: float
    ) -> None:
        """添加配置

        Args:
            symbol: 资产符号
            weight: 权重
            value: 价值
        """
        target_weight = self.target_allocations.get(symbol, weight)
        target_value = target_weight * self.total_value if self.total_value > 0 else value
        drift = weight - target_weight
        rebalance_needed = target_value - value

        allocation = PortfolioAllocation(
            symbol=symbol,
            weight=weight,
            target_weight=target_weight,
            current_value=value,
            target_value=target_value,
            drift=drift,
            rebalance_needed=rebalance_needed
        )

        self.allocations[symbol] = allocation

    def update_total_value(self, value: float) -> None:
        """更新总价值"""
        self.total_value = value

        # 重新计算配置
        for symbol, allc in self.allocations.items():
            allc.weight = allc.current_value / value if value > 0 else 0
            allc.drift = allc.weight - allc.target_weight
            allc.rebalance_needed = allc.target_value - allc.current_value

    def needs_rebalance(self) -> bool:
        """检查是否需要再平衡"""
        for allc in self.allocations.values():
            if abs(allc.drift) > self.rebalance_threshold:
                return True
        return False

    def get_rebalance_orders(
        self,
        available_exchanges: List[str]
    ) -> List[Dict[str, Any]]:
        """获取再平衡订单"""
        if not self.needs_rebalance():
            return []

        orders = []
        for allc in self.allocations.values():
            if abs(allc.rebalance_needed) > 10:  # 最小交易量
                # 确定方向
                if allc.rebalance_needed > 0:
                    side = "BUY"
                else:
                    side = "SELL"

                orders.append({
                    "symbol": allc.symbol,
                    "side": side,
                    "quantity": abs(allc.rebalance_needed) / allc.current_value,
                    "reason": f"rebalance: {allc.drift:.2%} drift"
                })

        return orders

    def get_diversification_score(self) -> float:
        """计算分散化评分"""
        if not self.allocations:
            return 0.0

        weights = [a.weight for a in self.allocations.values()]

        # 使用HHI (Herfindahl-Hirschman Index)
        hhi = sum(w ** 2 for w in weights)

        # 转换为分散化评分 (1 - HHI)
        diversification = 1 - hhi

        return diversification


# 全局单例
_risk_analytics: Optional[RiskAnalytics] = None
_portfolio_manager: Optional[PortfolioManager] = None


def get_risk_analytics() -> Optional[RiskAnalytics]:
    """获取风险分析器"""
    return _risk_analytics


def initialize_risk_analytics(
    config: Optional[Dict[str, Any]] = None
) -> RiskAnalytics:
    """初始化风险分析器"""
    global _risk_analytics
    _risk_analytics = RiskAnalytics(config)
    return _risk_analytics


def get_portfolio_manager() -> Optional[PortfolioManager]:
    """获取投资组合管理器"""
    return _portfolio_manager


def initialize_portfolio_manager(
    config: Optional[Dict[str, Any]] = None
) -> PortfolioManager:
    """初始化投资组合管理器"""
    global _portfolio_manager
    _portfolio_manager = PortfolioManager(config)
    return _portfolio_manager


__all__ = [
    # 枚举
    'RiskType',
    'RiskLevel',
    'VaRMethod',
    # 数据类
    'RiskMetric',
    'PositionRisk',
    'RiskReport',
    'PortfolioAllocation',
    # 主类
    'VaRCalculator',
    'RiskAnalytics',
    'StressTester',
    'PortfolioManager',
    # 工厂函数
    'get_risk_analytics',
    'initialize_risk_analytics',
    'get_portfolio_manager',
    'initialize_portfolio_manager',
]