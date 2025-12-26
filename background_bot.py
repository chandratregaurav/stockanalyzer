
import time
import json
import os
import yfinance as yf
import pytz
from datetime import datetime, date, timedelta
from paper_trader import PaperTrader
from stock_screener import StockScreener

# Version to help UI identify updated bots
BOT_VERSION = "2.1-IST-FIX"

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
    try:
        tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(tz)
        today = now_ist.date()
        
        # 1. Weekend Check
        if now_ist.weekday() >= 5:
            return False, "Closed (Weekend)"
            
        # 2. Holiday Check
        if today in get_nse_holidays_2025():
            return False, "Closed (Market Holiday)"
            
        # 3. Time Check (9:15 to 15:30 IST)
        # Use simple integer comparison for robustness
        current_minutes = now_ist.hour * 60 + now_ist.minute
        open_minutes = 9 * 60 + 15
        close_minutes = 15 * 60 + 30
        
        if current_minutes < open_minutes:
            return False, f"Market opens at 09:15 AM (IST)"
        if current_minutes > close_minutes:
            return False, f"Market closed at 03:30 PM (IST)"
            
        return True, "Market is LIVE"
    except Exception as e:
        return False, f"Time Error: {str(e)}"

def run_bot():
    """Background loop with IST enforcement and status heartbeat."""
    print(f"[{datetime.now()}] AI Background Bot {BOT_VERSION} Starting...")
    trader = PaperTrader(initial_balance=10000.0)
    ist = pytz.timezone('Asia/Kolkata')
    
    while True:
        try:
            market_open, msg = is_market_open()
            last_run_ist = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
            
            # Record status with VERSION and IST timestamp
            status = {
                "active": market_open,
                "msg": msg,
                "last_run": last_run_ist,
                "version": BOT_VERSION,
                "timezone": "Asia/Kolkata"
            }
            with open("bot_status.json", "w") as f:
                json.dump(status, f)

            # --- Marquee Data fetching ---
            # Always fetch marquee data so users see closing prices when market is closed
            try:
                marquee_symbols = {
                    "^NSEI": "NIFTY 50", "^BSESN": "SENSEX", "^NSEBANK": "BANK NIFTY",
                    "^NSEMDCP100": "MIDCAP 100", "^INDIAVIX": "INDIA VIX",
                    "RELIANCE.NS": "RELIANCE", "HDFCBANK.NS": "HDFC BANK", "ICICIBANK.NS": "ICICI BANK",
                    "TCS.NS": "TCS", "INFY.NS": "INFY", "SBIN.NS": "SBI", "BHARTIARTL.NS": "AIRTEL",
                    "ITC.NS": "ITC", "TATAMOTORS.NS": "TATA MOTORS", "ADANIENT.NS": "ADANI ENT",
                    "BAJFINANCE.NS": "BAJAJ FIN", "MARUTI.NS": "MARUTI", "TITAN.NS": "TITAN",
                    "SUNPHARMA.NS": "SUN PHARMA", "LT.NS": "L&T", "HCLTECH.NS": "HCL TECH",
                    "AXISBANK.NS": "AXIS BANK", "ASIANPAINT.NS": "ASIAN PAINT", "KOTAKBANK.NS": "KOTAK BANK"
                }
                m_data = yf.download(list(marquee_symbols.keys()), period="2d", interval="1d", progress=False, group_by='ticker')
                marquee_results = []
                for sym, name in marquee_symbols.items():
                    try:
                        df = m_data[sym] if len(marquee_symbols) > 1 else m_data
                        df = df.dropna(subset=['Close'])
                        if not df.empty:
                            lp = float(df['Close'].iloc[-1])
                            prev = float(df['Close'].iloc[-2]) if len(df) > 1 else lp
                            chg = ((lp - prev) / prev) * 100 if prev != 0 else 0
                            marquee_results.append({"name": name, "price": lp, "change": chg})
                    except: continue
                with open("marquee_data.json", "w") as f:
                    json.dump(marquee_results, f)
            except Exception as e:
                print(f"Marquee fetch error: {e}")

            if not market_open:
                # If market is closed, sleep for 5 mins but update heartbeat
                time.sleep(300) 
                continue

            # --- Trading Logic ---
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

            # Scan every 1 minute when live
            time.sleep(60)
            
        except Exception as e:
            # Silence errors in background but log to file if needed
            print(f"Bot Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_bot()
