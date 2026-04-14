import matplotlib.pyplot as plt

def buat_grafik_tren(df):
    if df is None or df.empty:
        print("Data kosong, tidak bisa membuat grafik.")
        return

    # Debug: Print kolom yang tersedia untuk memastikan (opsional)
    print("Kolom yang tersedia di data:", df.columns.tolist())

    plt.figure(figsize=(12, 7))
    
    tickers = df['ticker'].unique()
    for ticker in tickers:
        data_saham = df[df['ticker'] == ticker]
        
        # Plot Harga Asli
        line, = plt.plot(data_saham['date'], data_saham['close_price'], marker='o', label=f'{ticker} Price')
        
        # Gunakan nama kolom yang sesuai dengan di database (biasanya kecil semua)
       # Kita cek apakah kolomnya 'MA5' atau 'ma5'
        col_ma5 = 'ma5' if 'ma5' in df.columns else 'MA5'
        
        if col_ma5 in data_saham.columns:
            color = line.get_color()
            plt.plot(data_saham['date'], data_saham[col_ma5], linestyle='--', alpha=0.6, color=color, label=f'{ticker} MA5')

    plt.title('Tren Harga & Moving Average', fontsize=14, fontweight='bold')
    plt.xlabel('Tanggal')
    plt.ylabel('Harga (IDR)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('tren_saham.png')
    print("Grafik berhasil diperbarui.")
