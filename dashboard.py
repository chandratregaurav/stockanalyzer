
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
import time
import importlib
import json
import os

# --- Page Configuration (MUST be first Streamlit command) ---
st.set_page_config(page_title="Stock Analysis Pro", layout="wide")

# Force Uppercase Display CSS
st.markdown("""
<style>
    input {
        text-transform: uppercase !important;
    }
</style>
""", unsafe_allow_html=True)

# Custom Modules
import stock_screener
importlib.reload(stock_screener)
from stock_screener import StockScreener
from stock_analyzer import StockAnalyzer

# Paper Trading & Assets
from paper_trader import PaperTrader
try:
    from assets import ALERT_SOUND_B64
except ImportError:
    ALERT_SOUND_B64 = "" 

# --- Market Hours Check ---
def is_market_open():
    """Check if NSE/BSE is open (9:15 AM - 3:30 PM IST, Mon-Fri)."""
    now = datetime.now()
    # Check weekday (0=Monday, 6=Sunday)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False, "Market Closed (Weekend)"
    
    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    
    if now < market_open:
        return False, f"Market Opens at 9:15 AM (in {(market_open - now).seconds // 60} mins)"
    elif now > market_close:
        return False, "Market Closed for today (After 3:30 PM)"
    else:
        return True, "Market is LIVE 🟢"

# --- Initialization ---
if 'trader' not in st.session_state:
    st.session_state['trader'] = PaperTrader(initial_balance=50000.0)

def play_alert_sound():
    """Plays a beep sound using HTML5 Audio from assets."""
    if ALERT_SOUND_B64 and st.session_state.get('audio_enabled', False):
        # Browsers require user interaction before playing audio. 
        # The toggle 'audio_enabled' satisfies this.
        st.markdown(
            f'<audio autoplay="true" style="display:none;"><source src="{ALERT_SOUND_B64}" type="audio/wav"></audio>',
            unsafe_allow_html=True
        )

st.title("📈 Stock Analysis & Projection")

# --- Constants ---
@st.cache_data
def load_ticker_db():
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, "ticker_db.json")
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            data = json.load(f)
            # Ensure uniqueness and sorted order
            data = sorted(data, key=lambda x: x['symbol'])
            return data
    return []

TICKER_DB = load_ticker_db()
TICKER_MAP = {s['symbol']: s['name'] for s in TICKER_DB}
TICKER_OPTIONS = [f"{s['symbol']} - {s['name']}" for s in TICKER_DB]

POPULAR_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LICI.NS",
    "RAJESHEXPO.NS", "NETWEB.NS", "ZOMATO.NS", "PAYTM.NS", "TATAMOTORS.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "BAJFINANCE.NS", "DLF.NS", "HAL.NS",
    "VBL.NS", "TRENT.NS", "COALINDIA.NS", "ONGC.NS", "SUNPHARMA.NS",
    "GOOGL", "AAPL", "MSFT", "AMZN", "NVDA", "TSLA", "META"
]

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("⚙️ Controls")
    st.session_state['audio_enabled'] = st.checkbox("🔊 Enable Sound Alerts", value=True)
    st.session_state['exchange'] = st.radio("Select Exchange", ["NSE", "BSE"], horizontal=True)
    st.divider()
    
    st.divider()
# --- Sidebar Navigation Logic (Robust) ---
nav_options = ["🔍 Deep Analyzer", "🚀 Trending Picks (Top 5)", "⚡ Intraday Surge (1-2 Hr)", "📊 Portfolio & Analytics"]

# Key-Rotation Pattern: Bypasses Streamlit's internal widget state
if 'nav_key' not in st.session_state:
    st.session_state['nav_key'] = 0

if 'page_target' in st.session_state:
    # Programmatic navigation requested!
    st.session_state['nav_key'] += 1 # Change key to force widget refresh
    try:
        nav_index = nav_options.index(st.session_state['page_target'])
    except:
        nav_index = 0
else:
    nav_index = 0

page = st.sidebar.radio("Navigation", nav_options, index=nav_index, key=f"nav_radio_{st.session_state['nav_key']}")

# Cleanup target after it influenced the widget
if 'page_target' in st.session_state:
    del st.session_state['page_target']

