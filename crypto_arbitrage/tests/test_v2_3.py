"""V2.3 Test Suite - Docker Deployment and Monitoring"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDockerConfiguration:
    """Test Docker configuration files"""

    def test_dockerfile_exists(self):
        """Test Dockerfile exists"""
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "Dockerfile not found"
        assert dockerfile_path.is_file(), "Dockerfile is not a file"

    def test_docker_compose_exists(self):
        """Test docker-compose.yml exists"""
        compose_path = Path("docker-compose.yml")
        assert compose_path.exists(), "docker-compose.yml not found"
        assert compose_path.is_file(), "docker-compose.yml is not a file"

    def test_dockerignore_exists(self):
        """Test .dockerignore exists"""
        dockerignore_path = Path(".dockerignore")
        assert dockerignore_path.exists(), ".dockerignore not found"
        assert dockerignore_path.is_file(), ".dockerignore is not a file"

    def test_env_example_exists(self):
        """Test .env.example exists"""
        env_example_path = Path(".env.example")
        assert env_example_path.exists(), ".env.example not found"
        assert env_example_path.is_file(), ".env.example is not a file"

    def test_dockerfile_content(self):
        """Test Dockerfile has required content"""
        dockerfile_path = Path("Dockerfile")
        content = dockerfile_path.read_text()

        required_directives = [
            "FROM python:",
            "WORKDIR /app",
            "COPY requirements.txt",
            "RUN pip install",
            "COPY . .",
            "CMD [\"python\", \"main.py\"]"
        ]

        for directive in required_directives:
            assert directive in content, f"Dockerfile missing directive: {directive}"

    def test_docker_compose_content(self):
        """Test docker-compose.yml has required services"""
        compose_path = Path("docker-compose.yml")
        content = compose_path.read_text()

        required_services = [
            "crypto-arbitrage:",
            "prometheus:",
            "grafana:",
            "redis:"
        ]

        for service in required_services:
            assert service in content, f"docker-compose.yml missing service: {service}"

    def test_docker_compose_healthcheck(self):
        """Test docker-compose.yml has health checks"""
        compose_path = Path("docker-compose.yml")
        content = compose_path.read_text()

        assert "healthcheck:" in content or "HEALTHCHECK" in content, \
            "docker-compose.yml missing health check configuration"

    def test_dockerignore_patterns(self):
        """Test .dockerignore has important patterns"""
        dockerignore_path = Path(".dockerignore")
        content = dockerignore_path.read_text()

        important_patterns = [
            "__pycache__/",
            ".git/",
            "*.log",
            "venv/",
            ".pytest_cache/"
        ]

        for pattern in important_patterns:
            assert pattern in content, f".dockerignore missing pattern: {pattern}"


class TestDeploymentScript:
    """Test deployment script functionality"""

    def test_deploy_script_exists(self):
        """Test deploy.sh exists"""
        deploy_script = Path("deploy.sh")
        assert deploy_script.exists(), "deploy.sh not found"
        assert deploy_script.is_file(), "deploy.sh is not a file"

    def test_deploy_script_commands(self):
        """Test deploy.sh has required commands"""
        deploy_script = Path("deploy.sh")
        content = deploy_script.read_text(encoding='utf-8')

        required_commands = [
            "setup",
            "build",
            "start",
            "stop",
            "restart",
            "logs",
            "status",
            "health",
            "help"
        ]

        for command in required_commands:
            assert command in content, f"deploy.sh missing command: {command}"

    def test_deploy_script_docker_commands(self):
        """Test deploy.sh uses docker-compose commands"""
        deploy_script = Path("deploy.sh")
        content = deploy_script.read_text(encoding='utf-8')

        docker_commands = [
            "docker-compose build",
            "docker-compose up -d",
            "docker-compose down",
            "docker-compose restart",
            "docker-compose logs"
        ]

        for command in docker_commands:
            assert command in content, f"deploy.sh missing docker command: {command}"


class TestHealthCheckScript:
    """Test health check script"""

    def test_health_check_script_exists(self):
        """Test health_check.py exists"""
        health_check = Path("scripts/health_check.py")
        assert health_check.exists(), "health_check.py not found"

    def test_health_check_class_exists(self):
        """Test HealthChecker class exists"""
        from scripts.health_check import HealthChecker
        assert HealthChecker is not None, "HealthChecker class not found"

    def test_health_checker_initialization(self):
        """Test HealthChecker can be initialized"""
        from scripts.health_check import HealthChecker
        checker = HealthChecker()
        assert checker is not None
        assert 'overall' in checker.status
        assert 'checks' in checker.status
        assert 'timestamp' in checker.status

    @pytest.mark.skipif(not os.path.exists('config/config.yaml'), reason="Config file not found")
    def test_health_check_config(self):
        """Test configuration check"""
        from scripts.health_check import HealthChecker
        checker = HealthChecker()
        result = checker.check_config()
        assert isinstance(result, bool), "check_config should return bool"

    @pytest.mark.skipif(not os.path.exists('logs'), reason="Logs directory not found")
    def test_health_check_filesystem(self):
        """Test filesystem check"""
        from scripts.health_check import HealthChecker
        checker = HealthChecker()
        result = checker.check_filesystem()
        assert isinstance(result, bool), "check_filesystem should return bool"


class TestMonitoringScript:
    """Test monitoring script"""

    def test_monitoring_script_exists(self):
        """Test start_monitoring.py exists"""
        monitoring_script = Path("scripts/start_monitoring.py")
        assert monitoring_script.exists(), "start_monitoring.py not found"

    def test_monitoring_class_exists(self):
        """Test TradingMonitor class exists"""
        from scripts.start_monitoring import TradingMonitor
        assert TradingMonitor is not None, "TradingMonitor class not found"

    def test_monitoring_initialization(self):
        """Test TradingMonitor can be initialized"""
        from scripts.start_monitoring import TradingMonitor
        config = {
            'monitoring': {
                'enabled': True,
                'alert_methods': ['console'],
                'performance_thresholds': {}
            }
        }
        monitor = TradingMonitor(config)
        assert monitor is not None
        assert monitor.enabled is True
        assert 'console' in monitor.alert_methods


class TestEnvironmentConfiguration:
    """Test environment configuration"""

    def test_env_example_has_sections(self):
        """Test .env.example has all required sections"""
        env_example = Path(".env.example")
        content = env_example.read_text()

        required_sections = [
            "# System Configuration",
            "# Exchange API Keys",
            "# Memo0 Configuration",
            "# Monitoring & Alerting",
            "# Risk Management"
        ]

        for section in required_sections:
            assert section in content, f".env.example missing section: {section}"

    def test_env_example_has_required_vars(self):
        """Test .env.example has required environment variables"""
        env_example = Path(".env.example")
        content = env_example.read_text()

        required_vars = [
            "SYSTEM_MODE",
            "LOG_LEVEL",
            "BINANCE_API_KEY",
            "BINANCE_SECRET",
            "MEM0_API_KEY",
            "MAX_DAILY_LOSS",
            "MAX_POSITION_SIZE"
        ]

        for var in required_vars:
            assert var in content, f".env.example missing variable: {var}"

    def test_env_example_values(self):
        """Test .env.example has valid example values"""
        env_example = Path(".env.example")
        content = env_example.read_text()

        assert "simulation" in content, "Missing simulation mode in .env.example"
        assert "INFO" in content, "Missing INFO log level in .env.example"
        assert "your_" in content, "Missing placeholder values in .env.example"


class TestMonitoringConfiguration:
    """Test monitoring configuration"""

    def test_prometheus_config_exists(self):
        """Test prometheus.yml exists"""
        prometheus_config = Path("monitoring/prometheus.yml")
        assert prometheus_config.exists(), "prometheus.yml not found"

    def test_prometheus_config_content(self):
        """Test prometheus.yml has required sections"""
        prometheus_config = Path("monitoring/prometheus.yml")
        content = prometheus_config.read_text()

        required_sections = [
            "global:",
            "scrape_configs:",
            "scrape_interval"
        ]

        for section in required_sections:
            assert section in content, f"prometheus.yml missing section: {section}"

    def test_monitoring_directories_exist(self):
        """Test monitoring directories exist"""
        grafana_dashboards = Path("monitoring/grafana/dashboards")
        grafana_datasources = Path("monitoring/grafana/datasources")

        assert grafana_dashboards.exists(), "Grafana dashboards directory not found"
        assert grafana_datasources.exists(), "Grafana datasources directory not found"


class TestVersionSync:
    """Test version synchronization across files"""

    def test_config_version_v23(self):
        """Test config.yaml version is V2.3"""
        import yaml
        config_path = Path("config/config.yaml")

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                version = config.get('system', {}).get('version', '')
                assert version == "2.3", f"Config version should be 2.3, got {version}"

    def test_base_strategy_version_v23(self):
        """Test base.py version is V2.3"""
        base_path = Path("strategies/base.py")

        if base_path.exists():
            content = base_path.read_text(encoding='utf-8')
            assert "V2.3" in content, "base.py should reference V2.3"

    def test_strategy_manager_version_v23(self):
        """Test strategy_manager.py version is V2.3"""
        manager_path = Path("strategies/strategy_manager.py")

        if manager_path.exists():
            content = manager_path.read_text(encoding='utf-8')
            assert "V2.3" in content, "strategy_manager.py should reference V2.3"


class TestV23Integration:
    """Integration tests for V2.3 features"""

    def test_v23_deployment_files_integrated(self):
        """Test all V2.3 deployment files are present"""
        v23_files = [
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
            ".env.example",
            "deploy.sh",
            "scripts/health_check.py",
            "scripts/start_monitoring.py",
            "monitoring/prometheus.yml"
        ]

        for file_path in v23_files:
            file_obj = Path(file_path)
            assert file_obj.exists(), f"V2.3 file not found: {file_path}"

    def test_v23_version_consistency(self):
        """Test V2.3 version consistency across all files"""
        import yaml

        # Check config file
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                assert config.get('system', {}).get('version') == "2.3"

        # Check strategy files
        base_path = Path("strategies/base.py")
        if base_path.exists():
            content = base_path.read_text(encoding='utf-8')
            assert "V2.3" in content

        manager_path = Path("strategies/strategy_manager.py")
        if manager_path.exists():
            content = manager_path.read_text(encoding='utf-8')
            assert "V2.3" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
