import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime

# Gunakan nama database yang konsisten
engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    all_dfs = {}
    
    try:
        # Membaca gudang data utama
        full_df = pd.read_sql('SELECT * FROM history_saham', engine, index_col='Date', parse_dates=True)
        print("✅ Berhasil memuat data dari tabel: history_saham")
    except Exception as e:
        print(f"❌ Tabel 'history_saham' tidak ditemukan: {e}")
        return

    for symbol in assets:
        try:
            # Filter data untuk simbol spesifik (misal: BBRI.JK)
            df = full_df[full_df['Symbol'] == symbol].copy()
            
            if df.empty:
                print(f"⚠️ Data untuk {symbol} tidak ditemukan di history_saham, skip...")
                continue
            
            # --- ANALISIS TEKNIKAL ---
            # Pastikan kolom Close tersedia
            if 'Close' not in df.columns and 'Adj Close' in df.columns:
                df['Close'] = df['Adj Close']

            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # Z-Score Anomali
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)

            # Backtesting sederhana
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # --- PENYIMPANAN ---
            # Simpan ke tabel terpisah agar app.py bisa membacanya (misal: BBRI_JK)
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            all_dfs[symbol] = df
            print(f"✅ Analisis {symbol} selesai dan disimpan ke tabel {table_name}")
            
        except Exception as e:
            print(f"❌ Error saat memproses {symbol}: {e}")

if __name__ == "__main__":
    # Daftar aset sesuai yang ada di history_saham
    assets_to_analyze = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
    run_specialist_analysis(assets_to_analyze)
