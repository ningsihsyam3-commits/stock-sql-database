import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine, inspect
import os

# Nama database harus sinkron
DB_NAME = 'database_investasi.db'
engine = create_engine(f'sqlite:///{DB_NAME}')

def run_specialist_analysis(assets):
    # 1. Cek isi gudang data
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"DEBUG: Tabel yang tersedia di awal: {tables}")

    if 'history_saham' not in tables:
        print("❌ ERROR: Tabel 'history_saham' tidak ditemukan. Downloader gagal atau nama database salah.")
        return

    try:
        # 2. Ambil semua data dari gudang utama
        full_df = pd.read_sql('SELECT * FROM history_saham', engine)
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        full_df.set_index('Date', inplace=True)
        print("✅ Data history_saham berhasil dimuat.")
    except Exception as e:
        print(f"❌ Gagal memproses data: {e}")
        return

    for symbol in assets:
        try:
            # 3. Filter data per simbol
            df = full_df[full_df['Symbol'] == symbol].copy()
            
            if df.empty:
                print(f"⚠️ Simbol {symbol} tidak ada di history_saham.")
                continue

            # 4. Hitung Indikator Teknikal
            if 'Close' not in df.columns and 'Adj Close' in df.columns:
                df['Close'] = df['Adj Close']

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

            # 5. Simpan ke tabel individual (BBRI_JK, dll) agar app.py senang
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Tabel {table_name} berhasil dibuat.")

        except Exception as e:
            print(f"❌ Gagal menganalisis {symbol}: {e}")

if __name__ == "__main__":
    assets = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
    run_specialist_analysis(assets)
