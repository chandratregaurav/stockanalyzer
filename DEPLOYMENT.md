# 🚀 How to Deploy Your Trading Bot for Free

The easiest way to host your Streamlit app for free is using **Streamlit Community Cloud**.

### 1️⃣ Push your code to GitHub
If you haven't already:
1.  Go to [GitHub](https://github.com) and create a new **Public** repository.
2.  Upload these files from your `antigravity` folder:
    *   `dashboard.py` (Main entry point)
    *   `stock_screener.py`
    *   `stock_analyzer.py`
    *   `paper_trader.py`
    *   `assets.py`
    *   `requirements.txt` (I just created this for you)

### 2️⃣ Deploy to Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io).
2.  Log in with your GitHub account.
3.  Click **"New app"**.
4.  Select your repository, branch, and set the Main file path to `dashboard.py`.
5.  Click **Deploy!** 🚀

### 3️⃣ Important Notes
*   **Public vs Private:** Streamlit Community Cloud is free for public repositories.
*   **Resources:** It provides enough CPU/RAM for this bot to run smoothly.
*   **Idle Apps:** If no one visits your app for a few days, it might "go to sleep" to save resources. It wakes up automatically when someone visits the link.

**Your app will be live at a URL like: `https://your-app-name.streamlit.app`**
