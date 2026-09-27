"""
Strategy Code Generator and Static Lookahead Bias Auditor.
Converts YAML/JSON schema into executable backtesting strategy classes and audits for leakage.
"""
import ast
import inspect
from typing import Dict, Any, List

class StaticLookaheadAuditor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []

    def visit_Call(self, node):
        # Detect shift(-1) or future indexing
        if isinstance(node.func, ast.Attribute) and node.func.attr == "shift":
            for arg in node.args:
                if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                    self.violations.append(f"Lookahead bias detected: negative shift '{ast.unparse(node)}' at line {node.lineno}")
                elif isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)) and arg.value < 0:
                    self.violations.append(f"Lookahead bias detected: negative shift '{ast.unparse(node)}' at line {node.lineno}")
        self.generic_visit(node)

class StrategyCoderAgent:
    def __init__(self):
        pass

    def generate_strategy_code(self, schema: Dict[str, Any]) -> str:
        """
        Generates Python code implementing the strategy rules.
        """
        meta = schema.get("strategy_metadata", {})
        univ = schema.get("universe_definition", {})
        ind = schema.get("indicators", {})
        exit_rules = schema.get("exit_conditions", {})

        code = f"""
# Generated Strategy: {meta.get('name', 'CustomStrategy')}
# Strategy ID: {meta.get('strategy_id')}
import pandas as pd
import numpy as np

class GeneratedOptionsStrategy:
    def __init__(self):
        self.strategy_id = "{meta.get('strategy_id')}"
        self.underlying = "{univ.get('underlying')}"
        self.fast_ema = {ind.get('fast_ema', 9)}
        self.slow_ema = {ind.get('slow_ema', 21)}
        self.sl_pct = {exit_rules.get('stop_loss_pct', 20.0) / 100.0}
        self.tp_ratio = {exit_rules.get('take_profit_ratio', 2.0)}

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        # Vectorized EMA calculation without future lookahead
        data['fast_ema'] = data['close'].ewm(span=self.fast_ema, adjust=False).mean()
        data['slow_ema'] = data['close'].ewm(span=self.slow_ema, adjust=False).mean()

        data['signal'] = 0
        # Signal on current bar based strictly on confirmed prior close
        bullish = (data['fast_ema'] > data['slow_ema']) & (data['fast_ema'].shift(1) <= data['slow_ema'].shift(1))
        bearish = (data['fast_ema'] < data['slow_ema']) & (data['fast_ema'].shift(1) >= data['slow_ema'].shift(1))

        data.loc[bullish, 'signal'] = 1   # BUY CALL
        data.loc[bearish, 'signal'] = -1  # BUY PUT
        return data
"""
        return code

    def audit_code_for_lookahead_bias(self, code_str: str) -> Dict[str, Any]:
        """
        Parses the code into an AST and detects future information leakage.
        """
        try:
            tree = ast.parse(code_str)
            auditor = StaticLookaheadAuditor()
            auditor.visit(tree)
            return {
                "passes_audit": len(auditor.violations) == 0,
                "violations": auditor.violations
            }
        except SyntaxError as e:
            return {
                "passes_audit": False,
                "violations": [f"Syntax Error in generated code: {str(e)}"]
            }
