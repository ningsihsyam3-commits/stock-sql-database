import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns

# Koneksi ke database SQLite
engine = create_engine('sqlite:///database_investasi.db')

st.title('Dashboard Analisis Investasi')

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
    st.header(f'Analisis untuk {selected_asset}')
    try:
        df_asset = pd.read_sql(f'SELECT * FROM {selected_asset}', engine, index_col='Date')
        st.subheader('Data Historis dan Indikator Teknikal')
        st.dataframe(df_asset[['Close', 'MA5', 'MA20', 'MA50', 'RSI']].tail(10))

        # Plot Close Price dan Moving Averages
        fig_price, ax_price = plt.subplots(figsize=(12, 6))
        df_asset[['Close', 'MA5', 'MA20', 'MA50']].plot(ax=ax_price)
        ax_price.set_title(f'Harga Penutupan dan Moving Average untuk {selected_asset}')
        ax_price.set_xlabel('Tanggal')
        ax_price.set_ylabel('Harga')
        st.pyplot(fig_price)

        st.subheader('Deteksi Anomali')
        anomalies = df_asset[df_asset['Is_Anomaly'] == 1]
        if not anomalies.empty:
            st.write("Ditemukan anomali:")
            st.dataframe(anomalies[['Close', 'MA20', 'Z_Score']])
        else:
            st.info("Tidak ada anomali yang terdeteksi berdasarkan Z-Score > 2.")

        st.subheader('Sinyal Strategi Perdagangan')
        st.dataframe(df_asset[['Signal', 'Daily_Return', 'Strategy_Return', 'Cumulative_Strategy']].tail(10))

        # Plot Cumulative Strategy Return
        fig_strategy, ax_strategy = plt.subplots(figsize=(12, 6))
        df_asset['Cumulative_Strategy'].plot(ax=ax_strategy)
        ax_strategy.set_title(f'Return Kumulatif Strategi untuk {selected_asset}')
        ax_strategy.set_xlabel('Tanggal')
        ax_strategy.set_ylabel('Return Kumulatif')
        st.pyplot(fig_strategy)

        st.subheader('Prediksi Tren')
        latest_trend = df_asset['Trend_Signal'].iloc[-1]
        st.write(f"Tren terbaru untuk {selected_asset}: **{latest_trend}**")
        st.dataframe(df_asset[['MA20', 'MA50', 'Trend_Signal']].tail(10))

    except Exception as e:
        st.error(f"Gagal memuat data untuk {selected_asset}: {e}")

st.sidebar.markdown('---')
st.sidebar.header('Analisis Korelasi Pasar')

try:
    df_corr = pd.read_sql('SELECT * FROM market_correlation', engine)
    if not df_corr.empty:
        st.sidebar.dataframe(df_corr)
    else:
        st.sidebar.info("Tabel korelasi pasar kosong.")
except Exception as e:
    st.sidebar.error(f"Gagal memuat korelasi pasar: {e}")

st.markdown("--- Personal Assistant ---")
