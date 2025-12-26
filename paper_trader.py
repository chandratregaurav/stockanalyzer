
import pandas as pd
from datetime import datetime
import json
import os

class PaperTrader:
    def __init__(self, initial_balance=10000.0):
        self.state_file = "paper_trader_state.json"
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {} # {ticker: {'qty': int, 'avg_price': float, 'ts': timestamp}}
        self.trade_log = [] # List of trade text logs
        self.total_profit = 0.0
        self.equity_history = [{"ts": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "value": initial_balance}]
        
        self.learning_file = "trading_rules.json"
        self.trade_history_file = "detailed_trade_logs.json"
        self.active_rules = self.load_learned_rules()
        
        self.load_state()

    def save_state(self):
        state = {
            "cash": self.cash,
            "positions": self.positions,
            "trade_log": self.trade_log,
            "total_profit": self.total_profit,
            "equity_history": self.equity_history
        }
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, default=str)
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.cash = state.get("cash", self.initial_balance)
                    self.positions = state.get("positions", {})
                    self.trade_log = state.get("trade_log", [])
                    self.total_profit = state.get("total_profit", 0.0)
                    self.equity_history = state.get("equity_history", [])
            except Exception as e:
                print(f"Error loading state: {e}")

    def get_portfolio_value(self, current_prices):
        holdings_value = 0.0
        for ticker, pos in self.positions.items():
            current_price = current_prices.get(ticker, pos['avg_price'])
            holdings_value += pos['qty'] * current_price
        return self.cash + holdings_value

    def log_portfolio_value(self, current_prices):
        val = self.get_portfolio_value(current_prices)
        self.equity_history.append({"ts": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "value": val})
        self.save_state()

    def load_learned_rules(self):
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, "r") as f:
                    return json.load(f)
            except: pass
        return {"blocklist_conditions": [], "min_confidence": 60, "last_learning_ts": None}

    def save_learned_rules(self):
        with open(self.learning_file, "w") as f:
            json.dump(self.active_rules, f, indent=2)

    def analyze_mistakes(self):
        if not os.path.exists(self.trade_history_file): return
        try:
            with open(self.trade_history_file, "r") as f:
                logs = json.load(f)
            failures = [l for l in logs if l.get('pnl_pct', 0) < 0]
            if len(failures) < 3: return
            fail_rsis = [l.get('rsi', 50) for l in failures]
            avg_rsi_fail = sum(fail_rsis) / len(fail_rsis)
            if avg_rsi_fail > 72:
                self._update_rule("Avoid entries when RSI > 72 (Exhausted Trend)")
            elif avg_rsi_fail < 35:
                self._update_rule("Avoid entries when RSI < 35 (Weak Momentum)")
            fail_vols = [l.get('vol_ratio', 1.0) for l in failures]
            avg_vol_fail = sum(fail_vols) / len(fail_vols)
            if avg_vol_fail > 4.0:
                self._update_rule("Avoid 'Ultra-Spikes' (>4x Vol) as they often lead to instant reversal.")
            self.active_rules['last_learning_ts'] = datetime.now().isoformat()
            self.save_learned_rules()
        except: pass

    def _update_rule(self, rule_desc):
        if rule_desc not in self.active_rules['blocklist_conditions']:
            self.active_rules['blocklist_conditions'].append(rule_desc)

    def log_detailed_trade(self, trade_data):
        all_logs = []
        if os.path.exists(self.trade_history_file):
            try:
                with open(self.trade_history_file, "r") as f:
                    all_logs = json.load(f)
            except: pass
        all_logs.append(trade_data)
        with open(self.trade_history_file, "w") as f:
            json.dump(all_logs, f, indent=2)

    def buy(self, ticker, price, amount=2000, metrics=None):
        if metrics:
            rsi = metrics.get('rsi', 50)
            for rule in self.active_rules['blocklist_conditions']:
                if "RSI > 72" in rule and rsi > 72: return False, f"Blocked: {rule}"
                if "RSI < 35" in rule and rsi < 35: return False, f"Blocked: {rule}"

        if ticker in self.positions: return False, "Already holding"
        if self.cash < amount: amount = self.cash
        if amount < price: return False, "Insufficient funds"
        qty = int(amount // price)
        if qty < 1: return False, "Price too high"
        cost = qty * price
        self.cash -= cost
        self.positions[ticker] = {
            'qty': qty,
            'avg_price': price,
            'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics_at_entry': metrics or {}
        }
        log_entry = f"🟢 BUY  {ticker}: {qty} qty @ {price:.2f}"
        self.trade_log.insert(0, log_entry)
        self.save_state()
        return True, f"Bought {qty} of {ticker}"

    def sell(self, ticker, price, reason="Manual"):
        if ticker not in self.positions: return False, "Not found"
        pos = self.positions[ticker]
        qty, avg_p = pos['qty'], pos['avg_price']
        revenue = qty * price
        profit = revenue - (qty * avg_p)
        pct_p = (profit / (qty * avg_p)) * 100
        self.cash += revenue
        self.total_profit += profit
        trade_summary = {
            "ticker": ticker, "pnl_pct": pct_p, "profit": profit,
            "rsi": pos.get('metrics_at_entry', {}).get('rsi', 50),
            "vol_ratio": pos.get('metrics_at_entry', {}).get('vol_ratio', 1.0),
            "exit_reason": reason, "ts": datetime.now().isoformat()
        }
        self.log_detailed_trade(trade_summary)
        del self.positions[ticker]
        icon = "🔴" if profit < 0 else "🟢"
        log_entry = f"{icon} SELL {ticker}: {qty} qty @ {price:.2f} | P&L: {profit:.2f} ({pct_p:.1f}%) | {reason}"
        self.trade_log.insert(0, log_entry)
        if profit < 0: self.analyze_mistakes()
        self.save_state()
        return True, f"Sold {ticker} for {profit:.2f}"

    def check_auto_exit(self, current_prices):
        exits = []
        for ticker in list(self.positions.keys()):
            if ticker not in current_prices: continue
            cur_p = current_prices[ticker]
            pos = self.positions[ticker]
            entry_p = pos['avg_price']
            pct_chg = ((cur_p - entry_p) / entry_p) * 100
            abs_profit = (cur_p - entry_p) * pos['qty']
            if pct_chg >= 0.80:
                success, msg = self.sell(ticker, cur_p, reason=f"Target +{pct_chg:.2f}% 🎯")
                if success: exits.append(msg)
            elif pct_chg <= -0.40:
                success, msg = self.sell(ticker, cur_p, reason=f"Stop {pct_chg:.2f}% 🛑")
                if success: exits.append(msg)
        return exits
