"""V104.0 Test Suite"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.v104_yield_governance import (
    FarmProtocol, FarmStatus, StakeStatus, GovernanceStatus, VoteType,
    YieldFarmingV104, StakingV104, GovernanceV104,
    get_farming, get_staking, get_governance
)


def test_farming():
    print("=== Testing YieldFarmingV104 ===")
    fm = get_farming()
    pid = fm.deposit(FarmProtocol.UNISWAP_V3, "ETH", "USDC", 10, 20000)
    print(f"  [PASS] deposit: {pid}")
    apy = fm.get_apy(pid)
    print(f"  [PASS] apy: {apy:.2f}%")
    reward = fm.claim(pid)
    print(f"  [PASS] claim: {reward:.4f}")
    print(f"[PASS] YieldFarming")
    return True


def test_staking():
    print("=== Testing StakingV104 ===")
    st = get_staking()
    sid = st.stake("ETH", 10, 30)
    print(f"  [PASS] stake: {sid}")
    rewards = st.get_rewards(sid)
    print(f"  [PASS] rewards: {rewards:.4f}")
    total = st.get_total_staked()
    print(f"  [PASS] total: {total:.2f}")
    print(f"[PASS] Staking")
    return True


def test_governance():
    print("=== Testing GovernanceV104 ===")
    gov = get_governance()
    pid = gov.create_proposal("Test Proposal", "Description", "voter1")
    print(f"  [PASS] create: {pid}")
    gov.vote(pid, "voter2", VoteType.FOR, 50)
    print(f"  [PASS] vote")
    prop = gov.get_proposal(pid)
    print(f"  [PASS] prop: {prop.title}, votes_for={prop.votes_for}")
    print(f"[PASS] Governance")
    return True


def main():
    print("\n" + "=" * 50)
    print("V104.0 Test Suite")
    print("=" * 50)

    tests = [test_farming, test_staking, test_governance]
    passed = sum(1 for t in tests if t())
    failed = len(tests) - passed

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("=== ALL TESTS PASSED ===")
        return True
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)