
import yfinance as yf
from datetime import date, timedelta
import pandas as pd

ticker = "RELIANCE.NS"
print(f"Checking data for {ticker}...")

# Simulation of what StockScreener does
end_date = date.today() + timedelta(days=1)
start_date = end_date - timedelta(days=5)

print(f"Fetching from {start_date} to {end_date}...")

df = yf.download(ticker, start=start_date, end=end_date, interval='1h', progress=False, auto_adjust=True)

if isinstance(df.columns, pd.MultiIndex):
    try:
        df.columns = df.columns.get_level_values(0)
    except:
        pass

print(f"\nLast 5 Timestamps:")
print(df.index[-5:])

print("\nLast 5 Rows (Close):")
print(df['Close'].tail(5))

# Check if today's date is in the index
today_str = date.today().strftime('%Y-%m-%d')
has_today = any(str(idx).startswith(today_str) for idx in df.index)

print(f"\nHas data for today ({today_str})? {'YES ✅' if has_today else 'NO ❌'}")
