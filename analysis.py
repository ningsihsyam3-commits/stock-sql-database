import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime

# Pastikan nama database sama dengan yang ada di file .yml
engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    try:
        # 1. Ambil data tanpa menentukan index dulu agar kita bisa cek kolomnya
        full_df = pd.read_sql('SELECT * FROM history_saham', engine)
        print(f"DEBUG Kolom yang ada: {full_df.columns.tolist()}")
        
        # 2. Standarisasi Kolom Tanggal (Mencari 'Date' atau 'date')
        date_col = next((c for c in full_df.columns if c.lower() == 'date'), None)
        if date_col:
            full_df[date_col] = pd.to_datetime(full_df[date_col])
            full_df.set_index(date_col, inplace=True)
            full_df.index.name = 'Date'
        else:
            print("⚠️ Kolom tanggal tidak ditemukan, mencoba menggunakan index bawaan.")
        
        print("✅ Data history_saham berhasil dimuat.")
    except Exception as e:
        print(f"❌ Gagal memuat data awal: {e}")
        return

    for symbol in assets:
        try:
            # 3. Filter data berdasarkan simbol
            df = full_df[full_df['Symbol'] == symbol].copy()
            
            if df.empty:
                print(f"⚠️ Data untuk {symbol} tidak ditemukan.")
                continue

            # 4. Analisis Teknis (MA5, MA20, RSI)
            if 'Close' not in df.columns and 'Adj Close' in df.columns:
                df['Close'] = df['Adj Close']

            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # 5. Deteksi Anomali
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)

            # 6. Simpan ke tabel individual (BBRI_JK, dll)
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Tabel {table_name} Berhasil diperbarui.")

        except Exception as e:
            print(f"❌ Error pada {symbol}: {e}")

if __name__ == "__main__":
    assets = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
    run_specialist_analysis(assets)
