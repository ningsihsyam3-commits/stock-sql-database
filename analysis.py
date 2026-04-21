import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine

# Pastikan nama database sinkron
engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    try:
        # 1. Ambil data dari tabel utama
        full_df = pd.read_sql('SELECT * FROM history_saham', engine)
        
        # Bersihkan nama kolom dari spasi dan duplikasi lama
        full_df.columns = full_df.columns.str.strip()
        cols_to_drop = ['ma5', 'ma20', 'rsi', 'MA5', 'MA20', 'RSI']
        full_df = full_df.drop(columns=[c for c in cols_to_drop if c in full_df.columns])
        
        # Mapping kolom sesuai data Anda
        full_df = full_df.rename(columns={
            'date': 'Date',
            'ticker': 'Symbol',
            'close_price': 'Close'
        })
        
        # Bersihkan isi kolom Symbol (Ticker) dari spasi atau karakter aneh
        full_df['Symbol'] = full_df['Symbol'].astype(str).str.strip().str.upper()
        
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        full_df.set_index('Date', inplace=True)
        print("✅ Data history_saham dimuat. Memulai pencarian fleksibel...")
    except Exception as e:
        print(f"❌ Gagal memuat data awal: {e}")
        return

    for symbol in assets:
        try:
            target = symbol.upper().strip()
            # Coba cari yang sama persis (misal: BBRI.JK)
            df = full_df[full_df['Symbol'] == target].copy()
            
            # Jika tidak ketemu, cari yang mengandung kata kuncinya (misal: CTRA)
            if df.empty:
                base = target.split('.')[0].split('-')[0]
                df = full_df[full_df['Symbol'].str.contains(base, na=False)].copy()

            if df.empty:
                print(f"⚠️ {symbol} tetap tidak ditemukan. Simbol yang ada di database: {full_df['Symbol'].unique()[:5]}")
                continue

            # --- ANALISIS TEKNIKAL ---
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # Z-Score & Strategy
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # Simpan ke tabel individual
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Berhasil membuat tabel: {table_name}")

        except Exception as e:
            print(f"❌ Error pada {symbol}: {e}")

    # --- Tambahkan di bagian akhir analysis.py ---

# Menghitung korelasi sederhana antara dua aset (contoh: BBRI dan BBNI)
# Anda bisa menggantinya dengan aset lain yang tersedia di database Anda
    try:
        df_bbri = pd.read_sql('SELECT Close FROM BBRI_JK', engine)
        df_bbni = pd.read_sql('SELECT Close FROM BBNI_JK', engine)
    
    # Pastikan jumlah baris sama sebelum menghitung korelasi
        correlation_value = df_bbri['Close'].corr(df_bbni['Close'])
    
    # Simpan ke tabel baru bernama market_correlation
        corr_df = pd.DataFrame({'Pair': ['BBRI vs BBNI'], 'Value': [correlation_value]})
        corr_df.to_sql('market_correlation', engine, if_exists='replace', index=False)
        print("✅ Tabel market_correlation berhasil dibuat.")
    except Exception as e:
        print(f"❌ Gagal membuat korelasi: {e}")

if __name__ == "__main__":
    # Ganti daftar di bawah ini agar SAMA PERSIS dengan isi database Anda
    assets = ['ASII.JK', 'BBNI.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK']
    run_specialist_analysis(assets)
