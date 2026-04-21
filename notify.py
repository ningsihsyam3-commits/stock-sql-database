import pandas as pd
import os
import requests
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime

# --- KONFIGURASI TELEGRAM ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def kirim_gambar_telegram(chat_id, image_path, caption):
    """Fungsi khusus untuk mengirim file gambar ke Telegram"""
    token_clean = TOKEN.replace('bot', '') if TOKEN else ""
    url = f"https://api.telegram.org/bot{token_clean}/sendPhoto"
    
    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            payload = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            r = requests.post(url, data=payload, files=files)
            if r.status_code != 200:
                print(f"Gagal kirim gambar: {r.text}")
            else:
                print(f"Laporan visual berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"Error saat mengirim gambar: {e}")

def buat_grafik(df_ticker, ticker):
    """Fungsi untuk menggambar Candlestick, MA5, MA20, dan RSI"""
    df_ticker = df_ticker.copy()
    
    # Mapping kolom untuk mplfinance
    df_ticker['Open']  = df_ticker['Close']
    df_ticker['High']  = df_ticker['Close']
    df_ticker['Low']   = df_ticker['Close']
    df_ticker['Volume'] = df_ticker['Volume'] if 'Volume' in df_ticker.columns else 0
    
    apds = []
    # Plot MA5 dan MA20
    if 'MA5' in df_ticker.columns and 'MA20' in df_ticker.columns:
        apds.append(mpf.make_addplot(df_ticker['MA5'], color='green', width=1)) 
        apds.append(mpf.make_addplot(df_ticker['MA20'], color='red', width=1))

    # Plot RSI di Panel bawah
    if 'RSI' in df_ticker.columns and not df_ticker['RSI'].isnull().all():
        apds.append(mpf.make_addplot(df_ticker['RSI'], panel=1, color='blue', ylabel='RSI'))
        apds.append(mpf.make_addplot([70]*len(df_ticker), panel=1, color='orange', width=0.7, linestyle='--'))
        apds.append(mpf.make_addplot([30]*len(df_ticker), panel=1, color='orange', width=0.7, linestyle='--'))

    image_filename = f"{ticker}_chart.png"
    
    try:
        mpf.plot(df_ticker, type='line', 
                 addplot=apds,
                 title=f"\nAnalisis Teknikal & Anomali: {ticker}",
                 ylabel='Harga',
                 style='charles',
                 savefig=image_filename,
                 figsize=(12, 8),
                 panel_ratios=(2, 1)
                )
        return image_filename
    except Exception as e:
        print(f"Error plotting {ticker}: {e}")
        return None

def cek_sinyal_dan_visualisasi():
    engine = create_engine('sqlite:///database_investasi.db')
    assets = ['BBRI_JK', 'CTRA_JK', 'TLKM_JK', 'ASII_JK', 'BTC_USD']
    
    # Header Pesan
    url_text = f"https://api.telegram.org/bot{TOKEN.replace('bot', '')}/sendMessage"
    requests.post(url_text, json={"chat_id": CHAT_ID, "text": "🔔 *LAPORAN SPECIALIST SMART BOT* 🔔\n---", "parse_mode": "Markdown"})

    try:
        for ticker in assets:
            # Load data dari tabel masing-masing
            df = pd.read_sql(f"SELECT * FROM {ticker} ORDER BY Date ASC", engine, index_col='Date', parse_dates=True)
            if df.empty: continue
            
            dft_plot = df.tail(40) # Ambil 40 data terakhir untuk grafik
            curr = df.iloc[-1]    # Data hari ini
            prev = df.iloc[-2]    # Data kemarin
            
            # 1. Logika Perubahan Harga
            perubahan = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
            tanda = "↗️ +" if perubahan > 0 else "↘️ "
            
            # 2. Logika Sinyal Golden Cross (MA5/MA20)
            sinyal = "🔍 *Stabil*"
            if prev['MA5'] <= prev['MA20'] and curr['MA5'] > curr['MA20']: sinyal = "🚀 *GOLDEN CROSS (BUY)*"
            elif prev['MA5'] >= prev['MA20'] and curr['MA5'] < curr['MA20']: sinyal = "💀 *DEATH CROSS (SELL)*"
            elif curr['MA5'] > curr['MA20']: sinyal = "✅ *Bullish Trend*"
            else: sinyal = "⚠️ *Bearish Trend*"

            # 3. Logika Anomali (Z-Score)
            status_anomali = "✅ Normal"
            if curr['Is_Anomaly'] == 1:
                status_anomali = f"🚨 *ANOMALI DETECTED* (Z-Score: {curr['Z_Score']:.2f})"

            # 4. Performa Strategi (Backtesting)
            strategy_perf = (curr['Cumulative_Strategy'] - 1) * 100

            # MENYUSUN CAPTION
            caption = f"📊 *Aset: {ticker.replace('_', '.')}*\n"
            caption += f"💰 Price: {curr['Close']:,.0f} ({tanda}{perubahan:.2f}%)\n"
            caption += f"📡 Signal: {sinyal}\n"
            caption += f"🛡️ Status: {status_anomali}\n"
            caption += f"📈 Strategy Return: *{strategy_perf:.2f}%*\n"
            caption += "--------------------------------\n"
            
            # PROSES VISUALISASI
            image_path = buat_grafik(dft_plot, ticker)
            if image_path and os.path.exists(image_path):
                kirim_gambar_telegram(CHAT_ID, image_path, caption)
                os.remove(image_path)
            else:
                requests.post(url_text, json={"chat_id": CHAT_ID, "text": caption, "parse_mode": "Markdown"})

        # 5. Tambahan: Informasi Korelasi
        try:
            corr_df = pd.read_sql("SELECT * FROM market_correlation", engine)
            if not corr_df.empty:
                corr_msg = f"🔗 *Market Correlation*\nBTC vs BBRI: `{corr_df['Value'].iloc[0]:.2f}`"
                requests.post(url_text, json={"chat_id": CHAT_ID, "text": corr_msg, "parse_mode": "Markdown"})
        except:
            pass

    except Exception as e:
        print(f"Error Pipeline: {e}")

if __name__ == "__main__":
    if TOKEN and CHAT_ID:
        cek_sinyal_dan_visualisasi()
    else:
        print("Error: Missing Telegram Config.")
