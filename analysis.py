import pandas as pd
import pandas_ta as ta
from sqlalchemy import create_engine

def hitung_indikator():
    engine = create_engine('sqlite:///database_investasi.db')
    
    try:
        # 1. Ambil data mentah dari database
        df = pd.read_sql("SELECT * FROM history_saham ORDER BY ticker, date ASC", engine)
        
        if df.empty:
            print("Database kosong, tidak ada yang bisa dianalisis.")
            return

        df_hasil = pd.DataFrame()

        # 2. Hitung indikator per ticker
        for ticker in df['ticker'].unique():
            dft = df[df['ticker'] == ticker].copy()
            
            # --- Indikator Harga ---
            dft['ma5'] = ta.sma(dft['close_price'], length=5)
            dft['ma20'] = ta.sma(dft['close_price'], length=20)
            dft['rsi'] = ta.rsi(dft['close_price'], length=14)
            
            # --- Indikator Volume (Baru!) ---
            # Menghitung rata-rata volume 10 hari untuk melihat lonjakan
            dft['vol_ma10'] = ta.sma(dft['volume'], length=10)
            
            df_hasil = pd.concat([df_hasil, dft])

        # 3. Simpan kembali ke database (replace tabel lama dengan data yang sudah ada indikatornya)
        df_hasil.to_sql('history_saham', engine, if_exists='replace', index=False)
        print("Analisis selesai: Indikator Harga & Volume berhasil diperbarui.")

    except Exception as e:
        print(f"Error saat menjalankan analisis: {e}")

if __name__ == "__main__":
    hitung_indikator()
