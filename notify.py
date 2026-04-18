import os
import requests
import pandas as pd
from sqlalchemy import create_engine

def kirim_telegram(pesan):
    # Mengambil token dan chat_id dari environment variable (GitHub Secrets)
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Error: Token atau Chat ID tidak ditemukan!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": pesan,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Notifikasi berhasil dikirim ke Telegram!")
        else:
            print(f"Gagal mengirim: {response.text}")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

def cek_sinyal_dan_notifikasi():
    engine = create_engine('sqlite:///database_investasi.db')
    try:
        # Mengambil data terbaru
        df = pd.read_sql("SELECT * FROM history_saham ORDER BY date DESC", engine)
        hari_ini = df.groupby('ticker').head(1)
        
        pesan_final = "🔔 *LAPORAN SAHAM HARIAN* 🔔\n"
        pesan_final += "----------------------------\n\n"
        
        for _, row in hari_ini.iterrows():
            ticker = row['ticker']
            harga = row['close_price']
            ma5 = row['ma5']
            ma20 = row['ma20']
            rsi = row['rsi']

        # --- LOGIKA PROTEKSI FINAL ---
        
        # 1. Logika Tren (Hanya jalan jika ma20 ada angkanya)
        if ma20 is not None and not pd.isna(ma20):
            status_ma = "✅ *Bullish*" if harga > ma20 else "⚠️ *Bearish*"
        else:
            status_ma = "⏳ *Menghitung MA20...*"

        # 2. Logika RSI (Hanya jalan jika rsi ada angkanya)
        if rsi is not None and not pd.isna(rsi):
            if rsi >= 70:
                status_rsi = f"🔥 *Overbought* ({rsi:.1f})"
            elif rsi <= 30:
                status_rsi = f"❄️ *Oversold* ({rsi:.1f})"
            else:
                status_rsi = f"⚖️ *Netral* ({rsi:.1f})"
        else:
            status_rsi = "⏳ *Menghitung RSI...*"
            
        # 1. Logika Tren (Harga vs MA20)
        if harga > ma20:
            status_ma = "✅ *Bullish* (Di atas MA20)"
        else:
            status_ma = "⚠️ *Bearish* (Di bawah MA20)"
            
        # 2. Logika RSI (Kesehatan Tren)
        if rsi >= 70:
            status_rsi = f"🔥 *Overbought* ({rsi:.1f})"
        elif rsi <= 30:
            status_rsi = f"❄️ *Oversold* ({rsi:.1f})"
        else:
            status_rsi = f"⚖️ *Netral* ({rsi:.1f})"
            
        # Menyusun Pesan dengan Angka Patokan yang Jelas
        pesan_final += f"📈 *{ticker}*\n"
        pesan_final += f"💰 Harga Saat Ini: Rp{harga:,.0f}\n"
        pesan_final += "----------------------------\n"
        
        # Menampilkan Angka Patokan sebagai referensi
        if ma5:
            pesan_final += f"📍 Patokan MA5  : Rp{ma5:,.0f}\n"
        if ma20:
            pesan_final += f"📍 Patokan MA20 : Rp{ma20:,.0f}\n"
            
        pesan_final += f"🌡️ Status RSI    : {status_rsi}\n"
        pesan_final += f"📊 Kondisi Tren  : {status_ma}\n"
        pesan_final += "----------------------------\n\n"
        
        kirim_telegram(pesan_final)
    except Exception as e:
        print(f"Error saat membaca database: {e}")
        
if __name__ == "__main__":
    cek_sinyal_dan_notifikasi()

