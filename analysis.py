import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine

engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    try:
        # VERIFIKASI: Membaca dari 'history_saham' di bagian paling atas
        full_df = pd.read_sql('SELECT * FROM history_saham', engine)
        
        # Pembersihan dan Mapping (Logika Anda)
        full_df.columns = full_df.columns.str.strip()
        cols_to_drop = ['ma5', 'ma20', 'rsi', 'MA5', 'MA20', 'RSI', 'MA50']
        full_df = full_df.drop(columns=[c for c in cols_to_drop if c in full_df.columns])
        
        full_df = full_df.rename(columns={
            'date': 'Date',
            'ticker': 'Symbol',
            'close_price': 'Close'
        })
        
        full_df['Symbol'] = full_df['Symbol'].astype(str).str.strip().str.upper()
        full_df['Date'] = pd.to_datetime(full_df['Date'])
        full_df.set_index('Date', inplace=True)
        print("✅ Data history_saham dimuat. Memulai analisis teknikal...")
    except Exception as e:
        print(f"❌ Gagal memuat data awal: {e}")
        return

    for symbol in assets:
        try:
            target = symbol.upper().strip()
            # Logika Pencarian Fleksibel
            df = full_df[full_df['Symbol'] == target].copy()
            if df.empty:
                base = target.split('.')[0].split('-')[0]
                df = full_df[full_df['Symbol'].str.contains(base, na=False)].copy()

            if df.empty:
                continue

            # --- ANALISIS (LAMA + PREDIKSI BARU) ---
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['MA50'] = ta.sma(df['Close'], length=50) # Prediksi Baru
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)
            
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # PREDIKSI TREND BARU
            df['Trend_Signal'] = np.where(df['MA20'] > df['MA50'], 'Bullish', 'Bearish')

            # Simpan ke tabel individual
            table_name = symbol.replace('.', '_').replace('-', '_').replace('^', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Update sukses: {table_name}")

        except Exception as e:
            print(f"❌ Error pada {symbol}: {e}")

    # Analisis Korelasi (Logika Anda)
    try:
        df_bbri = pd.read_sql('SELECT Close FROM BBRI_JK', engine)
        df_bmri = pd.read_sql('SELECT Close FROM BMRI_JK', engine)
        correlation_value = df_bbri['Close'].corr(df_bmri['Close'])
        corr_df = pd.DataFrame({'Pair': ['BBRI vs BMRI'], 'Value': [correlation_value]})
        corr_df.to_sql('market_correlation', engine, if_exists='replace', index=False)
        print("✅ Tabel market_correlation diperbarui.")
    except:
        pass

if __name__ == "__main__":
    # DAFTAR ASET (Verifikasi: Sama dengan download.py)
    all_assets = ['BBRI.JK', 'TLKM.JK', 'BMRI.JK', 'ASII.JK', 'ICBP.JK', 'ADRO.JK', 'BTC-USD', '^JKSE']
    run_specialist_analysis(all_assets)
