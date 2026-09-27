import json
"""
Autonomous Optimization Loop Agent.
Diagnoses underperforming parameters, introduces regime conditioning (India VIX & Trend filters), and stabilizes OOS metrics.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np

class OptimizationLoopAgent:
    def __init__(self):
        pass

    def diagnose_strategy(self, metrics: Dict[str, Any], benchmark: Dict[str, Any]) -> List[str]:
        """
        Identifies why a strategy failed benchmark criteria.
        """
        diagnoses = []
        if metrics.get("profit_factor", 0) < benchmark.get("min_profit_factor", 1.5):
            diagnoses.append("Unfavorable profit factor: Win rate or reward-to-risk ratio is insufficient to cover fees.")
        if metrics.get("cost_drag_pct", 0) > benchmark.get("max_cost_drag_pct", 15.0):
            diagnoses.append("High frictional drag: High frequency of small trades is eroded by STT and exchange fees.")
        if metrics.get("max_drawdown_pct", 0) > benchmark.get("max_drawdown_pct", 10.0):
            diagnoses.append("Excessive drawdown: Strategy suffers continuous losses during choppy/sideways market regimes.")
        if metrics.get("win_rate_pct", 0) < benchmark.get("min_win_rate_pct", 45.0):
            diagnoses.append("Low win rate: Trend signals generating whipsaws in range-bound market conditions.")
        return diagnoses

    def generate_regime_enhancements(self, diagnoses: List[str], current_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Injects quantitative filters to address diagnosed issues.
        """
        optimized = json.loads(json.dumps(current_schema)) # Deep copy
        
        # 1. Address Choppy Regimes -> Add Volatility & ADX / Trend Filter
        optimized["regime_filters"] = {
            "india_vix_filter": {"min_vix": 12.0, "max_vix": 24.0},
            "trend_strength_filter": {"indicator": "ADX", "threshold": 22.0}
        }
        
        # 2. Address Frictional Drag -> Widen targets & reduce noise trades
        optimized["time_and_session_rules"]["timeframe"] = "5m"  # Avoid 1m noise
        optimized["exit_conditions"]["take_profit_ratio"] = 2.5   # Improve R:R
        optimized["exit_conditions"]["trailing_stop"] = True

        return optimized
