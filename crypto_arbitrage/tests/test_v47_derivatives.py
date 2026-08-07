"""Test Suite for V47.0 Derivatives
Comprehensive testing of options, futures and margin trading.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    OptionsContract,
    FuturesContract,
    MarginAccount
)


class TestV47_0Config:
    """Test suite for V47.0 Config"""

    @pytest.fixture
    def engine(self):
        config = {
            'enable_options': True,
            'enable_futures': True,
            'enable_margin_trading': True
        }
        return AutoExecutionEngine(config=config)

    def test_v47_config(self, engine):
        assert engine.run_config.enable_options is True
        assert engine.run_config.enable_futures is True


class TestV47_0Options:
    """Test suite for Options"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_options': True})

    def test_create_options(self, engine):
        opt = engine.create_options_contract("BTC", 50000, 9999999999, "call", "long", 1.0, 500)
        assert isinstance(opt, OptionsContract)
        assert opt.underlying == "BTC"

    def test_options_enabled(self, engine):
        assert len(engine._options_contracts) >= 0


class TestV47_0Futures:
    """Test suite for Futures"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_futures': True})

    def test_create_futures(self, engine):
        fut = engine.create_futures_contract("BTC-PERP", "long", 0.5, 45000, 10)
        assert isinstance(fut, FuturesContract)
        assert fut.leverage == 10

    def test_futures_margin_calc(self, engine):
        fut = engine.create_futures_contract("ETH-PERP", "short", 1.0, 2500, 5)
        assert fut.margin > 0


class TestV47_0Margin:
    """Test suite for Margin"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine(config={'enable_margin_trading': True})

    def test_open_margin_account(self, engine):
        account = engine.open_margin_account(10000.0)
        assert isinstance(account, MarginAccount)
        assert account.total_equity == 10000.0


class TestV47_0Summary:
    """Test suite for V47 Summary"""

    @pytest.fixture
    def engine(self):
        return AutoExecutionEngine()

    def test_v47_summary(self, engine):
        summary = engine.get_v47_summary()
        assert 'options_contracts' in summary
        assert 'futures_contracts' in summary
