import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime

# Pastikan nama database sama dengan yang ada di file .yml
engine = create_engine('sqlite:///database_investasi.db')

def run_specialist_analysis(assets):
    all_dfs = {}
    for symbol in assets:
        table_name = symbol.replace('.', '_').replace('-', '_')
        
        try:
            # 1. Ambil data dari database
            with engine.connect() as conn:
                df = pd.read_sql(table_name, conn, index_col='Date', parse_dates=True)
            
            if df.empty:
                continue

            # 2. Perbaikan Kolom (Proteksi MultiIndex yfinance)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if 'Close' not in df.columns and 'Adj Close' in df.columns:
                df['Close'] = df['Adj Close']
                
            if 'Close' not in df.columns:
                print(f"Warning: Kolom Close tidak ditemukan untuk {symbol}")
                continue

            # 3. Analisis Teknis (MA5 & MA20)
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # 4. Deteksi Anomali (Z-Score)
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)

            # 5. Backtesting (Strategy Return)
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # 6. Simpan kembali ke database
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            all_dfs[symbol] = df
            print(f"✅ Analisis untuk {symbol} berhasil.")

        except Exception as e:
            print(f"❌ Error pada {symbol}: {e}")

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
