
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
import time
import importlib
import json
import os
import yfinance as yf
import stock_screener
from stock_screener import StockScreener
from stock_analyzer import StockAnalyzer

# --- Page Configuration (MUST be first Streamlit command) ---
st.set_page_config(page_title="Stock Analysis Pro", layout="wide")

# Force Uppercase Display CSS
st.markdown("""
<style>
    input {
        text-transform: uppercase !important;
    }
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        background-color: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }
    /* Marquee Styling */
    .marquee {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        background: rgba(0,0,0,0.3);
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        position: relative;
    }
    .marquee-content {
        display: inline-block;
        animation: marquee 30s linear infinite;
        padding-left: 100%;
    }
    @keyframes marquee {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }
    .marquee-item {
        display: inline-block;
        padding-right: 50px;
        font-size: 16px;
        font-weight: bold;
    }
    
    /* Navigation Sidebar Custom Styling */
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s ease;
        text-align: left;
        padding: 10px 15px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.05);
        color: rgba(255,255,255,0.8);
        width: 100%;
        margin-bottom: 5px;
        animation: slideIn 0.5s ease forwards;
        opacity: 0;
    }
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    .stButton > button:hover {
        background: rgba(0, 255, 0, 0.1);
        border-color: rgba(0, 255, 0, 0.4);
        transform: translateX(5px);
        color: #00FF00;
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.1);
    }
    .active-nav > div > button {
        background: rgba(0, 255, 0, 0.15) !important;
        border-color: rgba(0, 255, 0, 0.6) !important;
        color: #00FF00 !important;
        font-weight: bold !important;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.2) !important;
    }

    /* Sentiment Bar Styling */
    .sentiment-bar {
        width: 100%;
        padding: 8px 0;
        text-align: center;
        font-weight: 800;
        font-size: 18px;
        color: white;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        border-radius: 0 0 10px 10px;
        margin-bottom: 2px;
        letter-spacing: 1px;
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(255, 0, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
    }
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(0, 255, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0); }
    }
    .blood-bath {
        animation: pulse-red 2s infinite;
        background: linear-gradient(90deg, #4A0000, #FF0000, #4A0000) !important;
    }
    .rally {
        animation: pulse-green 2s infinite;
        background: linear-gradient(90deg, #002B00, #00FF00, #002B00) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Footfall Tracker Logic ---
def get_footfall():
    """Tracks and increments website visits."""
    count_file = "visitor_count.json"
    
    # Initialize session tracking to prevent refresh-counting
    if 'counted' not in st.session_state:
        st.session_state['counted'] = True
        try:
            if os.path.exists(count_file):
                with open(count_file, "r") as f:
                    data = json.load(f)
                    total = data.get("total", 0) + 1
            else:
                total = 1
            
            with open(count_file, "w") as f:
                json.dump({"total": total}, f)
            return total
        except:
            return 0
    else:
        # Just read the current count
        try:
            if os.path.exists(count_file):
                with open(count_file, "r") as f:
                    data = json.load(f)
                    return data.get("total", 0)
        except:
            pass
        return 0

# --- Market Sentiment Logic ---
@st.cache_data(ttl=300) # Cache for 5 mins
def get_market_sentiment():
    """Fetches Nifty 50 to gauge overall mood."""
    try:
        nifty = yf.download("^NSEI", period="2d", progress=False)
        if nifty.empty or len(nifty) < 2: 
            return "MARKET NEUTRAL ⚖️", 0, "rgba(255,255,255,0.1)", ""
        
        last_close = float(nifty['Close'].iloc[-1])
        prev_close = float(nifty['Close'].iloc[-2])
        change_pct = ((last_close - prev_close) / prev_close) * 100
        
        if change_pct <= -2.0:
            return "BLOOD BATH 🩸", change_pct, "", "blood-bath"
        elif change_pct <= -0.5:
            return "MARKET NOT OK ⚠️", change_pct, "#FF4B4B", ""
        elif change_pct <= 0.5:
            return "SIDEWAYS / CHOPPY ⚖️", change_pct, "rgba(255,255,255,0.1)", ""
        elif change_pct <= 1.5:
            return "MARKET OK 🟢", change_pct, "#00FF00", ""
        else:
            return "BULLISH RALLY 🚀", change_pct, "", "rally"
    except Exception as e:
        return "MARKET DATA UNAVAILABLE", 0, "rgba(255,255,255,0.1)", ""

# Add Sentiment Hub (Absolute Top)
mood, change, color, anim_class = get_market_sentiment()
st.markdown(f"""
<div class="sentiment-bar {anim_class}" style="background-color: {color};">
    <span style="font-size: 14px; opacity: 0.8;">INDIA MARKET MOOD:</span> {mood} ({change:+.2f}%)
</div>
""", unsafe_allow_html=True)

# Add Marquee UI
st.markdown("""
<div class="marquee">
    <div class="marquee-content">
        <span class="marquee-item" style="color:#00FF00;">🟢 NIFTY 50: 24,120 (+0.8%)</span>
        <span class="marquee-item" style="color:#00FF00;">🟢 SENSEX: 79,230 (+0.75%)</span>
        <span class="marquee-item" style="color:#FF4B4B;">🔴 BANK NIFTY: 51,450 (-0.2%)</span>
        <span class="marquee-item" style="color:#00FF00;">🟢 RELIANCE: 2,980 (+1.2%)</span>
        <span class="marquee-item" style="color:#00FF00;">🟢 TCS: 3,920 (+0.95%)</span>
        <span class="marquee-item" style="color:#FF4B4B;">🔴 INFY: 1,840 (-0.4%)</span>
    </div>
</div>
""", unsafe_allow_html=True)

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
    "VBL.NS", "TRENT.NS", "COALINDIA.NS", "ONGC.NS", "SUNPHARMA.NS"
]

# --- Sidebar Navigation Logic (Robust) ---
nav_options = [
    "🔍 Deep Analyzer", 
    "🚀 Trending Picks (Top 5)", 
    "⚡ Intraday Surge (1-2 Hr)", 
    "💎 Potential Multibaggers",
    "📊 Portfolio & Analytics"
]

# Key-Rotation Pattern: Bypasses Streamlit's internal widget state
if 'nav_key' not in st.session_state:
    st.session_state['nav_key'] = 0

if 'page_target' in st.session_state:
    # Programmatic navigation requested! (including Home)
    st.session_state['nav_key'] += 1 
    if st.session_state['page_target'] == "Home":
        st.session_state['current_page'] = "Home"
    else:
        try:
            nav_index = nav_options.index(st.session_state['page_target'])
            st.session_state['current_page'] = st.session_state['page_target']
        except:
            st.session_state['current_page'] = "Home"
else:
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Home"

# --- Sidebar Content ---
with st.sidebar:
    st.write("### 🧭 Navigation")
    
    # Home Button
    is_home = (st.session_state['current_page'] == "Home")
    if is_home:
        st.markdown('<div class="active-nav">', unsafe_allow_html=True)
    if st.button("🏠 Home / Market Hub", key="btn_home", use_container_width=True):
        st.session_state['current_page'] = "Home"
        st.rerun()
    if is_home:
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.write("") # Spacer

    # Navigation Options
    for opt in nav_options:
        is_active = (st.session_state['current_page'] == opt)
        if is_active:
            st.markdown('<div class="active-nav">', unsafe_allow_html=True)
        
        if st.button(opt, key=f"btn_{opt}", use_container_width=True):
            st.session_state['current_page'] = opt
            st.rerun()
            
        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # Controls (Sound Alerts etc)
    st.header("⚙️ Settings")
    st.session_state['audio_enabled'] = st.checkbox("🔊 Enable Sound Alerts", value=True)
    st.divider()
    
    # Footfall Badge
    total_visits = get_footfall()
    st.markdown(f"""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(0, 255, 0, 0.2);
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,255,0,0.05);
    ">
        <div style="font-size: 10px; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px;">Global Footfall</div>
        <div style="font-size: 24px; font-weight: 800; color: #00FF00; text-shadow: 0 0 10px rgba(0,255,0,0.3);">
            {total_visits:,}
        </div>
        <div style="font-size: 10px; color: #00FF00; opacity: 0.8; margin-top: 5px;">
             👁️ Professional Sessions
        </div>
    </div>
    """, unsafe_allow_html=True)

page = st.session_state['current_page']

# Cleanup target
if 'page_target' in st.session_state:
    del st.session_state['page_target']

if page == "Home":
    st.header("🏠 Market Intelligence Hub")
    
    # 1. Market Status Bar
    is_open, status_msg = is_market_open()
    st.info(f"📅 **Status:** {status_msg}")

    # 2. 🌟 Market Stars Section
    st.subheader("🌟 Market Leaders")
    
    with st.spinner("Scanning for top performers..."):
        screener = StockScreener(POPULAR_STOCKS)
        day_stars, month_stars = screener.get_market_stars()
        
    # --- Line 1: Stars of the Month (Fixed 2) ---
    st.subheader("🏆 Monthly Leaderboard (Top 2)")
    mc1, mc2 = st.columns(2)
    for i, star in enumerate(month_stars[:2]):
        col = mc1 if i == 0 else mc2
        with col:
            st.markdown(f"""
            <div style="background-color: rgba(255, 215, 0, 0.05); border: 2px solid rgba(255, 215, 0, 0.3); padding: 20px; border-radius: 12px; text-align: center;">
                <h4 style="margin:0; opacity: 0.8;">Star of the Month</h4>
                <h2 style="color: #FFD700; margin: 10px 0;">{star['ticker']}</h2>
                <p style="font-size: 20px; font-weight: bold; margin:0;">{star['change']:+.2f}%</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Analyze {star['ticker']} (Month)", key=f"month_btn_{i}", use_container_width=True):
                 st.session_state['page_target'] = "🔍 Deep Analyzer"
                 st.session_state['ticker_target'] = star['ticker']
                 st.session_state['trigger_analyze'] = True
                 st.rerun()

    st.write("") # Spacer
    
    # --- Line 2 & 3: Stars of the Day (Top 4) ---
    st.subheader("🔥 Daily Breakouts (Top 4)")
    # Row 1 of Day Stars
    dc1, dc2 = st.columns(2)
    for i, star in enumerate(day_stars[:2]):
        col = dc1 if i == 0 else dc2
        with col:
            st.markdown(f"""
            <div style="background-color: rgba(0, 255, 0, 0.05); border: 2px solid rgba(0, 255, 0, 0.3); padding: 20px; border-radius: 12px; text-align: center;">
                <h4 style="margin:0; opacity: 0.8;">Star of the Day</h4>
                <h2 style="color: #00FF00; margin: 10px 0;">{star['ticker']}</h2>
                <p style="font-size: 20px; font-weight: bold; margin:0;">{star['change']:+.2f}%</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Analyze {star['ticker']} (Day)", key=f"day_btn_{i}", use_container_width=True):
                 st.session_state['page_target'] = "🔍 Deep Analyzer"
                 st.session_state['ticker_target'] = star['ticker']
                 st.session_state['trigger_analyze'] = True
                 st.rerun()

    # Row 2 of Day Stars
    dc3, dc4 = st.columns(2)
    for i, star in enumerate(day_stars[2:4]):
        col = dc3 if i == 0 else dc4
        with col:
            st.markdown(f"""
            <div style="background-color: rgba(0, 255, 0, 0.05); border: 2px solid rgba(0, 255, 0, 0.3); padding: 20px; border-radius: 12px; text-align: center;">
                <h4 style="margin:0; opacity: 0.8;">Star of the Day</h4>
                <h2 style="color: #00FF00; margin: 10px 0;">{star['ticker']}</h2>
                <p style="font-size: 20px; font-weight: bold; margin:0;">{star['change']:+.2f}%</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Analyze {star['ticker']} (Day)", key=f"day_btn_{i+2}", use_container_width=True):
                 st.session_state['page_target'] = "🔍 Deep Analyzer"
                 st.session_state['ticker_target'] = star['ticker']
                 st.session_state['trigger_analyze'] = True
                 st.rerun()

    st.divider()
    
    # 3. Quick Tips / Global Context
    tc1, tc2 = st.columns(2)
    with tc1:
        st.write("### 🚀 Market Sentiment")
        st.write("Broad indices are showing strength in the IT and Pharma sectors today.")
    with tc2:
        st.write("### 💡 Trading Pro Tip")
        st.write("Always wait for confirmation from the **EMA Cloud** before entering a trade on a breakout star.")

elif page == "💎 Potential Multibaggers":
    st.title("💎 Potential Multibaggers (Advanced Strategy Scan)")
    st.info("Scanner objective: Identify high-growth gems using professional institutional-grade filters. **Note:** Scans are randomized to prevent ticker bias.")
    
    # Strategy Selector
    strat_col1, strat_col2 = st.columns([2, 1])
    with strat_col1:
        selected_strat = st.selectbox(
            "🎯 Select Multibagger Strategy",
            ["Strong Formula (Default)", "CAN SLIM (William O'Neil)", "Minervini Trend Template", "Low-Cap Moonshot (Beta)"],
            help="Choose the screening logic used to find potential 10x stocks."
        )
    
    with strat_col2:
        st.write("") # Spacer
        run_scan = st.button("🚀 Run Strategy Scan", type="primary", use_container_width=True)

    if run_scan:
        with st.spinner(f"Executing {selected_strat} on 500+ Indian Stocks..."):
            screener = StockScreener([s['symbol'] for s in TICKER_DB])
            # Map choice to backend key
            strat_key = selected_strat.split(' (')[0] if '(' in selected_strat else selected_strat.split(' (')[0]
            candidates = screener.get_multibagger_candidates(limit=10, strategy=selected_strat)
            
            if candidates:
                st.write(f"### 💎 Top 10 Multibagger Recommendations")
                st.markdown("---")
                # 2-Column Grid for 10 items
                for i in range(0, len(candidates), 2):
                    cols = st.columns(2)
                    chunk = candidates[i:i+2]
                    for j, stock in enumerate(chunk):
                        with cols[j]:
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.03); padding: 25px; border-radius: 15px; border: 1px solid rgba(0, 255, 0, 0.2); min-height: 200px; margin-bottom: 20px;">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <h2 style="color: #00FF00; margin: 0;">{stock['ticker']}</h2>
                                    <div style="font-size: 14px; font-weight: bold; background: rgba(0,255,0,0.15); padding: 5px 12px; border-radius: 20px; color: #00FF00;">
                                        {stock['score']}% Signal
                                    </div>
                                </div>
                                <div style="font-size: 16px; opacity: 0.9; margin: 10px 0;">Current Price: **₹{stock['current_price']:.2f}**</div>
                                <div style="font-size: 13px; color: #AAA; line-height: 1.6;">
                                    {" • ".join(stock['reasons'])}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(f"Analyze {stock['ticker']}", key=f"multi_{stock['ticker']}", use_container_width=True):
                                st.session_state['ticker_target'] = stock['ticker']
                                st.session_state['page_target'] = "🔍 Deep Analyzer"
                                st.session_state['trigger_analyze'] = True 
                                st.rerun()
                st.success("Multibagger logic check successful for 10 candidates.")
            else:
                st.warning("No clear multibagger setups detected today. Markets might be in a cool-down phase.")
    else:
        st.write("Click the button above to start the professional-grade scan.")

