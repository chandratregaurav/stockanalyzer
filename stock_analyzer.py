
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
        if self.data is None or len(self.data) < 5:
            return

        df = self.data
        # 1. Bollinger Bands (20-day, but adaptive)
        df['MA20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        df['STD20'] = df['Close'].rolling(window=20, min_periods=1).std()
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

    def generate_forecast(self, days=30):
        """
        Generates financial projections using Monte Carlo simulation (Geometric Brownian Motion).
        This is the industry standard for modeling stock price paths.
        """
        import numpy as np
        
        if self.data is None or len(self.data) < 5:
            print("Insufficient data for Monte Carlo.")
            return None

        df = self.data.copy()
        
        # 1. Calculate Returns & Volatility
        # Log returns are additive and standard for GBM
        df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Volatility (Sigma): Standard deviation of returns
        sigma = df['Log_Ret'].std()
        
        # Drift (Mu): Average return
        # To make it "Smart", we don't just take the simple mean of the whole period.
        # We blend the Long-term Mean with the Short-term Mean (Momentum).
        mu_long = df['Log_Ret'].mean()
        
        # Short-term (last 20 days or 1/4th of data)
        short_window = min(20, len(df) // 4)
        if short_window > 2:
            mu_short = df['Log_Ret'].tail(short_window).mean()
        else:
            mu_short = mu_long
            
        # Weighted Drift: 60% Short-term (Momentum), 40% Long-term (Mean Reversion anchor)
        # This prevents "horizontal lines" by respecting recent powerful moves.
        mu = (0.6 * mu_short) + (0.4 * mu_long)
        
        # Annualize for reference (optional debug)
        # annual_vol = sigma * np.sqrt(252)
        # annual_ret = mu * 252
        
        # 2. Monte Carlo Simulation (Geometric Brownian Motion)
        # Formula: S_t = S_0 * exp((mu - 0.5*sigma^2)*t + sigma*W_t)
        
        last_price = df['Close'].iloc[-1]
        simulation_runs = 1000 # Run 1000 possible futures
        
        # Generate random shocks for all runs at once
        # Shape: (days, simulation_runs)
        dt = 1 # 1 day time step
        random_shocks = np.random.normal(0, 1, (days, simulation_runs))
        
        # Calculate drift component (constant)
        drift_comp = (mu - 0.5 * sigma**2) * dt
        
        # Calculate diffusion component (random)
        diffusion_comp = sigma * np.sqrt(dt) * random_shocks
        
        # Sum them to get daily log returns for every path
        daily_log_returns = drift_comp + diffusion_comp
        
        # Cumulative sum to get total return curve
        cumulative_log_returns = np.cumsum(daily_log_returns, axis=0)
        
        # Convert to prices
        # prices[t] = last_price * exp(cumulative_log_returns[t])
        future_prices = last_price * np.exp(cumulative_log_returns)
        
        # 3. Aggregation (The "Prediction")
        # We take the MEDIAN path as the most probable "Center" forecast.
        # We can also return 10th and 90th percentile for confidence intervals later.
        median_path = np.median(future_prices, axis=1)
        
        # 4. Construct Output
        future_predictions = []
        
        # Determine step size (Days)
        last_date = df.index[-1]
        if isinstance(last_date, (int, float)): # If index is not datetime (rare)
             last_date = date.today()
             
        for i in range(days):
            price = median_path[i]
            future_predictions.append({
                'Date': (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                'Price': price,
                'Day': i+1
            })

        # 5. Generate Key Targets
        targets = {}
        target_days = [10, 30, 60, 90, 120]
        
        for d in target_days:
            if d <= len(future_predictions):
                p = future_predictions[d-1]['Price']
                chg = ((p - last_price) / last_price) * 100
                targets[d] = {'price': p, 'change': chg}
        
        return {
            'model_name': 'Monte Carlo (GBM) Simulation',
            'projections': future_predictions,
            'targets': targets,
            'last_close': last_price,
            'volatility': sigma
        }
        
        return {
            'model_name': 'RandomForest AI (Recursive)',
            'projections': future_predictions,
            'targets': targets,
            'last_close': base_price
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
