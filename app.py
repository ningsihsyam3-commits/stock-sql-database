import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect

# --- BAGIAN 1: KONFIGURASI DATABASE ---
engine = create_engine('sqlite:///database_investasi.db')
inspector = inspect(engine)

# --- BAGIAN 2: LOGIKA DINAMIS SIDEBAR ---
st.sidebar.header("📊 Asset Selection")

# Mengambil semua nama tabel yang ada di database secara otomatis
# Kita filter agar tabel sistem seperti 'market_correlation' tidak masuk ke pilihan dropdown
all_tables = inspector.get_table_names()
asset_tables = [t for t in all_tables if t not in ['market_correlation', 'portfolio_summary']]

if asset_tables:
    # Dropdown akan terisi otomatis dengan tabel yang tersedia di SQLite
    selected_table = st.sidebar.selectbox(
        "Pilih Aset untuk Dianalisis:",
        options=asset_tables,
        index=0
    )
    
    # Tombol Refresh untuk menarik data terbaru dari tabel terpilih
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
else:
    st.sidebar.warning("⚠️ Tidak ada tabel aset ditemukan di database.")
    st.stop()

# --- BAGIAN 3: FUNGSI LOAD DATA YANG OPTIMAL ---
@st.cache_data
def load_selected_data(table_name):
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        
        # Konversi kolom Date menjadi index datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Gagal memuat data tabel {table_name}: {e}")
        return None

# Memanggil data berdasarkan pilihan di sidebar
df = load_selected_data(selected_table)

# --- BAGIAN 4: HEADER DASHBOARD DINAMIS ---
if df is not None:
    st.title(f"💹 Strategic Asset Engine: {selected_table.replace('_', '.')}")
    # ... Lanjutkan dengan visualisasi grafik Anda di sini
