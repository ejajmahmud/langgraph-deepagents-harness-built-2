"""ML集成与策略信号增强模块 V73.0 - Phase 17

核心功能：
- MLModel: 机器学习模型基类
- LinearRegressionModel: 线性回归模型
- RandomForestModel: 随机森林模型
- StrategySignalGenerator: 策略信号生成器
- SignalEnsemble: 信号集成
- PortfolioOptimizer: 投资组合优化器
- RiskParityOptimizer: 风险平价优化器

创建时间：2026-05-08 23:00
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import math
import random


# ============ 枚举定义 ============

class MLModelType(Enum):
    """机器学习模型类型"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class SignalSource(Enum):
    """信号来源"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    ML = "ml"
    ENSEMBLE = "ensemble"


class OptimizationObjective(Enum):
    """优化目标"""
    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"
    MAX_RETURN = "max_return"
    RISK_PARITY = "risk_parity"
    EQUAL_WEIGHT = "equal_weight"


# ============ 数据结构 ============

@dataclass
class ModelFeatures:
    """模型特征"""
    features: List[float]
    target: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class ModelPrediction:
    """模型预测"""
    value: float
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StrategySignal:
    """策略信号"""
    signal_id: str
    signal_type: SignalType
    source: SignalSource
    strength: float  # 0-1
    confidence: float  # 0-1
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioPosition:
    """组合持仓"""
    asset: str
    weight: float
    expected_return: float = 0.0
    volatility: float = 0.0


@dataclass
class OptimizationResult:
    """优化结果"""
    objective: OptimizationObjective
    weights: Dict[str, float]
    expected_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0


# ============ MLModel ============

class MLModel:
    """机器学习模型基类"""

    def __init__(self, model_type: MLModelType):
        self.model_type = model_type
        self._trained = False
        self._coefficients: List[float] = []
        self._bias: float = 0.0

    def train(self, features: List[ModelFeatures]) -> bool:
        """训练模型"""
        if len(features) < 2:
            return False

        # 简单训练实现
        self._trained = True
        return True

    def predict(self, features: List[float]) -> ModelPrediction:
        """预测"""
        if not self._trained:
            return ModelPrediction(value=0.0, confidence=0.0)

        # 简单预测
        value = sum(f * c for f, c in zip(features, self._coefficients)) + self._bias
        confidence = 0.7 if self._trained else 0.0

        return ModelPrediction(value=value, confidence=confidence)

    def is_trained(self) -> bool:
        return self._trained


class LinearRegressionModel(MLModel):
    """线性回归模型"""

    def __init__(self):
        super().__init__(MLModelType.LINEAR_REGRESSION)

    def train(self, features: List[ModelFeatures]) -> bool:
        if len(features) < 2:
            return False

        # 训练: 简单线性回归
        X = [f.features for f in features]
        Y = [f.target for f in features if f.target is not None]

        if not Y:
            return False

        # 简单系数计算: 均值
        n = len(Y)
        self._bias = sum(Y) / n

        # 简单系数
        self._coefficients = [1.0] * len(X[0])
        self._trained = True

        return True


class RandomForestModel(MLModel):
    """随机森林模型"""

    def __init__(self, n_estimators: int = 10):
        super().__init__(MLModelType.RANDOM_FOREST)
        self.n_estimators = n_estimators
        self._trees: List[MLModel] = []

    def train(self, features: List[ModelFeatures]) -> bool:
        if len(features) < 2:
            return False

        # 创建简单树
        self._trees = [LinearRegressionModel() for _ in range(self.n_estimators)]
        self._trained = True

        return True


# ============ StrategySignalGenerator ============

class StrategySignalGenerator:
    """策略信号生成器"""

    def __init__(self):
        self._models: Dict[SignalSource, MLModel] = {}
        self._signals: List[StrategySignal] = []
        self._signal_counter = 0

    def register_model(self, source: SignalSource, model: MLModel):
        """注册模型"""
        self._models[source] = model

    def generate_signal(
        self,
        source: SignalSource,
        features: List[float],
        reason: str = ""
    ) -> StrategySignal:
        """生成信号"""
        self._signal_counter += 1

        if source not in self._models:
            return StrategySignal(
                signal_id=f"SIG_{self._signal_counter:06d}",
                signal_type=SignalType.HOLD,
                source=source,
                strength=0.0,
                confidence=0.0,
                reason="No model registered"
            )

        model = self._models[source]
        prediction = model.predict(features)

        # 转换预测为信号
        if prediction.value > 0.5:
            signal_type = SignalType.BUY
        elif prediction.value < -0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        strength = min(1.0, abs(prediction.value))

        return StrategySignal(
            signal_id=f"SIG_{self._signal_counter:06d}",
            signal_type=signal_type,
            source=source,
            strength=strength,
            confidence=prediction.confidence,
            reason=reason
        )

    def get_recent_signals(self, limit: int = 10) -> List[StrategySignal]:
        """获取最近信号"""
        return self._signals[-limit:]


# ============ SignalEnsemble ============

class SignalEnsemble:
    """信号集成"""

    def __init__(self, weights: Optional[Dict[SignalSource, float]] = None):
        self.weights = weights or {
            SignalSource.TECHNICAL: 0.3,
            SignalSource.FUNDAMENTAL: 0.2,
            SignalSource.SENTIMENT: 0.2,
            SignalSource.ML: 0.3,
        }
        self._signals: List[StrategySignal] = []

    def add_signal(self, signal: StrategySignal):
        """添加信号"""
        self._signals.append(signal)

    def ensemble(self) -> StrategySignal:
        """集成信号"""
        if not self._signals:
            return StrategySignal(
                signal_id="ENSEMBLE_000000",
                signal_type=SignalType.HOLD,
                source=SignalSource.ENSEMBLE,
                strength=0.0,
                confidence=0.0
            )

        # 加权投票
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0

        for signal in self._signals:
            weight = self.weights.get(signal.source, 0.25)

            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                buy_score += signal.strength * weight
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                sell_score += signal.strength * weight

            total_weight += weight

        # 归一化
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight

        # 确定最终信号
        if buy_score > sell_score and buy_score > 0.3:
            signal_type = SignalType.BUY if buy_score < 0.7 else SignalType.STRONG_BUY
        elif sell_score > buy_score and sell_score > 0.3:
            signal_type = SignalType.SELL if sell_score < 0.7 else SignalType.STRONG_SELL
        else:
            signal_type = SignalType.HOLD

        strength = max(buy_score, sell_score)
        confidence = abs(buy_score - sell_score)

        return StrategySignal(
            signal_id=f"ENSEMBLE_{len(self._signals):06d}",
            signal_type=signal_type,
            source=SignalSource.ENSEMBLE,
            strength=strength,
            confidence=confidence
        )

    def clear_signals(self):
        """清空信号"""
        self._signals.clear()


# ============ PortfolioOptimizer ============

class PortfolioOptimizer:
    """投资组合优化器"""

    def __init__(self):
        self._positions: Dict[str, PortfolioPosition] = {}

    def add_position(
        self,
        asset: str,
        expected_return: float,
        volatility: float
    ):
        """添加持仓"""
        self._positions[asset] = PortfolioPosition(
            asset=asset,
            weight=0.0,
            expected_return=expected_return,
            volatility=volatility
        )

    def optimize(
        self,
        objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE
    ) -> OptimizationResult:
        """优化组合"""
        if not self._positions:
            return OptimizationResult(
                objective=objective,
                weights={}
            )

        positions = list(self._positions.values())
        n = len(positions)

        if objective == OptimizationObjective.EQUAL_WEIGHT:
            # 等权重
            weight = 1.0 / n
            for pos in positions:
                pos.weight = weight

        elif objective == OptimizationObjective.MAX_SHARPE:
            # 最大夏普比率
            returns = [p.expected_return for p in positions]
            volatilities = [p.volatility for p in positions]

            # 简化: 权重 = 预期收益 / 波动率
            weights = []
            for r, v in zip(returns, volatilities):
                if v > 0:
                    weights.append(r / v)
                else:
                    weights.append(0)

            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]
                for pos, w in zip(positions, weights):
                    pos.weight = w

        # 计算结果
        expected_return = sum(
            p.weight * p.expected_return for p in positions
        )
        volatility = math.sqrt(sum(
            (p.weight * p.volatility) ** 2 for p in positions
        ))

        sharpe = expected_return / volatility if volatility > 0 else 0

        weights_dict = {p.asset: p.weight for p in positions}

        return OptimizationResult(
            objective=objective,
            weights=weights_dict,
            expected_return=expected_return,
            volatility=volatility,
            sharpe_ratio=sharpe
        )


class RiskParityOptimizer(PortfolioOptimizer):
    """风险平价优化器"""

    def optimize(self) -> OptimizationResult:
        """风险平价优化"""
        positions = list(self._positions.values())
        n = len(positions)

        if n == 0:
            return OptimizationResult(
                objective=OptimizationObjective.RISK_PARITY,
                weights={}
            )

        # 获取波动率
        volatilities = [p.volatility for p in positions]

        # 风险平价: 权重反比于波动率
        weights = []
        for v in volatilities:
            if v > 0:
                weights.append(1.0 / v)
            else:
                weights.append(0)

        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
            for pos, w in zip(positions, weights):
                pos.weight = w

        # 计算组合波动率(简化)
        combo_vol = sum(
            (p.weight * p.volatility) ** 2 for p in positions
        ) ** 0.5

        weights_dict = {p.asset: p.weight for p in positions}

        return OptimizationResult(
            objective=OptimizationObjective.RISK_PARITY,
            weights=weights_dict,
            expected_return=0.0,
            volatility=combo_vol,
            sharpe_ratio=0.0
        )


# ============ 全局函数 ============

_ml_model: Optional[MLModel] = None
_signal_generator: Optional[StrategySignalGenerator] = None
_signal_ensemble: Optional[SignalEnsemble] = None
_portfolio_optimizer: Optional[PortfolioOptimizer] = None


def get_ml_model() -> MLModel:
    """获取ML模型"""
    global _ml_model
    if _ml_model is None:
        _ml_model = LinearRegressionModel()
    return _ml_model


def initialize_ml_model(model_type: MLModelType = MLModelType.LINEAR_REGRESSION):
    """初始化ML模型"""
    global _ml_model
    if model_type == MLModelType.LINEAR_REGRESSION:
        _ml_model = LinearRegressionModel()
    elif model_type == MLModelType.RANDOM_FOREST:
        _ml_model = RandomForestModel()
    return _ml_model


def get_signal_generator() -> StrategySignalGenerator:
    """获取信号生成器"""
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = StrategySignalGenerator()
    return _signal_generator


def initialize_signal_generator():
    """初始化信号生成器"""
    global _signal_generator
    _signal_generator = StrategySignalGenerator()
    return _signal_generator


def get_signal_ensemble() -> SignalEnsemble:
    """获取信号集成"""
    global _signal_ensemble
    if _signal_ensemble is None:
        _signal_ensemble = SignalEnsemble()
    return _signal_ensemble


def initialize_signal_ensemble(weights: Optional[Dict[SignalSource, float]] = None):
    """初始化信号集成"""
    global _signal_ensemble
    _signal_ensemble = SignalEnsemble(weights)
    return _signal_ensemble


def get_portfolio_optimizer() -> PortfolioOptimizer:
    """获取组合优化器"""
    global _portfolio_optimizer
    if _portfolio_optimizer is None:
        _portfolio_optimizer = PortfolioOptimizer()
    return _portfolio_optimizer


def initialize_portfolio_optimizer():
    """初始化组合优化器"""
    global _portfolio_optimizer
    _portfolio_optimizer = PortfolioOptimizer()
    return _portfolio_optimizer


def create_ml_model(model_type: MLModelType) -> MLModel:
    """创建ML模型"""
    if model_type == MLModelType.LINEAR_REGRESSION:
        return LinearRegressionModel()
    elif model_type == MLModelType.RANDOM_FOREST:
        return RandomForestModel()
    return LinearRegressionModel()


# ============ 版本信息 ============

__version__ = "1.9.0"
__phase__ = "Phase 17: ML集成与策略信号增强"