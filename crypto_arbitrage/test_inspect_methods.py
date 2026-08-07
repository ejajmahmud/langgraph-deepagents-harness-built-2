"""使用inspect模块访问原始函数"""
import inspect
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

    print("=== Using inspect module to find original functions ===")

    # Check the class __dict__ before @tool decorator
    print("\n1. Checking class attributes:")
    for name, value in vars(CryptoArbitrageAgent).items():
        if 'tool' in name.lower():
            print(f"   {name}: {type(value)}")
            # Try to get original function
            if hasattr(value, '__wrapped__'):
                print(f"      Has __wrapped__: {value.__wrapped__}")
            if hasattr(value, '__func__'):
                print(f"      Has __func__: {value.__func__}")

    # Try to find the original implementation
    print("\n2. Trying to find original implementation:")
    try:
        # Check if the tool has a _run method
        sync_tool = agent.get_risk_status_tool
        print(f"   Tool has _run: {hasattr(sync_tool, '_run')}")
        if hasattr(sync_tool, '_run'):
            print(f"   _run method: {sync_tool._run}")

        # Check internal attributes
        for attr in ['_func', 'func', 'coroutine', 'f']:
            if hasattr(sync_tool, attr):
                value = getattr(sync_tool, attr)
                print(f"   {attr}: {value}")
    except Exception as e:
        print(f"   Error: {e}")

    # Try to call via _run
    print("\n3. Trying to call via _run:")
    try:
        sync_tool = agent.get_risk_status_tool
        # The _run method expects the tool_input dict
        result = sync_tool._run({})
        print(f"   Success via _run: {len(result)} chars")
    except Exception as e:
        print(f"   Failed via _run: {e}")


if __name__ == "__main__":
    asyncio.run(test())