if page == "🔍 Deep Analyzer":
    # --- Sidebar Inputs for Analyzer ---
    with st.sidebar:
        st.header("Configuration")
        # Ticker Selection & Search
        st.write("### 🔍 Search Stock")
        
        # Get target ticker or default
        ticker_val = st.session_state.get('ticker_target', "")
        
        # Helper: Sync Logic
        def sync_from_list():
            if st.session_state['master_search']:
                sym = st.session_state['master_search'].split(' - ')[0]
                st.session_state['manual_ticker'] = sym

        # 1. Universal Search (SYMBOL - NAME)
        # We find the pre-selected index if ticker_val exists
        select_idx = None
        if ticker_val:
            clean_ticker = ticker_val.split('.')[0]
            for i, opt in enumerate(TICKER_OPTIONS):
                if opt.startswith(f"{clean_ticker} -"):
                    select_idx = i
                    break

        st.selectbox(
            "Search Ticker or Company Name",
            TICKER_OPTIONS,
            index=select_idx,
            key="master_search",
            on_change=sync_from_list,
            help="Type to search through 500+ Indian stocks"
        )

        # 2. Manual Ticker (Auto-Uppercase via CSS + Logic)
        ticker_input_raw = st.text_input(
            "Ticker (e.g. RELIANCE)", 
            value=ticker_val if ticker_val else "",
            key="manual_ticker",
            help="Characters appear in UPPERCASE as you type!"
        ).upper()
        
        # Show detected name if ticker matches
        clean_manual = ticker_input_raw.split('.')[0]
        if clean_manual in TICKER_MAP:
             st.caption(f"✨ Detected: **{TICKER_MAP[clean_manual]}**")

        # Cleanup target
        if 'ticker_target' in st.session_state:
            del st.session_state['ticker_target']
        
        # Final Ticker Processing
        if ticker_input_raw:
            suffix = ".NS" if st.session_state.get('exchange', 'NSE') == "NSE" else ".BO"
            ticker_input = ticker_input_raw if "." in ticker_input_raw else f"{ticker_input_raw}{suffix}"
        else:
            # Fallback to selection if manual is empty
            if st.session_state.get('master_search'):
                sym = st.session_state['master_search'].split(' - ')[0]
                suffix = ".NS" if st.session_state.get('exchange', 'NSE') == "NSE" else ".BO"
                ticker_input = f"{sym}{suffix}"
            else:
                ticker_input = "RELIANCE.NS" # True fallback
        
        # Date Selection
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("Start Date", date.today() - timedelta(days=365))
        with c2:
             end_date = st.date_input("End Date", date.today())
             
        # Interval Selection (New)
        interval_choice = st.selectbox("Data Interval", ["Daily (1d)", "Hourly (1h)"])
        interval_code = "1h" if "Hourly" in interval_choice else "1d"
        
        # Smart Logic: Warn/Switch if range is short
        days_diff = (end_date - start_date).days
        if days_diff < 7 and interval_code == "1d":
            st.warning("⚠️ Range < 7 days. Switching to Hourly data for better charts.")
            interval_code = "1h"
        
        # Auto-trigger if redirected
        if st.session_state.get('trigger_analyze', False):
             st.session_state['trigger_analyze'] = False # Reset
             auto_click = True
        else:
             auto_click = False

        if st.button("Generate Projections", type="primary") or auto_click:
            with st.spinner(f"Fetching {interval_code} data for {ticker_input}..."):
                analyzer = StockAnalyzer(ticker_input)
                # Fetch Data & Fundamentals
                success = analyzer.fetch_data(start=start_date, end=end_date, interval=interval_code)
                analyzer.fetch_fundamentals()
                analyzer.get_news()
                
                if success and analyzer.data is not None and not analyzer.data.empty:
                    df = analyzer.data
                    st.session_state['data'] = df
                    st.session_state['analyzer'] = analyzer
                    st.session_state['ticker'] = ticker_input
                    st.success("Analysis Ready!")
                else:
                    st.error("No data found. Check ticker or date range.")

        # --- Indicator Toggles ---
        st.write("### 📊 Chart Options")
        show_bb = st.checkbox("Bollinger Bands", value=False)
        show_emas = st.checkbox("EMA Cloud (20/50/200)", value=False)
        show_macd = st.checkbox("Show MACD Chart", value=True)

    # --- Analyzer Main Content ---
    if 'data' in st.session_state:
        df = st.session_state['data']
        analyzer = st.session_state['analyzer']
        ticker = st.session_state['ticker']
        
        st.header(f"{ticker} Analysis ({len(df)} candles)")
        
        # --- Quick Alert UI (Relocated) ---
        with st.expander("🔔 Set Real-Time Price Alert", expanded=False):
            c1, c2 = st.columns([2, 1])
            with c1:
                cur_p = float(df['Close'].iloc[-1])
                new_a = st.number_input(f"Target Price for {ticker}", value=cur_p, step=1.0, key="screen_alert_val")
            with c2:
                if st.button("Confirm Alert", use_container_width=True, key="screen_alert_btn"):
                    if 'alerts' not in st.session_state: st.session_state['alerts'] = []
                    st.session_state['alerts'].append({"ticker": ticker, "price": new_a, "active": True})
                    st.toast(f"Alert Active: {ticker} @ ₹{new_a}", icon="🚀")
        st.divider()
        
        # 1. Fundamentals Section (New)
        if analyzer.info:
            with st.container():
                st.subheader("🏛️ Fundamentals & Info")
                info = analyzer.info
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Market Cap", f"₹{info['market_cap']/1e7:.1f} Cr")
                c2.metric("P/E Ratio", f"{info['pe']:.1f}")
                c3.metric("Div. Yield", f"{info['dividend_yield']:.1f}%")
                c4.metric("Beta", f"{info['beta']:.2f}")
                
                with st.expander("Business Summary"):
                    st.write(f"**Sector:** {info['sector']}")
                    st.write(f"**52W Range:** ₹{info['52w_low']:.2f} - ₹{info['52w_high']:.2f}")
                    st.write(info['summary'])
                
                st.divider()

        # 2. Candlestick Chart (Interactive)
        st.subheader("Interactive Price Chart")
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name="Price")])
        
        # Add Bollinger Bands if requested
        if show_bb and 'Upper_Band' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['Upper_Band'], name='BB Upper', line=dict(color='rgba(173, 216, 230, 0.4)', width=1)))
            fig.add_trace(go.Scatter(x=df.index, y=df['Lower_Band'], name='BB Lower', line=dict(color='rgba(173, 216, 230, 0.4)', width=1), fill='tonexty'))
            
        # Add EMAs if requested
        if show_emas:
            if 'EMA20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='EMA 20', line=dict(color='yellow', width=1)))
            if 'EMA50' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50', line=dict(color='orange', width=1)))
            if 'EMA200' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='red', width=1.5)))

        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # 3. MACD Chart (New Sub-chart)
        if show_macd and 'MACD' in df.columns:
            macd_fig = go.Figure()
            macd_fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue', width=1.5)))
            macd_fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name='Signal', line=dict(color='orange', width=1)))
            macd_fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Hist', marker_color='gray', opacity=0.5))
            macd_fig.update_layout(height=250, title="MACD (12, 26, 9)", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(macd_fig, use_container_width=True)
        
        # 2. Projections
        st.subheader("🔮 Blended Momentum Projections (Multi-Horizon)")
        st.markdown("""
        **Methodology:** 
        *   **Short-Term (10-30 Days):** Follows current 30-Day Momentum.
        *   **Long-Term (60-90 Days):** Anchors back to the Yearly Trend.
        *   **Curved Path:** Uses a weighted blend for a realistic flight path.
        """)
        
        projections = analyzer.analyze_and_project()
        
        # Display Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Price", f"{projections['current_price']:.2f}")
        
        p10 = projections['forecasts'][10]
        c2.metric("10-Day Target", f"{p10['price']:.2f}", f"{p10['change']:.2f}%")
        
        p30 = projections['forecasts'][30]
        c3.metric("30-Day Target", f"{p30['price']:.2f}", f"{p30['change']:.2f}%")
        
        p90 = projections['forecasts'][90]
        c4.metric("90-Day Target", f"{p90['price']:.2f}", f"{p90['change']:.2f}%")
        
        # Charting the Projection
        projected_dates = [datetime.today() + timedelta(days=i) for i in [10, 30, 60, 90]]
        # Wait, the projections['forecasts'] is keyed by integer days.
        
        proj_fig = go.Figure()
        
        # Historical
        proj_fig.add_trace(go.Scatter(x=df.index[-60:], y=df['Close'][-60:], name='History (60d)', line=dict(color='gray')))
        
        # Segments
        colors = ['green', 'blue', 'orange', 'red']
        prev_date = df.index[-1]
        prev_price = projections['current_price']
        
        for i, days in enumerate([10, 30, 60, 90]):
            tgt_date = datetime.today() + timedelta(days=days)
            tgt_price = projections['forecasts'][days]['price']
            
            proj_fig.add_trace(go.Scatter(
                x=[prev_date, tgt_date], 
                y=[prev_price, tgt_price],
                mode='lines+markers',
                line=dict(width=3, color=colors[i]),
                name=f'{days}d Horizon'
            ))
            prev_date = tgt_date
            prev_price = tgt_price
            
        st.plotly_chart(proj_fig, use_container_width=True)

        # 4. News Section (Optimized)
        st.subheader("📰 Latest News")
        if analyzer.news:
            for n in analyzer.news:
                # yfinance news keys: 'title', 'publisher', 'link', 'providerPublishTime'
                title = n.get('title', n.get('headline', 'News Update'))
                pub = n.get('publisher', n.get('source', 'Financial News'))
                url = n.get('link', n.get('url', '#'))
                
                with st.expander(f"📌 {title}"):
                    st.write(f"**Source:** {pub}")
                    if url != '#':
                        st.markdown(f"[Read Full Article]({url})")
                    else:
                        st.write("*Link unavailable*")
        else:
            st.info("No recent headlines found for this stock.")

elif page == "📊 Portfolio & Analytics":
    st.header("📊 Portfolio Performance & Analytics")
    trader = st.session_state['trader']
    
    # 1. Performance Overview
    c1, c2, c3, c4 = st.columns(4)
    # Get current holdings value to update equity
    curr_prices = {} 
    # (Simple fallback: use average price if we don't have a live scan running)
    for t, p in trader.positions.items(): curr_prices[t] = p['avg_price']
    
    total_val = trader.get_portfolio_value(curr_prices)
    
    c1.metric("Total Value", f"₹{total_val:.2f}")
    c2.metric("Cash", f"₹{trader.cash:.2f}")
    c3.metric("Total P&L", f"₹{trader.total_profit:.2f}")
    
    # Equity history logging (Simple: logs once per page view for demo)
    if not trader.equity_history or trader.equity_history[-1]['value'] != total_val:
        trader.log_portfolio_value(curr_prices)

    # 2. Equity Curve
    st.subheader("📈 Portfolio Equity Curve")
    if trader.equity_history:
        h_df = pd.DataFrame(trader.equity_history)
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(x=h_df['ts'], y=h_df['value'], mode='lines+markers', name='Equity', line=dict(color='#00FF00', width=2)))
        fig_equity.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_equity, use_container_width=True)
    
    # 3. Allocation
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("💼 Allocation")
        if trader.positions:
            labels = list(trader.positions.keys()) + ["Cash"]
            values = [p['qty']*p['avg_price'] for p in trader.positions.values()] + [trader.cash]
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No open positions.")
    
    with col_b:
        st.subheader("📝 Trade Statistics")
        st.write(f"- **Initial Capital:** ₹{trader.initial_balance:.2f}")
        st.write(f"- **Total Trades:** {len(trader.trade_log)}")
        st.write(f"- **Current Holdings:** {len(trader.positions)}")

