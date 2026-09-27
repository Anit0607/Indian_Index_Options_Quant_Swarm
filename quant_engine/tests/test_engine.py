import unittest
import numpy as np
import pandas as pd
from quant_engine.config import INSTRUMENT_CONFIGS, StatutoryCostConfig
from quant_engine.analytics.greeks import Black76Greeks
from quant_engine.backtest.frictions import IndianFrictionModel
from quant_engine.data.chain_stitcher import OptionsChainStitcher
from quant_engine.data.dhan_client import DhanDataClient

class TestQuantEngine(unittest.TestCase):
    def test_put_call_parity(self):
        F = 24500.0
        K = 24500.0
        T = 7.0 / 365.0
        r = 0.065
        sigma = 0.14
        
        ce_price = Black76Greeks.price(F, K, T, r, sigma, 'CE')
        pe_price = Black76Greeks.price(F, K, T, r, sigma, 'PE')
        
        expected_diff = np.exp(-r * T) * (F - K)
        actual_diff = ce_price - pe_price
        self.assertAlmostEqual(actual_diff, expected_diff, places=2)

    def test_greeks_properties(self):
        F = 24500.0
        K = 24500.0
        T = 5.0 / 365.0
        r = 0.065
        sigma = 0.15

        ce_greeks = Black76Greeks.greeks(F, K, T, r, sigma, 'CE')
        pe_greeks = Black76Greeks.greeks(F, K, T, r, sigma, 'PE')

        self.assertTrue(0.48 <= ce_greeks["delta"] <= 0.53)
        self.assertTrue(-0.53 <= pe_greeks["delta"] <= -0.48)
        self.assertGreater(ce_greeks["gamma"], 0.0)
        self.assertGreater(ce_greeks["vega"], 0.0)
        self.assertLess(ce_greeks["theta"], 0.0)
        self.assertLess(pe_greeks["theta"], 0.0)

    def test_iv_solver(self):
        F = 24500.0
        K = 24600.0
        T = 10.0 / 365.0
        r = 0.065
        target_iv = 0.185

        ce_price = Black76Greeks.price(F, K, T, r, target_iv, 'CE')
        solved_iv = Black76Greeks.implied_volatility(ce_price, F, K, T, r, 'CE')
        self.assertAlmostEqual(solved_iv, target_iv, places=3)

    def test_indian_frictions(self):
        friction = IndianFrictionModel()
        cost = friction.calculate_trade_costs(price=100.0, quantity=25, side='SELL', slippage_points=0.0)
        
        self.assertEqual(cost.gross_turnover, 2500.0)
        self.assertEqual(cost.stt, 2.50)
        self.assertEqual(cost.brokerage, 20.0)
        self.assertEqual(cost.exchange_charges, 1.24)
        self.assertGreater(cost.gst, 0.0)
        self.assertGreater(cost.total_costs, 25.0)

    def test_chain_stitcher(self):
        stitcher = OptionsChainStitcher("NIFTY")
        chain = stitcher.generate_chain_snapshot(spot_price=24500.0, time_to_expiry_years=5/365.0, base_iv=0.14)
        
        self.assertEqual(len(chain), 11)
        atm_row = stitcher.select_strike_by_offset(chain, 0)
        self.assertEqual(atm_row["strike"], 24500)
        
        delta_strike = stitcher.select_strike_by_delta(chain, target_delta=0.50, option_type='CE')
        self.assertEqual(delta_strike["strike"], 24500)
        self.assertAlmostEqual(delta_strike["ce_delta"], 0.50, delta=0.03)

if __name__ == '__main__':
    unittest.main()
