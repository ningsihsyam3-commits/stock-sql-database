import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns

# Koneksi ke database SQLite
engine = create_engine('sqlite:///database_investasi.db')

st.title('📈 Dashboard Analisis Investasi Saham') # Added emoji and more specific title

# Daftar aset yang tersedia (sesuai dengan tabel di database)
# Kita ambil daftar tabel yang bukan 'history_saham' dan 'market_correlation'
def get_asset_tables():
    # Gunakan query SQL langsung untuk mendapatkan nama tabel
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    df_tables = pd.read_sql(query, engine)
    all_tables = df_tables['name'].tolist()

    # Filter tabel sistem SQLite dan tabel analisis lainnya
    asset_tables = [table for table in all_tables if table not in ['history_saham', 'market_correlation', 'sqlite_sequence']]
    return asset_tables

asset_options = get_asset_tables()

# Pilihan aset dari sidebar
selected_asset = st.sidebar.selectbox('Pilih Aset untuk Analisis Detail', asset_options)

if selected_asset:
    st.header(f'Detail Analisis untuk {selected_asset}') # Changed to Detail Analisis

    try:
        df_asset = pd.read_sql(f'SELECT * FROM {selected_asset}', engine, index_col='Date')
        df_asset.index = pd.to_datetime(df_asset.index) # Ensure index is datetime

        # Get latest data for metrics
        latest_data = df_asset.iloc[-1]
        latest_close = latest_data['Close']
        latest_ma20 = latest_data['MA20']
        latest_ma50 = latest_data['MA50']
        latest_rsi = latest_data['RSI']
        latest_trend = latest_data['Trend_Signal']

        # Display key metrics using st.columns and st.metric
        st.subheader('💡 Metrik Utama')
        col1, col2, col3, col4, col5 = st.columns(5) # 5 columns for 5 metrics

        with col1:
            st.metric(label="Harga Penutupan Terakhir", value=f"{latest_close:,.2f}")
        with col2:
            st.metric(label="MA 20", value=f"{latest_ma20:,.2f}")
        with col3:
            st.metric(label="MA 50", value=f"{latest_ma50:,.2f}")
        with col4:
            st.metric(label="RSI (14 hari)", value=f"{latest_rsi:,.2f}")
        with col5:
            st.metric(label="Sinyal Tren", value=latest_trend)


        st.subheader('📊 Data Historis dan Indikator Teknikal') # Added emoji
        st.dataframe(df_asset[['Close', 'MA5', 'MA20', 'MA50', 'RSI']].tail(10))

        # Plot Close Price dan Moving Averages
        fig_price, ax_price = plt.subplots(figsize=(12, 6))
        df_asset[['Close', 'MA5', 'MA20', 'MA50']].plot(ax=ax_price, title=f'Harga Penutupan & Moving Average {selected_asset}') # Improved title
        ax_price.set_xlabel('Tanggal')
        ax_price.set_ylabel('Harga')
        st.pyplot(fig_price)

        # Plot RSI
        fig_rsi, ax_rsi = plt.subplots(figsize=(12, 4))
        df_asset['RSI'].plot(ax=ax_rsi, title=f'Relative Strength Index (RSI) {selected_asset}', color='purple')
        ax_rsi.axhline(70, color='red', linestyle='--', alpha=0.6, label='Overbought (70)')
        ax_rsi.axhline(30, color='green', linestyle='--', alpha=0.6, label='Oversold (30)')
        ax_rsi.set_xlabel('Tanggal')
        ax_rsi.set_ylabel('RSI')
        ax_rsi.legend()
        st.pyplot(fig_rsi)


        st.subheader('🔍 Deteksi Anomali') # Added emoji
        with st.expander("Lihat Detail Anomali"): # Using expander
            anomalies = df_asset[df_asset['Is_Anomaly'] == 1]
            if not anomalies.empty:
                st.write("Ditemukan anomali (berdasarkan Z-Score > 2):")
                st.dataframe(anomalies[['Close', 'MA20', 'Z_Score']])
            else:
                st.info("Tidak ada anomali yang terdeteksi berdasarkan Z-Score > 2.")

        st.subheader('💹 Sinyal Strategi Perdagangan') # Added emoji
        st.dataframe(df_asset[['Signal', 'Daily_Return', 'Strategy_Return', 'Cumulative_Strategy']].tail(10))

        # Plot Cumulative Strategy Return
        fig_strategy, ax_strategy = plt.subplots(figsize=(12, 6))
        df_asset['Cumulative_Strategy'].plot(ax=ax_strategy, title=f'Return Kumulatif Strategi {selected_asset}') # Improved title
        ax_strategy.set_xlabel('Tanggal')
        ax_strategy.set_ylabel('Return Kumulatif')
        st.pyplot(fig_strategy)

        st.subheader('📈 Prediksi Tren') # Added emoji
        st.write(f"Tren terbaru untuk {selected_asset}: **{latest_trend}**") # Already showing latest_trend, can remove redundant datafram
        # st.dataframe(df_asset[['MA20', 'MA50', 'Trend_Signal']].tail(10)) # Redundant after metric, but keep for full detail

    except Exception as e:
        st.error(f"Gagal memuat data untuk {selected_asset}: {e}")

st.sidebar.markdown('---')
st.sidebar.header('Analisis Korelasi Pasar')

try:
    df_corr = pd.read_sql('SELECT * FROM market_correlation', engine)
    if not df_corr.empty:
        st.sidebar.subheader('Pasangan dengan Korelasi Tinggi') # Added subheader
        st.sidebar.dataframe(df_corr)
    else:
        st.sidebar.info("Tabel korelasi pasar kosong.")
except Exception as e:
    st.sidebar.error(f"Gagal memuat korelasi pasar: {e}")

st.markdown("--- Personal Assistant ---") # Footer with emoji
