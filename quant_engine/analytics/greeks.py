"""
Institutional Black-76 Greeks & Implied Volatility Engine for European Index Options.
"""
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from typing import Dict, Tuple

class Black76Greeks:
    @staticmethod
    def calc_d1_d2(F: float, K: float, T: float, sigma: float) -> Tuple[float, float]:
        if T <= 0.0 or sigma <= 0.0:
            return 0.0, 0.0
        d1 = (np.log(F / K) + 0.5 * (sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2

    @classmethod
    def price(cls, F: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        if T <= 1e-6:
            return max(0.0, F - K) if option_type.upper() == 'CE' else max(0.0, K - F)
        if sigma <= 1e-4:
            return max(0.0, (F - K) if option_type.upper() == 'CE' else (K - F)) * np.exp(-r * T)

        d1, d2 = cls.calc_d1_d2(F, K, T, sigma)
        discount = np.exp(-r * T)
        if option_type.upper() == 'CE':
            return float(discount * (F * norm.cdf(d1) - K * norm.cdf(d2)))
        elif option_type.upper() == 'PE':
            return float(discount * (K * norm.cdf(-d2) - F * norm.cdf(-d1)))
        else:
            raise ValueError(f"Unknown option_type {option_type}")

    @classmethod
    def greeks(cls, F: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict[str, float]:
        if T <= 1e-6 or sigma <= 1e-4:
            intrinsic_delta = 1.0 if (option_type.upper() == 'CE' and F >= K) else (-1.0 if (option_type.upper() == 'PE' and F <= K) else 0.0)
            return {"delta": intrinsic_delta, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

        d1, d2 = cls.calc_d1_d2(F, K, T, sigma)
        discount = np.exp(-r * T)
        sqrt_T = np.sqrt(T)
        pdf_d1 = norm.pdf(d1)

        delta = discount * norm.cdf(d1) if option_type.upper() == 'CE' else discount * (norm.cdf(d1) - 1.0)
        gamma = (discount * pdf_d1) / (F * sigma * sqrt_T)
        vega_1pct = (discount * F * pdf_d1 * sqrt_T) * 0.01

        theta_common = - (discount * F * pdf_d1 * sigma) / (2.0 * sqrt_T)
        if option_type.upper() == 'CE':
            theta_annual = theta_common + r * discount * (F * norm.cdf(d1) - K * norm.cdf(d2))
        else:
            theta_annual = theta_common - r * discount * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
        theta_daily = theta_annual / 365.0
        rho = (K * T * discount * norm.cdf(d2)) * 0.01 if option_type.upper() == 'CE' else (-K * T * discount * norm.cdf(-d2)) * 0.01

        return {
            "delta": round(float(delta), 4),
            "gamma": round(float(gamma), 6),
            "theta": round(float(theta_daily), 4),
            "vega": round(float(vega_1pct), 4),
            "rho": round(float(rho), 4)
        }

    @classmethod
    def implied_volatility(cls, market_price: float, F: float, K: float, T: float, r: float, option_type: str) -> float:
        if T <= 1e-6:
            return 0.0
        intrinsic = max(0.0, (F - K) if option_type.upper() == 'CE' else (K - F)) * np.exp(-r * T)
        if market_price <= intrinsic:
            return 0.001
        def obj(sig: float) -> float:
            return cls.price(F, K, T, r, sig, option_type) - market_price
        try:
            return round(float(brentq(obj, 1e-4, 5.0, xtol=1e-5, maxiter=100)), 4)
        except (ValueError, RuntimeError):
            return 0.0
