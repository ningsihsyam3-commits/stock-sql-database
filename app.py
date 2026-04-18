import streamlit as st
import pandas as pd
import sqlite3

# Konfigurasi Halaman
st.set_page_config(page_title="Stock Automation Dashboard", layout="wide")

st.title("📈 Autonomous Stock Analysis Dashboard")
st.markdown("""
Dashboard ini menampilkan hasil analisis otomatis dari bot Python yang berjalan di GitHub Actions.
Data diperbarui secara mandiri ke database SQLite.
""")

# Fungsi Loading Data dengan Nama Tabel yang Benar
def load_data():
    conn = sqlite3.connect('database_investasi.db')
    # Menggunakan nama tabel: history_saham
    df = pd.read_sql_query("SELECT * FROM history_saham", conn)
    conn.close()
    
    # Memastikan format tanggal benar
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

try:
    df_raw = load_data()
    
    # Sidebar
    st.sidebar.header("Control Panel")
    symbol = st.sidebar.selectbox("Pilih Kode Saham", df_raw['Symbol'].unique())
    
    # Filter data berdasarkan simbol
    df = df_raw[df_raw['Symbol'] == symbol].copy()

    # Layout Kolom untuk Indikator Utama (Metric)
    col1, col2, col3 = st.columns(3)
    last_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    change = last_price - prev_price

    col1.metric("Harga Terakhir", f"Rp{last_price:,.0f}", f"{change:,.0f}")
    
    # Cek apakah kolom RSI tersedia di database
    if 'RSI' in df.columns:
        current_rsi = df['RSI'].iloc[-1]
        col2.metric("RSI (14)", f"{current_rsi:,.2f}")
    else:
        col2.metric("RSI (14)", "N/A")
        
    col3.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")

    # Visualisasi Chart Teknikal
    st.subheader(f"Price Action: {symbol}")
    
    # Menyiapkan SMA jika kolomnya tersedia
    add_ons = []
    if 'SMA_5' in df.columns:
        add_ons.append(mpf.make_addplot(df['SMA_5'], color='orange'))
    if 'SMA_20' in df.columns:
        add_ons.append(mpf.make_addplot(df['SMA_20'], color='blue'))

    # Plot menggunakan mplfinance
    fig, ax = mpf.plot(df.tail(60), type='candle', style='charles',
                       addplot=add_ons, volume=True, 
                       returnfig=True, figsize=(12, 7))
    st.pyplot(fig)

    # Tabel Data (Expander agar rapi)
    with st.expander("Lihat Data Histori Lengkap"):
        st.dataframe(df.sort_index(ascending=False))

except Exception as e:
    st.error(f"Gagal memuat data. Error: {e}")
