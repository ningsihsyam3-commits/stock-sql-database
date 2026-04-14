from download_data import download_stock_data
from visualize import buat_grafik_tren

def main():
    print("--- Memulai Pipeline Otomasi ---")
    
    # 1. Jalankan Download & Hitung MA (Outputnya DataFrame)
    df_matang = download_stock_data()
    
    # 2. Jalankan Visualisasi
    if df_matang is not None:
        buat_grafik_tren(df_matang)
        print("--- Pipeline Sukses! ---")

if __name__ == "__main__":
    main()
