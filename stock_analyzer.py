
import yfinance as yf
import pandas as pd
from datetime import timedelta, date
from sklearn.linear_model import LinearRegression
import numpy as np

class StockAnalyzer:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = None
        self.model = None
        self.info = {}
        self.news = []

    def fetch_data(self, start=None, end=None, interval='1d'):
        """Fetches historical data.
        
        Args:
            start (date, optional): Start date. Defaults to 1 year ago.
            end (date, optional): End date. Defaults to today.
            interval (str, optional): Data interval. '1d' or '1h'. Defaults to '1d'.
        """
        print(f"Fetching data for {self.ticker} (Interval: {interval})...")
        
        if end is None:
            end = date.today()
        if start is None:
            start = end - timedelta(days=365)
            
        self.interval = interval
        
        # Download data
        # yfinance expects date objects or strings
        self.data = yf.download(self.ticker, start=start, end=end, interval=interval, progress=False, auto_adjust=True)
        
        # --- FIX: yfinance MultiIndex columns ---
        if isinstance(self.data.columns, pd.MultiIndex):
            self.data.columns = self.data.columns.droplevel('Ticker')
            
        self.data = self.data.loc[:, ~self.data.columns.duplicated()].copy()
        
        if self.data.empty:
            print(f"No data found for {self.ticker}")
            return False
            
        print(f"Successfully fetched {len(self.data)} rows of data.")
        self.calculate_indicators()
        return True

    def calculate_indicators(self):
        """Calculates advanced technical indicators (MACD, Bollinger Bands)."""
        if self.data is None or len(self.data) < 26:
            return

        df = self.data
        # 1. Bollinger Bands (20-day, 2 Std Dev)
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['STD20'] = df['Close'].rolling(window=20).std()
        df['Upper_Band'] = df['MA20'] + (df['STD20'] * 2)
        df['Lower_Band'] = df['MA20'] - (df['STD20'] * 2)

        # 2. MACD (12, 26, 9)
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

        # 3. EMAs
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        self.data = df

    def fetch_fundamentals(self):
        """Fetches fundamental data using yfinance.info."""
        try:
            tick = yf.Ticker(self.ticker)
            info = tick.info
            self.info = {
                'name': info.get('longName', self.ticker),
                'pe': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'market_cap': info.get('marketCap', 0),
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'beta': info.get('beta', 0),
                '52w_high': info.get('fiftyTwoWeekHigh', 0),
                '52w_low': info.get('fiftyTwoWeekLow', 0),
                'sector': info.get('sector', 'N/A'),
                'summary': info.get('longBusinessSummary', 'No summary available.')
            }
            return True
        except:
            return False

    def get_news(self):
        """Fetches recent news for the ticker."""
        try:
            tick = yf.Ticker(self.ticker)
            self.news = tick.news[:5] # Top 5 news items
            return self.news
        except:
            return []

    def analyze_and_project(self):
        """Analyzes data and projects targets."""
        if self.data is None or self.data.empty:
            print("No data to analyze. Please fetch data first.")
            return

        # Prepare data for regression
        df = self.data.copy()
        df = df.reset_index()
        
        # Handle MultiIndex columns if necessary
        if isinstance(df.columns, pd.MultiIndex):
             df.columns = df.columns.get_level_values(0)

        # Detect Date/Datetime column
        date_col = None
        for col in df.columns:
            # Check for both date and datetime types
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_col = col
                break
        
        if not date_col and 'Date' in df.columns:
             date_col = 'Date'
        elif not date_col and 'Datetime' in df.columns:
             date_col = 'Datetime'
             
        if not date_col:
            print("Could not find Date/Datetime column.")
            return

        close_col = 'Close'
        df = df.dropna(subset=[close_col])

        if len(df) < 5:
             print("Not enough data points for analysis.")
             return
             
        # Use Timestamp (seconds) for X to handle both dates and times (hours) uniformly
        df['Timestamp'] = df[date_col].apply(lambda x: x.timestamp())
        
        X = df[['Timestamp']].values
        y = df[close_col].values
        
        # --- Trend Calculation ---
        # 1. Long Term Trend (1 Year)
        # ---------------------------
        self.model = LinearRegression()
        self.model.fit(X, y)
        trend_long_per_sec = self.model.coef_[0]
        
        # 2. Short Term Trend (Last 30 Days)
        # ----------------------------------
        # Filter for last 30 days approx
        cutoff_idx = max(0, len(df) - 30)
        X_short = X[cutoff_idx:]
        y_short = y[cutoff_idx:]
        
        model_short = LinearRegression()
        model_short.fit(X_short, y_short)
        trend_short_per_sec = model_short.coef_[0]

        # Basic stats
        current_price = y[-1]
        
        # Display Trend (Show Long Term by default in metrics, or maybe weighted average)
        # Let's show Long Term as the "Trend" metric for stability
        trend_per_second = trend_long_per_sec
        
        # Convert trend to meaningful unit for display
        if self.interval == '1h':
            display_trend = trend_per_second * 3600  # Per Hour
            trend_unit = "per hour"
        else:
            display_trend = trend_per_second * 86400 # Per Day
            trend_unit = "per day"
        
        print(f"\n--- Analysis for {self.ticker} ---")
        
        last_data_date = df[date_col].iloc[-1]
        start_data_date = df[date_col].iloc[0]
        
        # For display, if it's datetime, keep time, if date, keep date
        if hasattr(last_data_date, 'date'):
             # It's likely a Timestamp
             pass 
        
        print(f"Data Freshness: {last_data_date}")
        print(f"Data Range: {start_data_date} to {last_data_date}")
        print(f"Analysis Date: {date.today()}")
        
        # Projections logic
        print(f"\n--- Projections ({'Next 24 Hours' if self.interval == '1h' else 'Next 90 Days'}) ---")
        print(f"Formula: Blended Momentum (Short Term -> Long Term)")
        
        predictions = []
        
        if self.interval == '1h':
            steps = 24
            step_delta = timedelta(hours=1)
            step_seconds = 3600
        else:
            steps = 90
            step_delta = timedelta(days=1)
            step_seconds = 86400

        # Simulation Loop
        simulated_price = current_price
        
        for i in range(1, steps + 1):
            next_time = last_data_date + (step_delta * i)
            
            # Determine effective slope for this step
            if self.interval == '1h':
                # For hourly, just use Short Term trend as it's intraday
                effective_slope = trend_short_per_sec
            else:
                # For Daily: Blend Short Term and Long Term
                # Days 1-10: 100% Short Term -> 50% Short Term
                # Days 10-30: 50% -> 0% Short Term (Transition to Long Term)
                # Days 30+: 100% Long Term
                if i <= 10:
                    weight_short = 1.0 - (0.2 * (i / 10)) # 1.0 down to 0.8
                elif i <= 30:
                    # Decay from 0.8 to 0.0
                    progress = (i - 10) / 20
                    weight_short = 0.8 * (1.0 - progress)
                else:
                    weight_short = 0.0
                
                effective_slope = (trend_short_per_sec * weight_short) + (trend_long_per_sec * (1.0 - weight_short))
            
            
            # Apply slope for this step
            simulated_price += (effective_slope * step_seconds)
            
            predictions.append({'Date': next_time, 'Projected_Close': simulated_price})
            
            # Print logic: Full print for hourly, Milestones for daily
            if self.interval == '1h':
                print(f"{next_time}: {simulated_price:.2f}")
            elif i in [10, 30, 60, 90]:
                print(f"Day {i} ({next_time.date()}): {simulated_price:.2f}")
            
        # Helper for Dashboard (Forecasts by Milestone)
        forecasts_map = {}
        for day_point in [10, 30, 60, 90]:
             # Find closest prediction
             if day_point <= len(predictions):
                 pred = predictions[day_point-1] # 0-indexed
                 p_price = pred['Projected_Close']
                 p_change = ((p_price - current_price) / current_price) * 100
                 forecasts_map[day_point] = {'price': p_price, 'change': p_change}
             else:
                 # Fallback if range is short (e.g. hourly)
                 # Just use last available as placeholder
                 if predictions:
                     pred = predictions[-1]
                     p_price = pred['Projected_Close']
                     p_change = ((p_price - current_price) / current_price) * 100
                     forecasts_map[day_point] = {'price': p_price, 'change': p_change}

        return {
            'historical_data': df[[date_col, close_col]],
            'projections': predictions,
            'forecasts': forecasts_map, # Added this key
            'current_price': current_price,
            'trend': display_trend,
            'trend_unit': trend_unit,
            'last_data_date': str(last_data_date),
            'start_data_date': str(start_data_date)
        }

    def get_pros_cons(self):
        """Generates heuristic-based Pros and Cons for the stock."""
        pros = []
        cons = []
        
        info = self.info
        df = self.data
        
        if not info or df is None or df.empty:
            return [], []

        # Fundamental Pros/Cons
        pe = info.get('pe', 0)
        div = info.get('dividend_yield', 0)
        beta = info.get('beta', 0)
        
        if 0 < pe < 20: pros.append("Attractive P/E: Stock is potentially undervalued relative to earnings.")
        elif pe > 50: cons.append("High P/E Ratio: Stock is trading at a high premium.")
        
        if div > 2: pros.append(f"Strong Dividends: Yield of {div:.1f}% provides passive income.")
        
        if beta > 1.5: cons.append(f"High Volatility: Beta of {beta:.2f} suggests significant price swings.")
        elif 0 < beta < 0.8: pros.append(f"Low Volatility: Beta of {beta:.2f} suggests a defensive, stable stock.")

        # Technical Pros/Cons
        cur_price = df['Close'].iloc[-1]
        if 'EMA200' in df.columns:
            ema200 = df['EMA200'].iloc[-1]
            if cur_price > ema200: pros.append("Bullish Trend: Trading above the 200-day EMA.")
            else: cons.append("Bearish Trend: Trading below the 200-day EMA.")

        # RSI logic (Calculate if not present)
        if 'RSI' not in df.columns:
            from stock_screener import StockScreener
            screener = StockScreener([]) # Empty for helper
            df['RSI'] = screener.calculate_rsi(df['Close'])
            
        rsi = df['RSI'].iloc[-1]
        if not np.isnan(rsi):
            if rsi < 35: pros.append(f"Oversold Condition: RSI ({rsi:.0f}) suggests a potential bounce.")
            elif rsi > 75: cons.append(f"Overbought Condition: RSI ({rsi:.0f}) suggests a possible correction.")
            elif 45 < rsi < 65: pros.append("Healthy Momentum: RSI is in a stable neutral-bullish zone.")

        return pros, cons

if __name__ == "__main__":
    # Simple test
    analyzer = StockAnalyzer("GOOGL")
    if analyzer.fetch_data():
        analyzer.analyze_and_project()
