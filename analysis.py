import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy import inspect # Tambahkan ini di bagian import paling atas  
    
        
# Pastikan nama database sama dengan yang ada di file .yml
engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    all_dfs = {}
    
    try:
        # Mengambil SEMUA data dari tabel history_saham
        full_df = pd.read_sql('SELECT * FROM history_saham', engine, index_col='Date', parse_dates=True)
        print("✅ Berhasil memuat tabel history_saham")
    except Exception as e:
        print(f"❌ Gagal memuat tabel history_saham: {e}")
        return

    for symbol in assets:
        try:
            # Filter data berdasarkan symbol (misal: BBRI.JK)
            df = full_df[full_df['Symbol'] == symbol].copy()
            
            if df.empty:
                print(f"⚠️ Data untuk {symbol} tidak ditemukan di history_saham")
                continue
            
            # --- ANALISIS TEKNIKAL ---
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # Z-Score Anomali
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)

            # Backtesting
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # Simpan kembali ke database sebagai tabel TERPISAH (agar app.py mudah membaca)
            table_name = symbol.replace('.', '_').replace('-', '_')
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            print(f"✅ Berhasil memproses dan menyimpan tabel: {table_name}")
            
        except Exception as e:
            print(f"❌ Error pada analisis {symbol}: {e}")

    # 7. Analisis Korelasi (Setelah semua loop selesai)
    if 'BTC-USD' in all_dfs and 'BBRI.JK' in all_dfs:
        try:
            corr_val = all_dfs['BTC-USD']['Close'].corr(all_dfs['BBRI.JK']['Close'])
            corr_df = pd.DataFrame({'Date': [datetime.now()], 'Pair': ['BTC_BBRI'], 'Value': [corr_val]})
            corr_df.to_sql('market_correlation', engine, if_exists='replace', index=False)
            print(f"🔗 Korelasi BTC vs BBRI diperbarui: {corr_val:.2f}")
        except Exception as e:
            print(f"❌ Gagal menghitung korelasi: {e}")

if __name__ == "__main__":
    assets_to_analyze = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
    run_specialist_analysis(assets_to_analyze)
