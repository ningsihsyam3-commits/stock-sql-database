import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

# Pastikan nama file database sama
engine = create_engine('sqlite:///database_investasi.db')

# DAFTAR ASET (Sama persis dengan analysis.py)
assets = ['BBRI.JK', 'TLKM.JK', 'BMRI.JK', 'ASII.JK', 'ICBP.JK', 'ADRO.JK', 'BTC-USD', '^JKSE']

def run_downloader():
    all_data = []
    for ticker in assets:
        try:
            print(f"📥 Mengunduh {ticker}...")
            # Ambil data 2 tahun agar indikator MA50 di analysis.py valid
            df = yf.download(ticker, period='2y')
            
            if not df.empty:
                df = df.reset_index()
                # Standarisasi kolom untuk mempermudah analysis.py
                df['ticker'] = ticker
                df = df.rename(columns={
                    'Date': 'date',
                    'Close': 'close_price'
                })
                # Hanya simpan kolom minimal yang dibutuhkan
                all_data.append(df[['date', 'ticker', 'close_price']])
                print(f"✅ {ticker} berhasil diambil.")
        except Exception as e:
            print(f"❌ Gagal mengunduh {ticker}: {e}")
    
    if all_data:
        final_df = pd.concat(all_data)
        # VERIFIKASI: Tabel tujuan bernama 'history_saham'
        final_df.to_sql('history_saham', engine, if_exists='replace', index=False)
        print("\n✨ history_saham berhasil diperbarui.")

if __name__ == "__main__":
    run_downloader()
