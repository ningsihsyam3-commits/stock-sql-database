import streamlit as st
import pandas as pd
import sqlite3

# Konfigurasi Halaman
st.set_page_config(page_title="Stock Automation Dashboard", layout="wide")

st.title("📈 Autonomous Stock Analysis Dashboard")

def load_data():
    conn = sqlite3.connect('database_investasi.db')
    df = pd.read_sql_query("SELECT * FROM history_saham", conn)
    conn.close()
    
    # Otomatis deteksi kolom tanggal (antisipasi 'Date' vs 'date')
    df.columns = [c.lower() for c in df.columns]
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    
    return df

try:
    df = load_data()
    
    # Sidebar Filter
    st.sidebar.header("Filter")
    symbol = st.sidebar.selectbox("Pilih Kode Saham", df['symbol'].unique() if 'symbol' in df.columns else ["No Data"])
    
    filtered_df = df[df['symbol'] == symbol] if 'symbol' in df.columns else df

    # Tampilkan Data Utama
    st.subheader(f"Data Saham Terkini: {symbol}")
    st.dataframe(filtered_df.tail(10), use_container_width=True)
    
    # Grafik Garis Sederhana (Menggunakan Pandas native agar tidak butuh library tambahan)
    if 'close' in filtered_df.columns:
        st.subheader("Tren Harga Penutupan")
        st.line_chart(filtered_df.set_index('date')['close'] if 'date' in filtered_df.columns else filtered_df['close'])

except Exception as e:
    st.error(f"Sistem menyala, tapi ada kendala pada data: {e}")
    st.info("Saran: Pastikan bot Telegram Anda sudah pernah mengirim data ke database ini.")
