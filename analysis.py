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
    
    return df


