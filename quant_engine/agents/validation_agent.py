"""
Statistical Validation & Anti-Overfitting Agent.
Executes Walk-Forward Analysis (WFA) and calculates Deflated Sharpe Ratio (DSR) per Bailey & Lopez de Prado.
"""
import numpy as np
import pandas as pd
from scipy.stats import norm, skew, kurtosis
from typing import Dict, Any, List, Tuple
from quant_engine.backtest.engine import OptionsBacktestEngine

class StatisticalValidationAgent:
    def __init__(self, engine: OptionsBacktestEngine):
        self.engine = engine

    @staticmethod
    def calculate_deflated_sharpe_ratio(observed_sharpe: float, num_trials: int, variance_sharpe_trials: float, returns_series: pd.Series) -> float:
        """
        Deflated Sharpe Ratio (DSR): Penalizes high Sharpe ratios arising from multiple testing.
        Ref: Bailey & Lopez de Prado (2014)
        """
        if len(returns_series) < 10 or observed_sharpe <= 0:
            return 0.0
        
        N = len(returns_series)
        s = float(skew(returns_series))
        k = float(kurtosis(returns_series, fisher=False)) # Pearson kurtosis (normal=3.0)

        # Expected maximum Sharpe ratio under the null hypothesis of 0 alpha across N trials
        # Euler-Mascheroni constant ~ 0.5772156649
        gamma = 0.5772156649
        if num_trials > 1:
            z_trial = (1.0 - gamma) * norm.ppf(1.0 - 1.0 / num_trials) + gamma * norm.ppf(1.0 - 1.0 / (num_trials * np.e))
            expected_max_sharpe = np.sqrt(variance_sharpe_trials) * z_trial
        else:
            expected_max_sharpe = 0.0

        # Standard error of the annualized Sharpe ratio
        sr_std_err = np.sqrt((1.0 + 0.5 * (observed_sharpe ** 2) - s * observed_sharpe + ((k - 3.0) / 4.0) * (observed_sharpe ** 2)) / (N - 1.0))
        
        if sr_std_err <= 1e-6:
            return 0.5

        z_stat = (observed_sharpe - expected_max_sharpe) / sr_std_err
        dsr_prob = float(norm.cdf(z_stat))
        return round(dsr_prob, 4)

    def run_walk_forward_analysis(self, ohlcv_df: pd.DataFrame, num_windows: int = 3, train_ratio: float = 0.65) -> Dict[str, Any]:
        """
        Splits dataset into sequential rolling Train/Test windows to evaluate out-of-sample stability.
        """
        total_len = len(ohlcv_df)
        window_size = total_len // num_windows
        results = []

        for w in range(num_windows):
            start_idx = w * (window_size // 2)
            end_idx = min(start_idx + window_size, total_len)
            sub_df = ohlcv_df.iloc[start_idx:end_idx]
            
            split_point = int(len(sub_df) * train_ratio)
            in_sample_df = sub_df.iloc[:split_point]
            out_of_sample_df = sub_df.iloc[split_point:]

            is_res = self.engine.run_intraday_momentum_test(in_sample_df)
            oos_res = self.engine.run_intraday_momentum_test(out_of_sample_df)

            results.append({
                "window": w + 1,
                "is_sharpe": is_res["metrics"]["sharpe_ratio"],
                "oos_sharpe": oos_res["metrics"]["sharpe_ratio"],
                "is_win_rate": is_res["metrics"]["win_rate_pct"],
                "oos_win_rate": oos_res["metrics"]["win_rate_pct"],
                "is_max_dd": is_res["metrics"]["max_drawdown_pct"],
                "oos_max_dd": oos_res["metrics"]["max_drawdown_pct"],
                "oos_trades": oos_res["metrics"]["total_trades"]
            })

        summary_df = pd.DataFrame(results)
        oos_persistence = (summary_df["oos_sharpe"] > 0).mean()

        return {
            "windows": results,
            "oos_persistence_rate": round(float(oos_persistence), 2),
            "is_stable": bool(oos_persistence >= 0.50)
        }
