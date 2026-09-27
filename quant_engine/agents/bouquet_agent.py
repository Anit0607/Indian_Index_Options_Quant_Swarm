"""
Bouquet Portfolio Allocation Agent.
Computes strategy return correlation matrices, applies Fractional Kelly, and manages risk parity weights.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List

class BouquetPortfolioAgent:
    def __init__(self, total_capital: float = 1000000.0):
        self.total_capital = total_capital

    def calculate_correlation_matrix(self, strategy_returns: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        Computes pairwise correlation matrix across strategies.
        """
        df = pd.DataFrame(strategy_returns)
        return df.corr()

    def allocate_risk_parity_weights(self, strategy_returns: Dict[str, pd.Series]) -> Dict[str, float]:
        """
        Allocates capital inversely proportional to realized volatility (Equal Risk Contribution).
        """
        volatilities = {}
        for name, rets in strategy_returns.items():
            vol = rets.std()
            volatilities[name] = vol if vol > 1e-6 else 1e-3

        inv_vols = {name: 1.0 / v for name, v in volatilities.items()}
        total_inv_vol = sum(inv_vols.values())
        weights = {name: round(inv_v / total_inv_vol, 4) for name, inv_v in inv_vols.items()}
        return weights

    def calculate_fractional_kelly(self, win_rate: float, win_loss_ratio: float, fraction: float = 0.5) -> float:
        """
        Computes Half-Kelly or Quarter-Kelly sizing factor to maximize geometric growth while limiting risk of ruin.
        f* = (p * b - q) / b
        """
        p = win_rate
        q = 1.0 - p
        b = win_loss_ratio
        if b <= 0:
            return 0.0
        full_kelly = (p * b - q) / b
        fractional_kelly = max(0.0, full_kelly * fraction)
        # Cap max risk per strategy at 15% of portfolio
        return round(min(0.15, fractional_kelly), 4)
