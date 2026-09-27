"""
Performance Metrics Suite.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any

class PerformanceMetrics:
    @staticmethod
    def calculate_metrics(trade_log: pd.DataFrame, initial_capital: float = 500000.0, risk_free_rate: float = 0.065) -> Dict[str, Any]:
        if trade_log.empty:
            return {
                "total_trades": 0, "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
                "max_drawdown_pct": 0.0, "calmar_ratio": 0.0, "profit_factor": 0.0,
                "win_rate_pct": 0.0, "expectancy": 0.0, "total_net_pnl": 0.0, "cost_drag_pct": 0.0
            }

        pnl = trade_log["net_pnl"]
        gross_pnl = trade_log["gross_pnl"]
        frictions = trade_log["total_friction"]
        total_trades = len(trade_log)

        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]
        win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0
        gross_profit = wins.sum() if len(wins) > 0 else 0.0
        gross_loss = abs(losses.sum()) if len(losses) > 0 else 0.0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

        equity_curve = initial_capital + pnl.cumsum()
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        max_dd_pct = round(abs(float(drawdown.min())) * 100.0, 2)

        daily_returns = pnl / initial_capital
        daily_rf = risk_free_rate / 252.0
        excess_returns = daily_returns - daily_rf
        mean_excess = excess_returns.mean()
        std_returns = daily_returns.std()
        sharpe = round(float(np.sqrt(252) * (mean_excess / std_returns)), 2) if std_returns > 0 else 0.0

        negative_returns = daily_returns[daily_returns < 0]
        downside_std = negative_returns.std() if len(negative_returns) > 1 else std_returns
        sortino = round(float(np.sqrt(252) * (mean_excess / downside_std)), 2) if downside_std > 0 else 0.0

        total_net_pnl = float(pnl.sum())
        total_return_pct = (total_net_pnl / initial_capital) * 100.0
        calmar = round(total_return_pct / max_dd_pct, 2) if max_dd_pct > 0 else 0.0

        avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
        avg_loss = float(abs(losses.mean())) if len(losses) > 0 else 0.0
        expectancy = round((win_rate / 100.0) * avg_win - ((100.0 - win_rate) / 100.0) * avg_loss, 2)

        total_friction = float(frictions.sum())
        cost_drag_pct = round((total_friction / gross_profit) * 100.0, 2) if gross_profit > 0 else 0.0

        return {
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown_pct": max_dd_pct,
            "calmar_ratio": calmar,
            "expectancy": expectancy,
            "total_net_pnl": round(total_net_pnl, 2),
            "cost_drag_pct": cost_drag_pct
        }
