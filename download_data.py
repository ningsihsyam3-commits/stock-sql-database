import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# --- KONFIGURASI DATABASE ---
# SQLite akan menyimpan data dalam satu file biner di repositori Anda
DB_NAME = "database_investasi.db"
engine = create_engine(f'sqlite:///{DB_NAME}')
Base = declarative_base()

# --- DEFINISI TABEL (MODEL) ---
class HargaSaham(Base):
    __tablename__ = 'history_saham'
    # Primary Key gabungan: Tidak boleh ada Ticker yang sama di Tanggal yang sama
    date = Column(Date, primary_key=True)
    ticker = Column(String, primary_key=True)
    close_price = Column(Float)

# Membuat tabel di dalam file .db jika belum ada
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- PROSES PENGAMBILAN DATA ---
tickers = ["BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK"]
print(f"Sedang menarik data terbaru untuk: {tickers}...")

# Ambil data 7 hari terakhir untuk sinkronisasi (mencegah data bolong di hari libur)
data = yf.download(tickers, period="7d", group_by='ticker')

count = 0
for t in tickers:
    if t in data:
        # Merapikan format data dari yfinance
        df_ticker = data[t].copy().reset_index()
        for index, row in df_ticker.iterrows():
            tgl = row['Date'].date()
            
            # Logika SQLAlchemy: Cek apakah data sudah ada sebelum insert
            exists = session.query(HargaSaham).filter_by(date=tgl, ticker=t).first()
            
            if not exists:
                entry = HargaSaham(
                    date=tgl,
                    ticker=t,
                    close_price=float(row['Close'])
                )
                session.add(entry)
                count += 1

# Simpan semua perubahan ke file .db
session.commit()
session.close()

print(f"Sukses! {count} baris data baru ditambahkan ke {DB_NAME}")
