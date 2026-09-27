"""
Options Backtesting Engine.
"""
import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, Any
from quant_engine.config import INSTRUMENT_CONFIGS, InstrumentConfig
from quant_engine.analytics.greeks import Black76Greeks
from quant_engine.backtest.frictions import IndianFrictionModel
from quant_engine.backtest.metrics import PerformanceMetrics
from quant_engine.data.chain_stitcher import OptionsChainStitcher

class OptionsBacktestEngine:
    def __init__(self, underlying_symbol: str = "NIFTY", initial_capital: float = 500000.0):
        self.symbol = underlying_symbol
        self.config: InstrumentConfig = INSTRUMENT_CONFIGS.get(underlying_symbol, INSTRUMENT_CONFIGS["NIFTY"])
        self.initial_capital = initial_capital
        self.friction_model = IndianFrictionModel()
        self.stitcher = OptionsChainStitcher(underlying_symbol)

    def run_intraday_momentum_test(self, ohlcv_df: pd.DataFrame, fast_ema: int = 9, slow_ema: int = 21, sl_pct: float = 0.20, tp_ratio: float = 2.0) -> Dict[str, Any]:
        df = ohlcv_df.copy()
        df["fast_ema"] = df["close"].ewm(span=fast_ema, adjust=False).mean()
        df["slow_ema"] = df["close"].ewm(span=slow_ema, adjust=False).mean()

        trades = []
        in_position = False
        pos_type = None
        entry_price = 0.0
        entry_time = None
        buy_friction = 0.0
        strike = 0
        qty = self.config.lot_size
        iv = 0.14
        r = self.config.risk_free_rate

        for i in range(1, len(df)):
            prev_row = df.iloc[i - 1]
            row = df.iloc[i]
            cur_time = row["timestamp"].time() if isinstance(row["timestamp"], datetime) else pd.to_datetime(row["timestamp"]).time()
            T = 1.0 / 365.0
            spot = row["close"]

            if not in_position:
                if time(9, 20) <= cur_time <= time(14, 30):
                    if prev_row["fast_ema"] <= prev_row["slow_ema"] and row["fast_ema"] > row["slow_ema"]:
                        strike = self.stitcher.get_atm_strike(spot)
                        entry_opt_price = Black76Greeks.price(spot, strike, T, r, iv, 'CE')
                        if entry_opt_price > 1.0:
                            buy_cost = self.friction_model.calculate_trade_costs(entry_opt_price, qty, 'BUY')
                            in_position = True
                            pos_type = 'CE'
                            entry_price = entry_opt_price
                            entry_time = row["timestamp"]
                            buy_friction = buy_cost.total_costs

                    elif prev_row["fast_ema"] >= prev_row["slow_ema"] and row["fast_ema"] < row["slow_ema"]:
                        strike = self.stitcher.get_atm_strike(spot)
                        entry_opt_price = Black76Greeks.price(spot, strike, T, r, iv, 'PE')
                        if entry_opt_price > 1.0:
                            buy_cost = self.friction_model.calculate_trade_costs(entry_opt_price, qty, 'BUY')
                            in_position = True
                            pos_type = 'PE'
                            entry_price = entry_opt_price
                            entry_time = row["timestamp"]
                            buy_friction = buy_cost.total_costs

            else:
                cur_opt_price = Black76Greeks.price(spot, strike, T, r, iv, pos_type)
                pct_change = (cur_opt_price - entry_price) / entry_price
                exit_triggered = False
                exit_reason = ""

                if pct_change <= -sl_pct:
                    exit_triggered = True
                    exit_reason = "STOP_LOSS"
                elif pct_change >= (sl_pct * tp_ratio):
                    exit_triggered = True
                    exit_reason = "TAKE_PROFIT"
                elif cur_time >= time(15, 15):
                    exit_triggered = True
                    exit_reason = "SQUARE_OFF"

                if exit_triggered:
                    sell_cost = self.friction_model.calculate_trade_costs(cur_opt_price, qty, 'SELL')
                    gross_pnl = (cur_opt_price - entry_price) * qty
                    total_friction = buy_friction + sell_cost.total_costs
                    net_pnl = gross_pnl - total_friction

                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": row["timestamp"],
                        "pos_type": pos_type,
                        "strike": strike,
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(cur_opt_price, 2),
                        "gross_pnl": round(gross_pnl, 2),
                        "total_friction": round(total_friction, 2),
                        "net_pnl": round(net_pnl, 2),
                        "exit_reason": exit_reason
                    })
                    in_position = False

        trades_df = pd.DataFrame(trades)
        metrics = PerformanceMetrics.calculate_metrics(trades_df, self.initial_capital)
        return {"metrics": metrics, "trade_log": trades_df}