elif page == "🔍 Deep Analyzer":
    # --- Main Screen Configuration (Consolidated Search & Period) ---
    st.header(f"🔍 Deep Analyzer")
    
    # 1. Search & Exchange Row
    sc1, sc2, sc3 = st.columns([1, 2, 2])
    
    with sc1:
        st.write("**🏛️ Exchange**")
        st.session_state['exchange'] = st.radio("Exchange", ["NSE", "BSE"], horizontal=True, label_visibility="collapsed")
    
    with sc2:
        st.write("**🔍 Search Name**")
        # Get target ticker or default
        ticker_val = st.session_state.get('ticker_target', "")
        
        def sync_from_list():
            if st.session_state.get('master_search'):
                sym = st.session_state['master_search'].split(' - ')[0]
                st.session_state['manual_ticker'] = sym

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
            label_visibility="collapsed"
        )

    with sc3:
        st.write("**⌨️ Manual Ticker**")
        ticker_input_raw = st.text_input(
            "Ticker (e.g. RELIANCE)", 
            value=ticker_val if ticker_val else "",
            key="manual_ticker",
            label_visibility="collapsed"
        ).upper()
        
    # Process Ticker
    if ticker_input_raw:
        suffix = ".NS" if st.session_state.get('exchange', 'NSE') == "NSE" else ".BO"
        ticker_input = ticker_input_raw if "." in ticker_input_raw else f"{ticker_input_raw}{suffix}"
    else:
        if st.session_state.get('master_search'):
            sym = st.session_state['master_search'].split(' - ')[0]
            suffix = ".NS" if st.session_state.get('exchange', 'NSE') == "NSE" else ".BO"
            ticker_input = f"{sym}{suffix}"
        else:
            ticker_input = "RELIANCE.NS"

    if 'ticker_target' in st.session_state:
        del st.session_state['ticker_target']

    clean_manual = ticker_input_raw.split('.')[0]
    if clean_manual in TICKER_MAP:
         st.caption(f"✨ Detected: **{TICKER_MAP[clean_manual]}**")
    
    st.write("") # Spacer

    # --- Main Screen Configuration (Execution) ---
    
    # ⏱️ Quick Period Row
    c_p, c_d = st.columns([2, 1])
    with c_p:
         period_preset = st.radio(
            "⏱️ Select Chart Period",
            ["1D", "1W", "1M", "1Y", "5Y", "Custom"],
            index=2, # Default to 1M
            horizontal=True
        )
    
    with c_d:
        with st.expander("📅 Custom Settings"):
            s_date = st.date_input("Start Date", date.today() - timedelta(days=365))
            e_date = st.date_input("End Date", date.today())
            i_choice = st.selectbox("Interval", ["Daily (1d)", "Hourly (1h)", "5-Min (5m)"])

    # Period Logic
    if period_preset != "Custom":
        end_date = date.today()
        if period_preset == "1D": start_date, interval_code = end_date - timedelta(days=2), "5m"
        elif period_preset == "1W": start_date, interval_code = end_date - timedelta(days=7), "1h"
        elif period_preset == "1M": start_date, interval_code = end_date - timedelta(days=30), "1d"
        elif period_preset == "1Y": start_date, interval_code = end_date - timedelta(days=365), "1d"
        elif period_preset == "5Y": start_date, interval_code = end_date - timedelta(days=365*5), "1wk"
    else:
        start_date, end_date = s_date, e_date
        interval_code = "1h" if "Hourly" in i_choice else ("5m" if "5-Min" in i_choice else "1d")

    # Generate Button
    auto_click = False
    if st.session_state.get('trigger_analyze', False):
         st.session_state['trigger_analyze'] = False
         auto_click = True

    if st.button("🚀 Run Analysis & Forecast", type="primary", use_container_width=True) or auto_click:
        with st.spinner(f"Fetching data for {ticker_input}..."):
            analyzer = StockAnalyzer(ticker_input)
            success = analyzer.fetch_data(start=start_date, end=end_date, interval=interval_code)
            analyzer.fetch_fundamentals()
            analyzer.get_news()
            
            if success and analyzer.data is not None and not analyzer.data.empty:
                st.session_state['data'] = analyzer.data
                st.session_state['analyzer'] = analyzer
                st.session_state['ticker'] = ticker_input
                st.success("Analysis Complete!")
            else:
                st.error("No data found. Try a different range.")


    # --- Analyzer Main Content ---
    if 'data' in st.session_state:
        df = st.session_state['data']
        analyzer = st.session_state['analyzer']
        ticker = st.session_state['ticker']
        
        st.header(f"{ticker} Analysis ({len(df)} candles)")
        
        # 1. Fundamentals Section (Moved to Top)
        if analyzer.info:
            with st.container():
                st.subheader(f"🏛️ {ticker} Overview")
                info = analyzer.info
                # Professional Styling for Summary
                st.markdown(f"**Sector:** {info['sector']} | **52W Range:** ₹{info['52w_low']:.2f} - ₹{info['52w_high']:.2f}")
                st.write(info['summary'])
                st.write("") # Spacer

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Market Cap", f"₹{info['market_cap']/1e7:.1f} Cr")
                c2.metric("P/E Ratio", f"{info['pe']:.1f}")
                c3.metric("Div. Yield", f"{info['dividend_yield']:.1f}%")
                c4.metric("Beta", f"{info['beta']:.2f}")
                st.divider()

        # 2. Alert & Chart Controls
        ac1, ac2 = st.columns([1, 2])
        with ac1:
            with st.expander("🔔 Set Price Alert", expanded=False):
                cur_p = float(df['Close'].iloc[-1])
                new_a = st.number_input(f"Target", value=cur_p, step=1.0, key="screen_alert_val", label_visibility="collapsed")
                if st.button("Confirm Alert", use_container_width=True, key="screen_alert_btn"):
                    if 'alerts' not in st.session_state: st.session_state['alerts'] = []
                    st.session_state['alerts'].append({"ticker": ticker, "price": new_a, "active": True})
                    st.toast(f"Alert Active: {ticker} @ ₹{new_a}", icon="🚀")
        
        with ac2:
             st.write("**📊 Chart Customization**")
             cc1, cc2, cc3 = st.columns(3)
             with cc1: show_bb = st.checkbox("BBands", value=False)
             with cc2: show_emas = st.checkbox("EMA Cloud", value=False)
             with cc3: show_macd = st.checkbox("MACD", value=True)
        
        st.divider()

        from plotly.subplots import make_subplots
        
        # Create Subplots: Price (row 1) and Volume (row 2)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, row_heights=[0.7, 0.3])

        # 1. Candlestick
        fig.add_trace(go.Candlestick(x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name="Price"), row=1, col=1)
        
        # 2. Volume
        # Fix: Use iloc for robust integer indexing
        vol_colors = ['red' if df['Open'].iloc[i] > df['Close'].iloc[i] else 'green' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=vol_colors, opacity=0.5), row=2, col=1)

        # Ensure indicators exist (Recalculate if missing)
        if (show_bb or show_emas or show_macd) and 'MA20' not in df.columns:
             analyzer.calculate_indicators()
             df = analyzer.data
             st.session_state['data'] = df

        # Add Bollinger Bands if requested
        if show_bb and 'Upper_Band' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['Upper_Band'], name='BB Upper', line=dict(color='rgba(173, 216, 230, 0.4)', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Lower_Band'], name='BB Lower', line=dict(color='rgba(173, 216, 230, 0.4)', width=1), fill='tonexty'), row=1, col=1)
            
        # Add EMAs if requested
        if show_emas:
            if 'EMA20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='EMA 20', line=dict(color='yellow', width=1)), row=1, col=1)
            if 'EMA50' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50', line=dict(color='orange', width=1)), row=1, col=1)
            if 'EMA200' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='red', width=1.5)), row=1, col=1)

        fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0), xaxis_rangeslider_visible=False)
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

        # 5. Professional Verdict (Pros & Cons)
        st.subheader("⚖️ Professional Verdict")
        pros, cons = analyzer.get_pros_cons()
        
        pc1, pc2 = st.columns(2)
        with pc1:
            st.success("✅ **Strengths (Pros)**")
            if pros:
                for p in pros: st.write(f"• {p}")
            else:
                st.write("*Analyzing fundamentals...*")
        with pc2:
            st.error("⚠️ **Risks (Cons)**")
            if cons:
                for c in cons: st.write(f"• {c}")
            else:
                st.write("*No major technical risks detected.*")
        
        st.divider()

        # 6. News Section (Optimized)
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
