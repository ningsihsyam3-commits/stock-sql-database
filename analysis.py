import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine
import os

# Gunakan database_investasi.db jika itu yang Anda gunakan di downloader
engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    try:
        # 1. Ambil data dari gudang utama
        full_df = pd.read_sql('SELECT * FROM history_saham', engine)
        
        # Mapping nama kolom sesuai DEBUG Anda: ['date', 'ticker', 'close_price', ...]
        # Kita ubah ke nama standar agar perhitungan library ta lancar
        full_df = full_df.rename(columns={
            'date': 'Date',
            'ticker': 'Symbol',
            'close_price': 'Close'
        })
        
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        full_df.set_index('Date', inplace=True)
        print("✅ Data history_saham berhasil dimuat dan kolom disesuaikan.")
    except Exception as e:
        print(f"❌ Gagal memuat data awal: {e}")
        return

    for symbol in assets:
        try:
            # 2. Filter berdasarkan kolom 'Symbol' (yang tadi sudah di-rename dari 'ticker')
            df = full_df[full_df['Symbol'] == symbol].copy()
            
            if df.empty:
                print(f"⚠️ Data untuk {symbol} tidak ditemukan di kolom ticker.")
                continue

            # 3. Analisis Teknis
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # Z-Score (Anomali)
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)

            # Strategy
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # 4. Simpan ke tabel individual untuk Dashboard (BBRI_JK, dll)
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Berhasil membuat tabel {table_name} untuk dashboard.")

        except Exception as e:
            print(f"❌ Error pada {symbol}: {e}")

if __name__ == "__main__":
    # Daftar aset sesuai ticker di yfinance
    assets = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
    run_specialist_analysis(assets)
