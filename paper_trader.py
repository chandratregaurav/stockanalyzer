
import pandas as pd
from datetime import datetime

class PaperTrader:
    def __init__(self, initial_balance=50000.0):
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {} # {ticker: {'qty': int, 'avg_price': float, 'ts': timestamp}}
        self.trade_log = [] # List of trade dicts
        self.total_profit = 0.0
        self.equity_history = [{"ts": datetime.now(), "value": initial_balance}]

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
        self.equity_history.append({"ts": datetime.now(), "value": val})

    def buy(self, ticker, price, amount=2000):
        """Buys a stock with a fixed amount of cash (approx)."""
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
            'ts': datetime.now()
        }
        
        log_entry = f"🟢 BUY  {ticker}: {qty} qty @ {price:.2f}"
        self.trade_log.insert(0, log_entry) # Add to top
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
        del self.positions[ticker]
        
        icon = "🔴" if profit < 0 else "🟢"
        log_entry = f"{icon} SELL {ticker}: {qty} qty @ {price:.2f} | P&L: {profit:.2f} ({pct_profit:.1f}%) | {reason}"
        self.trade_log.insert(0, log_entry)
        
        return True, f"Sold {ticker} for {profit:.2f} profit"

    def check_auto_exit(self, current_prices):
        """Auto-Sell logic: Target ₹2/share profit, Stop Loss ₹1/share (2:1 ratio)."""
        exits = []
        
        for ticker in list(self.positions.keys()):
            if ticker not in current_prices:
                continue
                
            current_price = current_prices[ticker]
            pos = self.positions[ticker]
            entry_price = pos['avg_price']
            
            # Absolute profit/loss per share
            profit_per_share = current_price - entry_price
            
            # Target Rule: Take Profit at ₹2 per share (2:1 reward)
            if profit_per_share >= 2.0:
                 success, msg = self.sell(ticker, current_price, reason=f"Target +₹{profit_per_share:.2f} 🎯")
                 if success: exits.append(msg)
            
            # Stop Rule: Cut Loss at ₹1 per share (tight stop)
            elif profit_per_share <= -1.0:
                 success, msg = self.sell(ticker, current_price, reason=f"Stop -₹{abs(profit_per_share):.2f} 🛑")
                 if success: exits.append(msg)
                 
        return exits
