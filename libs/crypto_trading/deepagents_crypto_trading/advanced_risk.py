"""Advanced risk analytics module.

This module provides:
- VaRCalculator: Value at Risk calculation (Historical/Parametric/Monte Carlo)
- StressTester: Stress testing scenarios
- RiskScenarioAnalyzer: Scenario analysis
- CorrelationAnalyzer: Correlation analysis
- RiskReport: Comprehensive risk reports
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class VaRMethod(str, Enum):
    """Value at Risk calculation method."""

    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


@dataclass
class VaRResult:
    """Value at Risk calculation result."""

    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    cvar_95: float  # Conditional VaR at 95%
    cvar_99: float  # Conditional VaR at 99%
    method: VaRMethod
    confidence_level: float = 0.95
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StressResult:
    """Stress test result."""

    scenario: str
    portfolio_value_before: float
    portfolio_value_after: float
    loss: float
    loss_pct: float
    severity: str  # low/medium/high/critical
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskScenario:
    """Risk scenario definition."""

    name: str
    description: str
    market_shock: dict[str, float] = field(default_factory=dict)  # symbol -> price change %
    correlation_change: float = 0.0
    volatility_multiplier: float = 1.0


@dataclass
class RiskReport:
    """Comprehensive risk report."""

    var_result: VaRResult
    stress_results: list[StressResult] = field(default_factory=list)
    max_drawdown: float = 0.0
    beta: float = 0.0
    correlation: dict[str, float] = field(default_factory=dict)
    risk_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class VaRCalculator:
    """Value at Risk (VaR) calculator.

    Supports multiple calculation methods:
    - Historical: Uses historical returns distribution
    - Parametric: Assumes normal distribution
    - Monte Carlo: Uses simulation
    """

    def __init__(self, confidence: float = 0.95) -> None:
        """Initialize VaR calculator.

        Args:
            confidence: Confidence level (default 95%).
        """
        self.confidence = confidence

    def calculate(
        self,
        returns: list[float],
        portfolio_value: float,
        method: VaRMethod = VaRMethod.HISTORICAL,
    ) -> VaRResult:
        """Calculate VaR.

        Args:
            returns: List of historical returns.
            portfolio_value: Current portfolio value.
            method: Calculation method.

        Returns:
            VaR result.
        """
        if not returns:
            return VaRResult(
                var_95=0.0,
                var_99=0.0,
                cvar_95=0.0,
                cvar_99=0.0,
                method=method,
                confidence_level=self.confidence,
            )

        if method == VaRMethod.HISTORICAL:
            return self._calculate_historical(returns, portfolio_value)
        elif method == VaRMethod.PARAMETRIC:
            return self._calculate_parametric(returns, portfolio_value)
        else:
            return self._calculate_monte_carlo(returns, portfolio_value)

    def _calculate_historical(
        self,
        returns: list[float],
        portfolio_value: float,
    ) -> VaRResult:
        """Calculate historical VaR."""
        returns_array = np.array(returns)

        # 95% VaR
        var_95 = np.percentile(returns_array, 5)
        var_95_value = abs(var_95) * portfolio_value

        # 99% VaR
        var_99 = np.percentile(returns_array, 1)
        var_99_value = abs(var_99) * portfolio_value

        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns_array[returns_array <= var_95].mean()
        cvar_95_value = abs(cvar_95) * portfolio_value if not np.isnan(cvar_95) else 0

        cvar_99 = returns_array[returns_array <= var_99].mean()
        cvar_99_value = abs(cvar_99) * portfolio_value if not np.isnan(cvar_99) else 0

        return VaRResult(
            var_95=var_95_value,
            var_99=var_99_value,
            cvar_95=cvar_95_value,
            cvar_99=cvar_99_value,
            method=VaRMethod.HISTORICAL,
            confidence_level=self.confidence,
        )

    def _calculate_parametric(
        self,
        returns: list[float],
        portfolio_value: float,
    ) -> VaRResult:
        """Calculate parametric VaR (Normal distribution)."""
        returns_array = np.array(returns)

        # Calculate mean and std
        mu = np.mean(returns_array)
        sigma = np.std(returns_array)

        # Z-scores for confidence levels
        z_95 = 1.645  # 95%
        z_99 = 2.326  # 99%

        # VaR using normal distribution
        var_95_value = (mu + z_95 * sigma) * portfolio_value
        var_99_value = (mu + z_99 * sigma) * portfolio_value

        # Conditional VaR (Expected Shortfall for normal)
        cvar_95_value = mu - z_95 * sigma
        cvar_95_value = abs(cvar_95_value) * portfolio_value

        cvar_99_value = mu - z_99 * sigma
        cvar_99_value = abs(cvar_99_value) * portfolio_value

        return VaRResult(
            var_95=var_95_value,
            var_99=var_99_value,
            cvar_95=cvar_95_value,
            cvar_99=cvar_99_value,
            method=VaRMethod.PARAMETRIC,
            confidence_level=self.confidence,
        )

    def _calculate_monte_carlo(
        self,
        returns: list[float],
        portfolio_value: float,
        num_simulations: int = 10000,
    ) -> VaRResult:
        """Calculate Monte Carlo VaR."""
        returns_array = np.array(returns)

        # Fit distribution
        mu = np.mean(returns_array)
        sigma = np.std(returns_array)

        # Generate simulations
        np.random.seed(42)
        simulated_returns = np.random.normal(mu, sigma, num_simulations)

        # Calculate VaR from simulations
        var_95 = np.percentile(simulated_returns, 5)
        var_99 = np.percentile(simulated_returns, 1)

        var_95_value = abs(var_95) * portfolio_value
        var_99_value = abs(var_99) * portfolio_value

        # Conditional VaR
        cvar_95 = simulated_returns[simulated_returns <= var_95].mean()
        cvar_99 = simulated_returns[simulated_returns <= var_99].mean()

        cvar_95_value = abs(cvar_95) * portfolio_value
        cvar_99_value = abs(cvar_99) * portfolio_value

        return VaRResult(
            var_95=var_95_value,
            var_99=var_99_value,
            cvar_95=cvar_95_value,
            cvar_99=cvar_99_value,
            method=VaRMethod.MONTE_CARLO,
            confidence_level=self.confidence,
        )


class StressTester:
    """Stress tester for portfolio scenarios."""

    def __init__(self) -> None:
        """Initialize stress tester."""
        self._scenarios = self._get_default_scenarios()

    def _get_default_scenarios(self) -> list[RiskScenario]:
        """Get default stress scenarios."""
        return [
            RiskScenario(
                name="Market Crash",
                description="20% market drop",
                market_shock={"BTCUSDT": -20.0, "ETHUSDT": -25.0, "SOLUSDT": -30.0},
                correlation_change=0.5,
                volatility_multiplier=2.0,
            ),
            RiskScenario(
                name="Crypto Winter",
                description="50% prolonged bear market",
                market_shock={"BTCUSDT": -50.0, "ETHUSDT": -60.0, "SOLUSDT": -70.0},
                correlation_change=0.8,
                volatility_multiplier=3.0,
            ),
            RiskScenario(
                name="Flash Crash",
                description="30% intraday crash",
                market_shock={"BTCUSDT": -30.0, "ETHUSDT": -35.0, "SOLUSDT": -40.0},
                correlation_change=0.3,
                volatility_multiplier=4.0,
            ),
            RiskScenario(
                name="High Volatility",
                description="High volatility period",
                market_shock={"BTCUSDT": -10.0, "ETHUSDT": -15.0, "SOLUSDT": -20.0},
                correlation_change=0.6,
                volatility_multiplier=3.0,
            ),
            RiskScenario(
                name="Bull Market Correction",
                description="10% correction in bull market",
                market_shock={"BTCUSDT": -10.0, "ETHUSDT": -12.0, "SOLUSDT": -15.0},
                correlation_change=0.2,
                volatility_multiplier=1.5,
            ),
        ]

    def run_stress_test(
        self,
        portfolio_value: float,
        positions: dict[str, float],  # symbol -> value
        scenario: Optional[RiskScenario] = None,
    ) -> StressResult:
        """Run stress test.

        Args:
            portfolio_value: Current portfolio value.
            positions: Position values per symbol.
            scenario: Specific scenario (uses default if None).

        Returns:
            Stress test result.
        """
        if scenario is None:
            # Use worst-case scenario
            scenario = self._scenarios[0]  # Market Crash

        # Calculate new portfolio value
        new_portfolio_value = portfolio_value

        for symbol, value in positions.items():
            shock = scenario.market_shock.get(symbol, -10.0)
            new_value = value * (1 + shock / 100)
            new_portfolio_value += new_value - value

        loss = portfolio_value - new_portfolio_value
        loss_pct = (loss / portfolio_value * 100) if portfolio_value > 0 else 0

        # Determine severity
        if loss_pct < 5:
            severity = "low"
        elif loss_pct < 15:
            severity = "medium"
        elif loss_pct < 30:
            severity = "high"
        else:
            severity = "critical"

        return StressResult(
            scenario=scenario.name,
            portfolio_value_before=portfolio_value,
            portfolio_value_after=new_portfolio_value,
            loss=loss,
            loss_pct=loss_pct,
            severity=severity,
        )

    def run_all_scenarios(
        self,
        portfolio_value: float,
        positions: dict[str, float],
    ) -> list[StressResult]:
        """Run all stress scenarios.

        Args:
            portfolio_value: Current portfolio value.
            positions: Position values per symbol.

        Returns:
            List of stress test results.
        """
        results = []
        for scenario in self._scenarios:
            result = self.run_stress_test(portfolio_value, positions, scenario)
            results.append(result)
        return results

    def get_worst_case(
        self,
        portfolio_value: float,
        positions: dict[str, float],
    ) -> StressResult:
        """Get worst-case scenario.

        Args:
            portfolio_value: Current portfolio value.
            positions: Position values per symbol.

        Returns:
            Worst-case stress result.
        """
        results = self.run_all_scenarios(portfolio_value, positions)
        worst = max(results, key=lambda r: r.loss)
        return worst


class CorrelationAnalyzer:
    """Portfolio correlation analyzer."""

    def __init__(self) -> None:
        """Initialize correlation analyzer."""
        self._correlations: dict[tuple[str, str], float] = {}

    def calculate_correlation(
        self,
        returns1: list[float],
        returns2: list[float],
    ) -> float:
        """Calculate correlation between two return series.

        Args:
            returns1: First return series.
            returns2: Second return series.

        Returns:
            Correlation coefficient (-1 to 1).
        """
        if len(returns1) != len(returns2) or not returns1:
            return 0.0

        arr1 = np.array(returns1)
        arr2 = np.array(returns2)

        correlation = np.corrcoef(arr1, arr2)[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0

    def calculate_portfolio_correlation(
        self,
        returns: dict[str, list[float]],  # symbol -> returns
    ) -> dict[tuple[str, str], float]:
        """Calculate correlation matrix for portfolio.

        Args:
            returns: Returns per symbol.

        Returns:
            Dictionary of correlations.
        """
        correlations = {}
        symbols = list(returns.keys())

        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i + 1:]:
                corr = self.calculate_correlation(
                    returns.get(sym1, []),
                    returns.get(sym2, []),
                )
                correlations[(sym1, sym2)] = corr
                correlations[(sym2, sym1)] = corr

        self._correlations = correlations
        return correlations

    def get_beta(
        self,
        asset_returns: list[float],
        market_returns: list[float],
    ) -> float:
        """Calculate beta relative to market.

        Args:
            asset_returns: Asset returns.
            market_returns: Market returns.

        Returns:
            Beta coefficient.
        """
        if not asset_returns or not market_returns:
            return 0.0

        arr_asset = np.array(asset_returns)
        arr_market = np.array(market_returns)

        # Calculate beta = Cov(asset, market) / Var(market)
        covariance = np.cov(arr_asset, arr_market)[0, 1]
        variance = np.var(arr_market)

        beta = covariance / variance if variance > 0 else 0.0
        return float(beta)


class RiskScenarioAnalyzer:
    """Risk scenario analyzer."""

    def __init__(self) -> None:
        """Initialize analyzer."""
        self.var_calculator = VaRCalculator()
        self.stress_tester = StressTester()
        self.correlation_analyzer = CorrelationAnalyzer()

    def analyze(
        self,
        returns: dict[str, list[float]],
        portfolio_value: float,
        positions: dict[str, float],
    ) -> RiskReport:
        """Run comprehensive risk analysis.

        Args:
            returns: Returns per symbol.
            portfolio_value: Portfolio value.
            positions: Positions per symbol.

        Returns:
            Risk report.
        """
        # Calculate overall returns
        all_returns = []
        for ret_list in returns.values():
            all_returns.extend(ret_list)

        # VaR calculation
        var_result = self.var_calculator.calculate(
            all_returns,
            portfolio_value,
            VaRMethod.HISTORICAL,
        )

        # Stress testing
        stress_results = self.stress_tester.run_all_scenarios(
            portfolio_value,
            positions,
        )

        # Max drawdown
        max_dd = self._calculate_max_drawdown(portfolio_value, all_returns)

        # Correlations
        correlations = self.correlation_analyzer.calculate_portfolio_correlation(returns)

        # Risk score (0-100)
        risk_score = self._calculate_risk_score(var_result, stress_results, max_dd)

        return RiskReport(
            var_result=var_result,
            stress_results=stress_results,
            max_drawdown=max_dd,
            correlation=correlations,
            risk_score=risk_score,
        )

    def _calculate_max_drawdown(
        self,
        initial_value: float,
        returns: list[float],
    ) -> float:
        """Calculate maximum drawdown."""
        if not returns:
            return 0.0

        equity = initial_value
        peak = equity
        max_dd = 0.0

        for ret in returns:
            equity *= (1 + ret)
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)

        return max_dd * 100

    def _calculate_risk_score(
        self,
        var_result: VaRResult,
        stress_results: list[StressResult],
        max_drawdown: float,
    ) -> float:
        """Calculate overall risk score (0-100)."""
        # Higher score = higher risk
        score = 0.0

        # VaR contribution (40%)
        if var_result.var_99 > 0:
            score += min(40, var_result.var_99 / 100)

        # Stress test contribution (40%)
        if stress_results:
            worst_loss = max(s.loss_pct for s in stress_results)
            score += min(40, worst_loss)

        # Max drawdown contribution (20%)
        score += min(20, max_drawdown / 5)

        return min(100, score)


class AdvancedRiskAnalytics:
    """Advanced risk analytics module.

    Provides comprehensive risk analysis including:
    - VaR (Value at Risk)
    - Stress testing
    - Scenario analysis
    - Correlation analysis
    """

    def __init__(self) -> None:
        """Initialize analytics."""
        self.var_calculator = VaRCalculator()
        self.stress_tester = StressTester()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.scenario_analyzer = RiskScenarioAnalyzer()

    def calculate_var(
        self,
        returns: list[float],
        portfolio_value: float,
        method: VaRMethod = VaRMethod.HISTORICAL,
    ) -> VaRResult:
        """Calculate Value at Risk.

        Args:
            returns: Historical returns.
            portfolio_value: Portfolio value.
            method: Calculation method.

        Returns:
            VaR result.
        """
        return self.var_calculator.calculate(returns, portfolio_value, method)

    def run_stress_test(
        self,
        portfolio_value: float,
        positions: dict[str, float],
        scenario: Optional[RiskScenario] = None,
    ) -> StressResult:
        """Run stress test.

        Args:
            portfolio_value: Portfolio value.
            positions: Positions per symbol.
            scenario: Scenario to test.

        Returns:
            Stress test result.
        """
        return self.stress_tester.run_stress_test(
            portfolio_value,
            positions,
            scenario,
        )

    def get_correlation(
        self,
        returns1: list[float],
        returns2: list[float],
    ) -> float:
        """Calculate correlation.

        Args:
            returns1: First return series.
            returns2: Second return series.

        Returns:
            Correlation coefficient.
        """
        return self.correlation_analyzer.calculate_correlation(returns1, returns2)

    def analyze_portfolio(
        self,
        returns: dict[str, list[float]],
        portfolio_value: float,
        positions: dict[str, float],
    ) -> RiskReport:
        """Analyze portfolio risk.

        Args:
            returns: Returns per symbol.
            portfolio_value: Portfolio value.
            positions: Positions per symbol.

        Returns:
            Risk report.
        """
        return self.scenario_analyzer.analyze(returns, portfolio_value, positions)

    def get_risk_summary(self, report: RiskReport) -> dict:
        """Get risk summary.

        Args:
            report: Risk report.

        Returns:
            Summary dictionary.
        """
        return {
            "var_95": report.var_result.var_95,
            "var_99": report.var_result.var_99,
            "cvar_95": report.var_result.cvar_95,
            "cvar_99": report.var_result.cvar_99,
            "max_drawdown": report.max_drawdown,
            "risk_score": report.risk_score,
            "worst_stress": max(r.loss_pct for r in report.stress_results) if report.stress_results else 0,
        }