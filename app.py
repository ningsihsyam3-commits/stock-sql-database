import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from datetime import date
import pandas_ta as ta # Import pandas_ta
import numpy as np # Import numpy for strategy calculations

# --- Konfigurasi Halaman --- #
st.set_page_config(layout="wide", page_title="Dashboard Analisis Investasi Saham", page_icon="📈")

# Koneksi ke database SQLite
engine = create_engine('sqlite:///database_investasi.db')

st.title('📈 Strategic Asset Engine')

# Daftar aset yang tersedia (sesuai dengan tabel di database)
def get_asset_tables():
    # Get unique tickers from history_saham table
    df_tickers = pd.read_sql('SELECT DISTINCT ticker FROM history_saham', engine)
    return df_tickers['ticker'].tolist()

asset_options = get_asset_tables()

# --- Sidebar untuk Pilihan Aset --- #
st.sidebar.header('Pilihan Aset')
selected_asset_raw = st.sidebar.selectbox('Pilih Aset untuk Analisis Detail', asset_options)
st.sidebar.markdown('---') # Separator di sidebar

# --- Pilihan Rentang Tanggal --- #
st.sidebar.header('Pilihan Rentang Tanggal')
today = date.today()
min_date_available = pd.to_datetime('2020-01-01') # Fallback
max_date_available = pd.to_datetime(today)

try:
    df_history_saham_dates = pd.read_sql('SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM history_saham', engine)
    if not df_history_saham_dates.empty:
        min_date_available = pd.to_datetime(df_history_saham_dates['min_date'].iloc[0])
        max_date_available = pd.to_datetime(df_history_saham_dates['max_date'].iloc[0])
except Exception as e:
    st.sidebar.warning(f"Could not retrieve full date range from history_saham: {e}")

default_start_date = max_date_available - pd.Timedelta(days=365) if (max_date_available - pd.Timedelta(days=365)) > min_date_available else min_date_available
default_end_date = max_date_available

start_date = st.sidebar.date_input('Tanggal Mulai', value=default_start_date, min_value=min_date_available, max_value=max_date_available)
end_date = st.sidebar.date_input('Tanggal Akhir', value=default_end_date, min_value=min_date_available, max_value=max_date_available)

st.sidebar.markdown('---')

# --- Sliders for Customizable Indicators --- (Trader's choice)
st.sidebar.header('Pengaturan Indikator (Trader)')
ma_short_length = st.sidebar.slider('Panjang MA Pendek (MA5)', min_value=3, max_value=20, value=5, step=1)
ma_medium_length = st.sidebar.slider('Panjang MA Menengah (MA20)', min_value=10, max_value=50, value=20, step=1)
ma_long_length = st.sidebar.slider('Panjang MA Panjang (MA50)', min_value=20, max_value=200, value=50, step=5)
rsi_length = st.sidebar.slider('Panjang Periode RSI (14)', min_value=7, max_value=30, value=14, step=1)
st.sidebar.markdown('---')

