import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- BAGIAN 1: KONFIGURASI HALAMAN & DATABASE ---
st.set_page_config(page_title="Strategic Asset Engine", layout="wide")

# CSS Khusus untuk Kartu Korelasi Hijau Besar
st.markdown("""
<style>
    .correlation-card {
        background-color: #1e2a1e; /* Hijau gelap */
        border-radius: 10px;
        padding: 20px;
        color: white;
        border-left: 5px solid #4caf50; /* Garis hijau terang di kiri */
    }
    .correlation-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 10px; }
    .correlation-value { font-size: 3.5rem; font-weight: bold; color: #4caf50; margin-bottom: 0px;}
    .correlation-pair { font-size: 0.9rem; color: #a0a0a0; margin-top: -5px; margin-bottom: 10px; }
    .correlation-desc {
        background-color: #2e7d32; /* Hijau kotak deskripsi */
        padding: 10px;
        border-radius: 5px;
        font-size: 1rem;
        margin-top: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

engine = create_engine('sqlite:///database_investasi.db')
inspector = inspect(engine)

# --- BAGIAN 2: LOGIKA DINAMIS SIDEBAR ---
st.sidebar.header("📊 Asset Selection")

all_tables = inspector.get_table_names()
# Filter tabel sistem
ignore_tables = ['market_correlation', 'history_saham', 'portfolio_summary']
asset_tables = [t for t in all_tables if t not in ignore_tables]

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

# --- BAGIAN 3: FUNGSI LOAD DATA OPTIMAL ---
@st.cache_data
def load_selected_data(table_name):
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        # Ambil hanya data 1 tahun terakhir untuk tampilan chart yang optimal
        return df.tail(252) 
    except Exception as e:
        st.error(f"Gagal memuat data tabel {table_name}: {e}")
        return None

df = load_selected_data(selected_table)

# --- BAGIAN 4: DASHBOARD UTAMA & VISUALISASI CANDLESTICK ---
if df is not None and not df.empty:
    display_name = selected_table.replace('_', '.')
    st.title(f"💹 Strategic Asset Engine: {display_name}")

    # A. Baris Metrik
    col1, col2, col3, col4 = st.columns(4)
    last_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    pct_change = ((last_close - prev_close) / prev_close) * 100
    current_trend = df['Trend_Signal'].iloc[-1] if 'Trend_Signal' in df.columns else "N/A"
    strategy_perf = (df['Cumulative_Strategy'].iloc[-1] - 1) * 100 if 'Cumulative_Strategy' in df.columns else 0
    current_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 0

    col1.metric("Current Price", f"{last_close:,.2f}", f"{pct_change:.2f}%")
    col2.metric("Trend Sinyal", current_trend, delta_color="normal" if current_trend == "Bullish" else "inverse")
    col3.metric("RSI (14)", f"{current_rsi:.2f}")
    col4.metric("Strategy Profit", f"{strategy_perf:.2f}%")

    # B. --- PERBAIKAN: Visualisasi Chart Candlestick (Gaya Referensi) ---
    st.subheader(f"Price Action & Anomalies: {display_name}")
    
    # Membuat subplot: Baris 1 untuk Candlestick, Baris 2 untuk Volume (tinggi 4:1)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(f'Candlestick & MA', 'Volume'), 
                        row_width=[0.2, 0.8])

    # 1. Candlestick Chart (Baris 1)
    # Tentukan data Open, High, Low, Close (asumsi kolom ini ada di database individual Anda)
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'] if 'Open' in df.columns else df['Close'],
                                 high=df['High'] if 'High' in df.columns else df['Close'],
                                 low=df['Low'] if 'Low' in df.columns else df['Close'],
                                 close=df['Close'],
                                 name="Candlestick",
                                 increasing_line_color= '#00ffcc', # Hijau Candlestick
                                 decreasing_line_color= '#ff1744'), # Merah Candlestick
                  row=1, col=1)

    # Menambahkan Moving Averages (Lama)
    if 'MA20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA20 (Fast)", line=dict(color='orange', width=1.5, dash='dot')), row=1, col=1)
    if 'MA50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name="MA50 (Slow/Trend)", line=dict(color='red', width=1.8)), row=1, col=1)

    # Menambahkan Anomaly Alert (jika ada)
    if 'Is_Anomaly' in df.columns and 'Z_Score' in df.columns:
        anomalies = df[df['Is_Anomaly'] == 1]
        fig.add_trace(go.Scatter(x=anomalies.index, y=anomalies['Close'], mode='markers',
                                 name='Anomaly Alert', marker=dict(color='yellow', size=10, symbol='x')), row=1, col=1)

    # 2. Volume Chart (Baris 2)
    if 'Volume' in df.columns:
        # Menentukan warna volume (hijau jika harga naik, merah jika turun)
        colors = ['#00ffcc' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ff1744' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=colors, opacity=0.7), row=2, col=1)

    # Layout Configuration
    fig.update_layout(template="plotly_dark",
                      height=700, # Chart dibuat tinggi agar proporsional di iPad
                      xaxis_rangeslider_visible=False, # Sembunyikan rangeslider bawah
                      hovermode="x unified",
                      margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    # Sembunyikan label sumbu x di baris pertama (karena dibagikan)
    fig.update_xaxes(row=1, col=1, showticklabels=False)
    
    st.plotly_chart(fig, use_container_width=True)

    # C. --- BAGIAN KORELASI (Tampilan Kotak Hijau Besar Besar) ---
    st.markdown("---") 
    col_a, col_b = st.columns([2, 1]) # Kotak korelasi di kolom kanan agar seimbang

    with col_b:
        try:
            corr_data = pd.read_sql('SELECT * FROM market_correlation', engine)
            if not corr_data.empty:
                corr_pair = corr_data['Pair'].iloc[0]
                corr_value = corr_data['Value'].iloc[0]
                
                if corr_value > 0.7: desc = "Korelasi Positif Kuat"
                elif corr_value > 0.4: desc = "Korelasi Positif Sedang"
                elif corr_value < -0.7: desc = "Korelasi Negatif Kuat"
                elif corr_value < -0.4: desc = "Korelasi Negatif Sedang"
                else: desc = "Korelasi Lemah"

                st.markdown(f"""
                <div class="correlation-card">
                    <div class="correlation-title">🔗 Market Correlation</div>
                    <div class="correlation-pair">Korelasi saat ini antara {corr_pair}</div>
                    <div class="correlation-value">{corr_value:.2f}</div>
                    <div class="correlation-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
                
        except:
            st.info("Data korelasi belum tersedia.")
            
    with col_a:
        # Tabel Detail (History Terakhir)
        with st.expander("📝 View Detailed Historical Data"):
            st.dataframe(df.sort_index(ascending=False).head(20), use_container_width=True)
        
        st.write(f"*Strategy: MA5 & MA20 Golden Cross / Death Cross crossover.*")

else:
    st.info("Pilih aset di sidebar untuk melihat analisis.")
