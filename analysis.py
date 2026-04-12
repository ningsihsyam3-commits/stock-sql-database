import pandas as pd
from sqlalchemy import create_engine

# Koneksi ke database
engine = create_engine('sqlite:///database_investasi.db')

def hitung_performa():
    # 1. Ambil semua data dari database
    df = pd.read_sql("SELECT * FROM history_saham ORDER BY ticker, date", engine)
    
    if df.empty:
        print("Data tidak ditemukan.")
        return

    # 2. Hitung Performa per Ticker
    # Menghitung selisih harga dengan hari sebelumnya (dalam persen)
    df['pct_change'] = df.groupby('ticker')['close_price'].pct_change() * 100
    
    # Menghitung Rata-rata Harga (Moving Average 3 hari terakhir)
    df['ma_3day'] = df.groupby('ticker')['close_price'].transform(lambda x: x.rolling(window=3).mean())

    print("--- ANALISIS PERFORMA SAHAM ---")
    # Ambil data terbaru untuk setiap saham
    latest_perf = df.groupby('ticker').tail(1)
    
    output = latest_perf[['date', 'ticker', 'close_price', 'pct_change', 'ma_3day']]
    print(output.to_string(index=False))

if __name__ == "__main__":
    hitung_performa()