if selected_asset_raw:
    st.header(f'Analisis Detail untuk {selected_asset_raw}')

    try:
        with st.spinner(f"Memuat dan menghitung ulang data historis untuk {selected_asset_raw}..."):
            # Load raw data from history_saham
            df_asset = pd.read_sql(f"SELECT date, close FROM history_saham WHERE ticker = '{selected_asset_raw}'", engine)
            df_asset['date'] = pd.to_datetime(df_asset['date'])
            df_asset = df_asset.rename(columns={'date': 'Date', 'close': 'Close'})
            df_asset = df_asset.set_index('Date')
            df_asset = df_asset.sort_index()

        # Filter berdasarkan rentang tanggal yang dipilih
        if start_date > end_date:
            st.error("Error: Tanggal mulai tidak boleh lebih lambat dari tanggal akhir.")
            st.stop() # Stop execution if dates are invalid

        df_asset = df_asset[(df_asset.index >= pd.to_datetime(start_date)) & (df_asset.index <= pd.to_datetime(end_date))]

        if df_asset.empty:
            st.warning(f"Tidak ada data ditemukan untuk {selected_asset_raw} dalam rentang tanggal yang dipilih.")
        else:
            # --- Dinamisasi Kalkulasi Indikator --- (Trader's choice)
            # Ensure sufficient data for calculations
            min_data_required = max(ma_short_length, ma_medium_length, ma_long_length, rsi_length)
            if len(df_asset) < min_data_required:
                st.warning(f"Data terlalu pendek ({len(df_asset)} baris) untuk menghitung semua indikator dengan panjang yang dipilih (minimal {min_data_required} baris diperlukan). Beberapa indikator mungkin kosong.")

            df_asset[f'MA{ma_short_length}'] = ta.sma(df_asset['Close'], length=ma_short_length)
            df_asset[f'MA{ma_medium_length}'] = ta.sma(df_asset['Close'], length=ma_medium_length)
            df_asset[f'MA{ma_long_length}'] = ta.sma(df_asset['Close'], length=ma_long_length)
            df_asset['RSI'] = ta.rsi(df_asset['Close'], length=rsi_length)

            # Anomali & Strategy - needs MA_medium and STD (which depends on rolling window)
            # Ensure sufficient data for STD calculation
            if len(df_asset) >= ma_medium_length:
                df_asset['STD_MA_Medium'] = df_asset['Close'].rolling(window=ma_medium_length).std()
                df_asset['Z_Score'] = (df_asset['Close'] - df_asset[f'MA{ma_medium_length}']) / df_asset['STD_MA_Medium']
                df_asset['Is_Anomaly'] = df_asset['Z_Score'].apply(lambda x: 1 if abs(x) > 2 else 0)
            else:
                df_asset['STD_MA_Medium'] = np.nan
                df_asset['Z_Score'] = np.nan
                df_asset['Is_Anomaly'] = 0 # No anomaly if not enough data for STD

            # Strategy Signal: Use customizable MA lengths for signal
            df_asset['Signal'] = np.where(df_asset[f'MA{ma_short_length}'] > df_asset[f'MA{ma_medium_length}'], 1, 0)
            df_asset['Daily_Return'] = df_asset['Close'].pct_change()
            df_asset['Strategy_Return'] = df_asset['Signal'].shift(1) * df_asset['Daily_Return']
            df_asset['Cumulative_Strategy'] = (1 + df_asset['Strategy_Return'].fillna(0)).cumprod()

            # PREDIKSI TREND BARU: Use customizable MA lengths for trend
            df_asset['Trend_Signal'] = np.where(df_asset[f'MA{ma_medium_length}'] > df_asset[f'MA{ma_long_length}'], 'Bullish', 'Bearish')

            # Ambil data terbaru untuk metrik
            latest_data = df_asset.iloc[-1]
            latest_close = latest_data['Close']
            latest_ma_medium_val = latest_data[f'MA{ma_medium_length}'] # Use the dynamically calculated MA
            latest_ma_long_val = latest_data[f'MA{ma_long_length}'] # Use the dynamically calculated MA
            latest_rsi = latest_data['RSI']
            latest_trend = latest_data['Trend_Signal']

            # --- Tampilan Metrik Utama --- #
            st.subheader('💡 Metrik Utama')
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric(label="Harga Penutupan Terakhir", value=f"{latest_close:,.2f}")
            with col2:
                st.metric(label=f"MA {ma_medium_length}", value=f"{latest_ma_medium_val:,.2f}")
            with col3:
                st.metric(label=f"MA {ma_long_length}", value=f"{latest_ma_long_val:,.2f}")
            with col4:
                st.metric(label=f"RSI ({rsi_length} hari)", value=f"{latest_rsi:,.2f}")
            with col5:
                trend_color = "green" if latest_trend == 'Bullish' else "red"
                st.metric(label="Sinyal Tren", value=f":{trend_color}[{latest_trend}]")

            st.markdown("--- --- --- --- --- --- --- --- --- ---") # Pemisah visual

            # --- Data Historis dan Indikator Teknikal --- #
            st.subheader('📊 Harga & Indikator Teknikal')

            fig_price = px.line(df_asset, x=df_asset.index, y=['Close', f'MA{ma_short_length}', f'MA{ma_medium_length}', f'MA{ma_long_length}'],
                                title=f'Harga Penutupan & Moving Average {selected_asset_raw}',
                                labels={'Date': 'Tanggal', 'value': 'Harga'})
            fig_price.update_layout(hovermode="x unified")

            anomalies = df_asset[df_asset['Is_Anomaly'] == 1]
            if not anomalies.empty:
                fig_price.add_scatter(x=anomalies.index, y=anomalies['Close'],
                                      mode='markers',
                                      marker=dict(color='red', size=8, symbol='circle'),
                                      name='Anomaly')
            st.plotly_chart(fig_price, use_container_width=True)

            fig_rsi = px.line(df_asset, x=df_asset.index, y='RSI',
                              title=f'Relative Strength Index (RSI) {selected_asset_raw}',
                              labels={'Date': 'Tanggal', 'RSI': 'RSI'},
                              color_discrete_sequence=['purple'])
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)", annotation_position="top right")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)", annotation_position="bottom right")
            fig_rsi.update_layout(hovermode="x unified")
            st.plotly_chart(fig_rsi, use_container_width=True)


            # --- Deteksi Anomali --- #
            st.subheader('🔍 Deteksi Anomali')
            if not anomalies.empty:
                st.write("Ditemukan anomali (ditandai pada grafik harga di atas).")
            else:
                st.info("Tidak ada anomali yang terdeteksi berdasarkan Z-Score > 2.")

            # --- Sinyal Strategi Perdagangan --- #
            st.subheader('💹 Sinyal Strategi Perdagangan')
            fig_strategy = px.line(df_asset, x=df_asset.index, y='Cumulative_Strategy',
                                   title=f'Return Kumulatif Strategi {selected_asset_raw}',
                                   labels={'Date': 'Tanggal', 'Cumulative_Strategy': 'Return Kumulatif'})
            fig_strategy.update_layout(hovermode="x unified")
            st.plotly_chart(fig_strategy, use_container_width=True)

            # --- Prediksi Tren --- #
            st.subheader('📈 Prediksi Tren')
            st.write(f"Tren terbaru untuk {selected_asset_raw}: **:{trend_color}[{latest_trend}]**")

    except Exception as e:
        st.error(f"Gagal memuat data atau menghitung indikator untuk {selected_asset_raw}: {e}")

