import pandas as pd
from sqlalchemy import create_engine

# Koneksi ke database
DB_NAME = "database_investasi.db"
engine = create_engine(f'sqlite:///{DB_NAME}')

print("--- MEMBACA DATABASE SQL ---")

try:
    # Query untuk mengambil data
    query = "SELECT * FROM history_saham ORDER BY date DESC, ticker ASC LIMIT 10"
    
    # Tambahkan index_col=None atau reset_index untuk memastikan Tanggal muncul
    df = pd.read_sql(query, engine)
    
    if df.empty:
        print("Database kosong.")
    else:
        print("\nDATA TERBARU:")
        print("-" * 40)
        # Menampilkan tabel dengan format yang lebih lengkap
        print(df.to_string(index=True)) 
        print("-" * 40)
        
except Exception as e:
    print(f"Error: {e}")
