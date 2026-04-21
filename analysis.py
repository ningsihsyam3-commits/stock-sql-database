import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine

# Pastikan nama database sesuai dengan yang ada di log Anda
engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    try:
        # 1. Ambil data dari tabel utama
        full_df = pd.read_sql('SELECT * FROM history_saham', engine)
        
        # 2. Sinkronisasi nama kolom agar standar dan tidak duplikat
        # Kita hapus kolom ma5, ma20, rsi bawaan agar tidak bentrok saat kita hitung ulang
        cols_to_drop = ['ma5', 'ma20', 'rsi', 'vol_ma10']
        full_df = full_df.drop(columns=[c for c in cols_to_drop if c in full_df.columns])
        
        full_df = full_df.rename(columns={
            'date': 'Date',
            'ticker': 'Symbol',
            'close_price': 'Close'
        })
        
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        full_df.set_index('Date', inplace=True)
        print("✅ Data dimuat. Kolom lama dibersihkan untuk menghindari duplikasi.")
    except Exception as e:
        print(f"❌ Gagal memuat data: {e}")
        return

    for symbol in assets:
        try:
            # Pencarian lebih fleksibel (tidak peduli huruf besar/kecil)
            df = full_df[full_df['Symbol'].str.upper() == symbol.upper()].copy()
            
            # Jika masih kosong, coba cari tanpa akhiran .JK atau -USD
            if df.empty:
                base_symbol = symbol.split('.')[0].split('-')[0]
                df = full_df[full_df['Symbol'].str.contains(base_symbol, case=False, na=False)].copy()

            if df.empty:
                print(f"⚠️ Data untuk {symbol} benar-benar tidak ditemukan di database.")
                continue

            # 4. Hitung Indikator (Menggunakan nama kapital agar seragam di Dashboard)
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

            # 5. Simpan ke tabel individual (BBRI_JK, dll)
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Tabel {table_name} berhasil dibuat.")

        except Exception as e:
            print(f"❌ Error pada {symbol}: {e}")

if __name__ == "__main__":
    # Daftar aset sesuai ticker yang Anda gunakan
    assets_to_analyze = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
    run_specialist_analysis(assets_to_analyze)
