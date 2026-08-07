"""尝试访问StructuredTool内部的原始方法"""
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

    print("=== Accessing internal methods ===")

    # Try accessing the class method directly
    print("\n1. Accessing class method directly:")
    try:
        # Get the actual method from the class
        original_method = CryptoArbitrageAgent.get_risk_status_tool
        print(f"   Method type: {type(original_method)}")
        result = original_method(agent)
        print(f"   Success: {len(result)} chars")
    except Exception as e:
        print(f"   Failed: {e}")

    print("\n2. Testing all tools via class methods:")
    tools_to_test = [
        ('get_risk_status_tool', []),
        ('get_performance_stats_tool', []),
        ('record_knowledge_tool', ['strategy', 'test']),
        ('search_knowledge_tool', ['test', 5]),
        ('get_monitoring_status_tool', []),
        ('get_alert_history_tool', [10]),
    ]

    for tool_name, args in tools_to_test:
        try:
            original_method = getattr(CryptoArbitrageAgent, tool_name)
            result = original_method(agent, *args)
            print(f"   {tool_name}: Success ({len(result)} chars)")
        except Exception as e:
            print(f"   {tool_name}: Failed ({e})")

    print("\n3. Testing async tools via class methods:")
    try:
        original_method = CryptoArbitrageAgent.scan_arbitrage_opportunities_tool
        result = await original_method(agent, "all")
        print(f"   scan_arbitrage_opportunities_tool: Success ({len(result)} chars)")
    except Exception as e:
        print(f"   scan_arbitrage_opportunities_tool: Failed ({e})")

    try:
        original_method = CryptoArbitrageAgent.execute_arbitrage_tool
        result = await original_method(agent, 0, "cross_exchange")
        print(f"   execute_arbitrage_tool: Success ({len(result)} chars)")
    except Exception as e:
        print(f"   execute_arbitrage_tool: Failed ({e})")


if __name__ == "__main__":
    asyncio.run(test())