# --- Analisis Korelasi Pasar --- #
st.sidebar.markdown('---')
st.sidebar.header('Analisis Korelasi Pasar')

try:
    # Load all historical data for correlation calculation (filtered by date range)
    all_assets_data = pd.read_sql('SELECT date, ticker, close FROM history_saham', engine)
    all_assets_data['date'] = pd.to_datetime(all_assets_data['date'])
    all_assets_data = all_assets_data[(all_assets_data['date'] >= pd.to_datetime(start_date)) & (all_assets_data['date'] <= pd.to_datetime(end_date))]
    pivot_df = all_assets_data.pivot(index='date', columns='ticker', values='close')
    correlation_matrix = pivot_df.corr()

    st.subheader('Analisis Korelasi Antar Aset (Heatmap)')
    if not correlation_matrix.empty:
        fig_corr_heatmap = px.imshow(correlation_matrix,
                                    text_auto=True, aspect="auto",
                                    title='Heatmap Korelasi Harga Penutupan Antar Aset',
                                    color_continuous_scale='RdBu_r',
                                    range_color=[-1, 1])
        st.plotly_chart(fig_corr_heatmap, use_container_width=True)
    else:
        st.info("Tidak ada data yang cukup untuk menghitung korelasi antar aset dalam rentang tanggal yang dipilih.")

    # Display existing market correlation data (e.g., BBRI vs BMRI)
    # df_corr = pd.read_sql('SELECT * FROM market_correlation', engine)
    # if not df_corr.empty:
    #     st.sidebar.subheader('Korelasi Spesifik (BBRI vs BMRI)')
    #     st.sidebar.dataframe(df_corr)
    # else:
    #     st.sidebar.info("Tabel korelasi pasar kosong.")
except Exception as e:
    st.sidebar.error(f"Gagal memuat korelasi pasar: {e}")

# --- Footer --- #
st.markdown("--- ")
st.markdown("<p style='text-align: center; color: gray;'>Dashboard Analisis Investasi Saham - Dibuat dengan Streamlit</p>", unsafe_allow_html=True)
