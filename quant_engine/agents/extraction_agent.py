"""
Multimodal Strategy Extraction Agent.
Parses unstructured descriptions, YouTube transcripts, and research papers into strict YAML/JSON schema.
"""
import re
import json
import yaml
from typing import Dict, Any, Tuple, List, Optional

class StrategyExtractionAgent:
    def __init__(self):
        self.supported_underlyings = ["NIFTY", "BANKNIFTY", "SENSEX"]
        self.supported_horizons = ["INTRADAY", "POSITIONAL"]

    def extract_from_text(self, text: str, source_metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Parses unstructured strategy text and extracts structured trading parameters.
        """
        text_upper = text.upper()
        
        # 1. Underlying detection
        underlying = "NIFTY"
        if "BANKNIFTY" in text_upper or "BANK NIFTY" in text_upper:
            underlying = "BANKNIFTY"
        elif "SENSEX" in text_upper:
            underlying = "SENSEX"

        # 2. Horizon detection
        horizon = "INTRADAY"
        if "POSITIONAL" in text_upper or "SWING" in text_upper or "CARRY" in text_upper:
            horizon = "POSITIONAL"

        # 3. Timeframe detection
        timeframe = "5m"
        if "15 MIN" in text_upper or "15M" in text_upper:
            timeframe = "15m"
        elif "1 MIN" in text_upper or "1M" in text_upper:
            timeframe = "1m"
        elif "DAILY" in text_upper:
            timeframe = "DAILY"

        # 4. Indicators detection (EMA, RSI, Supertrend, etc.)
        fast_ema = 9
        slow_ema = 21
        ema_match = re.search(r'(\d+)\s*(?:AND|&|,|-)?\s*(\d+)?\s*EMA', text_upper)
        if ema_match:
            try:
                fast_ema = int(ema_match.group(1))
                if ema_match.group(2):
                    slow_ema = int(ema_match.group(2))
            except (ValueError, TypeError):
                pass

        # 5. Strike selection
        strike_mode = "ATM_OFFSET"
        offset = 0
        if "OTM" in text_upper:
            strike_mode = "OTM"
            offset = 1
        elif "ITM" in text_upper:
            strike_mode = "ITM"
            offset = -1

        # 6. Stop Loss & Take Profit
        sl_pct = 20.0
        sl_match = re.search(r'STOP\s*LOSS.*?(\d+)\s*%', text_upper)
        if sl_match:
            sl_pct = float(sl_match.group(1))

        tp_ratio = 2.0
        tp_match = re.search(r'1\s*:\s*(\d+(?:\.\d+)?)', text_upper)
        if tp_match:
            tp_ratio = float(tp_match.group(1))

        # Build Standardized Schema
        schema = {
            "schema_version": "1.0",
            "strategy_metadata": {
                "strategy_id": f"STRAT_{underlying}_{horizon}_{fast_ema}_{slow_ema}",
                "name": f"{underlying} {horizon} {fast_ema}-{slow_ema} EMA Momentum",
                "source": (source_metadata or {}).get("source_url", "manual_input"),
                "horizon": horizon,
                "asset_class": "INDEX_OPTIONS"
            },
            "universe_definition": {
                "underlying": underlying,
                "exchange": "NSE" if underlying in ["NIFTY", "BANKNIFTY"] else "BSE",
                "instrument_type": "OPTIDX",
                "expiry_preference": "CURRENT_WEEK",
                "contract_selection": {
                    "strike_selection_mode": strike_mode,
                    "target_delta": 0.50 if offset == 0 else (0.35 if offset > 0 else 0.65),
                    "atm_offset_strikes": offset,
                    "option_type": "DYNAMIC"
                }
            },
            "time_and_session_rules": {
                "timeframe": timeframe,
                "entry_window_start": "09:20:00",
                "entry_window_end": "14:30:00" if horizon == "INTRADAY" else "15:00:00",
                "hard_square_off_time": "15:15:00" if horizon == "INTRADAY" else "EXPIRY_DAY_15:15:00"
            },
            "indicators": {
                "fast_ema": fast_ema,
                "slow_ema": slow_ema
            },
            "entry_conditions": [
                {"signal": "BULLISH_CROSSOVER", "action": "BUY_CALL"},
                {"signal": "BEARISH_CROSSOVER", "action": "BUY_PUT"}
            ],
            "exit_conditions": {
                "stop_loss_pct": sl_pct,
                "take_profit_ratio": tp_ratio,
                "trailing_stop": True
            },
            "risk_and_money_management": {
                "max_risk_percent_per_trade": 1.5,
                "max_trades_per_day": 4,
                "daily_portfolio_stop_loss_pct": 2.0
            }
        }
        
        validation_report = self.validate_schema(schema)
        return {
            "schema": schema,
            "validation_report": validation_report
        }

    def validate_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        
        meta = schema.get("strategy_metadata", {})
        if not meta.get("strategy_id"):
            errors.append("Missing strategy_id")
        if meta.get("horizon") not in self.supported_horizons:
            errors.append(f"Invalid horizon: {meta.get('horizon')}")

        univ = schema.get("universe_definition", {})
        if univ.get("underlying") not in self.supported_underlyings:
            errors.append(f"Invalid underlying: {univ.get('underlying')}")

        exit_c = schema.get("exit_conditions", {})
        if not exit_c.get("stop_loss_pct"):
            errors.append("Missing stop_loss_pct in exit conditions")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
