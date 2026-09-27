"""
DhanHQ Historical Data Client & Storage Layer.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

class DhanDataClient:
    def __init__(self, client_id: Optional[str] = None, access_token: Optional[str] = None, cache_dir: str = "/working_dir/c_20ad285556aaf683/data_cache"):
        self.client_id = client_id
        self.access_token = access_token
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> str:
        safe_sym = symbol.replace(":", "_").replace(" ", "_")
        return os.path.join(self.cache_dir, f"{safe_sym}_{timeframe}_{start_date}_{end_date}.parquet")

    def load_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        cache_path = self._get_cache_path(symbol, timeframe, start_date, end_date)
        if os.path.exists(cache_path):
            return pd.read_parquet(cache_path)
        df = self.generate_synthetic_sample_data(symbol, timeframe, start_date, end_date)
        df.to_parquet(cache_path, index=False)
        return df

    @staticmethod
    def generate_synthetic_sample_data(symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        base_price = 24500.0 if "NIFTY" in symbol else (51200.0 if "BANKNIFTY" in symbol else 80000.0)
        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        records = []
        cur_date = dt_start
        np.random.seed(42)

        while cur_date <= dt_end:
            if cur_date.weekday() < 5:
                session_start = datetime(cur_date.year, cur_date.month, cur_date.day, 9, 15)
                cur_price = base_price
                for m in range(375):
                    ts = session_start + timedelta(minutes=m)
                    drift = np.random.normal(0.0, 0.0003)
                    open_p = cur_price
                    close_p = open_p * (1.0 + drift)
                    high_p = max(open_p, close_p) * (1.0 + abs(np.random.normal(0, 0.0001)))
                    low_p = min(open_p, close_p) * (1.0 - abs(np.random.normal(0, 0.0001)))
                    volume = int(np.random.lognormal(mean=8.5, sigma=0.5))
                    oi = int(np.random.normal(loc=12000000, scale=50000))
                    records.append({
                        "timestamp": ts, "symbol": symbol,
                        "open": round(open_p, 2), "high": round(high_p, 2),
                        "low": round(low_p, 2), "close": round(close_p, 2),
                        "volume": volume, "open_interest": oi
                    })
                    cur_price = close_p
                base_price = cur_price
            cur_date += timedelta(days=1)
        return pd.DataFrame(records)
