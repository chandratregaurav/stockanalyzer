
import schedule
import time
import argparse
import sys
from stock_analyzer import StockAnalyzer
from datetime import datetime

def job(ticker):
    print(f"\n[{datetime.now()}] Starting daily job for {ticker}")
    analyzer = StockAnalyzer(ticker)
    if analyzer.fetch_data():
        analyzer.fetch_fundamentals()
        # You can add more processing here if needed, 
        # but avoid calling non-existent analyze_and_project()
        print(f"Analysis complete for {ticker}")
    print(f"[{datetime.now()}] Job finished.")

def main():
    parser = argparse.ArgumentParser(description='Stock Analysis and Projection App')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., GOOGL, RELIANCE.NS)')
    parser.add_argument('--run-once', action='store_true', help='Run the analysis once immediately and exit')
    
    args = parser.parse_args()
    
    ticker = args.ticker
    
    if args.run_once:
        job(ticker)
        sys.exit(0)

    # Schedule the job to run daily at a specific time (e.g., 09:00 AM)
    # For demonstration, we'll set it to run immediately then wait, or just loop
    # The requirement says "once per day". Let's set it to 10:00 AM.
    schedule.every().day.at("10:00").do(job, ticker=ticker)
    
    print(f"Scheduler started. Job for {ticker} will run daily at 10:00 AM.")
    print("Press Ctrl+C to exit.")
    
    # Also run once at startup so the user sees something immediately? 
    # Maybe better to let them decide with --run-once. 
    # But usually a scheduler app runs forever.
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
