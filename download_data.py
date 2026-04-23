import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///database_investasi.db')
assets = ['BBRI.JK', 'TLKM.JK', 'BMRI.JK', 'ASII.JK', 'ICBP.JK', 'ADRO.JK', 'BTC-USD', '^JKSE']

def run_downloader():
    all_data = []
    for ticker in assets:
        try:
            print(f"📥 Mengunduh {ticker}...")
            df = yf.download(ticker, period='2y')
            if not df.empty:
                df = df.reset_index() # Menarik 'Date' dari index ke kolom
                
                # PAKSA: Ambil hanya 2 kolom pertama (Tanggal & Close) apapun namanya
                # Biasanya kolom 0 adalah Date, kolom 4 atau terakhir adalah Close
                temp_df = pd.DataFrame()
                temp_df['date'] = df.iloc[:, 0]  # Kolom pertama pasti tanggal
                temp_df['close'] = df.iloc[:, 4] # Kolom kelima biasanya Close
                temp_df['ticker'] = ticker
                
                all_data.append(temp_df)
        except Exception as e:
            print(f"Gagal di {ticker}: {e}")
    
    if all_data:
        final_df = pd.concat(all_data)
        # Simpan tanpa index agar bersih
        final_df.to_sql('history_saham', engine, if_exists='replace', index=False)
        print("✅ download.py: history_saham siap dengan kolom 'date'.")

if __name__ == "__main__":
    run_downloader()
