"""测试StructuredTool的不同调用方法"""
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

    print("=== Testing different invocation methods ===")

    # Test 1: Sync tool with .run()
    print("\n1. get_risk_status_tool (sync) with .run():")
    try:
        result = agent.get_risk_status_tool.run({})
        print(f"   Success via .run(): {len(result)} chars")
    except Exception as e:
        print(f"   Failed via .run(): {e}")

    # Test 2: Sync tool with .invoke()
    print("\n2. get_risk_status_tool (sync) with .invoke():")
    try:
        result = agent.get_risk_status_tool.invoke({})
        print(f"   Success via .invoke(): {len(result)} chars")
    except Exception as e:
        print(f"   Failed via .invoke(): {e}")

    # Test 3: Async tool with .arun()
    print("\n3. scan_arbitrage_opportunities_tool (async) with .arun():")
    try:
        result = await agent.scan_arbitrage_opportunities_tool.arun({"strategy_type": "all"})
        print(f"   Success via .arun(): {len(result)} chars")
    except Exception as e:
        print(f"   Failed via .arun(): {e}")

    # Test 4: Check available methods
    print("\n4. Available methods for sync tool:")
    sync_tool = agent.get_risk_status_tool
    methods = [attr for attr in dir(sync_tool) if not attr.startswith('_') and callable(getattr(sync_tool, attr))]
    for method in methods[:10]:  # Show first 10 methods
        try:
            print(f"   {method}: {type(getattr(sync_tool, method))}")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(test())
