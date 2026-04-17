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
        df = pd.read_sql("SELECT * FROM history_saham ORDER BY date DESC", engine)
        
        # Ambil data terbaru untuk setiap ticker
        hari_ini = df.groupby('ticker').head(1)
        
        pesan_final = "🔔 *LAPORAN SAHAM HARIAN* 🔔\n"
        pesan_final += "----------------------------\n\n"
        
        for _, row in hari_ini.iterrows():
            ticker = row['ticker']
            harga = row['close_price']
            ma20 = row['ma20']
            
            # Logika sederhana: Cek posisi harga terhadap MA20
            if ma20 and harga > ma20:
                sinyal = "✅ *Bullish* (Di atas MA20)"
            elif ma20 and harga < ma20:
                sinyal = "⚠️ *Bearish* (Di bawah MA20)"
            else:
                sinyal = "⚪ *Neutral*"
                
            pesan_final += f"📈 *{ticker}*\n"
            pesan_final += f"💰 Harga: Rp{harga:,.0f}\n"
            pesan_final += f"📊 Status: {sinyal}\n\n"
        
        kirim_telegram(pesan_final)
    except Exception as e:
        print(f"Error saat membaca database: {e}")

if __name__ == "__main__":
    cek_sinyal_dan_notifikasi()
