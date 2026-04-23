import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Strategic Asset Engine", layout="wide")

# CSS untuk Kartu Korelasi (Agar tetap rapi di bawah)
st.markdown("""
<style>
    .correlation-card {
        background-color: #1e2a1e; border-radius: 10px; padding: 20px;
        color: white; border-left: 5px solid #4caf50;
    }
    .correlation-value { font-size: 3rem; font-weight: bold; color: #4caf50; }
    .correlation-desc { background-color: #2e7d32; padding: 10px; border-radius: 5px; text-align: center; }
</style>
""", unsafe_allow_html=True)

engine = create_engine('sqlite:///database_investasi.db')

# --- SIDEBAR ---
st.sidebar.header("Navigation")
inspector = inspect(engine)
asset_tables = [t for t in inspector.get_table_names() if t not in ['market_correlation', 'history_saham']]

if asset_tables:
    selected_table = st.sidebar.selectbox("Pilih Aset:", options=sorted(asset_tables))
    st.sidebar.markdown("---")
    st.sidebar.write("📅 Last updated: 23 April 2026")
else:
    st.sidebar.error("Database Kosong")
    st.stop()

# --- LOAD DATA ---
@st.cache_data
def load_data(table_name):
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df.tail(100) # Batasi 100 data terakhir agar tidak sesak

df = load_data(selected_table)

# --- GRAFIK BERSIH & RAPI (SUBPLOTS) ---
if not df.empty:
    st.title(f"Strategic Asset Engine: {selected_table.replace('_', '.')}")

    # Menggunakan make_subplots untuk memisahkan Harga dan RSI (seperti gambar 2)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1, # Memberi jarak antar grafik
        subplot_titles=("Price Action & Anomalies", "Relative Strength Index (RSI)"),
        row_width=[0.3, 0.7] # Grafik atas lebih besar (70%), bawah lebih kecil (30%)
    )

    # 1. Panel Atas: Candlestick & Moving Averages
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Price", increasing_line_color='#00ffcc', decreasing_line_color='#ff1744'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA 20 (Slow)", line=dict(color='#ff1744', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name="MA 5 (Fast)", line=dict(color='#4caf50', width=1.5, dash='dash')), row=1, col=1)

    # Tambahkan Anomali (Marker Kuning)
    if 'Is_Anomaly' in df.columns:
        anomalies = df[df['Is_Anomaly'] == 1]
        fig.add_trace(go.Scatter(
            x=anomalies.index, y=anomalies['Close'], mode='markers',
            name='Anomaly Alert', marker=dict(color='yellow', size=10, symbol='x')
        ), row=1, col=1)

    # 2. Panel Bawah: RSI (Clean Look)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#9c27b0', width=2)), row=2, col=1)
    
    # Tambahkan garis batas RSI (30 & 70)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # Update Layout agar rapi
    fig.update_layout(
        template="plotly_dark",
        height=800,
        xaxis_rangeslider_visible=False, # Matikan slider agar lebih clean
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- KARTU KORELASI DI BAWAH ---
    st.markdown("---")
    try:
        corr_df = pd.read_sql("SELECT * FROM market_correlation", engine)
        if not corr_df.empty:
            c_val = corr_df['Value'].iloc[0]
            st.markdown(f"""
            <div class="correlation-card">
                <div style="font-size: 1.2rem;">🔗 Market Correlation</div>
                <div style="color: #a0a0a0;">Korelasi saat ini antara aset terkait</div>
                <div class="correlation-value">{c_val:.2f}</div>
                <div class="correlation-desc">Korelasi Positif Kuat</div>
            </div>
            """, unsafe_allow_html=True)
    except:
        pass
