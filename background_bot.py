
import time
import json
import os
import yfinance as yf
import pytz
from datetime import datetime, date, timedelta
from paper_trader import PaperTrader
from stock_screener import StockScreener

POPULAR_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", 
    "BHARTIARTL.NS", "SBIN.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "TATAMOTORS.NS", "AXISBANK.NS", "ONGC.NS", "TITAN.NS"
]

def get_nse_holidays_2025():
    return [
        date(2025, 1, 26), date(2025, 3, 14), date(2025, 3, 31),
        date(2025, 4, 10), date(2025, 4, 14), date(2025, 4, 18),
        date(2025, 5, 1), date(2025, 6, 7), date(2025, 8, 15),
        date(2025, 8, 27), date(2025, 10, 2), date(2025, 10, 21),
        date(2025, 11, 1), date(2025, 11, 5), date(2025, 12, 25),
    ]

def is_market_open():
    """Precise market hour logic for background service using IST."""
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    today = now.date()
    
    if today in get_nse_holidays_2025():
        return False, "Closed (Holiday)"
    if now.weekday() >= 5:
        return False, "Closed (Weekend)"
        
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if now < market_open:
        return False, f"Market Opens at 09:15 AM (IST)"
    if now > market_close:
        return False, f"Market Closed for Today"
        
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
                "last_run": datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
            }
            with open("bot_status.json", "w") as f:
                json.dump(status, f)

            if not market_open:
                time.sleep(300) 
                continue

            screener = StockScreener(POPULAR_STOCKS)
            top_scalps = screener.screen_intraday()
            
            current_prices = {}
            if trader.positions:
                for ticker in trader.positions.keys():
                    try:
                        found = False
                        for s in top_scalps:
                            if s['ticker'] == ticker:
                                current_prices[ticker] = s['price']; found = True; break
                        if not found:
                            d = yf.download(ticker, period="1d", interval="1m", progress=False)
                            if not d.empty: current_prices[ticker] = d['Close'].iloc[-1]
                    except: pass
            
            if current_prices:
                trader.check_auto_exit(current_prices)

            if top_scalps:
                for pick in top_scalps:
                    if pick['score'] >= 50:
                        trader.buy(pick['ticker'], pick['price'], metrics={'rsi': pick.get('rsi', 50), 'vol_ratio': pick.get('vol_ratio', 1.0)})

            time.sleep(60)
        except Exception as e:
            time.sleep(30)

if __name__ == "__main__":
    run_bot()
