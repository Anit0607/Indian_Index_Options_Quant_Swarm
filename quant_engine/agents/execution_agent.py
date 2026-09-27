"""
Execution & Risk Management System (RMS) Agent.
Enforces non-negotiable hard circuit breakers (-2% daily loss, 70% margin ceiling) and SEBI HITL approval cards.
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

class ExecutionRMSAgent:
    def __init__(self, total_equity: float = 500000.0, max_daily_loss_pct: float = 2.0, max_margin_utilization_pct: float = 70.0):
        self.total_equity = total_equity
        self.max_daily_loss = total_equity * (max_daily_loss_pct / 100.0)
        self.max_margin_utilization = total_equity * (max_margin_utilization_pct / 100.0)
        self.current_daily_pnl = 0.0
        self.current_utilized_margin = 0.0
        self.kill_switch_active = False

    def check_rms_limits(self, proposed_margin: float, proposed_risk: float) -> Tuple[bool, str]:
        """
        Deterministic safety gatekeeper before any trade ticket is generated.
        """
        if self.kill_switch_active:
            return False, "BLOCKED: Emergency Kill-Switch is active."

        if self.current_daily_pnl <= -self.max_daily_loss:
            self.trigger_kill_switch("Daily maximum loss limit (-2.0% equity) breached.")
            return False, f"BLOCKED: Daily loss limit (Rs {self.max_daily_loss}) breached."

        if (self.current_utilized_margin + proposed_margin) > self.max_margin_utilization:
            return False, f"BLOCKED: Margin ceiling ({self.max_margin_utilization_pct}%) would be exceeded."

        return True, "APPROVED: Pre-trade RMS checks passed."

    def trigger_kill_switch(self, reason: str):
        self.kill_switch_active = True
        print(f"[CRITICAL RMS] KILL-SWITCH TRIGGERED: {reason}")

    def generate_sebi_hitl_ticket(self, symbol: str, option_type: str, strike: int, qty: int, price: float, sl_price: float, tp_price: float, required_margin: float) -> Dict[str, Any]:
        """
        Generates SEBI-compliant Human-in-the-Loop trade confirmation payload.
        """
        max_loss = round(abs(price - sl_price) * qty, 2)
        expected_profit = round(abs(tp_price - price) * qty, 2)
        
        ticket = {
            "ticket_id": f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{strike}_{option_type}",
            "status": "AWAITING_HUMAN_CONFIRMATION",
            "compliance_type": "SEBI_DISCRETIONARY_HITL",
            "order_details": {
                "symbol": symbol,
                "contract": f"{symbol} {strike} {option_type}",
                "transaction_type": "BUY",
                "quantity": qty,
                "estimated_price": price,
                "stop_loss_trigger": sl_price,
                "take_profit_target": tp_price,
                "required_margin": required_margin,
                "maximum_risk_amount": max_loss,
                "target_reward_amount": expected_profit
            },
            "timestamp": datetime.now().isoformat()
        }
        return ticket
