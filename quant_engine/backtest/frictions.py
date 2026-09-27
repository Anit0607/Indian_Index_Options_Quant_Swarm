"""
Indian Regulatory Statutory Frictions & Slippage Calculator.
"""
from dataclasses import dataclass
from quant_engine.config import StatutoryCostConfig, DEFAULT_COSTS

@dataclass
class TradeCostBreakdown:
    gross_turnover: float
    stt: float
    exchange_charges: float
    sebi_charges: float
    stamp_duty: float
    brokerage: float
    gst: float
    total_costs: float
    net_cash_flow: float

class IndianFrictionModel:
    def __init__(self, config: StatutoryCostConfig = DEFAULT_COSTS):
        self.config = config

    def calculate_trade_costs(self, price: float, quantity: int, side: str, slippage_points: float = 0.20) -> TradeCostBreakdown:
        side_upper = side.upper()
        if side_upper == 'BUY':
            exec_price = price + slippage_points
            turnover = exec_price * quantity
            stamp_duty = turnover * self.config.stamp_duty_buy_rate
            stt = 0.0
        elif side_upper == 'SELL':
            exec_price = max(0.05, price - slippage_points)
            turnover = exec_price * quantity
            stamp_duty = 0.0
            stt = turnover * self.config.stt_sell_rate
        else:
            raise ValueError(f"side must be 'BUY' or 'SELL', got {side}")

        exchange_charges = turnover * self.config.exchange_fee_rate
        sebi_charges = turnover * self.config.sebi_turnover_rate
        brokerage = self.config.brokerage_per_order
        taxable_services = brokerage + exchange_charges + sebi_charges
        gst = taxable_services * self.config.gst_rate
        total_costs = stt + exchange_charges + sebi_charges + stamp_duty + brokerage + gst

        if side_upper == 'BUY':
            net_cash_flow = - (turnover + total_costs)
        else:
            net_cash_flow = turnover - total_costs

        return TradeCostBreakdown(
            gross_turnover=round(turnover, 2),
            stt=round(stt, 2),
            exchange_charges=round(exchange_charges, 2),
            sebi_charges=round(sebi_charges, 2),
            stamp_duty=round(stamp_duty, 2),
            brokerage=round(brokerage, 2),
            gst=round(gst, 2),
            total_costs=round(total_costs, 2),
            net_cash_flow=round(net_cash_flow, 2)
        )
