import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# --- KONFIGURASI DATABASE ---
DB_NAME = "database_investasi.db"
engine = create_engine(f'sqlite:///{DB_NAME}')
Base = declarative_base()

# --- DEFINISI TABEL (MODEL) ---
# Di sini kita tambahkan kolom ma5 dan ma20
class HargaSaham(Base):
    __tablename__ = 'history_saham'
    date = Column(Date, primary_key=True) 
    ticker = Column(String, primary_key=True)
    close_price = Column(Float)
    ma5 = Column(Float)   # Kolom baru
    ma20 = Column(Float)  # Kolom baru
    # Di dalam class HargaSaham(Base):
    rsi = Column(Float, nullable=True)

# Membuat tabel atau memperbarui struktur jika belum ada
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def download_stock_data():
    tickers = ["BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK"]
    print(f"Sedang menarik data terbaru untuk: {tickers}...")

    # Ambil data 30 hari terakhir agar perhitungan MA20 akurat
    data = yf.download(tickers, period="30d", group_by='ticker')

    count = 0
    for t in tickers:
        if t in data:
            df_ticker = data[t].copy().reset_index()
            
            # --- HITUNG MA DI SINI SEBELUM SIMPAN ---
            # Kita hitung di sini agar data yang masuk ke database sudah lengkap
            df_ticker['MA5'] = df_ticker['Close'].rolling(window=5).mean()
            df_ticker['MA20'] = df_ticker['Close'].rolling(window=20).mean()
            
            for index, row in df_ticker.iterrows():
                tgl = row['Date'].date()
                
                # Cek apakah data sudah ada
                exists = session.query(HargaSaham).filter_by(date=tgl, ticker=t).first()
                
                if not exists:
                    # Buat entri baru dengan nilai MA
                    entry = HargaSaham(
                        date=tgl,
                        ticker=t,
                        close_price=float(row['Close']),
                        ma5=float(row['MA5']) if pd.notnull(row['MA5']) else None,
                        ma20=float(row['MA20']) if pd.notnull(row['MA20']) else None
                    )
                    session.add(entry)
                    count += 1

    session.commit()
    print(f"Sukses! {count} baris data baru ditambahkan.")
    
    # PENTING: Ambil data terbaru dari database agar kolom MA5 dan MA20 ikut terbawa
    df_result = pd.read_sql("SELECT * FROM history_saham", engine)
    return df_result

if __name__ == "__main__":
    download_stock_data()
    session.close()
