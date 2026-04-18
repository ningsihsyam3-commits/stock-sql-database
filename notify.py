import pandas as pd
import os
import requests
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import mplfinance as mpf
import io

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
                print("Laporan visual berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"Error saat mengirim gambar: {e}")

def buat_grafik(df_ticker, ticker):
    """Fungsi untuk menggambar Candlestick, MA, dan RSI"""
    # Pastikan index adalah Datetime (kebutuhan mplfinance)
    df_ticker = df_ticker.copy()
    df_ticker['date'] = pd.to_datetime(df_ticker['date'])
    df_ticker = df_ticker.set_index('date')
    
    # Menyiapkan data untuk Candlestick (mplfinance butuh kolom OHLC)
    # Kita butuh Open, High, Low. Jika belum disimpan di DB, 
    # untuk sementara kita gunakan Close sebagai perwakilan OHLC 
    # agar tidak perlu update download_data lagi.
    # (Di masa depan, sebaiknya download O,H,L juga)
    if 'open' not in df_ticker:
        df_ticker['open'] = df_ticker['close_price']
        df_ticker['high'] = df_ticker['close_price']
        df_ticker['low'] = df_ticker['close_price']
    
    # 1. Menyiapkan Plot MA (Moving Average)
    apds = []
    if 'ma5' in df_ticker and 'ma20' in df_ticker:
        apds.append(mpf.make_addplot(df_ticker['ma5'], color='green', width=1)) # MA5
        apds.append(mpf.make_addplot(df_ticker['ma20'], color='red', width=1))   # MA20

    # 2. Menyiapkan Plot RSI (di panel bawah)
    if 'rsi' in df_ticker and not df_ticker['rsi'].isnull().all():
        # Panel=1 artinya diletakkan di bawah grafik utama
        apds.append(mpf.make_addplot(df_ticker['rsi'], panel=1, color='blue', ylabel='RSI (14)', secondary_y=False))
        # Tambahkan garis batas 70 dan 30 (opsional, tapi bagus untuk portofolio)
        apds.append(mpf.make_addplot([70]*len(df_ticker), panel=1, color='orange', width=0.7, linestyle='--'))
        apds.append(mpf.make_addplot([30]*len(df_ticker), panel=1, color='orange', width=0.7, linestyle='--'))

    # Nama file gambar temporer
    image_filename = f"{ticker}_chart.png"
    
    # 3. Menjalankan Plotting dengan mplfinance
    try:
        # Mengatur style grafik (kita gunakan 'charles' yang cerah)
        # Type='candle' untuk candlestick, atau type='line' untuk garis harga
        mpf.plot(df_ticker, type='line', 
                 addplot=apds,
                 title=f"\nGrafik Analisis Teknikal: {ticker}",
                 ylabel='Harga (Rp)',
                 style='charles',
                 savefig=image_filename, # Simpan sebagai file
                 figsize=(12, 8),      # Ukuran gambar yang optimal
                 panel_ratios=(2, 1)   # Ratio grafik utama vs RSI (2:1)
                )
        return image_filename
    except Exception as e:
        print(f"Error saat membuat grafik untuk {ticker}: {e}")
        return None

def cek_sinyal_dan_visualisasi():
    """Fungsi utama untuk membaca DB, membuat grafik, dan mengirim laporan"""
    engine = create_engine('sqlite:///database_investasi.db')
    try:
        # 1. Ambil seluruh data historis untuk plotting
        df_full = pd.read_sql("SELECT * FROM history_saham ORDER BY ticker, date ASC", engine)
        if df_full.empty:
            print("Database kosong.")
            return
            
        tickers = df_full['ticker'].unique()
        
        # Header Laporan (Pesan Teks pembuka)
        header_pesan = "🔔 *LAPORAN VISUAL SMART BOT* 🔔\n"
        header_pesan += "--------------------------------\n\n"
        
        # Kita kirim teks header terlebih dahulu agar tidak error jika grafik gagal
        url_text = f"https://api.telegram.org/bot{TOKEN.replace('bot', '')}/sendMessage"
        requests.post(url_text, json={"chat_id": CHAT_ID, "text": header_pesan, "parse_mode": "Markdown"})
        
        for ticker in tickers:
            # Data historis untuk plotting (misal ambil 40 hari terakhir)
            dft_full = df_full[df_full['ticker'] == ticker].tail(40)
            
            # Data terbaru untuk sinyal teks
            data_ticker = dft_full.tail(2) 
            if len(data_ticker) < 2: continue
            curr = data_ticker.iloc[1] # Hari Ini
            prev = data_ticker.iloc[0] # Kemarin
            
            # --- LOGIKA SINYAL (Sama seperti sebelumnya) ---
            # 1. Perubahan Harga
            perubahan = ((curr['close_price'] - prev['close_price']) / prev['close_price']) * 100
            tanda = "↗️ +" if perubahan > 0 else "↘️ "
            
            # 2. Golden Cross Logic
            ma5_c, ma20_c = curr.get('ma5'), curr.get('ma20')
            ma5_p, ma20_p = prev.get('ma5'), prev.get('ma20')
            sinyal = "🔍 *Analisis Tren...*"
            if all(v is not None and not pd.isna(v) for v in [ma5_c, ma20_c, ma5_p, ma20_p]):
                if ma5_p <= ma20_p and ma5_c > ma20_c: sinyal = "🚀 *GOLDEN CROSS (STRONG BUY)*"
                elif ma5_p >= ma20_p and ma5_c < ma20_c: sinyal = "💀 *DEATH CROSS (STRONG SELL)*"
                elif ma5_c > ma20_c: sinyal = "✅ *Bullish Trend*"
                else: sinyal = "⚠️ *Bearish Trend*"

            # 3. Volume Logic (Membandingkan vol_ma10)
            vol_status = "Normal"
            if curr.get('vol_ma10') and curr['volume'] > (curr['vol_ma10'] * 1.5):
                vol_status = "🔥 *High Accumulation*"

            # MENYUSUN CAPTION (Teks di bawah gambar)
            caption_visual = f"📊 *Analisis: {ticker}*\n"
            caption_visual += "--------------------------------\n"
            caption_visual += f"💰 Price: Rp{curr['close_price']:,.0f} ({tanda}{perubahan:.2f}%)\n"
            caption_visual += f"📡 Signal: {sinyal}\n"
            caption_visual += f"🔊 Volume: {vol_status}\n"
            caption_visual += "--------------------------------\n\n"
            
            # --- PROSES VISUALISASI ---
            print(f"Sedang membuat grafik untuk {ticker}...")
            image_path = buat_grafik(dft_full, ticker)
            
            # Jika grafik berhasil dibuat, kirim ke Telegram
            if image_path and os.path.exists(image_path):
                kirim_gambar_telegram(CHAT_ID, image_path, caption_visual)
                # Hapus file gambar setelah dikirim agar tidak memenuhi penyimpanan
                os.remove(image_path) 
            else:
                # Jika grafik gagal, kirim teks saja sebagai cadangan
                requests.post(url_text, json={"chat_id": CHAT_ID, "text": f"Gagal membuat grafik {ticker}.\n{caption_visual}", "parse_mode": "Markdown"})

    except Exception as e:
        print(f"Error Pipeline Visual: {e}")

if __name__ == "__main__":
    # Pastikan TOKEN dan CHAT_ID tersedia
    if not TOKEN or not CHAT_ID:
        print("Error: TELEGRAM_TOKEN atau TELEGRAM_CHAT_ID tidak ditemukan di environment variables.")
    else:
        cek_sinyal_dan_visualisasi()
