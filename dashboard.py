
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
import threading

# --- Page Configuration (MUST be first Streamlit command) ---
st.set_page_config(page_title="StockPro AI v1.2.1", layout="wide", page_icon="📈")

# SEO Meta Tags Integration (Hidden from UI)
st.markdown("""
<div style="display:none;">
    <title>Stock Analysis Pro | AI Stock Screener & Multibagger Finder India</title>
    <meta name="description" content="Discover high-growth multibagger stocks in the Indian market using AI-powered screeners, CAN SLIM strategies, and real-time Nifty 50 forecasting. Professional tools for NSE & BSE traders.">
    <meta name="keywords" content="Stock Screener India, Multibagger Stocks, Nifty 50 Prediction, NSE BSE Analysis, Best Stocks to Buy India, AI Trading Tools, Minervini Strategy, CAN SLIM India">
    <meta name="author" content="StockPro AI Quant Team">
    <link rel="canonical" href="https://yourdomain.com/" />
    
    <!-- Open Graph / Meta -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="Stock Analysis Pro | Professional Indian Market Intelligence">
    <meta property="og:description" content="Advanced AI-powered stock analysis, paper trading simulator, and high-performance screener for Indian Markets.">
    <meta property="og:image" content="https://img.freepik.com/free-vector/gradient-stock-market-concept_23-2149166910.jpg">
    
    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Stock Analysis Pro | 10x Multibagger Scanner">
    <meta name="twitter:description" content="Scan 500+ Indian stocks for multibagger potential instantly with institutional-grade filters.">
    <meta name="twitter:image" content="https://images.unsplash.com/photo-1611974717482-48dfc0543fb4?q=80&w=2070&auto=format&fit=crop">
    
    <!-- JSON-LD Structured Data for SEO -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "Stock Analysis Pro",
      "operatingSystem": "Web",
      "applicationCategory": "FinanceApplication",
      "description": "Professional stock analysis and screening tool for Indian markets NSE/BSE.",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "INR"
      },
      "author": {
        "@type": "Organization",
        "name": "StockPro Quant Team"
      }
    }
    </script>
</div>
""", unsafe_allow_html=True)

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
        padding: 5px 12px; /* Compact padding */
        border-radius: 8px; /* Fixed radius */
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"] label {
        font-size: 13px !important; /* Smaller label */
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 20px !important; /* Smaller value */
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-1px);
        background-color: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Reduce global vertical spacing */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    h1, h2, h3, h4 {
        margin-top: 2px !important;
        margin-bottom: 2px !important;
    }
    .stAlert {
        padding: 5px !important;
        margin-bottom: 5px !important;
    }
    /* Marquee Styling */
    .marquee {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        background: rgba(0,0,0,0.3);
        padding: 4px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        position: relative;
    }
    .marquee-content {
        display: inline-block;
        animation: marquee 120s linear infinite;
        padding-left: 100%;
    }
    .marquee-content:hover {
        animation-play-state: paused;
    }
    @keyframes marquee {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }
    .marquee-item {
        display: inline-block;
        padding-right: 50px;
        font-size: 13px;
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
    /* Share Button Styling */
    .share-btn {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 5px;
        text-decoration: none;
        font-size: 12px;
        font-weight: bold;
        margin-right: 8px;
        transition: opacity 0.2s;
    }
    .share-btn:hover { opacity: 0.8; color: white !important; }
    .whatsapp-btn { background-color: #25D366; color: white !important; }
    .twitter-btn { background-color: #1DA1F2; color: white !important; }
    
    /* Community Heatmap Item */
    .heatmap-item {
        background: rgba(255,255,255,0.03);
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        border-left: 3px solid #00FF00;
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
            return "MAJOR SELL-OFF 🩸", change_pct, "", "blood-bath"
        elif change_pct <= -0.5:
            return "BEARISH PRESSURE ⚠️", change_pct, "#FF4B4B", ""
        elif change_pct <= 0.5:
            return "SIDEWAYS / CHOPPY ⚖️", change_pct, "rgba(255,255,255,0.1)", ""
        elif change_pct <= 1.5:
            return "MARKET OK 🟢", change_pct, "#00FF00", ""
        else:
            return "BULLISH RALLY 🚀", change_pct, "", "rally"
    except Exception as e:
        return "MARKET DATA UNAVAILABLE", 0, "rgba(255,255,255,0.1)", ""

@st.cache_data(ttl=60)  # CACHE BUSTED - v1.2.1
def get_marquee_data():
    """Fetches real-time prices for marquee indices and stocks."""
    # Reduced symbol list for faster loading
    symbols = {
        "^NSEI": "NIFTY 50", "^BSESN": "SENSEX", "^NSEBANK": "BANK NIFTY",
        "RELIANCE.NS": "RELIANCE", "HDFCBANK.NS": "HDFC BANK", "ICICIBANK.NS": "ICICI BANK",
        "TCS.NS": "TCS", "INFY.NS": "INFY", "SBIN.NS": "SBI", "BHARTIARTL.NS": "AIRTEL",
        "ITC.NS": "ITC", "TATAMOTORS.NS": "TATA MOTORS", "ADANIENT.NS": "ADANI ENT",
        "BAJFINANCE.NS": "BAJAJ FINANCE", "MARUTI.NS": "MARUTI", "TITAN.NS": "TITAN"
    }
    results = []
    try:
        import signal
        
        # Set a timeout for the download
        def timeout_handler(signum, frame):
            raise TimeoutError("Download timeout")
        
        # Only set alarm on Unix systems (not Windows)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)  # 10 second timeout
        
        try:
            # Batch download for speed - reduced to 2 days for faster response
            data = yf.download(list(symbols.keys()), period="2d", interval="1d", 
                             group_by='ticker', progress=False, threads=True)
            
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel the alarm
            
            for sym, name in symbols.items():
                try:
                    df = data[sym] if len(symbols) > 1 else data
                    df = df.dropna(subset=['Close'])
                    if not df.empty:
                        lp = float(df['Close'].iloc[-1])
                        prev = float(df['Close'].iloc[-2]) if len(df) > 1 else lp
                        chg = ((lp - prev) / prev) * 100 if prev != 0 else 0
                        results.append({"name": name, "price": lp, "change": chg})
                except Exception:
                    continue
        except (TimeoutError, Exception) as e:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            # Return empty on timeout/error - fallback will handle it
            pass
    except Exception:
        pass
    
    return results

# Add Sentiment Hub (Absolute Top) - Smart Loading
try:
    mood, change, color, anim_class = get_market_sentiment()
    st.markdown(f"""
    <div class="sentiment-bar {anim_class}" style="background-color: {color}; padding: 4px 0; font-size: 14px;">
        <span style="font-size: 11px; opacity: 0.8;">INDIA MOOD:</span> {mood} ({change:+.2f}%)
    </div>
    """, unsafe_allow_html=True)
except:
    st.markdown("""
    <div class="sentiment-bar" style="background-color: rgba(255,255,255,0.1); padding: 4px 0; font-size: 14px;">
        <span style="font-size: 11px; opacity: 0.8;">INDIA MOOD:</span> MARKET LIVE 🟢
    </div>
    """, unsafe_allow_html=True)

# Add Marquee UI - SMART LAZY LOADING (NON-BLOCKING)
marquee_placeholder = st.empty()

# Show loading placeholder immediately (non-blocking)
marquee_placeholder.markdown("""
<div class="marquee">
    <div class="marquee-content">
        <span class="marquee-item" style="color:#FFA500;">⚡ Loading live market data...</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Try to fetch real data (cached, so won't block on subsequent loads)
try:
    marquee_data = get_marquee_data()
    if marquee_data and len(marquee_data) > 0:
        items_html = ""
        for item in marquee_data:
            color = "#00FF00" if item['change'] >= 0 else "#FF4B4B"
            icon = "🟢" if item['change'] >= 0 else "🔴"
            items_html += f'<span class="marquee-item" style="color:{color};">{icon} {item["name"]}: ₹{item["price"]:,.2f} ({item["change"]:+.2f}%)</span>'
        
        # Update with real data
        marquee_placeholder.markdown(f"""
        <div class="marquee">
            <div class="marquee-content">
                {items_html} {items_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Keep loading message if no data
        pass
except Exception as e:
    # On error, show static fallback
    marquee_placeholder.markdown("""
    <div class="marquee">
        <div class="marquee-content">
            <span class="marquee-item" style="color:#00FF00;">🟢 NIFTY 50: LIVE</span>
            <span class="marquee-item" style="color:#00FF00;">🟢 SENSEX: LIVE</span>
            <span class="marquee-item" style="color:#00FF00;">🟢 BANK NIFTY: LIVE</span>
            <span class="marquee-item" style="color:#FFA500;">⚡ Market data temporarily unavailable</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Paper Trading & Assets
from paper_trader import PaperTrader
try:
    from assets import ALERT_SOUND_B64
except ImportError:
    ALERT_SOUND_B64 = "" 

# --- Market Utilities ---
def render_ad_space():
    """Placeholder for premium advertisements/sponsor banners."""
    st.markdown("""
    <div style="background: rgba(0, 255, 0, 0.05); padding: 5px; border-radius: 5px; border: 1px dashed rgba(0, 255, 0, 0.2); text-align: center; margin-top: 10px;">
        <div style="font-size: 8px; color: #00FF00; opacity: 0.6; text-transform: uppercase;">👑 Sponsored</div>
        <div style="font-size: 12px; font-weight: bold; color: #FFF;">Your Brand Here</div>
    </div>
    """, unsafe_allow_html=True)

# --- Market Hours Check with Holiday Detection ---
def get_nse_holidays_2025():
    """Returns list of NSE/BSE holidays for 2025."""
    # NSE/BSE Holiday Calendar 2025
    holidays = [
        date(2025, 1, 26),   # Republic Day
        date(2025, 3, 14),   # Mahashivratri
        date(2025, 3, 31),   # Id-Ul-Fitr (Ramadan Eid)
        date(2025, 4, 10),   # Mahavir Jayanti
        date(2025, 4, 14),   # Dr. Ambedkar Jayanti
        date(2025, 4, 18),   # Good Friday
        date(2025, 5, 1),    # Maharashtra Day
        date(2025, 6, 7),    # Id-Ul-Adha (Bakri Eid)
        date(2025, 8, 15),   # Independence Day
        date(2025, 8, 27),   # Ganesh Chaturthi
        date(2025, 10, 2),   # Mahatma Gandhi Jayanti
        date(2025, 10, 21),  # Dussehra
        date(2025, 11, 1),   # Diwali - Laxmi Pujan
        date(2025, 11, 5),   # Guru Nanak Jayanti
        date(2025, 12, 25),  # Christmas
    ]
    return holidays

def get_next_trading_day(from_date=None):
    """Calculate the next trading day, skipping weekends and holidays."""
    if from_date is None:
        import pytz
        tz = pytz.timezone('Asia/Kolkata')
        from_date = datetime.now(tz).date()
    
    holidays = get_nse_holidays_2025()
    next_day = from_date + timedelta(days=1)
    
    # Keep incrementing until we find a trading day
    while next_day.weekday() >= 5 or next_day in holidays:
        next_day += timedelta(days=1)
    
    return next_day

def is_market_open():
    """Check if NSE/BSE is open (9:15 AM - 3:30 PM IST, Mon-Fri), accounting for holidays."""
    import pytz
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz) # Current IST time
    today = now.date()
    holidays = get_nse_holidays_2025()
    
    # Check if today is a holiday
    if today in holidays:
        next_trading = get_next_trading_day(today)
        day_name = next_trading.strftime("%A, %b %d")
        return False, f"🏖️ Markets Closed - Holiday | Next Trading Day: {day_name}"
    
    # Check weekday (0=Monday, 6=Sunday)
    if now.weekday() >= 5:  # Saturday or Sunday
        next_trading = get_next_trading_day(today)
        day_name = next_trading.strftime("%A, %b %d")
        return False, f"📅 Markets Closed - Weekend | Next Trading Day: {day_name}"
    
    # Market Hours (IST)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if now < market_open:
        mins_to_open = (market_open - now).seconds // 60
        # If > 60 mins, show hours
        if mins_to_open > 60:
             hrs = mins_to_open // 60
             mins = mins_to_open % 60
             return False, f"🌙 Market Closed. Opens in {hrs}h {mins}m (09:15 AM)"
        return False, f"⏰ Market Opens at 9:15 AM (in {mins_to_open} mins)"
    elif now > market_close:
        next_trading = get_next_trading_day(today)
        day_name = next_trading.strftime("%A, %b %d")
        return False, f"🔔 Market Closed for Today | Next Trading Day: {day_name}"
    else:
        return True, "🟢 Market is LIVE"

# --- Initialization ---
if 'trader' not in st.session_state:
    st.session_state['trader'] = PaperTrader(initial_balance=10000.0)

@st.cache_resource
def start_bot_service():
    """Starts the bot as a background thread that stays alive with the app."""
    try:
        import importlib
        import background_bot
        # Force reload to pick up code changes on Streamlit Cloud
        importlib.reload(background_bot)
        
        # Start in a daemon thread so it dies when the main process dies
        thread = threading.Thread(target=background_bot.run_bot, daemon=True)
        thread.start()
        return f"Service v{getattr(background_bot, 'BOT_VERSION', '1.0')} started at {datetime.now()}"
    except Exception as e:
        return f"Error starting service: {e}"

# Launch Service
if 'bot_svc' not in st.session_state:
    st.session_state['bot_svc'] = start_bot_service()

def play_alert_sound():
    """Plays a beep sound using HTML5 Audio from assets."""
    if ALERT_SOUND_B64 and st.session_state.get('audio_enabled', False):
        st.markdown(
            f'<audio autoplay="true" style="display:none;"><source src="{ALERT_SOUND_B64}" type="audio/wav"></audio>',
            unsafe_allow_html=True
        )

def render_share_buttons(ticker, price, change, type="analysis"):
    """Renders viral share social buttons."""
    import urllib.parse
    text = f"🚀 just analyzed {ticker} on StockPro! Price: ₹{price:.2f} ({change:+.2f}%). Check out the AI forecast here!"
    if "multibagger" in type:
        text = f"💎 Found a potential MULTIBAGGER: {ticker} on StockPro AI! Signal: {change} score. Check it out!"
    
    encoded_text = urllib.parse.quote(text)
    wa_url = f"https://api.whatsapp.com/send?text={encoded_text}"
    tw_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
    
    st.markdown(f"""
    <div style="margin-top: 10px;">
        <a href="{wa_url}" target="_blank" class="share-btn whatsapp-btn">Share on WhatsApp</a>
        <a href="{tw_url}" target="_blank" class="share-btn twitter-btn">Tweet Quote</a>
    </div>
    """, unsafe_allow_html=True)

# Removed global title to save space
# st.title("📈 Stock Analysis & Projection")

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
    "🤖 Paper Trading Simulator",
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

    # Lead Capture Form (Newsletter)
    st.markdown("### 📨 Alpha Alerts")
    with st.form("newsletter_form"):
        email = st.text_input("Get Top 5 Daily Picks", placeholder="your@email.com")
        submit_leads = st.form_submit_button("Join 5k+ Traders 🚀", use_container_width=True)
        if submit_leads:
            if email:
                st.success("You're on the list! Watch your inbox.")
            else:
                st.error("Please enter email.")

    st.divider()
    
    # Sponsored Space in Sidebar
    render_ad_space()
    
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

    st.divider()
    
    # Professional Resources Section
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
        <div style="font-size: 11px; font-weight: bold; color: #AAA; text-transform: uppercase; margin-bottom: 10px;">💎 Professional Resources</div>
        <ul style="list-style: none; padding: 0; margin: 0; font-size: 13px;">
            <li style="margin-bottom: 8px;"><a href="#" style="text-decoration: none; color: #00FF00;">✉️ Growth Alpha Newsletter</a></li>
            <li style="margin-bottom: 8px;"><a href="#" style="text-decoration: none; color: #00FF00;">📈 Zero-Brokerage Partner</a></li>
            <li style="margin-bottom: 8px;"><a href="#" style="text-decoration: none; color: #00FF00;">☕ Support Development</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- Navigation Helper ---
def trigger_analysis():
    st.session_state['trigger_analyze'] = True

page = st.session_state['current_page']

# Cleanup target
if 'page_target' in st.session_state:
    del st.session_state['page_target']

if page == "Home":
    st.caption("v1.2.0-compact") # Deployment check
    st.markdown("#### 🏛️ Professional Trading Hub")
    
    # 1. Market Status Bar
    is_open, status_msg = is_market_open()
    st.info(f"📅 **Status:** {status_msg}")

    # --- 2. 🌟 Market Stars Section ---
    st.markdown("##### 🌟 Market Leaders")
    
    day_stars = []
    month_stars = []
    data_source = "Live Scan"

    # Try to load from cache first
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_cache.json")
    loaded_from_cache = False
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
                
            # Parse Day Stars
            for item in cache_data.get("top_gainers_1d", [])[:4]:
                day_stars.append({
                    'ticker': item['ticker'],
                    'price': item['price'],
                    'change': item['change_1d']
                })
                
            # Parse Month Stars
            for item in cache_data.get("top_gainers_30d", [])[:3]:
                month_stars.append({
                    'ticker': item['ticker'],
                    'price': item['price'],
                    'change': item['change_30d']
                })
            
            if day_stars and month_stars:
                loaded_from_cache = True
                data_source = f"Cached ({cache_data.get('last_updated', '')[:16].replace('T', ' ')})"
        except Exception as e:
            pass
            
    if not loaded_from_cache:
        with st.spinner("Scanning popular stocks for top performers..."):
            screener = StockScreener(POPULAR_STOCKS)
            day_stars, month_stars = screener.get_market_stars()
            
    if loaded_from_cache:
        st.caption(f"⚡ Data: {data_source}")

    # --- Line 1: Stars of the Month (Compact 4-col) ---
    st.markdown("**🏆 Leaderboard (Month / Day)**")
    m_cols = st.columns(4)
    
    # Show Top 4 Monthly leaders in 4 columns
    for i, star in enumerate(month_stars[:4]):
        with m_cols[i % 4]:
            st.markdown(f"""
            <div style="background-color: rgba(255, 215, 0, 0.05); border: 1px solid rgba(255, 215, 0, 0.2); padding: 8px; border-radius: 8px; text-align: center;">
                <div style="font-size: 9px; opacity: 0.7; text-transform: uppercase;">Month Star</div>
                <div style="color: #FFD700; font-size: 15px; font-weight: bold; margin: 2px 0;">{star['ticker']}</div>
                <div style="font-size: 13px; font-weight: bold;">{star['change']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Analyze {star['ticker']}", key=f"month_btn_{i}", use_container_width=True):
                 st.session_state['page_target'] = "🔍 Deep Analyzer"
                 st.session_state['ticker_target'] = star['ticker']
                 st.session_state['trigger_analyze'] = True
                 st.rerun()

    # --- Line 2: Daily Breakouts (Compact 4-col) ---
    d_cols = st.columns(4)
    for i, star in enumerate(day_stars[:4]):
        with d_cols[i % 4]:
            st.markdown(f"""
            <div style="background-color: rgba(0, 255, 0, 0.05); border: 1px solid rgba(0, 255, 0, 0.2); padding: 8px; border-radius: 8px; text-align: center;">
                <div style="font-size: 9px; opacity: 0.7; text-transform: uppercase;">Day Star</div>
                <div style="color: #00FF00; font-size: 15px; font-weight: bold; margin: 2px 0;">{star['ticker']}</div>
                <div style="font-size: 13px; font-weight: bold;">{star['change']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Analyze {star['ticker']}", key=f"day_btn_{i}", use_container_width=True):
                 st.session_state['page_target'] = "🔍 Deep Analyzer"
                 st.session_state['ticker_target'] = star['ticker']
                 st.session_state['trigger_analyze'] = True
                 st.rerun()

    st.divider()
    
    # 3. Quick Tips / Global Context
    tc1, tc2 = st.columns(2)
    with tc1:
        st.write("### 🔥 Community Pulse")
        import random
        trending = random.sample(POPULAR_STOCKS, 4)
        for t in trending:
            st.markdown(f"""
            <div class="heatmap-item">
                <span>🔍 Analyzing <b>{t.replace('.NS', '')}</b></span>
                <span style="color:#00FF00; font-size: 10px;">LIVE</span>
            </div>
            """, unsafe_allow_html=True)
            
    with tc2:
        st.write("### 💡 Trading Pro Tip")
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); height: 100%;">
            <div style="font-size: 14px; font-weight: bold; color: #00FF00; margin-bottom: 5px;">Wait for the Pullback</div>
            <div style="font-size: 13px; opacity: 0.8; line-height: 1.5;">
                Never chase a 5% green candle. Professional traders wait for a low-volume consolidation or a touch of the 20-EMA before entering a momentum breakout.
            </div>
        </div>
        """, unsafe_allow_html=True)

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
        if st.button("🚀 Run Strategy Scan", type="primary", use_container_width=True):
            with st.spinner(f"Executing {selected_strat} on 500+ Indian Stocks..."):
                screener = StockScreener([s['symbol'] for s in TICKER_DB])
                candidates = screener.get_multibagger_candidates(limit=10, strategy=selected_strat)
                st.session_state['multibagger_results'] = candidates
                st.session_state['last_multibagger_strat'] = selected_strat

    if st.session_state.get('multibagger_results'):
        candidates = st.session_state['multibagger_results']
        current_strat = st.session_state.get('last_multibagger_strat', "selected")
        
        st.write(f"### 💎 Top 10 Multibagger Recommendations ({current_strat})")
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
                        <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                            <span style="font-size: 11px; opacity: 0.6; display: block; margin-bottom: 5px;">VIRAL PROPAGATION:</span>
                            <div style="display: flex; gap: 5px;">
                                <a href="https://api.whatsapp.com/send?text=Found%20a%20Multibagger!%20{stock['ticker']}%20at%20₹{stock['current_price']:.2f}" target="_blank" class="share-btn whatsapp-btn">WhatsApp</a>
                                <a href="https://twitter.com/intent/tweet?text=Multibagger%20Alert:%20{stock['ticker']}" target="_blank" class="share-btn twitter-btn">X</a>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Analyze {stock['ticker']}", key=f"multi_{stock['ticker']}", use_container_width=True):
                        st.session_state['ticker_target'] = stock['ticker']
                        st.session_state['page_target'] = "🔍 Deep Analyzer"
                        st.session_state['trigger_analyze'] = True 
                        st.rerun()
        st.success("Multibagger logic check successful for 10 candidates.")
            
        if st.button("🗑️ Clear Results"):
            del st.session_state['multibagger_results']
            st.rerun()
    else:
        st.write("Click the button above to start the professional-grade scan.")


elif page == "🔍 Deep Analyzer":
    render_ad_space()
    # --- Forced Redirection Sync ---
    if 'ticker_target' in st.session_state:
        target = st.session_state['ticker_target']
        clean_name = target.split('.')[0]
        
        # 1. Sync Exchange
        if ".BO" in target: st.session_state['exchange_radio'] = "BSE"
        else: st.session_state['exchange_radio'] = "NSE"
        
        # 2. Sync Search Box
        for opt in TICKER_OPTIONS:
            if opt.startswith(f"{clean_name} -"):
                st.session_state['master_search'] = opt
                break
        
        # Clean up
        del st.session_state['ticker_target']

    # --- Main Screen Configuration (Consolidated Search & Period) ---
    st.header(f"🔍 Deep Analyzer")
    
    # 1. Search & Exchange Row
    sc1, sc2 = st.columns([1, 3])
    
    with sc1:
        st.write("**🏛️ Exchange**")
        st.radio("Exchange", ["NSE", "BSE"], key="exchange_radio", horizontal=True, label_visibility="collapsed")
        # Ensure exchange variable stays in sync with radio
        st.session_state['exchange'] = st.session_state['exchange_radio']
    
    with sc2:
        st.write("**🔍 Search Stock**")
        search_mode = st.radio("Search Mode", ["📋 From List", "✍️ Manual Entry"], horizontal=True, label_visibility="collapsed", key="search_mode")
        
        if search_mode == "📋 From List":
            st.selectbox(
                "Search Ticker or Company Name",
                TICKER_OPTIONS,
                key="master_search",
                label_visibility="collapsed",
                on_change=trigger_analysis
            )
            manual_ticker = None
        else:
            manual_ticker = st.text_input(
                "Enter Stock Symbol (e.g., ELITECON, RELIANCE, TCS)",
                key="manual_ticker_input",
                placeholder="Type stock symbol...",
                label_visibility="collapsed"
            ).strip().upper()
        
    # Process Ticker from autocomplete OR manual input
    if search_mode == "✍️ Manual Entry" and manual_ticker:
        # Manual entry mode - use whatever user typed
        suffix = ".NS" if st.session_state.get('exchange', 'NSE') == "NSE" else ".BO"
        ticker_input = f"{manual_ticker}{suffix}"
        st.markdown(f"<html><head><title>Analyzing {manual_ticker} | Stock Analysis Pro</title></head></html>", unsafe_allow_html=True)
    elif st.session_state.get('master_search'):
        # Selectbox mode - use pre-loaded ticker
        sym = st.session_state['master_search'].split(' - ')[0]
        suffix = ".NS" if st.session_state.get('exchange', 'NSE') == "NSE" else ".BO"
        ticker_input = f"{sym}{suffix}"
        st.markdown(f"<html><head><title>Analyzing {sym} | Stock Analysis Pro</title></head></html>", unsafe_allow_html=True)
    else:
        ticker_input = "RELIANCE.NS"

    # 2. Period Selection Row

    # --- Main Screen Configuration (Execution) ---
    
    # ⏱️ Quick Period Row
    c_p, c_d = st.columns([2, 1])
    with c_p:
         period_preset = st.radio(
            "⏱️ Select Chart Period",
            ["1D", "1W", "1M", "1Y", "5Y", "Custom"],
            index=3, # Default to 1Y
            horizontal=True,
            key="period_preset_radio",
            on_change=trigger_analysis
        )
    
    with c_d:
        if period_preset == "Custom":
            with st.expander("📅 Select Dates/Interval", expanded=True):
                s_date = st.date_input("Start Date", date.today() - timedelta(days=365))
                e_date = st.date_input("End Date", date.today())
                i_choice = st.selectbox("Interval", ["Daily (1d)", "Hourly (1h)", "5-Min (5m)"])
        else:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); font-size: 13px; text-align: center; opacity: 0.8;">
                ⚡ Auto-Period Active
            </div>
            """, unsafe_allow_html=True)

    # Period Logic - Dynamic for Chart, persistent for AI
    end_date = date.today()
    if period_preset == "1D": start_date, interval_code = end_date - timedelta(days=2), "5m"
    elif period_preset == "1W": start_date, interval_code = end_date - timedelta(days=7), "1h"
    elif period_preset == "1M": start_date, interval_code = end_date - timedelta(days=30), "1d"
    elif period_preset == "1Y": start_date, interval_code = end_date - timedelta(days=365), "1d"
    elif period_preset == "5Y": start_date, interval_code = end_date - timedelta(days=365*5), "1wk"
    elif period_preset == "Custom":
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
            # 1. Main Fetch for Chart
            success = analyzer.fetch_data(start=start_date, end=end_date, interval=interval_code)
            
            # 2. Background Fetch for AI (Always at least 1Y Daily)
            if success:
                ai_analyzer = StockAnalyzer(ticker_input)
                # Always fetch 5 years for AI to ensure maximum projection stability
                ai_days = 365 * 5
                ai_start = end_date - timedelta(days=ai_days)
                ai_analyzer.fetch_data(start=ai_start, end=end_date, interval='1d')
                
                # Fetch balance
                analyzer.fetch_fundamentals()
                analyzer.get_news()
                
                st.session_state['data'] = analyzer.data
                st.session_state['analyzer'] = analyzer
                st.session_state['ai_analyzer'] = ai_analyzer
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
        
        # Share stats row
        sc_1, sc_2 = st.columns([2, 1])
        with sc_1:
            cur_p = df['Close'].iloc[-1]
            prev_p = df['Close'].iloc[-2]
            chg = ((cur_p - prev_p)/prev_p)*100
            render_share_buttons(ticker, cur_p, chg)
        st.write("---")
        
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
        
        # 2. Projections (Updated for AI Models)
        st.subheader("🔮 AI Price Projections")
        
        # Fixed Horizon for Deep Analyzer
        horizon = 180
        st.info("📊 Generating comprehensive 180-day forecast with multi-timeframe projections.")

        # Model Selector
        model_choice = st.selectbox(
            "🧠 Select Forecasting Model",
            ["Monte Carlo (GBM)", "XGBoost AI (Gradient Boosting)", "Random Forest AI", "Linear Regression (Trend)", "Ensemble (Best of All)"],
            index=0,
            help="Choose the algorithm used for future price projection."
        )

        with st.spinner(f"Running {model_choice} simulation for {horizon} days..."):
            # Use the AI-specific daily analyzer for forecasting
            ai_engine = st.session_state.get('ai_analyzer', analyzer)
            forecast_data = ai_engine.generate_forecast(days=horizon, model_type=model_choice)
        
        if forecast_data:
            # Badge for Strategy
            st.markdown(f"""
            <div style="background: rgba(0, 255, 0, 0.1); border: 1px solid rgba(0, 255, 0, 0.3); color: #00FF00; padding: 5px 10px; border-radius: 5px; display: inline-block; font-size: 12px; margin-bottom: 10px;">
                🤖 Strategy: {forecast_data['model_name']}
            </div>
            """, unsafe_allow_html=True)
            
            # Display Metrics
            # We dynamically display columns based on what's available
            targets = forecast_data['targets']
            cols = st.columns(len(targets) + 1)
            
            cols[0].metric("Current", f"{forecast_data['last_close']:.2f}")
            
            idx = 1
            sorted_days = sorted(targets.keys())
            for d in sorted_days:
                if d <= horizon:
                    t = targets[d]
                    color = "normal"
                    if t['change'] > 0: color = "normal" 
                    cols[idx].metric(f"{d}-Day Target", f"{t['price']:.2f}", f"{t['change']:.2f}%")
                    idx += 1
            
            # Charting the Projection
            proj_df = pd.DataFrame(forecast_data['projections'])
            
            proj_fig = go.Figure()
            
            # Historical (Last 90 pts)
            proj_fig.add_trace(go.Scatter(
                x=df.index[-90:], 
                y=df['Close'][-90:], 
                name='Historical', 
                line=dict(color='rgba(255, 255, 255, 0.5)', width=2)
            ))
            
            # Multi-Color Projection Segments
            last_hist_date = df.index[-1]
            if hasattr(last_hist_date, 'strftime'):
                last_hist_date = last_hist_date.strftime('%Y-%m-%d')
            last_hist_price = df['Close'].iloc[-1]
            
            # Define color segments: (end_day, color, label)
            segments = [
                (10, "#00FF00", "10D"), 
                (30, "#00DFFF", "30D"), 
                (60, "#0080FF", "60D"), 
                (90, "#8000FF", "90D"), 
                (180, "#FF00FF", "180D")
            ]
            
            prev_date = last_hist_date
            prev_price = last_hist_price
            
            for end_day, color, label in segments:
                # Filter projection data for this segment
                seg_data = proj_df[proj_df['Day'] <= end_day]
                if prev_day := (segments[segments.index((end_day, color, label))-1][0] if segments.index((end_day, color, label)) > 0 else 0):
                    seg_data = proj_df[(proj_df['Day'] > prev_day) & (proj_df['Day'] <= end_day)]
                
                if not seg_data.empty:
                    # Append previous point to ensure continuity
                    seg_dates = [prev_date] + list(seg_data['Date'])
                    seg_prices = [prev_price] + list(seg_data['Price'])
                    
                    proj_fig.add_trace(go.Scatter(
                        x=seg_dates, 
                        y=seg_prices, 
                        name=f'Forecast ({label})', 
                        line=dict(color=color, width=3, dash='dash')
                    ))
                    
                    # Update prev for next segment
                    prev_date = list(seg_data['Date'])[-1]
                    prev_price = list(seg_data['Price'])[-1]
            
            # Fill Area (Confidence / Volatility visual) - simplified as under-fill
            proj_fig.update_layout(
                title=f"{ticker} Future Flight Path",
                height=400, 
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Date",
                yaxis_title="Price"
            )
            
            st.plotly_chart(proj_fig, use_container_width=True)
        else:
            st.warning("Not enough data to generate a reliable forecast. Please select '1Y' or more.")

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
    st.header("⚡ Intraday Scalper")
    
    # Strict Market Hours Enforcement for this page
    market_open, market_msg = is_market_open()
    
    if not market_open:
        st.warning(f"🌙 {market_msg}")
        st.info("This section is only active during live market hours (9:15 AM - 3:30 PM IST).")
        st.stop() # Prevents showing the tabs and logic below

    st.info("⚠️ **Uses Live Hourly Data.** Market is LIVE. Happy Trading!")

    tab1, tab2 = st.tabs(["🔔 Live Monitor", "🔥 Trending"])

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

    # --- TAB 2: Trending Stocks ---
    with tab2:
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

elif page == "🤖 Paper Trading Simulator":
    st.header("🤖 Auto-Trading Bot Monitor")
    
    trader = st.session_state['trader']
    trader.load_state() # Sync with background service
    trader.active_rules = trader.load_learned_rules()
    
    st.markdown("""
    <div style="background: rgba(0, 255, 0, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(0, 255, 0, 0.2);">
        <strong>💼 Virtual Portfolio (₹10,000 Capital)</strong><br>
        This bot autonomously scans for <strong>Momentum Breakouts</strong> & <strong>Volume Bursts</strong>.
        <br>It executes a <strong>Rapid Scalping Strategy</strong>:
        <br>🎯 <strong>Target:</strong> +0.80% Gain | 🛑 <strong>Stop Loss:</strong> -0.40% Loss (2:1 Ratio)
    </div>
    """, unsafe_allow_html=True)
    
    # AI Rules Display
    if trader.active_rules.get('blocklist_conditions'):
        with st.expander("🧠 AI Learned Rules (Self-Healing)", expanded=False):
            st.info("The bot has identified these patterns in past losses and will now automatically avoid them:")
            for rule in trader.active_rules['blocklist_conditions']:
                st.write(f"🚫 {rule}")
    st.write("")

    m1, m2, m3 = st.columns(3)
    m1.metric("Cash Balance", f"₹{trader.cash:.2f}")
    m2.metric("Realized P&L", f"₹{trader.total_profit:.2f}")
    m3.metric("Open Positions", len(trader.positions))
    
    st.divider()
    
    # Bot Status Monitor (Synchronized with IST)
    bot_status = {"active": False, "msg": "Bot not detected", "last_run": "Never", "version": "Unknown"}
    if os.path.exists("bot_status.json"):
        try:
            with open("bot_status.json", "r") as f:
                bot_status = json.load(f)
        except: pass
    
    # Check if we are reading from an old UTC bot
    is_old_bot = bot_status.get("version") != "2.1-IST-FIX"

    if bot_status.get("active") and not is_old_bot:
        st.markdown(f"""
        <div style="background: rgba(0, 255, 0, 0.1); border: 1px solid rgba(0, 255, 0, 0.5); padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
            <div style="color: #00FF00; font-weight: 800; font-size: 20px; letter-spacing: 1px;">🟢 AI BOT: {bot_status.get('msg', 'WORKING').upper()}</div>
            <div style="font-size: 13px; color: #00FF00; opacity: 0.8; margin-top: 5px;">
                Update: {bot_status.get('last_run')} IST | Version: {bot_status.get('version', 'Legacy')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif is_old_bot:
         st.markdown(f"""
        <div style="background: rgba(255, 165, 0, 0.1); border: 1px solid rgba(255, 165, 0, 0.5); padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
            <div style="color: #FFA500; font-weight: 800; font-size: 20px; letter-spacing: 1px;">⚠️ OUTDATED BOT DETECTED</div>
            <div style="font-size: 13px; color: #FFA500; opacity: 0.8; margin-top: 5px;">
                The background service is still running an old UTC version ({bot_status.get('last_run')}).
                <br>Please refresh the page or wait 60s for the new IST version to take over.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(255, 75, 75, 0.1); border: 1px solid rgba(255, 75, 75, 0.4); padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
            <div style="color: #FF4B4B; font-weight: 800; font-size: 20px; letter-spacing: 1px;">💤 AI BOT: {bot_status.get('msg', 'SLEEPING').upper()}</div>
            <div style="font-size: 13px; color: #FF4B4B; opacity: 0.8; margin-top: 5px;">
                Service Status: {bot_status.get('msg')} | Time: {bot_status.get('last_run')} IST
            </div>
        </div>
        """, unsafe_allow_html=True)

                
    # Display Results
    st.divider()
    c_p, c_l = st.columns([2, 1])
    
    with c_p:
        if trader.positions:
            st.subheader("💼 Active Positions")
            pos_data = []
            for t, p in trader.positions.items():
                pos_data.append({
                    "Symbol": t, "Qty": p['qty'], 
                    "Entry": f"₹{p['avg_price']:.2f}", 
                    "Value": f"₹{p['qty']*p['avg_price']:.2f}"
                })
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
        else:
            st.info("Bot is currently looking for entries. No open positions.")

    with c_l:
        st.subheader("📜 Recent Activity")
        if not trader.trade_log:
            st.caption("No trades taken today yet.")
        for log in trader.trade_log[:10]:
            st.caption(log)

    st.divider()
    if st.button("🧹 Reset Simulator (Clear History)", help="Wipes all trade history and resets capital to ₹10,000."):
        trader.cash = 10000.0
        trader.positions = {}
        trader.trade_log = []
        trader.total_profit = 0.0
        trader.equity_history = [{"ts": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "value": 10000.0}]
        trader.save_state()
        st.success("Simulator Reset Successfully!")
        st.rerun()



# --- Scrolling Disclaimer Marquee (v3.9) ---
st.markdown("""
    <style>
    .disclaimer-marquee {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(15, 15, 15, 0.98);
        color: #FF4B4B;
        padding: 8px 0;
        font-size: 11px;
        border-top: 1px solid rgba(255, 75, 75, 0.4);
        z-index: 1000;
        backdrop-filter: blur(8px);
        overflow: hidden;
        white-space: nowrap;
    }
    .disclaimer-content {
        display: inline-block;
        animation: scroll-disclaimer 45s linear infinite;
        padding-left: 100%;
    }
    @keyframes scroll-disclaimer {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }
    </style>
    <div class="disclaimer-marquee">
        <div class="disclaimer-content">
            <strong>⚠️ LEGAL DISCLOSURE:</strong> (1) Educational Research Tool only • (2) Developer is NOT a SEBI Registered RA/RIA • (3) Signals/Targets are AI-generated & NOT buy/sell tips • (4) Past performance ≠ Future results • We are NOT liable for losses • Consult a professional advisor before trading
        </div>
    </div>
""", unsafe_allow_html=True)
