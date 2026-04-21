import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime

engine = create_engine('sqlite:///data_investasi.db')

def run_specialist_analysis(assets):
    all_dfs = {}
    with engine.connect() as conn:
        for symbol in assets:
            table_name = symbol.replace('.', '_').replace('-', '_')
            # Ambil seluruh data historis untuk analisis yang akurat
            df = pd.read_sql(table_name, conn, index_col='Date', parse_dates=True)
            
            # --- ANALISIS TEKNIS (MA5 & MA20) ---
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # --- DETEKSI ANOMALI (Z-Score berbasis MA20) ---
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
            df['Is_Anomaly'] = df['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)

            # --- BACKTESTING (Strategy Return) ---
            df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
            df['Daily_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
            df['Cumulative_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

            # --- SIMPAN KEMBALI HASIL ANALISIS (Replace table dengan kolom baru) ---
            df.to_sql(table_name, engine, if_exists='replace', index=True)
            all_dfs[symbol] = df
            print(f"Analisis Specialist untuk {symbol} telah diperbarui.")

        # --- ANALISIS KORELASI MULTI-ASET ---
        if 'BTC-USD' in all_dfs and 'BBRI.JK' in all_dfs:
            corr_val = all_dfs['BTC-USD']['Close'].corr(all_dfs['BBRI.JK']['Close'])
            corr_df = pd.DataFrame({'Date': [datetime.now()], 'Pair': ['BTC_BBRI'], 'Value': [corr_val]})
            corr_df.to_sql('market_correlation', engine, if_exists='replace', index=False)
            print(f"Korelasi BTC vs BBRI diperbarui: {corr_val:.2f}")

assets = ['BBRI.JK', 'CTRA.JK', 'TLKM.JK', 'ASII.JK', 'BTC-USD']
run_specialist_analysis(assets)
