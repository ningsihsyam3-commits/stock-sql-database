import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.graph_objects as go

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Strategic Asset Engine", layout="wide")

# 2. KONEKSI DATABASE
engine = create_engine('sqlite:///database_investasi.db')

# Fungsi untuk mendeteksi tabel hasil analisis secara otomatis
def get_analyzed_assets():
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    # Hanya ambil tabel individual aset, abaikan tabel log/mentah
    ignore = ['history_saham', 'market_correlation']
    assets = [t for t in all_tables if t not in ignore]
    return sorted(assets)

# 3. SIDEBAR DINAMIS
st.sidebar.header("📊 Strategic Control")
available_assets = get_analyzed_assets()

if not available_assets:
    st.sidebar.warning("⚠️ Database belum berisi hasil analisis. Jalankan skrip analisis terlebih dahulu.")
    selected_asset = None
else:
    selected_asset = st.sidebar.selectbox("Pilih Aset untuk Dipantau", available_assets)

# 4. DASHBOARD UTAMA
if selected_asset:
    # Judul yang bersih (BBRI_JK -> BBRI.JK)
    display_name = selected_asset.replace('_', '.')
    st.title(f"📈 Dashboard: {display_name}")
    
    # Load data dari tabel terpilih
    df = pd.read_sql(f'SELECT * FROM {selected_asset}', engine)
    
    # Pastikan Date menjadi Index untuk visualisasi
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # --- BARIS METRIK UTAMA ---
    col1, col2, col3, col4 = st.columns(4)
    
    last_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    change = ((last_price - prev_price) / prev_price) * 100
    
    # Ambil hasil dari analysis.py
    trend = df['Trend_Signal'].iloc[-1] if 'Trend_Signal' in df.columns else "N/A"
    rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 0
    perf = (df['Cumulative_Strategy'].iloc[-1] - 1) * 100 if 'Cumulative_Strategy' in df.columns else 0

    col1.metric("Harga Terakhir", f"{last_price:,.2f}", f"{change:.2f}%")
    col2.metric("Sinyal Trend", trend, delta_color="normal" if trend == "Bullish" else "inverse")
    col3.metric("RSI (14)", f"{rsi:.2f}")
    col4.metric("Strategi Profit", f"{perf:.2f}%")

    # --- VISUALISASI CHART ---
    tab1, tab2 = st.tabs(["Harga & MA", "Strategi Kumulatif"])
    
    with tab1:
        fig = go.Figure()
        # Candlestick atau Line (disini menggunakan Line untuk kesederhanaan iPad)
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color='#00ffcc', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA20 (Short)", line=dict(color='orange', dash='dot')))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name="MA50 (Long)", line=dict(color='red', width=1.5)))
        
        fig.update_layout(template="plotly_dark", height=500, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Menampilkan performa strategi MA Crossover dari analysis.py
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(x=df.index, y=df['Cumulative_Strategy'], fill='tozeroy', name="Strategy Return"))
        fig_perf.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_perf, use_container_width=True)

    # --- ANOMALI DETECTOR ---
    if 'Is_Anomaly' in df.columns:
        anomalies = df[df['Is_Anomaly'] == 1].tail(5)
        if not anomalies.empty:
            st.subheader("⚠️ Deteksi Anomali Harga Terakhir")
            st.warning(f"Terdeteksi {len(anomalies)} pergerakan harga tidak wajar dalam periode terakhir.")
            st.table(anomalies[['Close', 'Z_Score']])

else:
    st.info("Gunakan sidebar di sebelah kiri untuk memilih aset yang ingin dipantau.")

# Footer informasi korelasi
with st.sidebar.expander("ℹ️ Info Korelasi"):
    try:
        corr_df = pd.read_sql('SELECT * FROM market_correlation', engine)
        st.write(f"Korelasi {corr_df['Pair'].iloc[0]}:")
        st.code(f"{corr_df['Value'].iloc[0]:.4f}")
    except:
        st.write("Data korelasi belum tersedia.")
