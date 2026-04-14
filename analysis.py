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


def calculate_moving_averages(df):
    """
    Fungsi untuk menghitung Moving Average 5 dan 20 hari.
    Input: DataFrame dengan kolom 'Simbol', 'Tanggal', 'Close'
    Output: DataFrame yang sudah ditambah kolom MA5 dan MA20
    """
    # Pastikan data terurut berdasarkan tanggal
    df = df.sort_values(by=['Simbol', 'Tanggal'])
    
    # Menghitung MA per simbol agar tidak bercampur
    df['MA5'] = df.groupby('Simbol')['Close'].transform(lambda x: x.rolling(window=5).mean())
    df['MA20'] = df.groupby('Simbol')['Close'].transform(lambda x: x.rolling(window=20).mean())
    
    return df
