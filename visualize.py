import matplotlib.pyplot as plt

def buat_grafik_tren(df):
    if df is None or df.empty:
        print("Data kosong, tidak bisa membuat grafik.")
        return

    plt.figure(figsize=(12, 7))
    
    # Loop untuk setiap ticker
    tickers = df['ticker'].unique()
    for ticker in tickers:
        data_saham = df[df['ticker'] == ticker]
        
        # Plot Harga Asli
        line, = plt.plot(data_saham['date'], data_saham['close_price'], marker='o', label=f'{ticker} Price')
        
        # Plot Moving Average (Gunakan warna yang sama dengan harga asli tapi garis putus-putus)
        color = line.get_color()
        plt.plot(data_saham['date'], data_saham['MA5'], linestyle='--', alpha=0.6, color=color, label=f'{ticker} MA5')

    plt.title('Tren Harga & Moving Average (MA5)', fontsize=14, fontweight='bold')
    plt.xlabel('Tanggal', fontsize=12)
    plt.ylabel('Harga (IDR)', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left') # Legend di luar agar rapi
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('tren_saham.png')
    print("Grafik baru (Price + MA5) berhasil disimpan.")
