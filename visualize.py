import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Koneksi ke database
engine = create_engine('sqlite:///database_investasi.db')

def buat_grafik():
    # 1. Ambil data
    df = pd.read_sql("SELECT * FROM history_saham ORDER BY date ASC", engine)
    
    if df.empty:
        print("Data kosong, tidak bisa membuat grafik.")
        return

    # 2. Pengaturan Grafis
    plt.figure(figsize=(10, 6))
    
    # 3. Loop untuk setiap kode saham (ticker)
    for ticker in df['ticker'].unique():
        data_saham = df[df['ticker'] == ticker]
        plt.plot(data_saham['date'], data_saham['close_price'], marker='o', label=ticker)

    # 4. Mempercantik Tampilan
    plt.title('Tren Harga Penutupan Saham', fontsize=14)
    plt.xlabel('Tanggal', fontsize=12)
    plt.ylabel('Harga (IDR)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 5. Simpan sebagai gambar
    plt.savefig('tren_saham.png')
    print("Grafik berhasil disimpan sebagai 'tren_saham.png'")

if __name__ == "__main__":
    buat_grafik()
