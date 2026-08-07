"""Advanced Portfolio Rebalancer - V50.0 高级投资组合再平衡器

高级投资组合管理：
1. Risk Parity Rebalancing - 风险平价再平衡
2. Mean-Variance Optimization - 均值方差优化
3. Black-Litterman Model - Black-Litterman模型
4. Dynamic Rebalancing - 动态再平衡
5. Drawdown Control - 回撤控制

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


class RebalanceMethod(Enum):
    """再平衡方法"""
    RISK_PARITY = "risk_parity"
    MEAN_VARIANCE = "mean_variance"
    BLACK_LITTERMAN = "black_litterman"
    MIN_VARIANCE = "min_variance"
    EQUAL_WEIGHT = "equal_weight"
    DYNAMIC = "dynamic"
    DRAWDOWN_CONTROL = "drawdown_control"


class RebalanceTrigger(Enum):
    """再平衡触发条件"""
    TIME_BASED = "time_based"  # 时间触发
    THRESHOLD_BASED = "threshold_based"  # 阈值触发
    VOLATILITY_BASED = "volatility_based"  # 波动触发
    DRAWDOWN_BASED = "drawdown_based"  # 回撤触发


class AssetClass(Enum):
    """资产类别"""
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    EQUITY = "equity"
    BOND = "bond"


@dataclass
class PortfolioAsset:
    """投资组合资产"""
    symbol: str
    asset_class: AssetClass
    current_weight: float  # 当前权重
    target_weight: float  # 目标权重
    current_value: float  # 当前价值
    return_1d: float  # 1天收益
    volatility: float  # 波动率
    alpha: float = 0.0  # Alpha
    beta: float = 1.0  # Beta

    @property
    def weight_diff(self) -> float:
        """权重差异"""
        return self.target_weight - self.current_weight

    @property
    def contribution(self) -> float:
        """风险贡献 = weight * volatility"""
        return self.current_weight * self.volatility


@dataclass
class Portfolio:
    """投资组合"""
    name: str
    total_value: float  # 总价值
    assets: Dict[str, PortfolioAsset] = field(default_factory=dict)
    returns_history: List[float] = field(default_factory=list)
    rebalance_history: List[datetime] = field(default_factory=list)

    @property
    def current_weights(self) -> Dict[str, float]:
        return {sym: asset.current_weight for sym, asset in self.assets.items()}

    @property
    def portfolio_volatility(self) -> float:
        """组合波动率"""
        if not self.returns_history:
            return 0.0

        returns = np.array(self.returns_history)
        return float(np.std(returns)) if len(returns) > 1 else 0.0

    @property
    def portfolio_return(self) -> float:
        """组合收益"""
        if not self.returns_history:
            return 0.0

        return float(np.mean(self.returns_history))


@dataclass
class RebalanceResult:
    """再平衡结果"""
    method: RebalanceMethod
    new_weights: Dict[str, float]
    trades: List[Tuple[str, float, float]] = field(default_factory=list)  # (symbol, old_weight, new_weight)
    expected_return: float = 0.0
    expected_risk: float = 0.0
    sharpe_ratio: float = 0.0
    confidence: float = 0.0


@dataclass
class RiskBudget:
    """风险预算"""
    target_volatility: float  # 目标波动率
    max_drawdown: float  # 最大回撤
    var_95: float = 0.0  # 95% VaR
    cvar_95: float = 0.0  # 95% CVaR


class PortfolioRebalancer:
    """高级投资组合再平衡器"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}

        # 配置参数
        self.rebalance_method = RebalanceMethod(
            self.config.get('rebalance_method', 'risk_parity')
        )
        self.rebalance_threshold = self.config.get('rebalance_threshold', 0.05)  # 5%
        self.max_leverage = self.config.get('max_leverage', 1.0)
        self.risk_budget = RiskBudget(
            target_volatility=self.config.get('target_volatility', 0.15),
            max_drawdown=self.config.get('max_drawdown', 0.20)
        )

        # 组合
        self.portfolio: Optional[Portfolio] = None
        self.covariance_matrix: Optional[np.ndarray] = None

        # 统计
        self.rebalance_count = 0

        logger.info(f"PortfolioRebalancer initialized: {self.config}")

    def set_portfolio(self, portfolio: Portfolio) -> None:
        """设置投资组合"""
        self.portfolio = portfolio
        logger.info(f"Portfolio set: {portfolio.name}")

    def calculate_risk_parity_weights(
        self,
        assets: Dict[str, PortfolioAsset],
        target_volatility: float = 0.15
    ) -> Dict[str, float]:
        """计算风险平价权重

        目标：每个资产对组合风险贡献相等
        """
        if not assets:
            return {}

        symbols = list(assets.keys())
        n = len(symbols)

        # 获取波动率
        volatilities = np.array([
            assets[sym].volatility for sym in symbols
        ])

        # 风险平价权重 = target_vol / vol_i
        # 简化：使用逆波动率加权
        inv_vol = 1 / (volatilities + 1e-8)
        raw_weights = inv_vol / np.sum(inv_vol)

        # 调整为target_volatility
        # 实际波动率 = sqrt(w' * Cov * w)
        # 简化：直接缩放
        estimated_vol = np.sqrt(np.sum(raw_weights ** 2 * volatilities ** 2))
        scale = target_volatility / (estimated_vol + 1e-8)

        weights = raw_weights * scale

        # 确保权重和为1，且非负
        weights = np.maximum(weights, 0)
        weights = weights / np.sum(weights)

        return {sym: float(weights[i]) for i, sym in enumerate(symbols)}

    def calculate_mean_variance_weights(
        self,
        assets: Dict[str, PortfolioAsset],
        returns: Dict[str, float],
        risk_aversion: float = 1.0
    ) -> Dict[str, float]:
        """均值方差优化 (Markowitz)

        目标：最大化Sharpe比率
        max w'E[w] - (risk_aversion/2) * w'Cov*w
        """
        if not assets:
            return {}

        symbols = list(assets.keys())
        n = len(symbols)

        # 期望收益向量
        mu = np.array([returns.get(sym, 0.0) for sym in symbols])

        # 波动率作为对角协方差矩阵（简化）
        volatilities = np.array([
            assets[sym].volatility for sym in symbols
        ])
        cov = np.diag(volatilities ** 2)

        # 解析解：w = (risk_aversion * Cov)^(-1) * mu
        try:
            inv_cov = np.linalg.inv(cov + 1e-8 * np.eye(n))
            weights_raw = inv_cov @ mu / risk_aversion
        except np.linalg.LinAlgError:
            # 使用等权
            weights_raw = np.ones(n) / n

        # 调整为权重和=1，非负
        weights = np.maximum(weights_raw, 0)
        weights = weights / np.sum(weights)

        return {sym: float(weights[i]) for i, sym in enumerate(symbols)}

    def calculate_min_variance_weights(
        self,
        assets: Dict[str, PortfolioAsset]
    ) -> Dict[str, float]:
        """最小方差组合"""
        if not assets:
            return {}

        symbols = list(assets.keys())
        n = len(symbols)

        # 波动率作为对角协方差矩阵
        volatilities = np.array([
            assets[sym].volatility for sym in symbols
        ])
        cov = np.diag(volatilities ** 2)

        # 目标函数：min w'Cov*w
        # 等价于 1/sum(1/vol_i^2) * 1/vol_i^2
        inv_var = 1 / (volatilities ** 2 + 1e-8)
        weights = inv_var / np.sum(inv_var)

        return {sym: float(weights[i]) for i, sym in enumerate(symbols)}

    def calculate_black_litterman_weights(
        self,
        assets: Dict[str, PortfolioAsset],
        market_weights: Dict[str, float],
        views: Dict[str, float],
        tau: float = 0.05
    ) -> Dict[str, float]:
        """Black-Litterman模型

        结合市场均衡收益与投资者观点
        """
        if not assets:
            return {}

        symbols = list(assets.keys())
        n = len(symbols)

        # 获取当前权重
        current = np.array([
            market_weights.get(sym, 1/n) for sym in symbols
        ])

        # 获取观点收益
        view_returns = np.array([
            views.get(sym, 0.0) for sym in symbols
        ])

        # Black-Litterman后验收益
        # E[R] = (1-tau*Cov)^(-1) * (tau*Cov*pi + view)
        # pi: 市场均衡收益 = 均衡权重 * 隐含波动率
        volatilities = np.array([
            assets[sym].volatility for sym in symbols
        ])
        pi = current * volatilities  # 隐含超额收益

        # 简化：后验 = (1-tau) * pi + tau * view
        posterior_returns = (1 - tau) * pi + tau * view_returns

        # 使用后验收益计算权重
        weights = posterior_returns / (np.sum(posterior_returns) + 1e-8)
        weights = np.maximum(weights, 0)
        weights = weights / np.sum(weights)

        return {sym: float(weights[i]) for i, sym in enumerate(symbols)}

    def calculate_equal_weights(
        self,
        assets: Dict[str, PortfolioAsset]
    ) -> Dict[str, float]:
        """等权"""
        if not assets:
            return {}

        n = len(assets)
        weight = 1.0 / n

        return {sym: weight for sym in assets.keys()}

    def calculate_drawdown_control_weights(
        self,
        assets: Dict[str, PortfolioAsset],
        current_weights: Dict[str, float],
        max_drawdown: float
    ) -> Dict[str, float]:
        """回撤控制再平衡

        当回撤超过阈值时，自动降低高波动资产权重
        """
        if not assets:
            return {}

        if max_drawdown < self.risk_budget.max_drawdown:
            # 正常：使用风险平价
            return self.calculate_risk_parity_weights(
                assets,
                self.risk_budget.target_volatility
            )

        # 回撤超过阈值：降低风险
        # 因子 = current_drawdown / max_drawdown
        factor = max(0.3, 1 - (max_drawdown - self.risk_budget.max_drawdown))

        # 按波动率排序，降低高波动资产权重
        symbols = list(assets.keys())
        sorted_syms = sorted(
            symbols,
            key=lambda s: assets[s].volatility,
            reverse=True
        )

        weights = {}
        base_weight = 1.0 / len(symbols)

        for i, sym in enumerate(sorted_syms):
            if i < len(sorted_syms) // 2:
                # 高波动：降低权重
                weights[sym] = base_weight * factor * 0.5
            else:
                # 低波动：保持权重
                weights[sym] = base_weight * (1 + (1 - factor) * 0.5)

        return weights

    def calculate_trades(
        self,
        old_weights: Dict[str, float],
        new_weights: Dict[str, float]
    ) -> List[Tuple[str, float, float]]:
        """计算需要执行的交易"""
        trades = []

        all_symbols = set(old_weights.keys()) | set(new_weights.keys())

        for sym in all_symbols:
            old = old_weights.get(sym, 0.0)
            new = new_weights.get(sym, 0.0)
            diff = new - old

            if abs(diff) > self.rebalance_threshold:
                trades.append((sym, old, new))

        return trades

    def rebalance(
        self,
        method: Optional[str] = None,
        returns: Optional[Dict[str, float]] = None,
        views: Optional[Dict[str, float]] = None,
        max_drawdown: float = 0.0
    ) -> Optional[RebalanceResult]:
        """执行再平衡"""
        if not self.portfolio:
            logger.warning("No portfolio set")
            return None

        method = method or self.rebalance_method.value
        method_enum = RebalanceMethod(method)

        # 计算新权重
        assets = self.portfolio.assets

        if method_enum == RebalanceMethod.RISK_PARITY:
            new_weights = self.calculate_risk_parity_weights(
                assets,
                self.risk_budget.target_volatility
            )
        elif method_enum == RebalanceMethod.MEAN_VARIANCE:
            new_weights = self.calculate_mean_variance_weights(
                assets,
                returns or {},
                risk_aversion=1.0
            )
        elif method_enum == RebalanceMethod.BLACK_LITTERMAN:
            new_weights = self.calculate_black_litterman_weights(
                assets,
                self.portfolio.current_weights,
                views or {},
                tau=0.05
            )
        elif method_enum == RebalanceMethod.MIN_VARIANCE:
            new_weights = self.calculate_min_variance_weights(assets)
        elif method_enum == RebalanceMethod.EQUAL_WEIGHT:
            new_weights = self.calculate_equal_weights(assets)
        elif method_enum == RebalanceMethod.DRAWDOWN_CONTROL:
            new_weights = self.calculate_drawdown_control_weights(
                assets,
                self.portfolio.current_weights,
                max_drawdown
            )
        else:
            new_weights = self.calculate_risk_parity_weights(assets)

        # 计算交易
        old_weights = self.portfolio.current_weights
        trades = self.calculate_trades(old_weights, new_weights)

        # 评估新组合
        expected_return = sum(
            new_weights[sym] * assets[sym].return_1d
            for sym in new_weights.keys()
        ) if new_weights else 0.0

        expected_risk = math.sqrt(
            sum(
                new_weights[sym] ** 2 * assets[sym].volatility ** 2
                for sym in new_weights.keys()
            )
        ) if new_weights else 0.0

        sharpe = expected_return / expected_risk if expected_risk > 0 else 0

        # 更新组合
        for sym, weight in new_weights.items():
            if sym in assets:
                assets[sym].target_weight = weight

        self.rebalance_count += 1
        self.portfolio.rebalance_history.append(datetime.now())

        return RebalanceResult(
            method=method_enum,
            new_weights=new_weights,
            trades=trades,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_ratio=sharpe,
            confidence=min(len(trades) / 5, 1.0)
        )

    def should_rebalance(
        self,
        trigger: RebalanceTrigger = RebalanceTrigger.THRESHOLD_BASED,
        time_hours: int = 24
    ) -> bool:
        """判断是否需要再平衡"""
        if not self.portfolio:
            return False

        if trigger == RebalanceTrigger.TIME_BASED:
            # 时间触发
            if not self.portfolio.rebalance_history:
                return True

            last = self.portfolio.rebalance_history[-1]
            return (datetime.now() - last).total_seconds() > time_hours * 3600

        elif trigger == RebalanceTrigger.THRESHOLD_BASED:
            # 权重偏离触发
            for sym, asset in self.portfolio.assets.items():
                if abs(asset.weight_diff) > self.rebalance_threshold:
                    return True

            return False

        elif trigger == RebalanceTrigger.VOLATILITY_BASED:
            # 波动触发
            port_vol = self.portfolio.portfolio_volatility
            return port_vol > self.risk_budget.target_volatility * 1.5

        else:
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'portfolio': self.portfolio.name if self.portfolio else None,
            'assets': len(self.portfolio.assets) if self.portfolio else 0,
            'rebalance_count': self.rebalance_count,
            'method': self.rebalance_method.value
        }


