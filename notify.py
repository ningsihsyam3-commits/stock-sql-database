import pandas as pd
import os
import requests
from sqlalchemy import create_engine
import mplfinance as mpf
from datetime import datetime

# --- KONFIGURASI TELEGRAM ---
# Langsung gunakan variabel lingkungan tanpa modifikasi string yang merusak URL
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def kirim_gambar_telegram(chat_id, image_path, caption):
    """Fungsi untuk mengirim file gambar ke Telegram dengan URL yang benar"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
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
                print(f"❌ Gagal kirim gambar: {r.text}")
            else:
                print(f"✅ Laporan visual {image_path} terkirim!")
    except Exception as e:
        print(f"❌ Error saat mengirim gambar: {e}")

def buat_grafik(df_ticker, ticker):
    """Membuat grafik teknikal yang bersih"""
    df_plot = df_ticker.copy()
    
    # Kelola mapping kolom agar tidak error jika OHLC tidak lengkap
    if 'Close' in df_plot.columns:
        df_plot['Open'] = df_plot['Close']
        df_plot['High'] = df_plot['Close']
        df_plot['Low'] = df_plot['Close']
    
    apds = []
    # Plot MA5 dan MA20 jika tersedia
    if 'MA5' in df_plot.columns and 'MA20' in df_plot.columns:
        apds.append(mpf.make_addplot(df_plot['MA5'], color='green', width=1)) 
        apds.append(mpf.make_addplot(df_plot['MA20'], color='red', width=1))

    # Plot RSI di Panel bawah
    if 'RSI' in df_plot.columns and not df_plot['RSI'].isnull().all():
        apds.append(mpf.make_addplot(df_plot['RSI'], panel=1, color='blue', ylabel='RSI'))

    image_filename = f"{ticker.replace('.', '_')}_chart.png"
    
    try:
        mpf.plot(df_plot, type='line', 
                 addplot=apds,
                 title=f"\nAnalisis: {ticker}",
                 ylabel='Price',
                 style='charles',
                 savefig=image_filename,
                 figsize=(10, 6),
                 panel_ratios=(2, 1))
        return image_filename
    except Exception as e:
        print(f"❌ Error plotting {ticker}: {e}")
        return None

def cek_sinyal_dan_visualisasi():
    engine = create_engine('sqlite:///database_investasi.db')
    # Daftar aset yang PASTI ada di database Anda berdasarkan log terakhir
    assets = ['ASII.JK', 'BBNI.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK']
    
    url_text = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url_text, json={"chat_id": CHAT_ID, "text": "🔔 *LAPORAN ANALISIS SMART BOT* 🔔", "parse_mode": "Markdown"})

    for ticker in assets:
        try:
            # SINKRONISASI: Ubah nama ticker menjadi nama tabel (Garis Bawah)
            table_name = ticker.replace('.', '_').replace('-', '_')
            
            # Gunakan tanda kutip ganda untuk nama tabel di SQL
            query = f'SELECT * FROM "{table_name}" ORDER BY Date ASC'
            df = pd.read_sql(query, engine, index_col='Date', parse_dates=True)
            
            if df.empty or len(df) < 2:
                continue
                
            dft_plot = df.tail(30) # 30 hari terakhir
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Logika Sinyal
            perubahan = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
            tanda = "↗️" if perubahan > 0 else "↘️"
            
            sinyal = "🔍 *Stabil*"
            if curr['MA5'] > curr['MA20'] and prev['MA5'] <= prev['MA20']: sinyal = "🚀 *BUY (Golden Cross)*"
            elif curr['MA5'] < curr['MA20'] and prev['MA5'] >= prev['MA20']: sinyal = "💀 *SELL (Death Cross)*"
            elif curr['MA5'] > curr['MA20']: sinyal = "✅ *Trend Bullish*"
            else: sinyal = "⚠️ *Trend Bearish*"

            # Caption
            caption = (f"📊 *Aset: {ticker}*\n"
                       f"💰 Price: {curr['Close']:,.0f} ({tanda} {perubahan:.2f}%)\n"
                       f"📡 Signal: {sinyal}\n"
                       f"🛡️ Anomali: {'🚨 YA' if curr.get('Is_Anomaly') == 1 else '✅ Normal'}\n"
                       f"📈 Strategy: *{(curr.get('Cumulative_Strategy', 1)-1)*100:.2f}%*")

            # Kirim Visual
            img = buat_grafik(dft_plot, ticker)
            if img:
                kirim_gambar_telegram(CHAT_ID, img, caption)
                if os.path.exists(img): os.remove(img)
            else:
                requests.post(url_text, json={"chat_id": CHAT_ID, "text": caption, "parse_mode": "Markdown"})

        except Exception as e:
            print(f"❌ Skip {ticker} karena error: {e}")

if __name__ == "__main__":
    if TOKEN and CHAT_ID:
        cek_sinyal_dan_visualisasi()
    else:
        print("❌ Konfigurasi Telegram (TOKEN/CHAT_ID) belum diset di Secrets!")
