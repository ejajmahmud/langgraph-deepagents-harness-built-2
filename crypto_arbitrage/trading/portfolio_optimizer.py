"""Portfolio Optimizer - V28.0 多策略组合优化器

根据风险收益目标，优化多个策略的资金分配。
支持均值-方差优化、风险平价、最小方差等组合优化方法。

核心功能：
1. 均值-方差优化 - Modern Portfolio Theory
2. 风险平价优化 - Risk Parity
3. 最小方差组合 - Minimum Variance
4. 最大夏普组合 - Maximum Sharpe
5. 等权重分配 - Equal Weight
6. 凯利公式优化 - Kelly Criterion

创建时间：2026-05-07 14:20
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationMethod(Enum):
    """组合优化方法"""
    MEAN_VARIANCE = "mean_variance"  # 均值-方差
    RISK_PARITY = "risk_parity"  # 风险平价
    MIN_VARIANCE = "min_variance"  # 最小方差
    MAX_SHARPE = "max_sharpe"  # 最大夏普
    EQUAL_WEIGHT = "equal_weight"  # 等权重
    KELLY = "kelly"  # 凯利公式


@dataclass
class StrategyPerformance:
    """策略绩效数据"""
    strategy_id: str
    name: str
    return_mean: float = 0.0  # 平均收益率
    return_std: float = 0.0  # 收益率标准差
    sharpe_ratio: float = 0.0  # 夏普比率
    max_drawdown: float = 0.0  # 最大回撤
    win_rate: float = 0.0  # 胜率
    avg_profit: float = 0.0  # 平均盈利
    avg_loss: float = 0.0  # 平均亏损
    trade_count: int = 0  # 交易次数
    correlation: float = 0.0  # 与其他策略相关性


@dataclass
class PortfolioAllocation:
    """组合分配结果"""
    strategy_id: str
    name: str
    weight: float = 0.0  # 权重 0-1
    capital: float = 0.0  # 分配资金
    expected_return: float = 0.0  # 预期收益
    expected_risk: float = 0.0  # 预期风险
    contribution_risk: float = 0.0  # 风险贡献


@dataclass
class PortfolioResult:
    """组合优化结果"""
    method: str
    allocations: List[PortfolioAllocation] = field(default_factory=list)
    expected_return: float = 0.0  # 组合预期收益
    expected_risk: float = 0.0  # 组合预期风险
    sharpe_ratio: float = 0.0  # 组合夏普比率
    diversification_benefit: float = 0.0  # 分散化收益
    timestamp: float = 0.0


class PortfolioOptimizer:
    """多策略组合优化器 V28.0

    实现多种组合优化方法，支持多策略资金分配。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化组合优化器

        Args:
            config: 配置字典，包含:
                - risk_aversion: 风险厌恶系数 (默认 1.0)
                - target_return: 目标收益率 (默认 0.10)
                - max_weight: 单策略最大权重 (默认 0.5)
                - min_weight: 单策略最小权重 (默认 0.05)
        """
        self.config = config or {}
        self.risk_aversion = self.config.get("risk_aversion", 1.0)
        self.target_return = self.config.get("target_return", 0.10)
        self.max_weight = self.config.get("max_weight", 0.5)
        self.min_weight = self.config.get("min_weight", 0.05)

    def optimize(
        self,
        strategies: List[StrategyPerformance],
        method: OptimizationMethod = OptimizationMethod.MAX_SHARPE,
        total_capital: float = 10000.0
    ) -> PortfolioResult:
        """优化策略组合

        Args:
            strategies: 策略绩效列表
            method: 优化方法
            total_capital: ��资金

        Returns:
            PortfolioResult: 优化结果
        """
        if not strategies:
            logger.warning("策略列表为空")
            return PortfolioResult(method=method.value)

        n = len(strategies)

        # 构建协方差矩阵
        returns = np.array([s.return_mean for s in strategies])
        stds = np.array([s.return_std for s in strategies])

        # 使用相关性构建协方差矩阵
        cov_matrix = self._build_covariance_matrix(stds, strategies)

        # 根据方法计算权重
        if method == OptimizationMethod.EQUAL_WEIGHT:
            weights = self._equal_weight(n)
        elif method == OptimizationMethod.MAX_SHARPE:
            weights = self._max_sharpe(returns, stds, cov_matrix)
        elif method == OptimizationMethod.MIN_VARIANCE:
            weights = self._min_variance(cov_matrix, n)
        elif method == OptimizationMethod.RISK_PARITY:
            weights = self._risk_parity(cov_matrix, stds, n)
        elif method == OptimizationMethod.KELLY:
            weights = self._kelly_criterion(returns, stds, n)
        else:
            weights = self._mean_variance(returns, cov_matrix)

        # 构建分配结果
        allocations = []
        for i, s in enumerate(strategies):
            capital = total_capital * weights[i]
            contrib_risk = weights[i] * cov_matrix[i].dot(weights) if n > 0 else weights[i] * stds[i]**2

            alloc = PortfolioAllocation(
                strategy_id=s.strategy_id,
                name=s.name,
                weight=weights[i],
                capital=capital,
                expected_return=s.return_mean * weights[i],
                expected_risk=weights[i] * s.return_std,
                contribution_risk=contrib_risk
            )
            allocations.append(alloc)

        # 计算组合指标
        port_return = sum(a.expected_return for a in allocations)
        port_risk = np.sqrt(weights @ cov_matrix @ weights) if n > 0 else 0.0
        sharpe = port_return / port_risk if port_risk > 0 else 0.0

        # 分散化收益 = 加权平均风险 - 组合风险
        avg_risk = sum(s.return_std for s in strategies) / n
        div_benefit = avg_risk - port_risk if n > 0 else 0.0

        return PortfolioResult(
            method=method.value,
            allocations=allocations,
            expected_return=port_return,
            expected_risk=port_risk,
            sharpe_ratio=sharpe,
            diversification_benefit=div_benefit,
            timestamp=__import__("time").time()
        )

    def _build_covariance_matrix(
        self,
        stds: np.ndarray,
        strategies: List[StrategyPerformance]
    ) -> np.ndarray:
        """构建协方差矩阵"""
        n = len(stds)
        if n == 0:
            return np.array([])

        cov = np.eye(n)
        for i in range(n):
            for j in range(n):
                if i != j:
                    # 使用策略间的相关性
                    corr = strategies[i].correlation if i < len(strategies) else 0.5
                    cov[i, j] = corr * stds[i] * stds[j]
                else:
                    cov[i, j] = stds[i] ** 2

        return cov

    def _equal_weight(self, n: int) -> np.ndarray:
        """等权重分配"""
        return np.ones(n) / n

    def _max_sharpe(
        self,
        returns: np.ndarray,
        stds: np.ndarray,
        cov: np.ndarray
    ) -> np.ndarray:
        """最大夏普比率优化"""
        n = len(returns)
        if n == 0 or cov.size == 0:
            return self._equal_weight(n)

        try:
            # 无风险收益为0
            inv_cov = np.linalg.inv(cov + np.eye(n) * 1e-6)
            weights = inv_cov @ returns
            weights = np.maximum(weights, 0)  # 不允许做空
            total = weights.sum()
            if total > 0:
                weights = weights / total
            else:
                weights = self._equal_weight(n)
        except Exception as e:
            logger.warning(f"最大夏普优化失败: {e}")
            weights = self._equal_weight(n)

        # 限制权重范围
        weights = np.clip(weights, self.min_weight, self.max_weight)
        weights = weights / weights.sum()

        return weights

    def _min_variance(self, cov: np.ndarray, n: int) -> np.ndarray:
        """最小方差组合"""
        if n == 0 or cov.size == 0:
            return self._equal_weight(n)

        try:
            ones = np.ones(n)
            inv_cov = np.linalg.inv(cov + np.eye(n) * 1e-6)
            weights = inv_cov @ ones
            weights = weights / weights.sum()
        except Exception as e:
            logger.warning(f"最小方差优化失败: {e}")
            weights = self._equal_weight(n)

        weights = np.clip(weights, self.min_weight, self.max_weight)
        weights = weights / weights.sum()

        return weights

    def _risk_parity(
        self,
        cov: np.ndarray,
        stds: np.ndarray,
        n: int
    ) -> np.ndarray:
        """风险平价组合 - 每个策略贡献相同风险"""
        if n == 0 or cov.size == 0:
            return self._equal_weight(n)

        try:
            # 迭代求解风险平价
            weights = np.ones(n) / n
            for _ in range(100):
                port_vol = np.sqrt(weights @ cov @ weights)
                marginal_risk = cov @ weights
                risk_contrib = weights * marginal_risk / (port_vol + 1e-8)
                target = np.ones(n) / n
                weights = weights * (target / (risk_contrib + 1e-8))
                weights = np.clip(weights, self.min_weight, self.max_weight)
                weights = weights / weights.sum()
        except Exception as e:
            logger.warning(f"风险平价优化失败: {e}")
            weights = self._equal_weight(n)

        return weights

    def _kelly_criterion(
        self,
        returns: np.ndarray,
        stds: np.ndarray,
        n: int
    ) -> np.ndarray:
        """凯利公式优化"""
        if n == 0:
            return np.array([])

        # 凯利比例 = (预期收益 - 无风险收益) / 预期方差
        kelly = np.maximum(returns - 0.02, 0) / (stds ** 2 + 1e-8)

        # 归一化
        if kelly.sum() > 0:
            kelly = kelly / kelly.sum()
        else:
            kelly = self._equal_weight(n)

        # 限制到最大权重
        kelly = np.clip(kelly, 0, self.max_weight)
        kelly = kelly / kelly.sum()

        return kelly

    def _mean_variance(
        self,
        returns: np.ndarray,
        cov: np.ndarray
    ) -> np.ndarray:
        """均值-方差优化"""
        n = len(returns)
        if n == 0 or cov.size == 0:
            return np.array([])

        try:
            # 最大化: 预期收益 - 风险厌恶 * 方差
            inv_cov = np.linalg.inv(cov + np.eye(n) * 1e-6)
            weights = inv_cov @ (returns * self.risk_aversion)
            weights = np.maximum(weights, 0)
            total = weights.sum()
            if total > 0:
                weights = weights / total
            else:
                weights = np.ones(n) / n
        except Exception as e:
            logger.warning(f"均值-方差优化失败: {e}")
            weights = np.ones(n) / n

        weights = np.clip(weights, self.min_weight, self.max_weight)
        weights = weights / weights.sum()

        return weights


def create_optimizer(config: Optional[Dict[str, Any]] = None) -> PortfolioOptimizer:
    """创建组合优化器"""
    return PortfolioOptimizer(config)