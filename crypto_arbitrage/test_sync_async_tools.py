"""测试同步和异步工具的调用方式"""
import asyncio
from agents.main_agent import CryptoArbitrageAgent


async def test():
    config = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']}
    }
    agent = CryptoArbitrageAgent(config)

    print("=== Testing async tools ===")

    # Async tool
    print("\n1. scan_arbitrage_opportunities_tool (async):")
    try:
        result = await agent.scan_arbitrage_opportunities_tool.coroutine(agent, "all")
        print(f"   Success via coroutine: {len(result)} chars")
    except Exception as e:
        print(f"   Failed via coroutine: {e}")

    # Try alternative for async tool
    print("\n2. execute_arbitrage_tool (async):")
    try:
        result = await agent.execute_arbitrage_tool.coroutine(agent, 0, "cross_exchange")
        print(f"   Success via coroutine: {len(result)} chars")
    except Exception as e:
        print(f"   Failed via coroutine: {e}")

    print("\n=== Testing sync tools ===")

    # Sync tools
    print("\n3. get_risk_status_tool (sync):")
    try:
        # Try calling the sync function directly
        result = agent.get_risk_status_tool(agent)
        print(f"   Success direct call: {len(result)} chars")
    except Exception as e:
        print(f"   Failed direct call: {e}")

    print("\n4. get_performance_stats_tool (sync):")
    try:
        result = agent.get_performance_stats_tool(agent)
        print(f"   Success direct call: {len(result)} chars")
    except Exception as e:
        print(f"   Failed direct call: {e}")

    print("\n5. record_knowledge_tool (sync):")
    try:
        result = agent.record_knowledge_tool(agent, "strategy", "test")
        print(f"   Success direct call: {len(result)} chars")
    except Exception as e:
        print(f"   Failed direct call: {e}")

    print("\n6. search_knowledge_tool (sync):")
    try:
        result = agent.search_knowledge_tool(agent, "test", 5)
        print(f"   Success direct call: {len(result)} chars")
    except Exception as e:
        print(f"   Failed direct call: {e}")

    print("\n7. get_monitoring_status_tool (sync):")
    try:
        result = agent.get_monitoring_status_tool(agent)
        print(f"   Success direct call: {len(result)} chars")
    except Exception as e:
        print(f"   Failed direct call: {e}")

    print("\n8. get_alert_history_tool (sync):")
    try:
        result = agent.get_alert_history_tool(agent, 10)
        print(f"   Success direct call: {len(result)} chars")
    except Exception as e:
        print(f"   Failed direct call: {e}")


if __name__ == "__main__":
    asyncio.run(test())
