import json
import os
import time
import yfinance as yf
import pandas as pd
from datetime import date, timedelta, datetime

class MarketDataFetcher:
    def __init__(self, db_path='ticker_db.json', cache_path='market_cache.json'):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_path, db_path)
        self.cache_path = os.path.join(self.base_path, cache_path)
        self.symbols = self.load_symbols()

    def load_symbols(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                data = json.load(f)
                # Append .NS for NSE stocks
                return [f"{item['symbol']}.NS" for item in data]
        return []

    def fetch_top_performers(self, batch_size=50):
        print(f"Fetching data for {len(self.symbols)} tickers...")
        
        all_stats = []
        
        # Process in batches to avoid overwhelming yfinance/network
        chunks = [self.symbols[i:i + batch_size] for i in range(0, len(self.symbols), batch_size)]
        
        for chunk in chunks:
            try:
                # Download last 1 month of data for the chunk (needed for monthly stats)
                # group_by='ticker' ensures we get a structure we can iterate easily
                df = yf.download(chunk, period="1mo", group_by='ticker', progress=False, threads=True)
                
                if df.empty:
                    continue
                    
                for symbol in chunk:
                    try:
                        # Handle case where single ticker download results in different structure
                        if len(chunk) == 1:
                            stock_df = df
                        else:
                            if symbol not in df.columns.levels[0]:
                                continue
                            stock_df = df[symbol]
                        
                        # Check we have enough data
                        stock_df = stock_df.dropna(subset=['Close'])
                        if len(stock_df) < 2:
                            continue
                            
                        last_close = float(stock_df['Close'].iloc[-1])
                        prev_close = float(stock_df['Close'].iloc[-2])
                        
                        # 1-Day Change
                        change_1d = ((last_close - prev_close) / prev_close) * 100
                        volume = int(stock_df['Volume'].iloc[-1]) if 'Volume' in stock_df.columns else 0
                        
                        # We could calculate more metrics here (e.g. 5-day change)
                        change_5d = 0
                        change_30d = 0
                        if len(stock_df) >= 5:
                            prev_5d = float(stock_df['Close'].iloc[-5])
                            change_5d = ((last_close - prev_5d) / prev_5d) * 100
                        if len(stock_df) >= 20: # Approx 1 month trading days
                            prev_30d = float(stock_df['Close'].iloc[0]) # Start of the 1mo period
                            change_30d = ((last_close - prev_30d) / prev_30d) * 100

                        all_stats.append({
                            'ticker': symbol,
                            'price': last_close,
                            'change_1d': change_1d,
                            'change_5d': change_5d,
                            'change_30d': change_30d,
                            'volume': volume
                        })
                        
                    except Exception as e:
                        # Silently skip errors for individual tickers
                        continue
                        
            except Exception as e:
                print(f"Batch failed: {e}")
                
        return all_stats

    def update_cache(self):
        stats = self.fetch_top_performers()
        
        if not stats:
            print("No data fetched.")
            return

        # Sort by 1D change
        sorted_by_day = sorted(stats, key=lambda x: x['change_1d'], reverse=True)
        
        # Sort by 30D change
        sorted_by_month = sorted(stats, key=lambda x: x['change_30d'], reverse=True)

        # Sort by Volume (Trending)
        sorted_by_volume = sorted(stats, key=lambda x: x['volume'], reverse=True)
        
        # Create cache structure
        cache_data = {
            "last_updated": datetime.now().isoformat(),
            "top_gainers_1d": sorted_by_day[:20],  # Store top 20
            "top_gainers_30d": sorted_by_month[:20], 
            "top_active_volume": sorted_by_volume[:20],
            "all_stats": stats # Optional: store minimal stats for all if needed, but might be large.
                               # For now, let's keep the user's specific request 'dynamic list'
        }
        
        # Save to JSON
        with open(self.cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)
            
        print(f"Cache updated at {cache_data['last_updated']}")
        print(f"Top Gainer: {sorted_by_day[0]['ticker']} (+{sorted_by_day[0]['change_1d']:.2f}%)")

if __name__ == "__main__":
    fetcher = MarketDataFetcher()
    # Continuous loop mode
    print("Starting Background Market Data Job...")
    while True:
        print("\n--- Starting Update Cycle ---")
        fetcher.update_cache()
        print("Sleeping for 10 minutes...")
        time.sleep(600)  # Sleep 10 minutes
