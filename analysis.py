import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine
import os

# Nama database harus konsisten dengan download_data.py
DB_NAME = 'database_investasi.db'
engine = create_engine(f'sqlite:///{DB_NAME}')

def run_specialist_analysis(assets):
    try:
        # 1. Ambil data dari gudang utama (history_saham)
        full_df = pd.read_sql('SELECT * FROM history_saham', engine)
        # Pastikan kolom Date menjadi index
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        full_df.set_index('Date', inplace=True)
        print("✅ Berhasil memuat data dari tabel: history_saham")
    except Exception as e:
        print(f"❌ Gagal membaca history_saham: {e}")
        return

    for symbol in assets:
        try:
            # 2. Filter data untuk masing-masing aset
            df = full_df[full_df['Symbol'] == symbol].copy()
            
            if df.empty:
                print(f"⚠️ Data untuk {symbol} tidak ditemukan di history_saham, skip...")
                continue
            
            # 3. Analisis Teknikal (Proteksi kolom Close)
            if 'Close' not in df.columns and 'Adj Close' in df.columns:
                df['Close'] = df['Adj Close']

            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # Deteksi Anomali
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)

            # Strategy Backtesting
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # 4. Simpan ke tabel individual (untuk dibaca app.py)
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Berhasil memproses {symbol} ke tabel {table_name}")
            
        except Exception as e:
            print(f"❌ Error pada analisis {symbol}: {e}")

if __name__ == "__main__":
    # Sesuaikan daftar ini dengan apa yang ada di history_saham
    assets_to_analyze = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
    run_specialist_analysis(assets_to_analyze)