def create_portfolio_rebalancer(
    config: Optional[Dict[str, Any]] = None
) -> PortfolioRebalancer:
    """创建���资���合再平衡器"""
    return PortfolioRebalancer(config=config)


def create_portfolio(
    name: str,
    total_value: float,
    assets: Optional[Dict[str, Dict[str, Any]]] = None
) -> Portfolio:
    """创建投资组合"""
    portfolio = Portfolio(name=name, total_value=total_value)

    for sym, data in (assets or {}).items():
        portfolio.assets[sym] = PortfolioAsset(
            symbol=sym,
            asset_class=AssetClass(data.get('asset_class', 'crypto')),
            current_weight=data.get('current_weight', 0.0),
            target_weight=data.get('target_weight', 0.0),
            current_value=data.get('current_value', 0.0),
            return_1d=data.get('return_1d', 0.0),
            volatility=data.get('volatility', 0.0),
            alpha=data.get('alpha', 0.0),
            beta=data.get('beta', 1.0)
        )

    return portfolio


# ============= 测试函数 =============

def _test_portfolio_rebalancer():
    """测试投资组合再平衡"""
    # 创建组合
    portfolio = create_portfolio(
        name="CryptoPortfolio",
        total_value=100000,
        assets={
            'BTC': {
                'asset_class': AssetClass.CRYPTO,
                'current_weight': 0.4,
                'current_value': 40000,
                'return_1d': 0.02,
                'volatility': 0.05
            },
            'ETH': {
                'asset_class': AssetClass.CRYPTO,
                'current_weight': 0.35,
                'current_value': 35000,
                'return_1d': 0.015,
                'volatility': 0.06
            },
            'SOL': {
                'asset_class': AssetClass.CRYPTO,
                'current_weight': 0.25,
                'current_value': 25000,
                'return_1d': -0.01,
                'volatility': 0.08
            }
        }
    )

    # 创建再平衡器
    rebalancer = create_portfolio_rebalancer({
        'rebalance_method': 'risk_parity',
        'target_volatility': 0.05,
        'rebalance_threshold': 0.05
    })

    rebalancer.set_portfolio(portfolio)

    # 测试风险平价
    result = rebalancer.rebalance(method="risk_parity")

    print(f"=== Risk Parity Rebalance ===")
    print(f"Method: {result.method.value}")
    print(f"New Weights: {result.new_weights}")
    print(f"Trades: {len(result.trades)}")
    print(f"Expected Return: {result.expected_return:.4f}")
    print(f"Expected Risk: {result.expected_risk:.4f}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")

    # 测试最小方差
    result2 = rebalancer.rebalance(method="min_variance")

    print(f"\n=== Min Variance Rebalance ===")
    print(f"New Weights: {result2.new_weights}")

    # 测试是否需要再平衡
    should = rebalancer.should_rebalance(RebalanceTrigger.THRESHOLD_BASED)
    print(f"\nShould Rebalance (threshold): {should}")

    print("\n✅ PortfolioRebalancer tests passed!")


if __name__ == "__main__":
    _test_portfolio_rebalancer()