import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Konfigurasi Database (Gunakan nama database yang konsisten)
engine = create_engine('sqlite:///database_investasi.db')
# Tambahkan ini di bawah baris engine = create_engine(...)
from sqlalchemy import inspect
inspector = inspect(engine)
st.sidebar.write("Tabel yang terdeteksi:", inspector.get_table_names())

# 2. Konfigurasi Halaman
st.set_page_config(page_title="Investment Specialist Dashboard", layout="wide")

st.title("💹 Financial Intelligence Specialist Dashboard")
st.markdown("---")

# 3. Sidebar untuk Pemilihan Aset
st.sidebar.header("Navigation")
assets = ['ASII.JK', 'BBNI.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK']
selected_asset = st.sidebar.selectbox("Pilih Aset", assets)

# 4. Fungsi Load Data
@st.cache_data
def load_data(ticker):
    # Mengubah ASII.JK menjadi ASII_JK agar sesuai nama tabel di database
    table_name = ticker.replace('.', '_').replace('-', '_')
    
    # Gunakan tanda kutip ganda " " untuk menjaga nama tabel tetap aman
    query = f'SELECT * FROM "{table_name}"'
    
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        # Memastikan kolom Date terbaca sebagai tanggal, bukan teks
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df = df.sort_index()
    return df
try:
    df = load_data(selected_asset)
    
    # 5. Row 1: Metrics (Health Cards)
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        price_diff = last_row['Close'] - prev_row['Close']
        st.metric("Last Price", f"Rp {last_row['Close']:,.0f}", f"{price_diff:,.0f}")
        
    with col2:
        status = "🚨 ANOMALY" if last_row['Is_Anomaly'] == 1 else "✅ NORMAL"
        st.metric("Market Status", status, f"Z-Score: {last_row['Z_Score']:.2f}", delta_color="inverse" if status == "🚨 ANOMALY" else "normal")
        
    with col3:
        rsi_val = last_row['RSI']
        st.metric("RSI (14)", f"{rsi_val:.2f}", "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral")
        
    with col4:
        perf = (last_row['Cumulative_Strategy'] - 1) * 100
        st.metric("Strategy Return", f"{perf:.2f}%")

    st.markdown("### 📈 Visual Analysis")

    # 6. Row 2: Main Chart (Price, MA, & Anomalies)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.1, subplot_titles=(f'Price Action & Anomalies: {selected_asset}', 'Relative Strength Index (RSI)'),
                       row_heights=[0.7, 0.3])

    # Candlestick / Line Chart
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Close Price", line=dict(color='royalblue', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name="MA 5 (Fast)", line=dict(color='green', width=1, dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA 20 (Slow)", line=dict(color='red', width=1)), row=1, col=1)

    # Menandai Anomali dengan Marker "X" Merah
    anomalies = df[df['Is_Anomaly'] == 1]
    fig.add_trace(go.Scatter(x=anomalies.index, y=anomalies['Close'], mode='markers', 
                             marker=dict(color='orange', size=10, symbol='x'),
                             name="Anomaly Alert"), row=1, col=1)

    # RSI Chart
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(height=700, template="plotly_dark", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # 7. Row 3: Backtesting & Correlation
    st.markdown("---")
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.subheader("📊 Backtesting Performance")
        st.line_chart(df['Cumulative_Strategy'])
        st.caption("Strategy: MA5 & MA20 Golden Cross / Death Cross crossover.")

    with right_col:
        st.subheader("🔗 Market Correlation")
        try:
            corr_df = pd.read_sql("SELECT * FROM market_correlation", engine)
            st.write(f"Korelasi saat ini antara **BTC** dan **BBRI**:")
            st.title(f"{corr_df['Value'].iloc[0]:.2f}")
            st.info("Korelasi di atas 0.7 menunjukkan hubungan searah yang kuat.")
        except:
            st.write("Data korelasi belum tersedia. Jalankan analysis.py terlebih dahulu.")

except Exception as e:
    st.error(f"Gagal memuat data aset '{selected_asset}'. Pastikan database sudah terupdate.")
    st.info("Tips: Jalankan 'python analysis.py' untuk membuat tabel hasil analisis.")

# 8. Footer
st.sidebar.markdown("---")
# Menambahkan pengecekan apakah df benar-benar ada isinya
if 'df' in locals() and df is not None and not df.empty:
    try:
        last_date = df.index[-1].strftime('%d %B %Y')
        st.sidebar.write(f"📅 Last updated: {last_date}")
    except:
        st.sidebar.write("📅 Last updated: N/A")
else:
    st.sidebar.write("📅 Data tidak tersedia")
