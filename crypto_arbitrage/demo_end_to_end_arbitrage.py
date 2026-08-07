"""
V54.0 Phase 5 - End-to-End Arbitrage Demo (Minimal Runnable Loop)

Goal: Run a complete loop in Mock mode:
    Signal Discovery -> Memo0 Historical Retrieval -> Confidence Assessment -> Decision Generation -> Simulated Execution -> Result Recording

Design Constraints:
- No external API dependency (auto-fallback to Mock when MEM0_API_KEY=NOT_SET)
- Do not modify any existing source code (read-only import + new file only)
- Use Memo0IntegratedArbitrageSystem from memo0_arbitrage_system.py as core
- Use UnifiedStorage for knowledge persistence
- Output clear step logs and final statistics
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("e2e_demo")

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ------------------------------------------------------------------
# 1. Import core components
# ------------------------------------------------------------------
from strategies.memo0_arbitrage_system import (
    Memo0IntegratedArbitrageSystem,
    ExecutionMode,
    DecisionConfidence,
)
from storage.mem0_storage import (
    get_unified_storage,
    add_trading_knowledge,
    search_trading_knowledge,
)


# ------------------------------------------------------------------
# 2. Mock market data feed
# ------------------------------------------------------------------
class MockMarketDataFeed:
    """Mock market data source - generates synthetic arbitrage opportunities"""

    def __init__(self):
        self._opportunities = [
            {
                "id": "opp_tri_001",
                "symbol": "BTC/USDT",
                "strategy": "triangular",
                "side": "long",
                "market": "spot",
                "timeframe": "1m",
                "entry_price": 65000.0,
                "expected_profit": 120.0,
                "profit_rate": 0.0018,
                "stop_loss": 64500.0,
                "take_profit": 66500.0,
                "position_size": 5000,
                "ttl": 60,
            },
            {
                "id": "opp_cross_001",
                "symbol": "ETH/USDT",
                "strategy": "cross_exchange",
                "side": "long",
                "market": "spot",
                "timeframe": "1m",
                "entry_price": 3500.0,
                "expected_profit": 8.5,
                "profit_rate": 0.0024,
                "stop_loss": 3480.0,
                "take_profit": 3550.0,
                "position_size": 3000,
                "ttl": 45,
            },
            {
                "id": "opp_fund_001",
                "symbol": "SOL/USDT",
                "strategy": "funding_rate",
                "side": "short",
                "market": "perpetual",
                "timeframe": "1h",
                "entry_price": 145.0,
                "expected_profit": 3.2,
                "profit_rate": 0.022,
                "stop_loss": 148.0,
                "take_profit": 140.0,
                "position_size": 2000,
                "ttl": 3600,
            },
            {
                "id": "opp_grid_001",
                "symbol": "DOGE/USDT",
                "strategy": "grid",
                "side": "long",
                "market": "spot",
                "timeframe": "5m",
                "entry_price": 0.165,
                "expected_profit": 0.8,
                "profit_rate": 0.0048,
                "stop_loss": 0.160,
                "take_profit": 0.170,
                "position_size": 1000,
                "ttl": 300,
            },
        ]
        self._index = 0

    def next_opportunity(self) -> dict:
        """Get next mock arbitrage opportunity"""
        opp = self._opportunities[self._index % len(self._opportunities)]
        self._index += 1
        opp = opp.copy()
        opp["entry_price"] = opp["entry_price"] * (1 + (time.time() % 10 - 5) / 1000)
        opp["expected_profit"] = opp["expected_profit"] * (1 + (time.time() % 5 - 2) / 100)
        return opp


# ------------------------------------------------------------------
# 3. Demo main flow
# ------------------------------------------------------------------
async def run_e2e_demo():
    """Run end-to-end arbitrage demo"""

    print("=" * 60)
    print("V54.0 Phase 5 - End-to-End Arbitrage Demo")
    print("=" * 60)
    print()

    # ---- 3.1 Initialize Memo0 / UnifiedStorage ----
    logger.info("[Step 1] Initialize Memo0 storage (Mock auto-fallback)...")
    unified = get_unified_storage()
    logger.info(f"  -> Storage backend: {'Memo0 API' if unified.is_using_mem0 else 'SQLite (Mock)'}")

    # ---- 3.2 Seed historical knowledge ----
    logger.info("[Step 2] Seed historical trading knowledge...")
    seed_knowledge = [
        ("arbitrage_decision", "BTC/USDT triangular arbitrage executed successfully, profit 0.15%"),
        ("arbitrage_decision", "ETH/USDT cross-exchange arbitrage failed due to slippage, loss -0.02%"),
        ("arbitrage_decision", "SOL/USDT funding rate arbitrage executed, profit 0.08%"),
        ("risk_assessment", "High volatility detected on DOGE/USDT, grid strategy paused"),
        ("market_condition", "BTC spot-perpetual basis turned positive, triangular opportunity emerging"),
    ]
    for cat, content in seed_knowledge:
        ok = add_trading_knowledge(cat, content, {"demo_seed": True, "timestamp": datetime.now().isoformat()})
        logger.info(f"  -> add_knowledge('{cat}'): {'OK' if ok else 'FAIL'}")

    all_knowledge = unified.get_all_knowledge()
    logger.info(f"  -> Current knowledge base size: {len(all_knowledge)} entries")
    print()

    # ---- 3.3 Initialize arbitrage system ----
    logger.info("[Step 3] Initialize Memo0IntegratedArbitrageSystem...")
    system = Memo0IntegratedArbitrageSystem(
        config={
            "execution_mode": "paper",
            "min_confidence": "medium",
            "min_success_rate": 0.3,
            "max_risk_score": 0.7,
        }
    )
    logger.info("  -> System initialized, execution mode: PAPER")
    print()

    # ---- 3.4 Run 4 rounds of signal->decision->execution loop ----
    logger.info("[Step 4] Start 4 rounds of signal->decision->execution loop...")
    feed = MockMarketDataFeed()

    for round_idx in range(1, 5):
        print("-" * 50)
        logger.info(f"[Round {round_idx}/4]")

        # 3.4.1 Discover opportunity
        opportunity = feed.next_opportunity()
        logger.info(f"  Signal discovery: {opportunity['symbol']} | strategy={opportunity['strategy']} | expected_profit=${opportunity['expected_profit']:.2f}")

        # 3.4.2 Analyze opportunity (internally retrieves Memo0 historical experience)
        signal = await system.analyze_opportunity(opportunity)
        logger.info(f"  Signal analysis: type={signal.signal_type.value} | confidence={signal.confidence.value} | strength={signal.strength:.2f} | historical_matches={signal.historical_matches}")
        logger.info(f"  Reasoning: {signal.reasoning}")

        # 3.4.3 Make decision
        decision = await system.decide(opportunity)
        if decision:
            logger.info(f"  [OK] Decision generated: ID={decision.decision_id} | position_size=${decision.position_size:.0f} | risk_score={decision.risk_score:.2f}")

            # 3.4.4 Execute trade (PAPER mode)
            result = await system.execute(decision)
            logger.info(f"  Execution result: status={result.status} | executed={result.executed} | profit=${result.profit or 0:.2f} | time={result.execution_time:.3f}s")

            # 3.4.5 Record to knowledge base
            add_trading_knowledge(
                "trade_result",
                f"Demo round {round_idx}: {opportunity['symbol']} {opportunity['strategy']} -> "
                f"profit={result.profit or 0:.2f}, executed={result.executed}, risk_score={decision.risk_score:.2f}",
                {"round": round_idx, "symbol": opportunity["symbol"], "strategy": opportunity["strategy"]}
            )
        else:
            logger.info(f"  [X] Decision filtered: opportunity did not pass risk/confidence checks")
            add_trading_knowledge(
                "filtered_opportunity",
                f"Demo round {round_idx}: {opportunity['symbol']} filtered, confidence={signal.confidence.value}, risk={signal.risk_score:.2f}",
                {"round": round_idx, "symbol": opportunity["symbol"]}
            )

    print()

    # ---- 3.5 Final statistics ----
    logger.info("[Step 5] Final statistics...")
    stats = system.get_statistics()
    print()
    print("=" * 60)
    print("Demo Statistics Report")
    print("=" * 60)
    print(f"  Total trades:      {stats['total_trades']}")
    print(f"  Successful trades: {stats['successful_trades']}")
    print(f"  Failed trades:     {stats['failed_trades']}")
    print(f"  Success rate:      {stats['success_rate']*100:.1f}%")
    print(f"  Active trades:     {stats['active_trades']}")
    print(f"  Execution mode:    {stats['execution_mode']}")
    print()

    # ---- 3.6 Retrieval verification ----
    logger.info("[Step 6] Verify knowledge base records...")
    search_results = search_trading_knowledge("Demo round", top_k=5)
    print(f"  Search 'Demo round' hits: {len(search_results)} entries")
    for i, r in enumerate(search_results[:3], 1):
        print(f"    {i}. [{r.get('category', 'N/A')}] {r.get('content', '')[:80]}...")

    all_knowledge_final = unified.get_all_knowledge()
    print(f"  Final knowledge base size: {len(all_knowledge_final)} entries")
    print()

    print("=" * 60)
    print("End-to-end Demo completed - signal->decision->execution->record loop verified")
    print("=" * 60)

    return stats


# ------------------------------------------------------------------
# 4. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    try:
        result = asyncio.run(run_e2e_demo())
    except KeyboardInterrupt:
        logger.info("User interrupted")
    except Exception as e:
        logger.exception(f"Demo execution failed: {e}")
        raise
