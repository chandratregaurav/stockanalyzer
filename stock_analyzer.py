
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

    def generate_forecast(self, days=30, model_type='Monte Carlo (GBM)'):
        """
        Generates concrete price predictions using the selected strategy.
        
        Args:
            days (int): Number of days to forecast.
            model_type (str): 'Monte Carlo (GBM)', 'Random Forest AI', 'Linear Regression (Trend)'
        """
        import numpy as np
        from datetime import timedelta, date
        
        if self.data is None or len(self.data) < 30:
            print("Insufficient data for forecasting.")
            return None

        df = self.data.copy()
        last_price = df['Close'].iloc[-1]
        
        # Determine step size (Days)
        last_date = df.index[-1]
        if isinstance(last_date, (int, float)):
             last_date = date.today()
             
        future_predictions = []

        # --- STRATEGY 1: Monte Carlo (GBM) ---
        if model_type == 'Monte Carlo (GBM)':
            # Log returns
            df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
            sigma = df['Log_Ret'].std()
            
            # Weighted Drift
            mu_long = df['Log_Ret'].mean()
            short_window = min(20, len(df) // 4)
            if short_window > 2:
                mu_short = df['Log_Ret'].tail(short_window).mean()
            else:
                mu_short = mu_long
            # Weighted Drift: Heavy biased towards recent momentum (90%)
            # This ensures the projection follows the immediate trend, solving the "flat line" issue
            mu = (0.9 * mu_short) + (0.1 * mu_long)
            
            # Simulation
            simulation_runs = 1000
            dt = 1
            random_shocks = np.random.normal(0, 1, (days, simulation_runs))
            drift_comp = (mu - 0.5 * sigma**2) * dt
            diffusion_comp = sigma * np.sqrt(dt) * random_shocks
            
            daily_log_returns = drift_comp + diffusion_comp
            cumulative_log_returns = np.cumsum(daily_log_returns, axis=0)
            future_prices = last_price * np.exp(cumulative_log_returns)
            
            # Median Path
            median_path = np.median(future_prices, axis=1)
            
            for i in range(days):
                future_predictions.append({
                    'Date': (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                    'Price': median_path[i],
                    'Day': i+1
                })

        # --- STRATEGY 2: Random Forest AI ---
        elif model_type == 'Random Forest AI':
            from sklearn.ensemble import RandomForestRegressor
            
            # Features
            df['Lag_1'] = df['Close'].shift(1)
            df['Lag_2'] = df['Close'].shift(2)
            df['Lag_5'] = df['Close'].shift(5)
            df['MA_10'] = df['Close'].rolling(window=10).mean()
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            df = df.dropna()
            
            if df.empty: return None
            
            X = df[['Lag_1', 'Lag_2', 'Lag_5', 'MA_10', 'MA_20']].values
            y = df['Close'].values
            
            model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            model.fit(X, y)
            
            # Recursive Forecast
            history_buffer = list(df['Close'].values[-20:])
            # Initial Input
            current_input = [
                history_buffer[-1], history_buffer[-2], history_buffer[-5],
                sum(history_buffer[-10:])/10, sum(history_buffer[-20:])/20
            ]
            current_input = np.array([current_input])
            
            for i in range(1, days + 1):
                pred_price = model.predict(current_input)[0]
                
                # Dynamic Constraint (Limit volatility to 5% per day to prevent explosion)
                prev = history_buffer[-1]
                pred_price = max(prev * 0.95, min(prev * 1.05, pred_price))
                
                future_predictions.append({
                    'Date': (last_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'Price': pred_price,
                    'Day': i
                })
                
                history_buffer.append(pred_price)
                history_buffer.pop(0)
                # Recalculate features
                new_input = [
                    history_buffer[-1], history_buffer[-2], history_buffer[-5],
                    sum(history_buffer[-10:])/10, sum(history_buffer[-20:])/20
                ]
                current_input = np.array([new_input])

        # --- STRATEGY 3: Linear Regression (Trend) ---
        elif model_type == 'Linear Regression (Trend)':
            from sklearn.linear_model import LinearRegression
            
            # Prepare X (timestamps) and y (prices)
            # Use whole period for trend
            df['Timestamp'] = df.index.astype(int) / 10**9 # Convert ns to seconds
            X = df[['Timestamp']].values.reshape(-1, 1)
            y = df['Close'].values
            
            lr = LinearRegression()
            lr.fit(X, y)
            
            # Predict
            start_ts = last_date.timestamp()
            seconds_per_day = 86400
            
            for i in range(1, days + 1):
                next_ts = start_ts + (i * seconds_per_day)
                pred_price = lr.predict([[next_ts]])[0]
                
                future_predictions.append({
                    'Date': (last_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'Price': pred_price,
                    'Day': i
                })

        # --- Common Output Construction ---
        targets = {}
        target_days = [10, 30, 60, 90, 120]
        
        for d in target_days:
            if d <= len(future_predictions):
                p = future_predictions[d-1]['Price']
                chg = ((p - last_price) / last_price) * 100
                targets[d] = {'price': p, 'change': chg}
        
        return {
            'model_name': model_type,
            'projections': future_predictions,
            'targets': targets,
            'last_close': last_price
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
