"""
Configuration and Parameters for Indian Index Options Quantitative Engine.
Supports NIFTY, BANKNIFTY, and SENSEX with accurate market specifications and statutory frictions.
"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class InstrumentConfig:
    symbol: str
    exchange: str
    lot_size: int
    strike_interval: int
    tick_size: float = 0.05
    risk_free_rate: float = 0.065

INSTRUMENT_CONFIGS: Dict[str, InstrumentConfig] = {
    "NIFTY": InstrumentConfig(symbol="NIFTY", exchange="NSE", lot_size=25, strike_interval=50),
    "BANKNIFTY": InstrumentConfig(symbol="BANKNIFTY", exchange="NSE", lot_size=15, strike_interval=100),
    "SENSEX": InstrumentConfig(symbol="SENSEX", exchange="BSE", lot_size=10, strike_interval=100),
}

@dataclass(frozen=True)
class StatutoryCostConfig:
    stt_sell_rate: float = 0.0010
    exchange_fee_rate: float = 0.000495
    gst_rate: float = 0.18
    stamp_duty_buy_rate: float = 0.00003
    sebi_turnover_rate: float = 0.000001
    brokerage_per_order: float = 20.0

DEFAULT_COSTS = StatutoryCostConfig()
