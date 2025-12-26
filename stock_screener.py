
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

class StockScreener:
    def __init__(self, tickers):
        self.tickers = tickers

    def fetch_history(self, ticker):
        """Fetches 6 months of history for a single ticker."""
        end_date = date.today() + timedelta(days=1) 
        start_date = end_date - timedelta(days=200) 
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df.empty or len(df) < 60:
                return None
            
            # --- FIX: yfinance MultiIndex columns ---
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel('Ticker')
            
            df = df.loc[:, ~df.columns.duplicated()].copy()
            
            required = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(c in df.columns for c in required):
                return None
                    
            return df
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def calculate_rsi(self, series, period=14):
        """Calculate RSI manually."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_score(self, ticker, df):
        """Calculates a recommendation score for the stock."""
        # 1. RSI (Momentum)
        # Optimal RSI is between 40 and 70 (Uptrend but not overbought)
        df['RSI'] = self.calculate_rsi(df['Close'])
        current_rsi = df['RSI'].iloc[-1]
        
        # 2. SMA Trend
        # Price > SMA 20 > SMA 50 is a strong uptrend
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
        
        current_price = df['Close'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        vol_sma = df['Vol_SMA_20'].iloc[-1]
        current_vol = df['Volume'].iloc[-1]
        
        # Safe check for NaNs
        if pd.isna(current_rsi) or pd.isna(sma_50):
            return None

        # --- Scoring Logic (0 to 100) ---
        score = 0
        reasons = []
        
        # Trend Score (Max 40)
        if current_price > sma_20:
            score += 20
            reasons.append("Price > 20d Avg")
        if sma_20 > sma_50:
            score += 20
            reasons.append("Golden Trend")
            
        # RSI Score (Max 30)
        # Penalize if > 75 (High risk correction) or < 30 (Falling knife)
        if 40 <= current_rsi <= 70:
            score += 30
            reasons.append(f"Healthy RSI ({current_rsi:.0f})")
        elif current_rsi > 70:
            score += 10 # Strong momentum but risky
            reasons.append("Overbought")
        else:
            score += 5 # Oversold bounce potential
            
        # Volume Score (Max 30)
        vol_ratio = current_vol / vol_sma if vol_sma > 0 else 1.0
        if vol_ratio > 1.5:
            score += 30
            reasons.append(f"Vol Spike ({vol_ratio:.1f}x)")
        elif vol_ratio > 1.0:
            score += 20
        
        return {
            'ticker': ticker,
            'price': current_price,
            'score': score,
            'reasons': ", ".join(reasons),
            'rsi': current_rsi,
            'change_pct': ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        }

    def fetch_hourly_history(self, ticker):
        """Fetches 5 days of hourly history for a single ticker."""
        end_date = date.today() + timedelta(days=1) 
        start_date = end_date - timedelta(days=5) 
        try:
            df = yf.download(ticker, start=start_date, end=end_date, interval='1h', progress=False, auto_adjust=True)
            if df.empty or len(df) < 20:
                return None
            
            # --- FIX: yfinance returns MultiIndex columns like ('Close', 'TICKER') ---
            # We need to completely flatten to simple column names
            if isinstance(df.columns, pd.MultiIndex):
                # Drop the Ticker level, keep only Price level
                df.columns = df.columns.droplevel('Ticker')
            
            # If any resulting columns are duplicated (shouldn't be), drop dups
            df = df.loc[:, ~df.columns.duplicated()].copy()
            
            # Verify we have what we need
            if 'Close' not in df.columns or 'Volume' not in df.columns:
                print(f"Missing Close/Volume for {ticker}")
                return None
                    
            return df
        except Exception as e:
            print(f"Hourly fetch error {ticker}: {e}")
            return None

    def calculate_intraday_score(self, ticker, df):
        """Calculates score for Intraday Scalping (1-2 Hr)."""
        # We need recent data
        if df.empty: return None
        
        # Calculate Hourly Indicators
        df['RSI'] = self.calculate_rsi(df['Close'], period=14)
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['Vol_SMA_10'] = df['Volume'].rolling(window=10).mean()
        
        current_price = df['Close'].iloc[-1]
        last_hourly_change = (current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
        current_rsi = df['RSI'].iloc[-1]
        current_vol = df['Volume'].iloc[-1]
        vol_avg = df['Vol_SMA_10'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        
        if pd.isna(current_rsi) or pd.isna(vol_avg) or vol_avg == 0:
            return None

        # --- Scalping Logic ---
        # 1. Volume Burst
        vol_ratio = current_vol / vol_avg
        
        # 2. Trend Alignment
        above_sma = current_price > sma_20
        
        # 3. Momentum
        # Strong but not totally exhausted (RSI 55-80 is the sweet spot for breakout continuation)
        good_momentum = 55 <= current_rsi <= 80
        
        score = 0
        reasons = []
        
        if vol_ratio > 1.5:
            score += 30
            reasons.append(f"🔥 Vol Burst ({vol_ratio:.1f}x)")
        elif vol_ratio > 1.1:
            score += 15
            reasons.append(f"Rising Vol ({vol_ratio:.1f}x)")
            
        if 45 <= current_rsi <= 85:
            score += 25
            reasons.append(f"Momentum ({current_rsi:.0f})")
            
        if above_sma:
            score += 20
            reasons.append("Uptrend")
            
        if last_hourly_change > 0:
            # Huge bonus just for being GREEN in the last hour
            score += 20 
            reasons.append(f"Appreciating (+{last_hourly_change:.2f}%)")
            
        # Very Relaxed Filter: 
        # Basically if it's Green (+20) and matches ONE other thing (Trend/RSI/Vol), it passes (35+)
        if score < 35:
            return None
            
        return {
            'ticker': ticker,
            'price': current_price,
            'score': score,
            'reasons': ", ".join(reasons),
            'last_hour_change': last_hourly_change,
            'vol_ratio': vol_ratio
        }

    def screen_intraday(self):
        """Scans for Intraday Scalping opportunities."""
        results = []
        
        # Sequential calls to avoid yfinance data mixing bug
        for ticker in self.tickers:
            df = self.fetch_hourly_history(ticker)
            if df is not None:
                stats = self.calculate_intraday_score(ticker, df)
                if stats:
                    results.append(stats)
        
        # Sort by Score (Desc) then by Last Hour Change
        results.sort(key=lambda x: (x['score'], x['last_hour_change']), reverse=True)
        
        return results[:5]

    def screen_market(self):
        """Scans all tickers and returns top 5."""
        results = []
        
        # Sequential calls to avoid yfinance data mixing bug
        for ticker in self.tickers:
            df = self.fetch_history(ticker)
            if df is not None:
                stats = self.calculate_score(ticker, df)
                if stats:
                    results.append(stats)
        
        # Sort by Score (Desc)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:5]

    def get_market_stars(self, limit_tickers=None):
        """Finds the 'Stars of the Day' (4) and 'Stars of the Month' (2)."""
        tickers_to_scan = limit_tickers if limit_tickers else self.tickers
        all_day = []
        all_month = []
        
        for ticker in tickers_to_scan:
            df = self.fetch_history(ticker)
            if df is not None and len(df) > 22:
                # 1D Change
                c_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                all_day.append({'ticker': ticker, 'price': df['Close'].iloc[-1], 'change': c_1d})
                
                # 30D Change
                c_30d = ((df['Close'].iloc[-1] - df['Close'].iloc[-22]) / df['Close'].iloc[-22]) * 100
                all_month.append({'ticker': ticker, 'price': df['Close'].iloc[-1], 'change': c_30d})
        
        # Sort and take top N
        all_day.sort(key=lambda x: x['change'], reverse=True)
        all_month.sort(key=lambda x: x['change'], reverse=True)
        
        return all_day[:4], all_month[:2]

    def get_multibagger_candidates(self, limit=10, strategy="Strong Formula"):
        """Scans for potential multibaggers using selected strategy heuristic."""
        import random
        results = []
        
        # Shuffle tickers to remove alphabetical bias (A... Z)
        scan_list = list(self.tickers)
        random.shuffle(scan_list)
        
        def process_ticker(ticker):
            try:
                # 1. Fetch historical data for indicators
                hist_df = yf.download(ticker, period="1y", progress=False, auto_adjust=True, threads=False)
                if hist_df is None or hist_df.empty or len(hist_df) < 100: return None
                
                # 2. Fetch LATEST price separately (disable auto-adjust for display price to match NSE)
                latest_data = yf.download(ticker, period="1d", interval="1m", progress=False, auto_adjust=False, threads=False)
                if latest_data.empty: return None
                
                # Flatten columns if MultiIndex
                if isinstance(hist_df.columns, pd.MultiIndex): hist_df.columns = hist_df.columns.droplevel('Ticker')
                if isinstance(latest_data.columns, pd.MultiIndex): latest_data.columns = latest_data.columns.droplevel('Ticker')
                
                cur_p = float(latest_data['Close'].iloc[-1])
                close_hist = hist_df['Close']
                
                score = 50 # Base
                reasons = []
                
                # --- Strategy Modules ---
                if strategy == "CAN SLIM (William O'Neil)":
                    hi_52 = close_hist.max()
                    dist_hi = (hi_52 - cur_p) / hi_52
                    ma50 = close_hist.rolling(window=50).mean().iloc[-1]
                    ma200 = close_hist.rolling(window=200).mean().iloc[-1]
                    if cur_p > ma50 > ma200 and dist_hi < 0.20:
                        score += 40
                        reasons.append("Institutional Breakout Trend")
                    else: score -= 20
                    
                elif strategy == "Minervini Trend Template":
                    ma50 = close_hist.rolling(window=50).mean().iloc[-1]
                    ma150 = close_hist.rolling(window=150).mean().iloc[-1]
                    ma200 = close_hist.rolling(window=200).mean().iloc[-1]
                    if cur_p > ma50 > ma150 > ma200:
                        score += 45
                        reasons.append("Perfect Stage-2 Alignment")
                    else: score -= 30
                    
                elif strategy == "Low-Cap Moonshot (Beta)":
                    v_sma = hist_df['Volume'].rolling(window=20).mean().iloc[-1]
                    v_ratio = latest_data['Volume'].sum() / v_sma if v_sma > 0 else 1.0
                    if v_ratio > 2.0:
                        score += 50
                        reasons.append("High Volume Accumulation")
                    else: score -= 10

                else: # Strong Formula
                    ma20 = close_hist.rolling(window=20).mean().iloc[-1]
                    ma50 = close_hist.rolling(window=50).mean().iloc[-1]
                    if cur_p > ma20 > ma50:
                        score += 20
                        reasons.append("Strong Price Action")
                    
                    rsi = self.calculate_rsi(close_hist).iloc[-1]
                    if 40 < rsi < 70: 
                        score += 20
                        reasons.append("Healthy RSI Structure")

                return {'ticker': ticker, 'score': score, 'current_price': cur_p, 'reasons': reasons}
            except:
                return None

        with ThreadPoolExecutor(max_workers=5) as executor:
            raw_results = list(executor.map(process_ticker, scan_list))
            
        results = [r for r in raw_results if r is not None and r['score'] >= 60]
        return sorted(results, key=lambda x: x['score'], reverse=True)[:limit]