elif page == "🚀 Trending Picks (Top 5)":
    st.header("🚀 Top 5 Trending Stocks")
    st.markdown("""
    Scans the market for stocks with the **Strongest Momentum** today.
    
    *   **Trend (40pts):** Is price above 50-SMA?
    *   **Momentum (30pts):** Is RSI healthy (40-70)?
    *   **Volume (30pts):** Is there a recent volume spike (>1.5x average)?
    """)
    
    if st.button("Start Market Scan", type="primary"):
        screener = StockScreener(POPULAR_STOCKS)
        
        progress_text = "Scanning market leaders... Please wait."
        my_bar = st.progress(0, text=progress_text)
        
        with st.spinner("Analyzing price action, volume, and momentum..."):
            top_picks = screener.screen_market()
            st.session_state['market_picks_global'] = top_picks
            my_bar.progress(100, text="Scan Complete!")
            
    # Persistent Results Display
    top_picks = st.session_state.get('market_picks_global', [])
    if top_picks:
        st.success(f"Found {len(top_picks)} potential winners!")
        
        for i, pick in enumerate(top_picks):
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    st.subheader(f"#{i+1} {pick['ticker']}")
                    st.caption(f"Price: {pick['price']:.2f}")
                    
                with col2:
                    st.metric("Recommendation Score", f"{pick['score']}/100", f"{pick['change_pct']:.2f}% Today")
                    st.markdown(f"**Why:** {pick['reasons']}")
                    
                with col3:
                     if st.button(f"Analyze {pick['ticker']}", key=f"btn_trend_global_{i}"):
                         st.session_state['page_target'] = "🔍 Deep Analyzer"
                         st.session_state['ticker_target'] = pick['ticker']
                         st.session_state['trigger_analyze'] = True
                         st.rerun()
                
                st.divider()
    elif 'market_picks_global' in st.session_state:
        st.warning("No stocks met the strict criteria today. Market might be choppy.")

