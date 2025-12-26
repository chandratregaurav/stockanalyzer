
import pandas as pd
from datetime import datetime

import json
import os

class PaperTrader:
    def __init__(self, initial_balance=50000.0):
        self.state_file = "paper_trader_state.json"
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {} # {ticker: {'qty': int, 'avg_price': float, 'ts': timestamp}}
        self.trade_log = [] # List of trade dicts
        self.total_profit = 0.0
        self.equity_history = [{"ts": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "value": initial_balance}]
        
        # --- NEW: Learning & Feedback Loop Meta ---
        self.learning_file = "trading_rules.json"
        self.trade_history_file = "detailed_trade_logs.json"
        self.active_rules = self.load_learned_rules()
        
        # Try loading existing state
        self.load_state()

    def save_state(self):
        """Saves current state to JSON file."""
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
        """Loads state from JSON file if exists."""
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
        """Calculates total value (Cash + Holdings)."""
        holdings_value = 0.0
        for ticker, pos in self.positions.items():
            current_price = current_prices.get(ticker, pos['avg_price'])
            holdings_value += pos['qty'] * current_price
        return self.cash + holdings_value

    def log_portfolio_value(self, current_prices):
        """Records current portfolio value for history plotting."""
        val = self.get_portfolio_value(current_prices)
        self.equity_history.append({"ts": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "value": val})
        self.save_state()

    # --- Learning Logic ---
    def load_learned_rules(self):
        """Loads rules learned from previous mistakes."""
        if os.path.exists(self.learning_file):
            with open(self.learning_file, "r") as f:
                return json.load(f)
        return {"blocklist_conditions": [], "min_confidence": 60}

    def save_learned_rules(self):
        with open(self.learning_file, "w") as f:
            json.dump(self.active_rules, f, indent=2)

    def analyze_mistakes(self):
        """
        AI 'Self-Correction' Logic:
        Scans detailed trade logs for recurring factors in failed trades (Stop Losses).
        """
        if not os.path.exists(self.trade_history_file): return
        
        with open(self.trade_history_file, "r") as f:
            logs = json.load(f)
        
        failures = [l for l in logs if l.get('pnl_pct', 0) < 0]
        if len(failures) >= 3:
            # Simple Pattern Recognition (can be replaced by an actual AI call)
            avg_rsi_fail = sum([l.get('rsi', 50) for l in failures]) / len(failures)
            if avg_rsi_fail > 70:
                self.active_rules['blocklist_conditions'].append("Avoid trades when RSI > 70 (Overbought Burn)")
                self.save_learned_rules()
            elif avg_rsi_fail < 30:
                self.active_rules['blocklist_conditions'].append("Avoid trades when RSI < 30 (Falling Knife)")
                self.save_learned_rules()

    def log_detailed_trade(self, trade_data):
        """Saves trade metrics for future model training/learning."""
        all_logs = []
        if os.path.exists(self.trade_history_file):
            with open(self.trade_history_file, "r") as f:
                all_logs = json.load(f)
        
        all_logs.append(trade_data)
        with open(self.trade_history_file, "w") as f:
            json.dump(all_logs, f, indent=2)

    def buy(self, ticker, price, amount=2000, metrics=None):
        """Buys a stock with a fixed amount of cash (approx)."""
        # Check against learned rules
        if metrics:
            rsi = metrics.get('rsi', 50)
            if rsi > 70 and "Avoid trades when RSI > 70" in str(self.active_rules['blocklist_conditions']):
                return False, "Blocked: RSI too high (Learned from previous fail)"

        if ticker in self.positions:
            return False, "Already holding position"
        
        if self.cash < amount:
            amount = self.cash # Use remaining cash if less than target amount
            
        if amount < price:
            return False, "Insufficient funds"
            
        qty = int(amount // price)
        if qty < 1:
            return False, "Price too high for balance"
            
        cost = qty * price
        self.cash -= cost
        self.positions[ticker] = {
            'qty': qty,
            'avg_price': price,
            'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics_at_entry': metrics or {}
        }
        
        log_entry = f"🟢 BUY  {ticker}: {qty} qty @ {price:.2f}"
        self.trade_log.insert(0, log_entry) # Add to top
        self.save_state()
        return True, f"Bought {qty} of {ticker}"

    def sell(self, ticker, price, reason="Manual"):
        """Sells a position completely."""
        if ticker not in self.positions:
            return False, "Position not found"
            
        pos = self.positions[ticker]
        qty = pos['qty']
        avg_price = pos['avg_price']
        
        revenue = qty * price
        profit = revenue - (qty * avg_price)
        pct_profit = (profit / (qty * avg_price)) * 100
        
        self.cash += revenue
        self.total_profit += profit
        
        # Log for learning
        trade_summary = {
            "ticker": ticker,
            "pnl_pct": pct_profit,
            "profit": profit,
            "rsi": pos.get('metrics_at_entry', {}).get('rsi', 50),
            "exit_reason": reason,
            "ts": datetime.now().isoformat()
        }
        self.log_detailed_trade(trade_summary)
        
        del self.positions[ticker]
        
        icon = "🔴" if profit < 0 else "🟢"
        log_entry = f"{icon} SELL {ticker}: {qty} qty @ {price:.2f} | P&L: {profit:.2f} ({pct_profit:.1f}%) | {reason}"
        self.trade_log.insert(0, log_entry)
        
        # Trigger 'AI' review after every loss
        if profit < 0:
            self.analyze_mistakes()

        self.save_state()
        return True, f"Sold {ticker} for {profit:.2f} profit"

    def check_auto_exit(self, current_prices):
        """
        Auto-Sell logic (Rapid Scalping):
        - Target: Take Profit at +0.80% Gain (Realistic for Large Caps)
        - Stop Loss: Cut Loss at -0.40% Loss
        - Risk:Reward Ratio: 1:2
        """
        exits = []
        
        for ticker in list(self.positions.keys()):
            if ticker not in current_prices:
                continue
                
            current_price = current_prices[ticker]
            pos = self.positions[ticker]
            entry_price = pos['avg_price']
            
            # Calculate Percentage P&L
            pct_change = ((current_price - entry_price) / entry_price) * 100
            abs_profit = (current_price - entry_price) * pos['qty']
            
            # Target Rule: +0.8% Scalp Target (Quick Profits)
            if pct_change >= 0.80:
                 success, msg = self.sell(ticker, current_price, reason=f"Target +{pct_change:.2f}% (₹{abs_profit:.0f}) 🎯")
                 if success: exits.append(msg)
            
            # Stop Rule: -0.4% Tight Stop
            elif pct_change <= -0.40:
                 success, msg = self.sell(ticker, current_price, reason=f"Stop {pct_change:.2f}% (₹{abs_profit:.0f}) 🛑")
                 if success: exits.append(msg)
                 
        return exits
