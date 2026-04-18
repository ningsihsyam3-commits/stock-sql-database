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

# Ganti bagian filter yang lama dengan ini:
try:
    df = load_data()
    
    # Sidebar Filter (Menyesuaikan dengan kolom 'ticker' di database Anda)
    st.sidebar.header("Filter")
    
    # Menggunakan 'ticker' karena itu nama kolom di database Anda
    target_column = 'ticker' if 'ticker' in df.columns else 'symbol'
    
    if target_column in df.columns:
        all_symbols = df[target_column].unique()
        selected_ticker = st.sidebar.selectbox("Pilih Kode Saham", all_symbols)
        filtered_df = df[df[target_column] == selected_ticker]
    else:
        selected_ticker = "Data"
        filtered_df = df

    # Tampilkan Judul yang Dinamis
    st.subheader(f"Data Saham Terkini: {selected_ticker}")
    st.dataframe(filtered_df.tail(10), use_container_width=True)
    
    # Grafik Garis (Menggunakan 'close_price' sesuai tabel Anda)
    if 'close_price' in filtered_df.columns:
        st.subheader(f"Tren Harga {selected_ticker}")
        chart_data = filtered_df.set_index('date')['close_price']
        st.line_chart(chart_data)

except Exception as e:
    st.error(f"Error: {e}")
