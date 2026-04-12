# 📈 Automated Stock Data Pipeline

Proyek ini adalah sistem otomatisasi data pipeline end-to-end yang dirancang untuk mengumpulkan, menyimpan, menganalisis, dan memvisualisasikan data pasar saham secara otomatis.

## 🚀 Alur Kerja Sistem (SOP)

Sistem ini terdiri dari 4 komponen utama yang bekerja secara sinkron:

1. **Data Ingestion (`download_data.py`)**: Mengambil data historis dari Yahoo Finance API dan menyimpannya ke database SQL (SQLite) menggunakan SQLAlchemy. Sistem dilengkapi logika pencegahan duplikasi data.
2. **Data Intelligence (`analysis.py`)**: Melakukan perhitungan teknis seperti *Daily Percentage Change* dan *Moving Average* (MA-3) untuk memantau performa tren.
3. **Data Visualization (`visualize.py`)**: Mengubah data mentah menjadi grafik tren harga penutupan (`tren_saham.png`) menggunakan Matplotlib.
4. **Cloud Automation (GitHub Actions)**: Robot yang menjalankan seluruh skrip di atas secara terjadwal atau manual melalui server GitHub.

## 🛠 Cara Menjalankan Pipeline
Untuk memperbarui data dan melihat analisis terbaru:
1. Klik tab **Actions** di bagian atas repositori ini.
2. Pilih workflow **Manual Historical Download**.
3. Klik tombol **Run workflow**.
4. Setelah selesai (centang hijau), hasil analisis dapat dilihat pada log "Run Analysis" dan grafik akan otomatis diperbarui di halaman utama.

## 📊 Visualisasi Tren Terbaru
![Tren Saham](./tren_saham.png)

---
*Dikembangkan untuk keperluan analisis data investasi dan otomatisasi laporan keuangan.*
