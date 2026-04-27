# 📈 Automated Financial Analysis & Visual Bot

An autonomous end-to-end pipeline that fetches stock market data, performs technical analysis (MA & RSI), and delivers visual reports directly to Telegram.

## 🚀 Key Features
- **Automated Ingestion**: Scheduled data fetching from Yahoo Finance.
- **Technical Indicator Engine**: Built with `pandas-ta` to calculate SMA (5, 20), RSI (14), and Volume Analysis.
- **Dynamic Visualization**: Generates technical charts with `mplfinance` including indicator overlays and RSI panels.
- **CI/CD Integration**: Fully automated via GitHub Actions with a headless Matplotlib configuration.

## 🛠️ Technology Stack
- **Language**: Python 3.12
- **Data Science**: Pandas, Pandas-TA, SQLAlchemy
- **Visualization**: Matplotlib, Mplfinance
- **Automation**: GitHub Actions (YAML)
- **Database**: SQLite (local persistence)
- **Notification**: Telegram Bot API

## 🔄 Workflow Architecture
1. **Download**: `download_data.py` fetches the latest market OHLCV data.
2. **Analyze**: `analys.py` processes raw data into technical signals.
3. **Notify**: `notify.py` renders visual charts and pushes alerts to Telegram.
4. **Dashboard**: `app.py`
