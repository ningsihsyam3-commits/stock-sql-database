import pandas as pd
import os
import requests
from sqlalchemy import create_engine

def kirim_telegram(pesan):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": pesan, "parse_mode": "Markdown"}
    
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            print("Notifikasi berhasil dikirim!")
        else:
            print(f"Gagal kirim: {r.text}")
    except Exception as e:
        print(f"Error kirim Telegram: {e}")

def cek_sinyal_dan_notifikasi():
    engine = create_engine('sqlite:///database_investasi.db')
    try:
        # Mengambil data terbaru dari database
        df = pd.read_sql("SELECT * FROM history_saham ORDER BY date DESC", engine)
        
        # Ambil baris terbaru untuk setiap saham (Last Close)
        hari_ini = df.groupby('ticker').head(1)
        
        pesan_final = "🔔 *LAPORAN SAHAM HARIAN* 🔔\n"
        pesan_final += "----------------------------\n\n"
        
        for _, row in hari_ini.iterrows():
            ticker = row['ticker']
            harga = row['close_price']
            ma5 = row.get('ma5') # Menggunakan .get agar tidak error jika kolom belum ada
            ma20 = row.get('ma20')
            rsi = row.get('rsi')
            
            # --- PROTEKSI & LOGIKA MA ---
            # Cek MA20 untuk Tren Utama
            if ma20 is not None and not pd.isna(ma20):
                status_ma = "✅ *Bullish*" if harga > ma20 else "⚠️ *Bearish*"
                txt_ma20 = f"Rp{ma20:,.0f}"
            else:
                status_ma = "⏳ *Menghitung...*"
                txt_ma20 = "-"

            # Cek MA5 untuk Patokan Jangka Pendek
            txt_ma5 = f"Rp{ma5:,.0f}" if (ma5 is not None and not pd.isna(ma5)) else "-"

            # --- PROTEKSI & LOGIKA RSI ---
            if rsi is not None and not pd.isna(rsi):
                if rsi >= 70:
                    status_rsi = f"🔥 *Overbought* ({rsi:.1f})"
                elif rsi <= 30:
                    status_rsi = f"❄️ *Oversold* ({rsi:.1f})"
                else:
                    status_rsi = f"⚖️ *Netral* ({rsi:.1f})"
            else:
                status_rsi = "⏳ *Menghitung...*"
            
            # --- PENYUSUNAN TAMPILAN PESAN ---
            pesan_final += f"📈 *{ticker}*\n"
            pesan_final += f"💰 Harga Terakhir: Rp{harga:,.0f}\n"
            pesan_final += "----------------------------\n"
            pesan_final += f"📍 Patokan MA5  : {txt_ma5}\n"
            pesan_final += f"📍 Patokan MA20 : {txt_ma20}\n"
            pesan_final += f"🌡️ Status RSI   : {status_rsi}\n"
            pesan_final += f"📊 Kondisi Tren : {status_ma}\n"
            pesan_final += "----------------------------\n\n"
            
        kirim_telegram(pesan_final)
        
    except Exception as e:
        # Menangkap error jika ada masalah pembacaan database
        print(f"Terjadi kesalahan saat memproses laporan: {e}")

if __name__ == "__main__":
    cek_sinyal_dan_notifikasi()
