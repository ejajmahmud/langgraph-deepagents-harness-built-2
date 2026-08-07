"""
V104.0 - Yield Farming, Staking & Governance
==========================================

数字货币交易系统 V104.0 - 收益农场/质押/治理

版本: 5.0.0
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import random
import math

# === 枚举类型 ===

class FarmProtocol(Enum):
    UNISWAP_V3 = "uniswap_v3"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    AAVE = "aave"
    COMPOUND = "compound"


class FarmStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLAIMED = "claimed"


class StakeStatus(Enum):
    UNSTAKED = "unstaked"
    STAKED = "staked"
    UNSTAKING = "unstaking"


class GovernanceStatus(Enum):
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VoteType(Enum):
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


# === 数据结构 ===

@dataclass
class FarmPosition:
    position_id: str
    protocol: FarmProtocol
    token_a: str
    token_b: str
    amount_a: float
    amount_b: float
    lp_tokens: float
    reward_pending: float
    apy: float
    status: FarmStatus


@dataclass
class StakePosition:
    stake_id: str
    token: str
    amount: float
    rewards: float
    start_time: datetime
    lock_period: int
    status: StakeStatus


@dataclass
class Proposal:
    proposal_id: str
    title: str
    description: str
    proposer: str
    votes_for: int
    votes_against: int
    status: GovernanceStatus
    created_at: datetime


@dataclass
class Vote:
    vote_id: str
    voter: str
    proposal_id: str
    vote_type: VoteType
    weight: float


# === Yield Farming Engine ===

class YieldFarmingV104:
    def __init__(self):
        self._positions: Dict[str, FarmPosition] = {}

    def deposit(self, protocol: FarmProtocol, token_a: str, token_b: str,
               amount_a: float, amount_b: float) -> str:
        pid = f"farm_{uuid.uuid4().hex[:8]}"
        apy = random.uniform(5, 50)  # 5-50% APY
        self._positions[pid] = FarmPosition(
            position_id=pid, protocol=protocol, token_a=token_a, token_b=token_b,
            amount_a=amount_a, amount_b=amount_b,
            lp_tokens=amount_a * amount_b,
            reward_pending=0, apy=apy, status=FarmStatus.ACTIVE
        )
        return pid

    def claim(self, pid: str) -> float:
        if pid not in self._positions:
            return 0.0
        pos = self._positions[pid]
        pos.reward_pending = pos.lp_tokens * pos.apy / 100
        pos.status = FarmStatus.CLAIMED
        return pos.reward_pending

    def get_apy(self, pid: str) -> float:
        if pid not in self._positions:
            return 0.0
        return self._positions[pid].apy

    def get_positions(self) -> List[FarmPosition]:
        return list(self._positions.values())


# === Staking Engine ===

class StakingV104:
    def __init__(self):
        self._positions: Dict[str, StakePosition] = {}

    def stake(self, token: str, amount: float, days: int) -> str:
        sid = f"stake_{uuid.uuid4().hex[:8]}"
        rewards = amount * 0.1 * days / 365  # 10% APY
        self._positions[sid] = StakePosition(
            stake_id=sid, token=token, amount=amount, rewards=rewards,
            start_time=datetime.now(), lock_period=days, status=StakeStatus.STAKED
        )
        return sid

    def unstake(self, sid: str) -> bool:
        if sid not in self._positions:
            return False
        self._positions[sid].status = StakeStatus.UNSTAKING
        return True

    def get_rewards(self, sid: str) -> float:
        if sid not in self._positions:
            return 0.0
        return self._positions[sid].rewards

    def get_total_staked(self) -> float:
        return sum(p.amount for p in self._positions.values() if p.status == StakeStatus.STAKED)


# === Governance Engine ===

class GovernanceV104:
    def __init__(self):
        self._proposals: Dict[str, Proposal] = {}
        self._votes: Dict[str, List[Vote]] = {}

    def create_proposal(self, title: str, desc: str, proposer: str) -> str:
        pid = f"prop_{uuid.uuid4().hex[:8]}"
        self._proposals[pid] = Proposal(
            proposal_id=pid, title=title, description=desc, proposer=proposer,
            votes_for=0, votes_against=0, status=GovernanceStatus.ACTIVE,
            created_at=datetime.now()
        )
        self._votes[pid] = []
        return pid

    def vote(self, pid: str, voter: str, vote_type: VoteType, weight: float) -> bool:
        if pid not in self._proposals:
            return False
        vote = Vote(vote_id=f"vote_{uuid.uuid4().hex[:8]}", voter=voter,
                   proposal_id=pid, vote_type=vote_type, weight=weight)
        self._votes[pid].append(vote)

        prop = self._proposals[pid]
        if vote_type == VoteType.FOR:
            prop.votes_for += weight
        else:
            prop.votes_against += weight

        # 自动通过或拒绝
        if prop.votes_for > 100:
            prop.status = GovernanceStatus.PASSED
        elif prop.votes_against > 100:
            prop.status = GovernanceStatus.REJECTED

        return True

    def get_proposal(self, pid: str) -> Optional[Proposal]:
        return self._proposals.get(pid)

    def get_active_proposals(self) -> List[Proposal]:
        return [p for p in self._proposals.values() if p.status == GovernanceStatus.ACTIVE]


# === 全局函数 ===

_farming: Optional[YieldFarmingV104] = None
_staking: Optional[StakingV104] = None
_governance: Optional[GovernanceV104] = None


def get_farming() -> YieldFarmingV104:
    global _farming
    if _farming is None:
        _farming = YieldFarmingV104()
    return _farming


def get_staking() -> StakingV104:
    global _staking
    if _staking is None:
        _staking = StakingV104()
    return _staking


def get_governance() -> GovernanceV104:
    global _governance
    if _governance is None:
        _governance = GovernanceV104()
    return _governance


def initialize_farming() -> YieldFarmingV104:
    global _farming
    _farming = YieldFarmingV104()
    return _farming


def initialize_staking() -> StakingV104:
    global _staking
    _staking = StakingV104()
    return _staking


def initialize_governance() -> GovernanceV104:
    global _governance
    _governance = GovernanceV104()
    return _governance


__version__ = "5.0.0"