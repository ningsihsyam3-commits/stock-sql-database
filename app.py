import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.graph_objects as go

# --- BAGIAN 1: KONFIGURASI DATABASE ---
engine = create_engine('sqlite:///database_investasi.db')
inspector = inspect(engine)

# --- BAGIAN 2: LOGIKA DINAMIS SIDEBAR ---
st.sidebar.header("📊 Asset Selection")

all_tables = inspector.get_table_names()
# Filter tabel sistem agar tidak masuk dropdown
asset_tables = [t for t in all_tables if t not in ['market_correlation', 'history_saham']]

if asset_tables:
    selected_table = st.sidebar.selectbox(
        "Pilih Aset untuk Dianalisis:",
        options=sorted(asset_tables),
        index=0
    )
    
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
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Gagal memuat data tabel {table_name}: {e}")
        return None

df = load_selected_data(selected_table)

# --- BAGIAN 4: DASHBOARD DINAMIS & ANALISIS BARU ---
if df is not None and not df.empty:
    st.title(f"💹 Strategic Asset Engine: {selected_table.replace('_', '.')}")

    # A. Baris Metrik (Analisis Baru)
    col1, col2, col3, col4 = st.columns(4)
    
    last_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    pct_change = ((last_close - prev_close) / prev_close) * 100
    
    # Ambil data hasil analysis.py
    current_trend = df['Trend_Signal'].iloc[-1] if 'Trend_Signal' in df.columns else "N/A"
    current_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 0
    strategy_perf = (df['Cumulative_Strategy'].iloc[-1] - 1) * 100 if 'Cumulative_Strategy' in df.columns else 0

    col1.metric("Price", f"{last_close:,.2f}", f"{pct_change:.2f}%")
    col2.metric("Trend (MA20/50)", current_trend, delta_color="normal" if current_trend == "Bullish" else "inverse")
    col3.metric("RSI (14)", f"{current_rsi:.2f}")
    col4.metric("Strategy Profit", f"{strategy_perf:.2f}%")

    # B. Grafik Harga & Moving Average (Visualisasi Baru)
    st.subheader("Price Movement & Moving Averages")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Close Price", line=dict(color='#00ffcc', width=2)))
    
    if 'MA20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA20 (Short)", line=dict(color='orange', dash='dot')))
    if 'MA50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name="MA50 (Long/Trend)", line=dict(color='red', width=1.5)))
    
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    # C. Tabel Detail (History Terakhir)
    with st.expander("📝 View Detailed Historical Data"):
        # Menampilkan data terbaru di atas
        st.dataframe(df.sort_index(ascending=False).head(20), use_container_width=True)

    # D. Info Korelasi di Sidebar (Tambahan)
    try:
        corr_data = pd.read_sql('SELECT * FROM market_correlation', engine)
        if not corr_data.empty:
            st.sidebar.markdown("---")
            st.sidebar.write("**Market Correlation:**")
            for i, row in corr_data.iterrows():
                st.sidebar.info(f"{row['Pair']}: **{row['Value']:.4f}**")
    except:
        pass
else:
    st.info("Pilih aset di sidebar untuk melihat analisis.")
