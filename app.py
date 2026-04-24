import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- SETUP HALAMAN & DATABASE ---
st.set_page_config(page_title="Strategic Asset Engine", layout="wide")
engine = create_engine('sqlite:///database_investasi.db')

# CSS untuk Kartu Korelasi Hijau Besar
st.markdown("""
<style>
    .correlation-card {
        background-color: #1e2a1e; border-radius: 10px; padding: 20px;
        color: white; border-left: 5px solid #4caf50;
    }
    .correlation-value { font-size: 3.5rem; font-weight: bold; color: #4caf50; margin: 0; }
    .correlation-desc { background-color: #2e7d32; padding: 10px; border-radius: 5px; text-align: center; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("Navigation")
inspector = inspect(engine)
asset_tables = [t for t in inspector.get_table_names() if t not in ['market_correlation', 'history_saham']]

# --- LOAD DATA (Function Definition) ---
@st.cache_data
def load_data(table_name):
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    return df.tail(80) # Batasi 80 data agar lilin/garis tidak menumpuk

if asset_tables:
    selected_table = st.sidebar.selectbox("Pilih Aset:", options=sorted(asset_tables))
    st.sidebar.markdown("---")
    st.sidebar.write("📅 Last updated: 23 April 2026")

    # Call load_data and subsequent plotting logic only if asset_tables is not empty
    df = load_data(selected_table)

    # --- GRAFIK BERSIH & RAPI (GAYA GAMBAR 2) ---
    if not df.empty:
        st.title(f"Strategic Asset Engine: {selected_table.replace('_', '.')}")

        # Menggunakan subplots untuk memisahkan panel Harga, RSI, dan MACD
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_width=[0.2, 0.2, 0.6] # Harga 60%, RSI 20%, MACD 20%
        )

        # 1. Panel Atas: Line Chart (Solusi jika data Open/High/Low tidak ada)
        # Gunakan Line Chart agar tidak KeyError 'Open'
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'], name="Close Price",
            line=dict(color='#3366ff', width=2.5),
            showlegend=True
        ), row=1, col=1)

        # Indikator MA
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA 20 (Slow)", line=dict(color='#ff1744', width=1.5), showlegend=True), row=1, col=1)
        if 'MA5' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name="MA 5 (Fast)", line=dict(color='#4caf50', width=1.2, dash='dash'), showlegend=True), row=1, col=1)

        # Bollinger Bands
        # Pastikan kolom BB_BBL_20_2.0, BB_BBM_20_2.0, BB_BBU_20_2.0 ada
        if 'BBL_20_2.0' in df.columns and 'BBM_20_2.0' in df.columns and 'BBU_20_2.0' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['BBM_20_2.0'], name="BB Middle", line=dict(color='yellow', width=1, dash='dot'), showlegend=True), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], name="BB Upper", line=dict(color='purple', width=1, dash='dot'), showlegend=True), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], name="BB Lower", line=dict(color='cyan', width=1, dash='dot'), showlegend=True), row=1, col=1)

        # Anomali
        if 'Is_Anomaly' in df.columns:
            anomalies = df[df['Is_Anomaly'] == 1]
            fig.add_trace(go.Scatter(
                x=anomalies.index, y=anomalies['Close'], mode='markers',
                name='Anomaly Alert', marker=dict(color='orange', size=10, symbol='x'),
                showlegend=True
            ), row=1, col=1)

        # 2. Panel Tengah: RSI
        if 'RSI' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#9c27b0', width=2), showlegend=True), row=2, col=1)
            # Garis ambang batas RSI
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

        # 3. Panel Bawah: MACD
        # Asumsi kolom yang dihasilkan pandas_ta adalah MACD_12_26_9, MACDH_12_26_9, MACDS_12_26_9
        if 'MACD_12_26_9' in df.columns and 'MACDH_12_26_9' in df.columns and 'MACDS_12_26_9' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], name='MACD', line=dict(color='blue', width=1.5), showlegend=True), row=3, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df['MACDH_12_26_9'], name='MACD Hist', marker_color='grey', showlegend=True), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACDS_12_26_9'], name='MACD Signal', line=dict(color='red', width=1), showlegend=True), row=3, col=1)

        # Penyesuaian Layout agar rapi seperti Gambar 2
        fig.update_layout(
            template="plotly_dark",
            height=750,
            xaxis_rangeslider_visible=False,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        # Update y-axis titles for better clarity
        fig.update_yaxes(title_text="Harga", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        fig.update_yaxes(title_text="MACD", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # --- KARTU KORELASI ---
        col_a, col_b = st.columns([2, 1])
        with col_b:
            try:
                corr_df = pd.read_sql("SELECT * FROM market_correlation", engine)
                if not corr_df.empty:
                    val = corr_df['Value'].iloc[0]
                    st.markdown(f'''
                    <div class="correlation-card">
                        <div style="font-weight: bold; font-size: 1.1rem;">🔗 Market Correlation</div>
                        <div style="color: #a0a0a0; font-size: 0.8rem;">Antara aset pilihan</div>
                        <div class="correlation-value">{val:.2f}</div>
                        <div class="correlation-desc">Korelasi Positif Kuat</div>
                    </div>
                    ''', unsafe_allow_html=True)
            except:
                pass
    else:
        st.warning(f"Tidak ada data historis yang cukup untuk aset '{selected_table.replace('_', '.')}' untuk ditampilkan.")

else: # This else belongs to 'if asset_tables:'
    st.sidebar.error("Database Kosong")
    st.warning("Tidak ada tabel aset yang ditemukan di database. Pastikan data telah diunduh dan dianalisis.")
"""

with open("app.py", "w") as f:
    f.write(streamlit_code)

print("Streamlit code saved to app.py")
