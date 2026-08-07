"""测试增强版引擎初始化"""

import asyncio
from agents.main_agent import CryptoArbitrageAgent


async def test_engine_init():
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

    print("Testing Enhanced Engine Initialization:")
    agent = CryptoArbitrageAgent(config)

    print(f"Enhanced engine object: {agent.enhanced_low_risk_engine}")
    print(f"Is None: {agent.enhanced_low_risk_engine is None}")

    if agent.enhanced_low_risk_engine:
        print("Enhanced engine attributes:")
        print(f"  - Has risk_predictor: {hasattr(agent.enhanced_low_risk_engine, 'risk_predictor')}")
        print(f"  - Has health_monitor: {hasattr(agent.enhanced_low_risk_engine, 'health_monitor')}")
        print(f"  - Has decision_assistant: {hasattr(agent.enhanced_low_risk_engine, 'decision_assistant')}")


if __name__ == "__main__":
    asyncio.run(test_engine_init())
