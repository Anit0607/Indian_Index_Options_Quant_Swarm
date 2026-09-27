"""
Options Chain & Strike Selection Matrix.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from quant_engine.config import INSTRUMENT_CONFIGS, InstrumentConfig
from quant_engine.analytics.greeks import Black76Greeks

class OptionsChainStitcher:
    def __init__(self, underlying_symbol: str = "NIFTY"):
        self.symbol = underlying_symbol
        self.config: InstrumentConfig = INSTRUMENT_CONFIGS.get(underlying_symbol, INSTRUMENT_CONFIGS["NIFTY"])

    def get_atm_strike(self, spot_price: float) -> int:
        interval = self.config.strike_interval
        return int(round(spot_price / interval) * interval)

    def generate_chain_snapshot(self, spot_price: float, time_to_expiry_years: float, base_iv: float = 0.14, num_strikes: int = 11) -> pd.DataFrame:
        atm_strike = self.get_atm_strike(spot_price)
        interval = self.config.strike_interval
        half = num_strikes // 2
        strikes = [atm_strike + (i - half) * interval for i in range(num_strikes)]
        rows = []
        r = self.config.risk_free_rate

        for K in strikes:
            moneyness = np.log(K / spot_price)
            ce_iv = max(0.05, base_iv - 0.15 * moneyness)
            pe_iv = max(0.05, base_iv + 0.25 * moneyness)

            ce_price = Black76Greeks.price(spot_price, K, time_to_expiry_years, r, ce_iv, 'CE')
            ce_greeks = Black76Greeks.greeks(spot_price, K, time_to_expiry_years, r, ce_iv, 'CE')
            pe_price = Black76Greeks.price(spot_price, K, time_to_expiry_years, r, pe_iv, 'PE')
            pe_greeks = Black76Greeks.greeks(spot_price, K, time_to_expiry_years, r, pe_iv, 'PE')

            rows.append({
                "strike": K,
                "atm_offset": int((K - atm_strike) / interval),
                "ce_price": round(ce_price, 2), "ce_iv": round(ce_iv, 4),
                "ce_delta": ce_greeks["delta"], "ce_gamma": ce_greeks["gamma"],
                "ce_theta": ce_greeks["theta"], "ce_vega": ce_greeks["vega"],
                "pe_price": round(pe_price, 2), "pe_iv": round(pe_iv, 4),
                "pe_delta": pe_greeks["delta"], "pe_gamma": pe_greeks["gamma"],
                "pe_theta": pe_greeks["theta"], "pe_vega": pe_greeks["vega"],
            })
        return pd.DataFrame(rows)

    def select_strike_by_delta(self, chain_df: pd.DataFrame, target_delta: float, option_type: str) -> Dict[str, Any]:
        col = "ce_delta" if option_type.upper() == 'CE' else "pe_delta"
        target = abs(target_delta) if option_type.upper() == 'CE' else -abs(target_delta)
        idx = (chain_df[col] - target).abs().idxmin()
        return chain_df.loc[idx].to_dict()

    def select_strike_by_offset(self, chain_df: pd.DataFrame, offset: int) -> Dict[str, Any]:
        idx = (chain_df["atm_offset"] - offset).abs().idxmin()
        return chain_df.loc[idx].to_dict()
