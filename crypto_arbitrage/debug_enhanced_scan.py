"""调试增强版扫描工具返回值"""

import asyncio
from agents.main_agent import CryptoArbitrageAgent


async def debug_enhanced_scan():
    config = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']},
        'enhanced_low_risk_engine': {
            'enabled': True,
            'enable_risk_prediction': True,
            'enable_health_monitoring': True,
            'enable_intelligent_decision': True
        }
    }

    agent = CryptoArbitrageAgent(config)

    print("Debugging Enhanced Scan Tool:")
    result = await agent.scan_with_enhanced_engine_tool.coroutine(agent, "BTC/USDT")

    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result)}")
    print(f"Result content:")
    print(result)
    print(f"\nContains 'Enhanced': {'Enhanced' in result}")
    print(f"Contains 'enhanced': {'enhanced' in result}")
    print(f"Contains 'Engine': {'Engine' in result}")


if __name__ == "__main__":
    asyncio.run(debug_enhanced_scan())
