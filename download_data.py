import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

def download_stock_data():
    tickers = ["BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK"]
    engine = create_engine('sqlite:///database_investasi.db')
    
    # Ambil 3 bulan agar indikator di analys.py akurat
    data = yf.download(tickers, period="3mo", group_by='ticker')
    
    df_list = []
    for t in tickers:
        if t in data:
            df_ticker = data[t].copy().reset_index()
            df_ticker['ticker'] = t
            # Normalisasi nama kolom (Close -> close_price, Volume -> volume)
            df_ticker = df_ticker.rename(columns={'Date': 'date', 'Close': 'close_price', 'Volume': 'volume'})
            df_list.append(df_ticker[['date', 'ticker', 'close_price', 'volume']])

    df_final = pd.concat(df_list)
    # Gunakan 'replace' untuk data mentah, nanti analys.py yang akan menghitung ulang indikatornya
    df_final.to_sql('history_saham', engine, if_exists='replace', index=False)
    print("Data mentah (Harga & Volume) berhasil diperbarui.")

if __name__ == "__main__":
    download_stock_data()
