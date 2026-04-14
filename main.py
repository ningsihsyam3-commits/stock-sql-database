from analys import get_analyzed_data
from visualize import buat_grafik_tren

def main():
    print("--- Memulai Pipeline Otomasi Data Saham ---")
    
    # Langkah 1 & 2: Ambil data dan hitung di analys.py
    data_matang = get_analyzed_data()
    
    # Langkah 3: Visualisasikan di visualize.py
    if data_matang is not None:
        buat_grafik_tren(data_matang)
        print("--- Pipeline Selesai Sukses ---")
    else:
        print("Pipeline gagal karena tidak ada data.")

if __name__ == "__main__":
    main()
