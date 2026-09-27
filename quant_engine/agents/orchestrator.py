"""
Master Trading Swarm Orchestrator.
Coordinates the complete lifecycle: Extraction -> Coder -> Validation -> Optimization -> Bouquet -> RMS Execution.
"""
from typing import Dict, Any
import pandas as pd
from quant_engine.agents.extraction_agent import StrategyExtractionAgent
from quant_engine.agents.coder_agent import StrategyCoderAgent
from quant_engine.agents.validation_agent import StatisticalValidationAgent
from quant_engine.agents.optimization_agent import OptimizationLoopAgent
from quant_engine.agents.bouquet_agent import BouquetPortfolioAgent
from quant_engine.agents.execution_agent import ExecutionRMSAgent
from quant_engine.backtest.engine import OptionsBacktestEngine

class TradingSwarmOrchestrator:
    def __init__(self, underlying: str = "NIFTY", initial_capital: float = 500000.0):
        self.engine = OptionsBacktestEngine(underlying, initial_capital)
        self.extractor = StrategyExtractionAgent()
        self.coder = StrategyCoderAgent()
        self.validator = StatisticalValidationAgent(self.engine)
        self.optimizer = OptimizationLoopAgent()
        self.bouquet = BouquetPortfolioAgent(initial_capital)
        self.rms = ExecutionRMSAgent(initial_capital)

    def process_strategy_pipeline(self, raw_input_text: str, ohlcv_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes end-to-end multi-agent pipeline.
        """
        # Step 1: Extraction
        extracted = self.extractor.extract_from_text(raw_input_text)
        schema = extracted["schema"]

        # Step 2: Code Generation & Static Lookahead Audit
        code = self.coder.generate_strategy_code(schema)
        audit = self.coder.audit_code_for_lookahead_bias(code)

        # Step 3: Statistical Validation (WFA & DSR)
        wfa_results = self.validator.run_walk_forward_analysis(ohlcv_df, num_windows=3)
        base_backtest = self.engine.run_intraday_momentum_test(ohlcv_df)

        # Step 4: Optimization Diagnosis
        benchmark = {"min_profit_factor": 1.5, "max_drawdown_pct": 10.0, "min_win_rate_pct": 45.0, "max_cost_drag_pct": 15.0}
        diagnoses = self.optimizer.diagnose_strategy(base_backtest["metrics"], benchmark)
        enhanced_schema = self.optimizer.generate_regime_enhancements(diagnoses, schema) if diagnoses else schema

        # Step 5: Bouquet Sizing
        sample_win_rate = base_backtest["metrics"]["win_rate_pct"] / 100.0
        fractional_kelly_weight = self.bouquet.calculate_fractional_kelly(sample_win_rate, win_loss_ratio=1.5, fraction=0.5)

        # Step 6: RMS Check & HITL Ticket
        rms_ok, rms_msg = self.rms.check_rms_limits(proposed_margin=25000.0, proposed_risk=1500.0)
        hitl_ticket = self.rms.generate_sebi_hitl_ticket(
            symbol=schema["universe_definition"]["underlying"],
            option_type="CE",
            strike=24500,
            qty=25,
            price=120.0,
            sl_price=96.0,
            tp_price=168.0,
            required_margin=25000.0
        ) if rms_ok else None

        return {
            "strategy_id": schema["strategy_metadata"]["strategy_id"],
            "extraction_status": "VALID" if extracted["validation_report"]["is_valid"] else "INVALID",
            "lookahead_audit": audit,
            "wfa_validation": wfa_results,
            "metrics": base_backtest["metrics"],
            "diagnoses": diagnoses,
            "fractional_kelly_allocation": fractional_kelly_weight,
            "rms_status": rms_msg,
            "hitl_ticket": hitl_ticket
        }
