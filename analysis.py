import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///database_investasi.db')

def get_analyzed_data():
    # Ambil data dari database
    df = pd.read_sql("SELECT * FROM history_saham ORDER BY ticker, date", engine)
    
    if df.empty:
        return None

    # Hitung Indikator (MA-5 dan MA-20 sesuai rencana kita)
    df['MA5'] = df.groupby('ticker')['close_price'].transform(lambda x: x.rolling(window=5).mean())
    df['MA20'] = df.groupby('ticker')['close_price'].transform(lambda x: x.rolling(window=20).mean())
    
    # Hitung perubahan persentase harian
    df['pct_change'] = df.groupby('ticker')['close_price'].pct_change() * 100
    
def hitung_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def update_indikator_rsi(df):
    # Pastikan data diurutkan berdasarkan tanggal lama ke baru untuk perhitungan yang benar
    df = df.sort_values(['ticker', 'date'])
    
    # Hitung RSI 14 hari untuk setiap ticker
    df['rsi'] = df.groupby('ticker')['close_price'].transform(lambda x: hitung_rsi(x))
    
    return df