elif page == "⚡ Intraday Surge (1-2 Hr)":
    st.header("⚡ Intraday Scalper & Paper Bot")
    
    # Strict Market Hours Enforcement for this page
    market_open, market_msg = is_market_open()
    
    if not market_open:
        st.warning(f"🌙 {market_msg}")
        st.info("This section is only active during live market hours (9:15 AM - 3:30 PM IST).")
        st.stop() # Prevents showing the tabs and logic below

    st.info("⚠️ **Uses Live Hourly Data.** Market is LIVE. Happy Trading!")

    tab1, tab2, tab3 = st.tabs(["🔔 Live Monitor", "🤖 Auto-Bot (Paper)", "🔥 Trending"])

    # --- TAB 1: Live Monitor ---
    with tab1:
        st.subheader("Market Monitor")
        col1, col2 = st.columns([1, 4])
        with col1:
            auto_refresh_monitor = st.toggle("🔔 Start Monitor (1m Loop)", value=False, key="toggle_monitor")
        
        monitor_placeholder = st.empty()
        
        if auto_refresh_monitor:
            st.toast("Monitor Started! Do not close this tab.")
            while True:
                with monitor_placeholder.container():
                    # Check if market is open
                    market_open, market_msg = is_market_open()
                    st.caption(f"🔔 {datetime.now().strftime('%H:%M:%S')} | {market_msg}")
                    
                    if not market_open:
                        st.warning(f"⏸️ {market_msg} - Monitor paused.")
                        time.sleep(60)
                        st.rerun()
                        continue

                    screener = StockScreener(POPULAR_STOCKS)
                    with st.spinner("Scanning..."):
                        top_scalps = screener.screen_intraday()
                    
                    if top_scalps:
                        st.error("🚨 OPPORTUNITY DETECTED! 🚨")
                        # Sound Alert
                        play_alert_sound()
                        
                        for i, scalp in enumerate(top_scalps):
                             with st.container():
                                 c1, c2, c3 = st.columns([1, 2, 1])
                                 with c1:
                                     st.subheader(f"⚡ {scalp['ticker']}")
                                     st.caption(f"Price: {scalp['price']:.2f}")
                                 with c2:
                                     # Convert last_hour_change to float if it isn't
                                     change_val = scalp['last_hour_change']
                                     if isinstance(change_val, str):
                                          change_val = float(str(change_val).replace('%', ''))
                                     st.metric("Score", f"{scalp['score']}", f"{change_val:.2f}%")
                                     st.markdown(f"**Trigger:** {scalp['reasons']}")
                                 st.divider()
                    else:
                        st.success("No setups found. Waiting...")
                
                time.sleep(15)
                st.rerun()

    # --- TAB 2: Paper Trading Bot ---
    with tab2:
        trader = st.session_state['trader']
        
        st.write("### 💼 Virtual Portfolio (₹50,000 Capital)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Cash Balance", f"₹{trader.cash:.2f}")
        m2.metric("Realized P&L", f"₹{trader.total_profit:.2f}")
        m3.metric("Open Positions", len(trader.positions))
        
        st.divider()
        
        # Bot Control
        col_bot, _ = st.columns([1, 4])
        with col_bot:
            auto_bot_active = st.toggle("🤖 START AUTO-TRADING BOT", value=False, key="toggle_bot")

        bot_placeholder = st.empty()
        log_placeholder = st.container()

        if auto_bot_active:
            st.toast("🤖 Bot Activated! Trading automatically...")
            
            while True:
                with bot_placeholder.container():
                    # Check if market is open
                    market_open, market_msg = is_market_open()
                    st.caption(f"🤖 {datetime.now().strftime('%H:%M:%S')} | {market_msg}")
                    
                    if not market_open:
                        st.warning(f"⏸️ {market_msg} - Bot paused.")
                        time.sleep(60)
                        st.rerun()
                        continue
                    
                    screener = StockScreener(POPULAR_STOCKS)
                    
                    with st.spinner("Scanning for opportunities..."):
                        # Run the Scan
                        top_scalps = screener.screen_intraday()
                        
                        # A. Check Exits
                        current_prices_map = {}
                        if trader.positions:
                             for t in trader.positions.keys():
                                 try:
                                     # Optimization: If the stock is in top_scalps, use that price
                                     found_in_scan = False
                                     if top_scalps:
                                         for s in top_scalps:
                                             if s['ticker'] == t:
                                                 current_prices_map[t] = s['price']
                                                 found_in_scan = True
                                                 break
                                     
                                     if not found_in_scan:
                                          import yfinance as yf
                                          tick = yf.Ticker(t)
                                          # Use fast_info or fallback
                                          try:
                                              p = tick.fast_info['last_price']
                                              if p: current_prices_map[t] = p
                                          except:
                                              d = yf.download(t, period="1d", interval="1m", progress=False)
                                              if not d.empty:
                                                  current_prices_map[t] = d['Close'].iloc[-1]
                                 except:
                                     pass
                        
                        exit_msgs = trader.check_auto_exit(current_prices_map)
                        if exit_msgs:
                            play_alert_sound()
                            for msg in exit_msgs:
                                st.toast(msg, icon="💰")

                        # C. Check Custom Alerts (New)
                        if st.session_state.get('alerts'):
                            for i, alert in enumerate(st.session_state['alerts']):
                                if alert['active']:
                                    t = alert['ticker']
                                    target_p = alert['price']
                                    # Use price from scan if available
                                    current_p = current_prices_map.get(t)
                                    if current_p:
                                        # Trigger if price hits or crosses target
                                        if current_p >= target_p:
                                            play_alert_sound()
                                            st.toast(f"🚨 ALERT: {t} hit ₹{current_p:.2f}! (Target: ₹{target_p})", icon="🔥")
                                            st.session_state['alerts'][i]['active'] = False # Deactivate after trigger

                        # B. Check Entries
                        if top_scalps:
                            best_pick = top_scalps[0]
                            ticker = best_pick['ticker']
                            price = best_pick['price']
                            score = best_pick['score']
                            
                            # Buy Condition: Score > 50 
                            if score >= 50:
                                success, msg = trader.buy(ticker, price)
                                if success:
                                    play_alert_sound()
                                    st.toast(msg, icon="🛍️")
                        
                        # Display Status
                        if top_scalps:
                            st.info(f"Top Pick: {top_scalps[0]['ticker']} (Score: {top_scalps[0]['score']})")
                        else:
                            st.write("Market Quiet. No new buys.")
                            
                # Log 
                with log_placeholder:
                    with st.expander("📜 Trade Log", expanded=True):
                        for log in trader.trade_log:
                            st.text(log)
                            
                time.sleep(15)
                st.rerun()

        # Display Open Positions Table (When not running loop)
        if trader.positions:
            st.subheader("Current Holdings")
            pos_data = []
            for t, p in trader.positions.items():
                pos_data.append({
                    "Ticker": t,
                    "Qty": p['qty'],
                    "Avg Price": f"₹{p['avg_price']:.2f}",
                    "Value": f"₹{p['qty']*p['avg_price']:.2f}"
                })
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
            
        with st.expander("📜 Trade Log"):
             for log in trader.trade_log:
                 st.text(log)

    # --- TAB 3: Trending Stocks ---
    with tab3:
        st.subheader("🔥 Market Movers (Day's Top Picks)")
        
        # Market Check for Trending
        st.success("✅ Market is LIVE. Scanning Popular Indian Stocks.")
        
        if st.button("Scan Market", key="trending_scan"):
            with st.spinner("Scanning top Indian stocks..."):
                screener = StockScreener(POPULAR_STOCKS)
                market_picks = screener.screen_market()
                st.session_state['market_picks_intraday'] = market_picks
                
        # Persistent Display for Tab 3
        market_picks = st.session_state.get('market_picks_intraday', [])
        if market_picks:
            for i, pick in enumerate(market_picks):
                with st.container():
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        st.subheader(pick['ticker'])
                        st.caption(f"₹{pick['price']:.2f}")
                    with c2:
                        st.metric("RSI", f"{pick['rsi']:.1f}", f"{pick['change_pct']:.2f}%")
                        st.write(f"**Why:** {pick['reasons']}")
                    with c3:
                        if st.button(f"Analyze {pick['ticker']}", key=f"btn_trend_intra_{i}"):
                             st.session_state['page_target'] = "🔍 Deep Analyzer"
                             st.session_state['ticker_target'] = pick['ticker']
                             st.session_state['trigger_analyze'] = True
                             st.rerun()
                    st.divider()
        elif 'market_picks_intraday' in st.session_state:
            st.warning("No strong trending setups found.")
