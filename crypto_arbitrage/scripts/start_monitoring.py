#!/usr/bin/env python3
"""
Monitoring and Alerting Script for CryptoArbitrage Trading System
V2.3 - Production Monitoring
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingMonitor:
    """Trading system monitor with alerting capabilities"""

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('monitoring', {}).get('enabled', True)
        self.alert_methods = config.get('monitoring', {}).get('alert_methods', ['console'])
        self.thresholds = config.get('monitoring', {}).get('performance_thresholds', {})
        self.metrics_interval = config.get('monitoring', {}).get('metrics_interval', 60)

        self.alerts_sent = []
        self.last_metrics = {}

    async def monitor_system_health(self) -> Dict:
        """Monitor system health"""
        try:
            import subprocess

            result = subprocess.run(
                ['python', 'scripts/health_check.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            health_status = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': time.time()
            }

            if result.returncode != 0:
                await self.send_alert('health_check_failed', {
                    'message': 'Health check failed',
                    'exit_code': result.returncode,
                    'stderr': result.stderr
                })

            return health_status

        except Exception as e:
            logger.error(f"Health check monitoring failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    async def monitor_trading_performance(self) -> Dict:
        """Monitor trading performance metrics"""
        try:
            from storage.unified_storage import UnifiedStorage

            storage = UnifiedStorage()
            metrics = {
                'timestamp': time.time(),
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'total_profit': 0.0,
                'win_rate': 0.0
            }

            # Get recent trade data (last 24 hours)
            recent_trades = storage.get_trades(hours=24)
            metrics['total_trades'] = len(recent_trades)

            if recent_trades:
                successful_trades = [t for t in recent_trades if t.get('status') == 'completed']
                metrics['successful_trades'] = len(successful_trades)
                metrics['failed_trades'] = metrics['total_trades'] - metrics['successful_trades']

                # Calculate total profit
                total_profit = sum(t.get('profit', 0) for t in successful_trades)
                metrics['total_profit'] = total_profit

                # Calculate win rate
                metrics['win_rate'] = (metrics['successful_trades'] / metrics['total_trades']) * 100

            # Check thresholds and send alerts
            low_win_rate_threshold = self.thresholds.get('low_win_rate', 50)
            if metrics['total_trades'] > 10 and metrics['win_rate'] < low_win_rate_threshold:
                await self.send_alert('low_win_rate', {
                    'message': f'Low win rate detected: {metrics["win_rate"]:.1f}%',
                    'win_rate': metrics['win_rate'],
                    'total_trades': metrics['total_trades']
                })

            return metrics

        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    async def monitor_strategy_performance(self) -> Dict:
        """Monitor individual strategy performance"""
        try:
            from strategies.strategy_manager import StrategyManager

            manager = StrategyManager(self.config)
            strategy_metrics = {
                'timestamp': time.time(),
                'strategies': {}
            }

            for strategy_name in manager.strategies.keys():
                performance = manager.get_strategy_performance(strategy_name)
                strategy_metrics['strategies'][strategy_name] = performance

            return strategy_metrics

        except Exception as e:
            logger.error(f"Strategy performance monitoring failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    async def monitor_errors(self) -> Dict:
        """Monitor system errors and exceptions"""
        try:
            from storage.unified_storage import UnifiedStorage

            storage = UnifiedStorage()

            # Get recent errors (last hour)
            recent_errors = storage.get_errors(hours=1)

            error_metrics = {
                'timestamp': time.time(),
                'error_count': len(recent_errors),
                'error_types': {},
                'critical_errors': []
            }

            # Count error types
            for error in recent_errors:
                error_type = error.get('error_type', 'unknown')
                error_metrics['error_types'][error_type] = error_metrics['error_types'].get(error_type, 0) + 1

                # Check for critical errors
                if error.get('severity') == 'critical':
                    error_metrics['critical_errors'].append(error)

            # Alert on critical errors
            if error_metrics['critical_errors']:
                await self.send_alert('critical_error', {
                    'message': f'Found {len(error_metrics["critical_errors"])} critical errors',
                    'errors': error_metrics['critical_errors']
                })

            return error_metrics

        except Exception as e:
            logger.error(f"Error monitoring failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    async def send_alert(self, alert_type: str, data: dict) -> None:
        """Send alert through configured channels"""
        alert_key = f"{alert_type}_{int(time.time())}"

        # Prevent duplicate alerts within a short time window
        recent_alerts = [k for k in self.alerts_sent if k.startswith(alert_type)]
        if len(recent_alerts) > 5:  # More than 5 similar alerts recently
            logger.warning(f"Too many {alert_type} alerts, throttling")
            return

        self.alerts_sent.append(alert_key)

        # Keep only last 100 alerts
        self.alerts_sent = self.alerts_sent[-100:]

        alert_message = f"🚨 [{alert_type.upper()}] {data.get('message', 'Unknown alert')}"
        logger.warning(alert_message)

        # Send to memo0
        if 'memo0' in self.alert_methods:
            try:
                from storage.memo0_storage import Memo0Storage
                memo0 = Memo0Storage()
                await memo0.add_trading_alert(alert_type, data)
            except Exception as e:
                logger.error(f"Failed to send alert to memo0: {e}")

        # Send to file
        if 'file' in self.alert_methods:
            try:
                alerts_dir = Path('logs/alerts')
                alerts_dir.mkdir(parents=True, exist_ok=True)

                alert_file = alerts_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"
                with open(alert_file, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now().isoformat()} - {alert_type} - {data}\n")
            except Exception as e:
                logger.error(f"Failed to write alert to file: {e}")

    async def collect_metrics(self) -> Dict:
        """Collect all monitoring metrics"""
        metrics = {
            'timestamp': time.time(),
            'health': await self.monitor_system_health(),
            'performance': await self.monitor_trading_performance(),
            'strategies': await self.monitor_strategy_performance(),
            'errors': await self.monitor_errors()
        }

        self.last_metrics = metrics
        return metrics

    async def start_monitoring(self) -> None:
        """Start continuous monitoring"""
        logger.info("Starting monitoring service...")
        logger.info(f"Metrics interval: {self.metrics_interval}s")

        while True:
            try:
                metrics = await self.collect_metrics()

                # Log summary
                logger.info(f"Monitoring update: {metrics['performance']['total_trades']} trades, "
                           f"win rate: {metrics['performance']['win_rate']:.1f}%, "
                           f"errors: {metrics['errors']['error_count']}")

            except Exception as e:
                logger.error(f"Monitoring cycle failed: {e}", exc_info=True)

            # Wait for next cycle
            await asyncio.sleep(self.metrics_interval)


async def main():
    """Main function"""
    import yaml

    # Load configuration
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Create and start monitor
    monitor = TradingMonitor(config)

    if monitor.enabled:
        await monitor.start_monitoring()
    else:
        logger.info("Monitoring is disabled in configuration")


if __name__ == "__main__":
    asyncio.run(main())
