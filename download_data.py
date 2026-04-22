import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine

# Konfigurasi database
engine = create_engine('sqlite:///data_investasi.db')

def download_incremental(assets):
    for symbol in assets:
        table_name = symbol.replace('.', '_').replace('-', '_')
        
        # 1. Cek Tanggal Terakhir menggunakan SQLAlchemy engine
        try:
            with engine.connect() as conn:
                last_date = pd.read_sql(f"SELECT MAX(Date) FROM {table_name}", conn).iloc[0, 0]
        except Exception:
            last_date = None

        # 2. Download Data
        start_date = (pd.to_datetime(last_date) + pd.Timedelta(days=1)) if last_date else None
        df_new = yf.download(symbol, start=start_date, period="1y" if not last_date else None)
        
        if not df_new.empty:
            # 3. Simpan dengan mode APPEND
            df_new.to_sql(table_name, engine, if_exists='append', index=True)
            print(f"Data mentah {symbol} berhasil ditambahkan ke database.")

# Pastikan daftar ini sama di semua file .py Anda
assets = [
    'BBRI.JK', 'TLKM.JK', 'BMRI.JK', 'ASII.JK', 'BBNI.JK',
    'ICBP.JK', 'ADRO.JK', 'BTC-USD', '^JKSE'
]download_incremental(assets)
