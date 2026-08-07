#!/usr/bin/env python3
"""
Health Check Script for CryptoArbitrage Trading System
V2.3 - Production Monitoring
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to Python path for proper imports
script_dir = Path(__file__).parent
project_dir = script_dir.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Store project directory for path resolution
BASE_DIR = project_dir

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """System health checker for CryptoArbitrage"""

    def __init__(self):
        self.status = {
            'overall': 'healthy',
            'checks': [],
            'timestamp': time.time()
        }

    def check_filesystem(self) -> bool:
        """Check filesystem health"""
        try:
            # Check essential directories exist and are writable
            essential_dirs = ['logs', 'data', 'storage', 'knowledge_base']

            for directory in essential_dirs:
                path = BASE_DIR / directory
                if not path.exists():
                    # Try to create missing directories
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created missing directory: {directory}")
                    except Exception as e:
                        logger.error(f"Directory not found and cannot create: {directory}: {e}")
                        return False

                if not path.is_dir():
                    logger.error(f"Path is not a directory: {directory}")
                    return False

                # Test write permission
                test_file = path / ".health_check"
                try:
                    test_file.touch()
                    test_file.unlink()
                except Exception as e:
                    logger.error(f"Cannot write to directory {directory}: {e}")
                    return False

            logger.info("✓ Filesystem check passed")
            return True
        except Exception as e:
            logger.error(f"Filesystem check failed: {e}")
            return False

    def check_config(self) -> bool:
        """Check configuration file"""
        try:
            import yaml

            config_path = BASE_DIR / 'config' / 'config.yaml'
            if not config_path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                return False

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Check essential configuration
            if 'system' not in config:
                logger.error("Missing 'system' section in config")
                return False

            if 'version' not in config['system']:
                logger.error("Missing 'version' in system config")
                return False

            logger.info(f"✓ Configuration check passed (version {config['system']['version']})")
            return True
        except Exception as e:
            logger.error(f"Configuration check failed: {e}")
            return False

    def check_python_environment(self) -> bool:
        """Check Python environment"""
        try:
            import sys

            # Check Python version
            if sys.version_info < (3, 10):
                logger.error(f"Python version {sys.version_info} is not supported (requires 3.10+)")
                return False

            # Check essential packages
            essential_packages = [
                'yaml', 'asyncio', 'logging', 'pathlib'
            ]

            for package in essential_packages:
                try:
                    __import__(package)
                except ImportError:
                    logger.error(f"Essential package not found: {package}")
                    return False

            logger.info(f"✓ Python environment check passed (Python {sys.version_info.major}.{sys.version_info.minor})")
            return True
        except Exception as e:
            logger.error(f"Python environment check failed: {e}")
            return False

    def check_database(self) -> bool:
        """Check database connectivity"""
        try:
            from storage.knowledge_base import initialize_knowledge_base

            db = initialize_knowledge_base('crypto_arbitrage_knowledge.db')

            # Test database operation using KnowledgeBase API
            stats = db.get_statistics()
            if stats is not None:
                logger.info("✓ Database check passed")
                return True
            else:
                logger.error("Database check failed: get_statistics returned None")
                return False
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False

    def check_strategies(self) -> bool:
        """Check strategy modules"""
        try:
            from strategies import (
                CrossExchangeArbitrageStrategy,
                TriangularArbitrageStrategy,
                BasisTradingStrategy,
                FundingRateArbitrageStrategy,
                StatisticalArbitrageStrategy
            )

            logger.info("✓ Strategy modules check passed")
            return True
        except Exception as e:
            logger.error(f"Strategy modules check failed: {e}")
            return False

    def check_v22_components(self) -> bool:
        """Check V2.2 intelligent components"""
        try:
            from storage import (
                IntelligentDecisionEngine,
                MarketPatternRecognizer,
                StrategyOptimizer
            )

            logger.info("✓ V2.2 intelligent components check passed")
            return True
        except Exception as e:
            logger.error(f"V2.2 intelligent components check failed: {e}")
            return False

    def check_logs(self) -> bool:
        """Check log system"""
        try:
            log_dir = BASE_DIR / 'logs'
            if not log_dir.exists():
                logger.warning("Logs directory not found")
                return True  # Not critical

            # Check if log files are being created
            log_files = list(log_dir.glob('*.log'))
            if log_files:
                latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"✓ Log system check passed (latest: {latest_log.name})")
            else:
                logger.info("✓ Log system check passed (no log files yet)")

            return True
        except Exception as e:
            logger.error(f"Log system check failed: {e}")
            return False

    def run_all_checks(self) -> Dict:
        """Run all health checks"""
        logger.info("Starting health checks...")

        checks = [
            ('Filesystem', self.check_filesystem),
            ('Configuration', self.check_config),
            ('Python Environment', self.check_python_environment),
            ('Database', self.check_database),
            ('Strategy Modules', self.check_strategies),
            ('V2.2 Components', self.check_v22_components),
            ('Log System', self.check_logs)
        ]

        results = []
        all_passed = True

        for name, check_func in checks:
            try:
                result = check_func()
                results.append({
                    'name': name,
                    'status': 'passed' if result else 'failed',
                    'timestamp': time.time()
                })

                if not result:
                    all_passed = False

            except Exception as e:
                logger.error(f"Check '{name}' raised exception: {e}")
                results.append({
                    'name': name,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                })
                all_passed = False

        self.status['checks'] = results
        self.status['overall'] = 'healthy' if all_passed else 'unhealthy'

        return self.status

    def print_report(self) -> None:
        """Print health check report"""
        logger.info("=" * 60)
        logger.info("Health Check Report")
        logger.info("=" * 60)

        logger.info(f"Overall Status: {self.status['overall'].upper()}")
        logger.info(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.status['timestamp']))}")
        logger.info("")

        for check in self.status['checks']:
            status_symbol = "✓" if check['status'] == 'passed' else "✗"
            logger.info(f"{status_symbol} {check['name']}: {check['status'].upper()}")

            if 'error' in check:
                logger.error(f"  Error: {check['error']}")

        logger.info("")
        logger.info("=" * 60)

        return self.status['overall'] == 'healthy'


def main():
    """Main function"""
    checker = HealthChecker()

    try:
        status = checker.run_all_checks()
        checker.print_report()

        # Exit with appropriate code
        if status['overall'] == 'healthy':
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Health check failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
