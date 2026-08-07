"""Test Suite for V41.0 Dashboard and Alerts
Comprehensive testing of dashboard widgets,
system alerts, and scheduling features.
"""

import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.auto_execution_engine import (
    AutoExecutionEngine,
    DashboardWidget,
    SystemAlert,
    ScheduleTask
)


class TestV41_0DashboardConfig:
    """Test suite for Dashboard Config - V41.0"""

    @pytest.fixture
    def engine(self):
        """Create engine with dashboard config"""
        config = {
            'enable_dashboard': True,
            'dashboard_refresh': 60,
            'enable_system_alerts': True,
            'enable_scheduling': True
        }
        return AutoExecutionEngine(config=config)

    def test_dashboard_config(self, engine):
        """Test dashboard configuration"""
        assert engine.run_config.enable_dashboard is True
        assert engine.run_config.dashboard_refresh == 60
        assert engine.run_config.enable_system_alerts is True


class TestV41_0Dashboard:
    """Test suite for Dashboard - V41.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_create_dashboard_widget(self, engine):
        """Test creating dashboard widget"""
        result = engine.create_dashboard_widget(
            widget_id="pnl_widget",
            widget_type="chart",
            title="P&L Chart",
            data_source="pnl_data",
            refresh_interval=30
        )

        assert result is True
        widget = engine.get_dashboard_widget("pnl_widget")
        assert widget is not None
        assert widget.widget_type == "chart"

    def test_get_dashboard_widget(self, engine):
        """Test getting dashboard widget"""
        engine.create_dashboard_widget("test", "metric", "Test", "data")

        widget = engine.get_dashboard_widget("test")
        assert widget is not None


class TestV41_0Alerts:
    """Test suite for Alerts - V41.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {'enable_system_alerts': True}
        return AutoExecutionEngine(config=config)

    def test_create_alert(self, engine):
        """Test creating alert"""
        result = engine.create_alert(
            alert_type="warning",
            source="risk",
            message="High volatility detected"
        )

        assert result is True

    def test_acknowledge_alert(self, engine):
        """Test acknowledging alert"""
        engine.create_alert("error", "system", "Test error")

        alerts = engine.get_active_alerts()
        if alerts:
            alert_id = alerts[0].alert_id
            result = engine.acknowledge_alert(alert_id)
            assert result is True

    def test_get_active_alerts(self, engine):
        """Test getting active alerts"""
        engine.create_alert("info", "system", "Info message")
        engine.create_alert("warning", "system", "Warning message")

        alerts = engine.get_active_alerts()
        assert len(alerts) >= 2


class TestV41_0Scheduling:
    """Test suite for Scheduling - V41.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {'enable_scheduling': True}
        return AutoExecutionEngine(config=config)

    def test_create_schedule_task(self, engine):
        """Test creating schedule task"""
        result = engine.create_schedule_task(
            task_id="daily_rebalance",
            task_type="rebalance",
            schedule="0 0 * * *"
        )

        assert result is True

    def test_get_schedule_task(self, engine):
        """Test getting schedule task"""
        engine.create_schedule_task("rotate", "rotate", "0 6 * * *")

        task = engine.get_schedule_task("rotate")
        assert task is not None


class TestV41_0SystemStatus:
    """Test suite for System Status - V41.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        return AutoExecutionEngine()

    def test_get_system_status(self, engine):
        """Test getting system status"""
        status = engine.get_system_status()

        assert 'running' in status
        assert 'positions' in status
        assert 'alerts' in status


class TestV41_0V41Summary:
    """Test suite for V41 Summary - V41.0"""

    @pytest.fixture
    def engine(self):
        """Create engine"""
        config = {'enable_dashboard': True, 'enable_system_alerts': True}
        return AutoExecutionEngine(config=config)

    def test_v41_summary(self, engine):
        """Test V41.0 summary"""
        summary = engine.get_v41_summary()

        assert 'dashboard_widgets' in summary
        assert 'alerts' in summary
        assert 'system_status' in summary

    def test_all_features_initialized(self, engine):
        """Test all V41.0 features are initialized"""
        assert engine._dashboard_widgets is not None
        assert engine._system_alerts is not None
        assert engine._schedule_tasks is not None