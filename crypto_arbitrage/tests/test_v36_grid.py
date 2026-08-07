#!/usr/bin/env python
"""V36.0 Grid Trading 快速测试"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_grid_trading():
    """测试网格交易系统"""
    from strategies.grid_trading import (
        GridTradingStrategy,
        GridOrderType,
        GridStatus,
        DCABot,
        DCAMode,
        GridBacktester
    )

    print("=" * 60)
    print("V36.0 网格交易系统测试")
    print("=" * 60)

    passed = 0
    failed = 0

    # 测试1: 创建网格交易策略
    try:
        config = {
            'symbol': 'BTC/USDT',
            'lower_price': 45000,
            'upper_price': 55000,
            'grid_count': 10,
            'investment_per_grid': 100,
            'profit_target': 0.5
        }
        strategy = GridTradingStrategy(config)

        assert strategy.symbol == 'BTC/USDT'
        assert strategy.lower_price == 45000
        assert strategy.upper_price == 55000

        print("[PASS] 网格交易策略创建")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 网格交易策略创建: {e}")
        failed += 1

    # 测试2: 网格价格生成
    try:
        config = {
            'symbol': 'BTC/USDT',
            'lower_price': 45000,
            'upper_price': 55000,
            'grid_count': 10,
            'investment_per_grid': 100
        }
        strategy = GridTradingStrategy(config)
        prices = strategy.grid_prices

        assert len(prices) == 10
        assert prices[0] == 45000

        print("[PASS] 网格价格生成")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 网格价格生成: {e}")
        failed += 1

    # 测试3: 创建网格级别
    try:
        config = {
            'symbol': 'BTC/USDT',
            'lower_price': 45000,
            'upper_price': 55000,
            'grid_count': 10,
            'investment_per_grid': 100
        }
        strategy = GridTradingStrategy(config)
        levels = strategy.create_grid_levels()

        assert len(levels) == 10
        assert levels[0].order_type == GridOrderType.BUY

        print("[PASS] 网格级别创建")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 网格级别创建: {e}")
        failed += 1

    # 测试4: DCA机器人
    try:
        config = {
            'symbol': 'BTC/USDT',
            'mode': 'fixed_amount',
            'amount': 100,
            'interval': 86400,
            'max_investments': 30
        }
        bot = DCABot(config)

        assert bot.symbol == 'BTC/USDT'
        assert bot.mode == DCAMode.FIXED_AMOUNT

        print("[PASS] DCA机器人创建")
        passed += 1
    except Exception as e:
        print(f"[FAIL] DCA机器人创建: {e}")
        failed += 1

    # 测试5: 马丁格尔模式
    try:
        config = {
            'symbol': 'BTC/USDT',
            'mode': 'martingale',
            'amount': 100,
            'interval': 86400,
            'martingale_multiplier': 2.0,
            'martingale_max': 8.0
        }
        bot = DCABot(config)

        amount1 = bot.calculate_investment_amount()
        bot.on_loss()
        amount2 = bot.calculate_investment_amount()

        assert amount1 == 100
        assert amount2 == 200

        print("[PASS] 马丁格尔模式")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 马丁格尔模式: {e}")
        failed += 1

    # 测试6: 回测引擎
    try:
        prices = [45000, 46000, 47000, 48000, 49000, 50000,
                 51000, 52000, 53000, 54000]

        config = {
            'symbol': 'BTC/USDT',
            'prices': prices,
            'lower_price': 45000,
            'upper_price': 55000,
            'grid_count': 10,
            'investment_per_grid': 100,
            'profit_target': 0.5,
            'stop_loss': 10.0
        }

        backtester = GridBacktester()
        result = backtester.run_backtest(config)

        assert result.symbol == 'BTC/USDT'

        print("[PASS] 回测引擎")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 回测引擎: {e}")
        failed += 1

    print("-" * 60)
    print(f"结果: {passed}/{passed+failed} 测试通过")
    print()

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_grid_trading()
    sys.exit(0 if failed == 0 else 1)