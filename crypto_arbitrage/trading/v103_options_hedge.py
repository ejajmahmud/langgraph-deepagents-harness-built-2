"""
V103.0 - Options Trading, Futures Hedging & AI Strategy Optimization
==========================================================================

数字货币交易系统 V103.0 - 期权交易/期货对冲/AI策略优化
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import random
import math

# ============ 枚举类型 ============

class OptionType(Enum):
    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    AMERICAN = "american"
    EUROPEAN = "european"


class OptionStatus(Enum):
    ACTIVE = "active"
    EXERCISED = "exercised"


class HedgeType(Enum):
    DELTA = "delta"
    GAMMA = "gamma"


class OptimizationMethod(Enum):
    GENETIC = "genetic"
    RL = "rl"


class SignalTypeV103(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


# ============ 数据结构 ============

@dataclass
class OptionContract:
    contract_id: str
    underlying: str
    option_type: OptionType
    style: OptionStyle
    strike_price: float
    expiry: datetime
    quantity: float
    premium: float


@dataclass
class OptionPosition:
    contract_id: str
    position_type: str
    quantity: float
    entry_premium: float
    current_premium: float
    pnl: float = 0.0


@dataclass
class OptionGreek:
    delta: float
    gamma: float
    vega: float


@dataclass
class HedgeSignal:
    symbol: str
    action: str
    quantity: float
    reason: str
    hedge_type: HedgeType
    confidence: float


@dataclass
class FuturesContract:
    contract_id: str
    underlying: str
    position_size: float
    entry_price: float
    current_price: float


@dataclass
class Genome:
    genome_id: str
    parameters: Dict[str, float]
    fitness: float = 0.0


@dataclass
class TradeSignal:
    signal_id: str
    symbol: str
    signal_type: SignalTypeV103
    confidence: float
    target_price: float


@dataclass
class AITrainingConfig:
    method: OptimizationMethod
    population_size: int = 50


# ============ Options Trading ============

class OptionsTradingV103:
    def __init__(self, underlying: str):
        self._underlying = underlying
        self._contracts: Dict[str, OptionContract] = {}
        self._positions: Dict[str, OptionPosition] = {}
        self._price_history: List[float] = []

    def create_option(self, opt_type: OptionType, style: OptionStyle,
                  strike: float, days: int, qty: float, prem: float) -> str:
        cid = f"opt_{uuid.uuid4().hex[:8]}"
        self._contracts[cid] = OptionContract(
            contract_id=cid, underlying=self._underlying,
            option_type=opt_type, style=style,
            strike_price=strike, expiry=datetime.now() + timedelta(days=days),
            quantity=qty, premium=prem
        )
        return cid

    def buy_option(self, cid: str, qty: float) -> bool:
        if cid not in self._contracts:
            return False
        self._positions[cid] = OptionPosition(
            contract_id=cid, position_type="long", quantity=qty,
            entry_premium=self._contracts[cid].premium,
            current_premium=self._contracts[cid].premium
        )
        return True

    def calculate_price(self, spot: float, strike: float, time: float, vol: float) -> float:
        if time <= 0:
            return 0.0
        d1 = (math.log(spot / strike) + (0.05 + vol**2/2) * time) / (vol * math.sqrt(time))
        return max(spot * 0.5 - strike * math.exp(-0.05 * time) * 0.3, 0.01)

    def calculate_greeks(self, spot: float, opt_type: OptionType) -> OptionGreek:
        delta = 0.5 if opt_type == OptionType.CALL else -0.5
        return OptionGreek(delta=delta, gamma=0.02, vega=0.1)

    def update_price(self, spot: float):
        self._price_history.append(spot)
        if len(self._price_history) > 100:
            self._price_history = self._price_history[-100:]

    def get_pnl(self) -> float:
        total = 0.0
        for pos in self._positions.values():
            if pos.position_type == "long":
                pos.pnl = (pos.current_premium - pos.entry_premium) * pos.quantity
            else:
                pos.pnl = (pos.entry_premium - pos.current_premium) * pos.quantity
            total += pos.pnl
        return total


# ============ Futures Hedging ============

class FuturesHedgingEngine:
    def __init__(self):
        self._spot: Dict[str, float] = {}
        self._futures: Dict[str, FuturesContract] = {}
        self._signals: List[HedgeSignal] = []

    def add_spot(self, symbol: str, qty: float):
        self._spot[symbol] = qty

    def add_futures(self, contract: FuturesContract):
        self._futures[contract.contract_id] = contract

    def calculate_delta(self, symbol: str) -> float:
        sq = self._spot.get(symbol, 0)
        fq = sum(f.position_size for f in self._futures.values() if f.underlying == symbol)
        return sq + fq

    def generate_signal(self, symbol: str, thresh: float = 0.1) -> Optional[HedgeSignal]:
        delta = self.calculate_delta(symbol)
        if abs(delta) < thresh:
            return None
        action = "sell" if delta > 0 else "buy"
        return HedgeSignal(symbol=symbol, action=action, quantity=abs(delta),
                        reason=f"delta={delta:.4f}", hedge_type=HedgeType.DELTA,
                        confidence=min(0.9, abs(delta)))

    def execute_hedge(self, sig: HedgeSignal, price: float):
        c = FuturesContract(
            contract_id=f"fut_{uuid.uuid4().hex[:8]}", underlying=sig.symbol,
            position_size=-sig.quantity if sig.action == "sell" else sig.quantity,
            entry_price=price, current_price=price
        )
        self.add_futures(c)
        self._signals.append(sig)

    def get_summary(self) -> Dict[str, Any]:
        return {"spot": self._spot, "futures": len(self._futures),
                "signals": len(self._signals)}


# ============ AI Optimizer ============

class AIStrategyOptimizerV103:
    def __init__(self, config: AITrainingConfig):
        self._config = config
        self._population: List[Genome] = []
        self._best: Optional[Genome] = None
        self._generation = 0

    def init_population(self, ranges: Dict[str, Tuple[float, float]]):
        for i in range(self._config.population_size):
            params = {k: random.uniform(v[0], v[1]) for k, v in ranges.items()}
            self._population.append(Genome(genome_id=f"gen_{i}", parameters=params))

    def fitness(self, params: Dict[str, float], feats: List, labs: List) -> float:
        if not feats:
            return 0.0
        correct = 0
        for i, f in enumerate(feats[:10]):
            pred = 0.0
            for j in range(min(3, len(f))):
                key = f"p{j}"
                if key in params:
                    pred += f[j] * params[key]
            if (pred > 0) == (labs[i] > 0):
                correct += 1
        return correct / min(len(feats), 10)

    def train_step(self, feats: List, labs: List) -> bool:
        if not self._population or not feats:
            return False
        for g in self._population:
            g.fitness = self.fitness(g.parameters, feats, labs)
        self._population.sort(key=lambda x: x.fitness, reverse=True)
        self._best = self._population[0]
        self._generation += 1
        return True

    def generate_signal(self, feats: List) -> Optional[TradeSignal]:
        if not self._best:
            return None
        score = 0.0
        for i in range(min(3, len(feats))):
            key = f"p{i}"
            if key in self._best.parameters:
                score += feats[i] * self._best.parameters[key]

        if score > 0.1:
            st = SignalTypeV103.BUY
        elif score < -0.1:
            st = SignalTypeV103.SELL
        else:
            st = SignalTypeV103.HOLD

        return TradeSignal(signal_id=f"sig_{uuid.uuid4().hex[:8]}", symbol="BTC",
                     signal_type=st, confidence=abs(score), target_price=45000)

    def get_status(self) -> Dict[str, Any]:
        return {"gen": self._generation, "fit": self._best.fitness if self._best else 0}


# ============ 全局函数 ============

_options: Optional[OptionsTradingV103] = None
_hedging: Optional[FuturesHedgingEngine] = None
_ai: Optional[AIStrategyOptimizerV103] = None


def get_options() -> OptionsTradingV103:
    global _options
    if _options is None:
        _options = OptionsTradingV103("BTC")
    return _options


def get_hedging() -> FuturesHedgingEngine:
    global _hedging
    if _hedging is None:
        _hedging = FuturesHedgingEngine()
    return _hedging


def get_ai() -> AIStrategyOptimizerV103:
    global _ai
    if _ai is None:
        _ai = AIStrategyOptimizerV103(AITrainingConfig(method=OptimizationMethod.GENETIC))
    return _ai


__version__ = "4.9.0"