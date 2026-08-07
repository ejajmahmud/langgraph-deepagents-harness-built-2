"""测试execute_arbitrage_tool的返回值"""
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

    print("Testing execute_arbitrage_tool:")
    try:
        result = await agent.execute_arbitrage_tool.coroutine(agent, 0, "cross_exchange")
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if isinstance(result, str) else 'N/A'}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
