import pandas as pd
from sqlalchemy import create_engine

# Koneksi ke database yang sudah ada
DB_NAME = "database_investasi.db"
engine = create_engine(f'sqlite:///{DB_NAME}')

# Query sederhana menggunakan Pandas
try:
    # Mengambil 10 data terbaru berdasarkan tanggal
    query = "SELECT * FROM history_saham ORDER BY date DESC, ticker ASC LIMIT 10"
    df = pd.read_sql(query, engine)
    
    print("--- 10 DATA TERAKHIR DI DATABASE ---")
    if df.empty:
        print("Database masih kosong.")
    else:
        print(df.to_string(index=False))
except Exception as e:
    print(f"Terjadi kesalahan saat membaca database: {e}")
