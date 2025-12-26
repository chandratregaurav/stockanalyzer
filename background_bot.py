
import time
import json
import os
import yfinance as yf
from datetime import datetime
from paper_trader import PaperTrader
from stock_screener import StockScreener
# We need to import the market check logic too
# Note: Since dashboard.py has the market check, we'll replicate or better yet, 
# if it's in a shared utility we'd use that. 
# For now, I'll define a simple version or use the logic from dashboard.

POPULAR_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", 
    "BHARTIARTL.NS", "SBIN.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "TATAMOTORS.NS", "AXISBANK.NS", "ONGC.NS", "TITAN.NS"
]

def is_market_open():
    """Shared market hour logic for background service."""
    now = datetime.now()
    # NSE/BSE Hours: 9:15 AM to 3:30 PM IST (UTC+5:30)
    # Simple check for now: 03:45 UTC to 10:00 UTC approx.
    # Better to use the local time from OS if possible.
    # Cursor current local time is 16:40 IST (Market Closed)
    
    if now.weekday() >= 5: # Weekend
        return False, "Market is closed (Weekend)"
        
    current_time = now.time()
    start_time = datetime.strptime("09:15", "%H:%M").time()
    end_time = datetime.strptime("15:30", "%H:%M").time()
    
    if current_time < start_time:
        return False, f"Market opens at 09:15 AM. Current: {current_time.strftime('%H:%M')}"
    if current_time > end_time:
        return False, f"Market closed at 03:30 PM. Current: {current_time.strftime('%H:%M')}"
        
    return True, "Market is LIVE"

def run_bot():
    print(f"[{datetime.now()}] AI Background Bot Starting...")
    trader = PaperTrader(initial_balance=10000.0)
    
    while True:
        try:
            market_open, msg = is_market_open()
            
            # Record status for UI to read
            status = {
                "active": market_open,
                "msg": msg,
                "last_run": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open("bot_status.json", "w") as f:
                json.dump(status, f)

            if not market_open:
                print(f"[{datetime.now()}] {msg}. Sleeping for 5 minutes...")
                time.sleep(300) 
                continue

            print(f"[{datetime.now()}] Scanning Market...")
            screener = StockScreener(POPULAR_STOCKS)
            top_scalps = screener.screen_intraday()
            
            # 1. Manage Exits (Profit Booking / Stop Loss)
            current_prices = {}
            if trader.positions:
                for ticker in trader.positions.keys():
                    try:
                        # Use scan price if available, otherwise fetch
                        found = False
                        for s in top_scalps:
                            if s['ticker'] == ticker:
                                current_prices[ticker] = s['price']
                                found = True; break
                        if not found:
                            d = yf.download(ticker, period="1d", interval="1m", progress=False)
                            if not d.empty:
                                current_prices[ticker] = d['Close'].iloc[-1]
                    except Exception as e:
                        print(f"Error fetching exit price for {ticker}: {e}")
            
            if current_prices:
                exits = trader.check_auto_exit(current_prices)
                for e in exits:
                    print(f"[{datetime.now()}] EXIT: {e}")

            # 2. Manage Entries
            if top_scalps:
                for pick in top_scalps:
                    if pick['score'] >= 50:
                        success, res = trader.buy(
                            pick['ticker'], 
                            pick['price'], 
                            metrics={'rsi': pick.get('rsi', 50), 'vol_ratio': pick.get('vol_ratio', 1.0)}
                        )
                        if success:
                            print(f"[{datetime.now()}] ENTRY: {res}")
                        elif "Blocked" in res:
                            print(f"[{datetime.now()}] AI BLOCKED: {pick['ticker']} - {res}")

            time.sleep(60) # Run every minute when market is open
            
        except Exception as e:
            print(f"CRITICAL ERROR in Bot Loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_bot()
