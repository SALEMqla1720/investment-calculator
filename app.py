import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import math
import yfinance as yf
from datetime import datetime
import numpy as np

# ============== KODE DARI constants.py ==============
pajak = {
    "Tanah": 0.0,
    "Emas": 0.0,
    "Crypto": 0.0,
    "Saham": 0.0,
    "ETF": 0.0,
    "Obligasi": 0.0,
    "Deposito": 0.0,
    "Reksadana Pasar Uang": 0.0,
    "Reksadana Pendapatan Tetap": 0.0,
    "Reksadana Saham": 0.0,
    "Reksadana Campuran": 0.0,
}

rate_default = {
    "Tanah-Jakarta": 0.08,
    "Tanah-Bandung": 0.08,
    "Tanah-Karawang": 0.075,
    "Tanah-Cikarang": 0.075,
    "Tanah-Bekasi": 0.075,
    "Tanah-Tangerang": 0.075,
    "Tanah-Custom": 0.07,
    "Emas": 0.07,
    "Crypto-BTC": 0.20,
    "Crypto-ETH": 0.15,
    "Crypto-SOL": 0.18,
    "Crypto-XRP": 0.1,
    "Crypto-BNB": 0.12,
    "Saham-BBCA": 0.1,
    "Saham-BMRI": 0.11,
    "Saham-BBRI": 0.1,
    "Saham-AAPL": 0.15,
    "ETF-SPY": 0.1,
    "ETF-QQQ": 0.12,
    "Obligasi": 0.07,
    "Deposito": 0.035,
    "Reksadana Pasar Uang": 0.045,
    "Reksadana Pendapatan Tetap": 0.065,
    "Reksadana Saham": 0.1,
    "Reksadana Campuran": 0.08
}

cg_ids_map = {
    "Crypto-BTC": "bitcoin",
    "Crypto-ETH": "ethereum",
    "Crypto-SOL": "solana",
    "Crypto-XRP": "ripple",
    "Crypto-BNB": "binancecoin"
}

crypto_ratios = {
    "Crypto-ETH": 0.9,
    "Crypto-SOL": 0.95,
    "Crypto-XRP": 0.8,
    "Crypto-BNB": 0.85
}

# ============== KODE DARI helpers.py ==============
def fmt_money(value):
    return f"Rp{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(value):
    return f"{value*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def beautify(df):
    def format_row(row):
        for col in df.columns:
            if "Rp" in col or "Nilai" in col or "Real" in col:
                row[col] = fmt_money(row[col])
            elif "%" in col or "Rate" in col:
                row[col] = f"{row[col]:,.2f}%"
        return row
    return df.apply(format_row, axis=1)

def proj(h0, r, t):
    return h0 * ((1 + r) ** t)

def realval(h, t, inf):
    return h / ((1 + inf) ** t)

def cagr(h0, h_end, t):
    if h0 == 0: return 0
    if h_end < 0: return -1
    return (h_end/h0)**(1/t) - 1 if t > 0 else 0

def fetch_usd_idr():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        if "rates" in data and "IDR" in data["rates"]:
            return data["rates"]["IDR"], "Exchangerate-API"
    except Exception as e:
        st.error(f"Gagal mengambil kurs USD/IDR: {e}")
    return None, None

def fetch_crypto_usd(ids):
    try:
        ids_str = ",".join(ids)
        response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd")
        data = response.json()
        prices = {k: v['usd'] for k, v in data.items() if 'usd' in v}
        return prices, "CoinGecko"
    except Exception as e:
        st.error(f"Gagal mengambil harga crypto: {e}")
    return {}, None

def fetch_yahoo_last_price(ticker):
    try:
        data = yf.download(ticker, period="1d", interval="1m")
        if not data.empty:
            return data['Close'].iloc[-1], "Yahoo Finance"
    except Exception as e:
        st.error(f"Gagal mengambil harga saham/ETF: {e}")
    return None, None

# ============== KODE UTAMA app.py (dengan semua perbaikan) ==============

# Konfigurasi halaman Streamlit agar lebih responsif
st.set_page_config(
    layout="wide",
    page_title="Kalkulator Investasi",
    page_icon="📈"
)

# === CSS IN-LINE (Disatukan ke dalam app.py) ===
st.markdown("""
<style>
/* --- PALET WARNA KONSISTEN --- */
/* Biru Tua: #1a437e (Judul, penekanan kuat) */
/* Biru Sedang/Primer: #2c5ba3 (Sub-judul, garis, info) */
/* Biru Muda (latar belakang): #f0f8ff */
/* Krem: #F5F5DC (Latar belakang elemen interaktif) */
/* Putih: #ffffff (Latar belakang konten, sidebar) */
/* Abu-abu Gelap (Teks): #333333 */


/* --- Gaya Umum Halaman & Teks --- */
.stApp {
    background-color: #f0f8ff !important;
    color: #333333 !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
}

/* Memastikan semua elemen teks, termasuk di dalam komponen, berwarna abu-abu gelap */
p, li, a, label, span, 
.css-1d3f6kr, .css-1a6x33v, .css-16txte9, 
.st-emotion-cache-1r65j0p p, 
.st-emotion-cache-10q2x7r p,
.st-emotion-cache-1y5w0a6 p,
.st-emotion-cache-1j0k816 input, 
.st-emotion-cache-19p087t input,
.st-emotion-cache-1r65j0p span {
    color: #333333 !important;
    font-size: 1.1rem !important;
}
div, span {
    color: #333333 !important;
}
/* Khusus untuk teks placeholder pada input */
.st-emotion-cache-1cpx92x::placeholder {
    color: #999999 !important;
}

/* --- Judul & Subheader --- */
h1 {
    color: #1a437e !important;
    font-weight: 700 !important;
    text-align: center !important;
    border-bottom: 3px solid #1a437e !important;
    padding-bottom: 15px !important;
    font-size: 2.2rem !important;
}
h3 {
    color: #2c5ba3 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #2c5ba3 !important;
    padding-bottom: 5px !important;
    font-size: 1.5rem !important;
}
h4 {
    color: #2c5ba3 !important;
    font-size: 1.3rem !important;
}

/* --- Sidebar --- */
.st-emotion-cache-16txte9 {
    background-color: #ffffff !important;
}

/* --- Tombol & Tombol FAQ --- */
.stButton > button {
    background-color: #2C5BA3 !important; /* Latar belakang biru laut */
    color: #FFFFFF !important; /* Teks putih */
    border-radius: 8px !important;
    font-weight: bold !important;
    padding: 10px 20px !important;
    transition: background-color 0.3s !important;
    font-size: 1rem !important;
}
.stButton > button:hover {
    background-color: #1a437e !important; /* Warna hover biru tua */
}

/* --- Kotak Info, Warning, Success --- */
div[data-testid="stInfo"] {
    background-color: #e6f7ff !important;
    border-left: 5px solid #0077c9 !important;
    color: #0056b3 !important;
}
div[data-testid="stInfo"] p {
    color: #0056b3 !important;
}
div[data-testid="stWarning"] {
    background-color: #fff8e1 !important;
    border-left: 5px solid #ff9900 !important;
    color: #e65100 !important;
}
div[data-testid="stWarning"] p {
    color: #e65100 !important;
}
div[data-testid="stSuccess"] {
    background-color: #d4edda !important;
    border-left: 5px solid #28a745 !important;
    color: #155724 !important;
}
div[data-testid="stSuccess"] p {
    color: #155724 !important;
}

/* --- PERBAIKAN UTAMA: INPUT DAN DROPDOWN --- */

/* Menargetkan semua input, select, dan multiselect */
.st-emotion-cache-1j0k816, .st-emotion-cache-1cpx92x, 
div[data-baseweb="input"], div[data-baseweb="select"] {
    background-color: #2C5BA3 !important; /* Biru Laut */
    color: #FFFFFF !important; /* Teks putih agar terbaca */
    border: 1px solid #1a437e !important;
    border-radius: 5px !important;
}
/* Khusus untuk teks placeholder pada input agar tetap terlihat */
.st-emotion-cache-1cpx92x::placeholder {
    color: #B0C4DE !important; /* Placeholder biru muda */
}
.st-emotion-cache-1j0k816 input {
    color: #FFFFFF !important; /* Teks input juga putih */
}

/* Latar belakang untuk dropdown options (di desktop) */
.st-emotion-cache-10q2x7r, .st-emotion-cache-1r65j0p, .st-emotion-cache-1y5w0a6 {
    background-color: #2C5BA3 !important;
    color: #FFFFFF !important;
}

/* Tombol + dan - pada number input */
.st-emotion-cache-106x616 {
    background-color: #1a437e !important; /* Biru tua */
    color: #ffffff !important;
}

/* Latar belakang dropdown yang muncul saat diklik (desktop dan mobile) */
div[data-baseweb="popover"] > div > div, 
div[role="listbox"] {
    background-color: #2C5BA3 !important; /* Biru Laut */
    color: #FFFFFF !important;
    border: 1px solid #1a437e !important;
    border-radius: 5px !important;
}
div[role="option"] {
    background-color: #2C5BA3 !important; /* Biru Laut */
    color: #FFFFFF !important;
}
div[role="option"]:hover {
    background-color: #1a437e !important; /* Biru tua saat hover */
}
/* Pastikan teks di dalam opsi juga benar */
div[role="option"] > div > span {
    color: #FFFFFF !important;
}

/* Opsi yang sudah dipilih dalam multiselect */
.st-emotion-cache-19p087t {
    background-color: #1a437e !important; /* Menggunakan warna yang sedikit lebih gelap */
    color: #ffffff !important;
    border-radius: 3px !important;
}
.st-emotion-cache-19p087t p {
    color: #ffffff !important;
}
/* Tombol hapus di multiselect */
.st-emotion-cache-1049l0r {
    color: #ffffff !important;
}

/* --- Expander (diperbarui) --- */
/* Header Expander */
.streamlit-expanderHeader {
    background-color: #2C5BA3 !important; /* Biru Laut */
    color: #ffffff !important;
    border-radius: 5px !important;
    font-weight: bold !important;
    padding: 10px !important;
    border: 1px solid #1a437e !important;
}
/* Konten Expander (bagian dalam) */
.streamlit-expanderContent {
    background-color: #ffffff !important;
    padding: 15px !important;
    border-bottom-left-radius: 5px !important;
    border-bottom-right-radius: 5px !important;
    border: 1px solid #e8f0f8;
    border-top: none;
}

/* --- Menghilangkan Elemen Bawaan Streamlit --- */
#MainMenu, footer {
    visibility: hidden !important;
    height: 0px !important;
}

/* --- Mengatur Lebar Konten Utama & Responsif --- */
.block-container {
    max-width: 900px !important;
    margin: auto !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-top: 1rem !important;
}

@media (max-width: 768px) {
    .stApp {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    .block-container {
        max-width: 100% !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    h1 {
        font-size: 1.8rem !important;
        padding-bottom: 10px !important;
    }
    h3 {
        font-size: 1.2rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ==================== Main Streamlit App ====================

st.title("📊 Kalkulator Proyeksi Investasi Multi-Aset")
st.markdown("""
<div style="font-size: 14px; color: #666; text-align: center;">
    Kalkulator ini membantu Anda memproyeksikan nilai investasi di masa depan berdasarkan aset yang Anda miliki atau rekomendasi portofolio.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Bagian Penjelasan Investasi
with st.expander("📚 Belajar Investasi: Mulai dari Aset hingga Strategi"):
    st.write("### 💰 Apa Itu Investasi?")
    st.write("Investasi adalah kegiatan menempatkan dana atau aset dengan harapan mendapatkan keuntungan di masa depan. Ada berbagai jenis instrumen investasi dengan tingkat risiko dan potensi keuntungan yang berbeda.")
    
    st.write("---")
    st.write("### 📈 Berbagai Instrumen Investasi")
    st.write("#### **1. Reksadana**")
    st.write("Wadah untuk mengumpulkan dana dari banyak investor untuk diinvestasikan dalam portofolio efek oleh Manajer Investasi. Cocok untuk pemula karena dikelola profesional dan diversifikasinya bagus.")
    st.write("#### **2. Saham & ETF**")
    st.write("**Saham** adalah bukti kepemilmam atas sebuah perusahaan. **ETF (Exchange Traded Fund)** adalah reksadana yang diperdagangkan seperti saham. Keduanya menawarkan potensi pertumbuhan tinggi.")
    st.write("#### **3. Obligasi**")
    st.write("Surat utang yang diterbitkan oleh pemerintah atau perusahaan. Investor akan mendapatkan imbal hasil (kupon) secara berkala. Risiko lebih rendah dari saham.")
    
    st.write("---")
    st.write("### 🏛️ Detail Khusus: Obligasi Pemerintah (SBN & FR)")
    st.write("#### **Surat Berharga Negara (SBN) Ritel**")
    st.write("Dikeluarkan oleh pemerintah untuk investor individu. Sangat aman dan kuponnya pasti.")
    st.markdown("- **ORI (Obligasi Negara Ritel)**: Kupon tetap, bisa diperdagangkan.")
    st.markdown("- **SBR (Savings Bond Ritel)**: Kupon mengambang, tidak bisa diperdagangkan.")
    st.markdown("- **SR (Sukuk Ritel)**: Obligasi Syariah dengan imbal hasil tetap, bisa diperdagangkan.")
    st.write("#### **Obligasi FR (Fixed Rate)**")
    st.write("Obligasi yang diperdagangkan di pasar sekunder dengan kupon tetap. Nilainya bisa naik-turun tergantung pergerakan suku bunga.")
    
    st.write("---")
    st.write("### 📊 Perbandingan Risiko & Keuntungan")
    risk_return = pd.DataFrame({
        'Aset': ['Reksadana Pasar Uang', 'Obligasi', 'Emas', 'Properti', 'Reksadana Saham', 'Saham', 'Crypto'],
        'Risiko': [1, 2, 3, 4, 4, 5, 5],
        'Potensi Keuntungan': [1, 2, 2.5, 3.5, 4, 4.5, 5]
    })
    
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.scatter(risk_return['Risiko'], risk_return['Potensi Keuntungan'], s=200, color='#2c5ba3', alpha=0.8)
    for i, txt in enumerate(risk_return['Aset']):
        ax.annotate(txt, (risk_return['Risiko'][i]+0.1, risk_return['Potensi Keuntungan'][i]), fontsize=10)
    
    ax.set_title('Hubungan Risiko vs. Potensi Keuntungan', fontsize=16)
    ax.set_xlabel('Tingkat Risiko (Skala 1-5)', fontsize=12)
    ax.set_ylabel("Potensi Keuntungan (Skala 1-5)", fontsize=12)
    ax.grid(True)
    st.pyplot(fig)


st.markdown("---")

st.subheader("⚠️ Cek Kesiapan Finansial")
col_c1, col_c2 = st.columns(2)
with col_c1:
    siap_tabungan = st.checkbox("Saya punya tabungan minimal Rp10.000.000", value=True)
with col_c2:
    siap_darurat = st.checkbox("Saya punya dana darurat minimal 3 bulan", value=True)
if not (siap_tabungan and siap_darurat):
    st.warning("Prioritaskan dana darurat & tabungan dulu. Rekomendasi akan difokuskan ke risiko RENDAH.")

st.markdown("---")

st.subheader("⚙️ Asumsi & Parameter Dasar")
col1, col2, col3 = st.columns(3)
with col1:
    inflasi = st.number_input("Asumsi inflasi tahunan (%)", min_value=0.0, value=4.0) / 100.0
with col2:
    tahun_beli = st.number_input("Tahun beli", value=datetime.now().year, format="%d")
with col3:
    tahun_target = st.number_input("Tahun target proyeksi", value=tahun_beli + 10, format="%d")

tahun_ke = max(0, tahun_target - tahun_beli)

usd_idr, fx_src = fetch_usd_idr()
if not usd_idr:
    usd_idr = st.number_input("Masukkan kurs USD/IDR manual", value=16000.0)
else:
    st.info(f"Kurs USD/IDR otomatis: {usd_idr:,.0f} ({fx_src})")

gold_idr_per_gram = st.number_input("Harga emas per gram (Rp)", value=1_200_000.0)
gold_src = "Manual"

btc_rate = st.number_input("Asumsi pertumbuhan BTC per tahun (%)", value=25.0) / 100.0

tab1, tab2, tab3 = st.tabs(["Kalkulator Aset Dimiliki", "Simulasi Portofolio Baru", "Tanya Jawab Investasi"])

with tab1:
    st.subheader("📝 Input Aset yang Anda Miliki")
    owned_values = {}
    owned_rates = {}
    owned_sources = {}
    owned = st.multiselect(
        "Pilih aset yang Anda miliki",
        ["Tanah", "Emas", "Crypto-BTC", "Crypto-ETH", "Crypto-SOL", "Crypto-XRP", "Crypto-BNB",
         "Saham-BBCA", "Saham-BMRI", "Saham-BBRI", "Saham-AAPL", "ETF-SPY", "ETF-QQQ", "Obligasi", "Deposito",
         "Reksadana Pasar Uang", "Reksadana Pendapatan Tetap", "Reksadana Saham",
         "Reksadana Campuran"]
    )

    with st.expander("Isi detail aset yang dipilih"):
        if "Tanah" in owned:
            st.write("---")
            st.write("### Tanah")
            wilayah = st.selectbox("Pilih wilayah", ["Jakarta", "Bandung", "Karawang", "Cikarang", "Bekasi", "Tangerang", "Custom"])
            wilayah_key = "Tanah-" + wilayah
            rate_tanah = st.number_input(f"Asumsi pertumbuhan tahunan {wilayah} (%)", value=rate_default.get(wilayah_key, 0.07) * 100) / 100.0
            luas = st.number_input("Luas tanah (m²)", value=100.0)
            harga_m2 = st.number_input("Harga awal per m² (Rp)", value=3_500_000, format="%d")
            biaya = st.number_input("Biaya tambahan (BPHTB/Notaris, Rp)", value=0, format="%d")
            nilai_awal = luas * harga_m2 + biaya
            owned_values[wilayah_key] = nilai_awal
            owned_rates[wilayah_key] = rate_tanah
            owned_sources[wilayah_key] = "Manual"

        if "Emas" in owned:
            st.write("---")
            st.write("### Emas")
            gram = st.number_input("Berat emas (gram)", value=10.0)
            nilai_awal = gram * gold_idr_per_gram
            owned_values["Emas"] = nilai_awal
            owned_rates["Emas"] = rate_default["Emas"]
            owned_sources["Emas"] = gold_src

        crypto_owned = [a for a in owned if a.startswith("Crypto-")]
        if crypto_owned:
            st.write("---")
            st.write("### Crypto")
            crypto_usd, cg_src = fetch_crypto_usd([cg_ids_map[a] for a in crypto_owned if a in cg_ids_map])
            for label in crypto_owned:
                cid = cg_ids_map.get(label)
                st.write(f"**{label}**")
                usd_price = crypto_usd.get(cid)
                if not usd_price:
                    usd_price = st.number_input(f"Harga {label} per coin (USD)", key=f"crypto_price_{label}", value=1000.0)
                else:
                    st.info(f"Harga otomatis {label}: ${usd_price:,.2f} ({cg_src})")
                jumlah = st.number_input(f"Jumlah {label}", key=f"crypto_jumlah_{label}", value=0.1 if "ETH" in label else (1.0 if "SOL" in label else 0.01))
                nilai_awal = jumlah * usd_price * usd_idr
                rate_coin = btc_rate * crypto_ratios.get(label, 1.0)
                owned_values[label] = nilai_awal
                owned_rates[label] = rate_coin
                owned_sources[label] = cg_src or "Manual"

        stock_map = {"Saham-BBCA": "BBCA.JK", "Saham-BMRI": "BMRI.JK", "Saham-BBRI": "BBRI.JK", "Saham-AAPL": "AAPL"}
        for label, ticker in stock_map.items():
            if label in owned:
                st.write("---")
                st.write(f"### {label}")
                h, src = fetch_yahoo_last_price(ticker)
                
                yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"
                
                if not h:
                    h_idr = st.number_input("Harga per unit (Rp)", key=f"stock_price_{label}", value=1000, format="%d")
                else:
                    h_idr = h * (usd_idr if "AAPL" in label else 1)
                    st.info(f"Harga otomatis {label}: Rp{h_idr:,.0f} ({src}) - [Cek di Yahoo Finance]({yahoo_link})")
                
                lot = st.number_input("Jumlah unit", key=f"stock_unit_{label}", value=1, format="%d")
                nilai_awal = lot * (100 if "Saham-" in label else 1) * h_idr
                owned_values[label] = nilai_awal
                owned_rates[label] = rate_default[label]
                owned_sources[label] = src or "Manual"
                
        etf_map = {"ETF-SPY": "SPY", "ETF-QQQ": "QQQ"}
        for label, ticker in etf_map.items():
            if label in owned:
                st.write("---")
                st.write(f"### {label}")
                h, src = fetch_yahoo_last_price(ticker)

                yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"

                if not h:
                    h_idr = st.number_input("Harga per unit (Rp)", key=f"etf_price_{label}", value=1000, format="%d")
                else:
                    h_idr = h * usd_idr
                    st.info(f"Harga otomatis {label}: Rp{h_idr:,.0f} ({src}) - [Cek di Yahoo Finance]({yahoo_link})")

                unit = st.number_input("Jumlah unit", key=f"etf_unit_{label}", value=1, format="%d")
                nilai_awal = unit * h_idr
                owned_values[label] = nilai_awal
                owned_rates[label] = rate_default[label]
                owned_sources[label] = src or "Manual"

        for rname in ["Obligasi", "Deposito", "Reksadana Pasar Uang", "Reksadana Pendapatan Tetap", "Reksadana Saham", "Reksadana Campuran"]:
            if rname in owned:
                st.write("---")
                st.write(f"### {rname}")
                nominal = st.number_input("Nominal awal (Rp)", key=f"nominal_{rname}", value=10_000_000, format="%d")
                owned_values[rname] = nominal
                owned_rates[rname] = rate_default[rname]
                owned_sources[rname] = "Manual"

    if st.button("Hitung Proyeksi Aset Dimiliki"):
        if owned_values:
            rows = {}
            for aset, h0 in owned_values.items():
                r = owned_rates.get(aset, 0.05)
                years = list(range(1, tahun_ke + 1))
                nominal_values = [proj(h0, r, y) for y in years]
                real_values = [realval(n, y, inflasi) for y, n in zip(years, nominal_values)]
                
                rows[aset] = {
                    "Nilai Awal (Rp)": h0,
                    f"Nilai di {tahun_target} (Rp)": nominal_values[-1] if nominal_values else h0,
                    f"Real di {tahun_target} (Rp)": real_values[-1] if real_values else h0,
                    "CAGR (%)": cagr(h0, nominal_values[-1] if nominal_values else h0, tahun_ke) * 100
                }
            df_owned = pd.DataFrame(rows).T.sort_values(by=f"Nilai di {tahun_target} (Rp)", ascending=False)
            
            st.subheader("=== RINGKASAN ASET DIMILIKI ===")
            st.dataframe(beautify(df_owned))
            
            st.subheader("Visualisasi Proyeksi Aset (Line Chart)")
            fig, ax = plt.subplots(figsize=(12, 7))
            
            for aset in owned_values:
                h0 = owned_values[aset]
                r = owned_rates.get(aset, 0.05)
                
                years_axis = list(range(tahun_beli, tahun_target + 1))
                nominal_values = [proj(h0, r, y - tahun_beli) for y in years_axis]
                real_values = [realval(n, y - tahun_beli, inflasi) for y, n in zip(years_axis, nominal_values)]

                ax.plot(years_axis, nominal_values, label=f'{aset} (Nominal)', marker='o', linestyle='-')
                ax.plot(years_axis, real_values, label=f'{aset} (Real)', marker='x', linestyle='--')
            
            ax.set_title("Proyeksi Nilai Aset Nominal vs. Real", fontsize=16)
            ax.set_xlabel("Tahun", fontsize=12)
            ax.set_ylabel("Nilai (Rp)", fontsize=12)
            ax.grid(True)
            ax.legend()
            
            st.pyplot(fig)
            
        else:
            st.info("Tidak ada aset yang diinput.")

with tab2:
    st.subheader("💼 Simulasi Portofolio Baru")
    col4, col5 = st.columns(2)
    with col4:
        # Perbaikan di sini: nilai default diubah menjadi integer
        modal_baru = st.number_input("Modal yang akan diinvestasikan (Rp)", value=100_000_000, format="%d")
    with col5:
        hold_thn = st.number_input("Lama hold (tahun)", value=3, format="%d")

    def rate_for_label(label):
        if label.startswith("Crypto-"):
            return btc_rate * crypto_ratios.get(label, 1.0)
        if label.startswith("Tanah-"):
            return rate_default.get(label, rate_default["Tanah-Custom"])
        return rate_default.get(label, 0.05)

    def simulate_portfolio(allocation_dict, capital, years):
        total_nominal_akhir = 0.0
        total_awal = capital
        breakdown = []
        for aset, pct in allocation_dict.items():
            nominal_awal = capital * (pct / 100.0)
            r = rate_for_label(aset)
            nominal_akhir = nominal_awal * ((1 + r) ** years)
            pajak_key = aset.split("-")[0] if "-" in aset else aset
            nominal_akhir_after_tax = nominal_akhir * (1 - pajak.get(pajak_key, 0))
            total_nominal_akhir += nominal_akhir_after_tax
            breakdown.append({
                "Aset": aset, "Alokasi (%)": pct, "Rate (%)": r * 100,
                "Nilai Akhir (Rp)": nominal_akhir_after_tax
            })
        real = total_nominal_akhir / ((1 + inflasi) ** years)
        return {
            "Nilai Awal (Rp)": total_awal,
            f"Nilai Akhir {tahun_beli + years} (Rp)": total_nominal_akhir,
            "Real (setelah inflasi)": real,
            "Profit (Rp)": total_nominal_akhir - total_awal,
            "Profit (%)": (total_nominal_akhir / total_awal - 1) if total_awal > 0 else 0,
            "CAGR (%)": cagr(total_awal, total_nominal_akhir, years) * 100
        }, pd.DataFrame(breakdown)

    portfolio_options = {
        "Rendah": {
            "Opsi 1": {"Obligasi": 50, "Emas": 30, "Reksadana Pasar Uang": 20},
            "Opsi 2": {"Reksadana Pendapatan Tetap": 50, "Deposito": 30, "Emas": 20},
            "Opsi 3": {"Obligasi": 40, "Reksadana Pasar Uang": 40, "Emas": 20},
        },
        "Sedang": {
            "Opsi 1": {"Saham-BBCA": 30, "Reksadana Campuran": 30, "Emas": 20, "Obligasi": 20},
            "Opsi 2": {"Obligasi": 40, "Reksadana Saham": 40, "Emas": 20},
            "Opsi 3": {"ETF-SPY": 30, "ETF-QQQ": 30, "Emas": 20, "Reksadana Campuran": 20},
        },
        "Tinggi": {
            "Opsi 1": {"Crypto-BTC": 40, "Crypto-ETH": 30, "Saham-AAPL": 30},
            "Opsi 2": {"Crypto-BTC": 40, "Crypto-ETH": 30, "Crypto-SOL": 20, "Emas": 10},
            "Opsi 3": {"Crypto-BTC": 35, "Crypto-ETH": 25, "Crypto-XRP": 20, "Crypto-BNB": 10, "ETF-QQQ": 10},
        }
    }

    prefer_category = "Rendah" if not (siap_tabungan and siap_darurat) else None
    order = ["Rendah", "Sedang", "Tinggi"]

    if st.button("Jalankan Simulasi Portofolio"):
        all_results = {}
        for kategori, opsi_map in portfolio_options.items():
            all_results[kategori] = {}
            for opsi, alloc in opsi_map.items():
                summary, breakdown = simulate_portfolio(alloc, modal_baru, hold_thn)
                all_results[kategori][opsi] = (summary, breakdown)

        for cat in order:
            st.markdown("---")
            st.subheader(f"=== REKOMENDASI - PROFIL RISIKO {cat.upper()} ===")

            ringkas_rows = {}
            for opsi, (summary, breakdown) in all_results[cat].items():
                ringkas_rows[opsi] = summary
            df_ringkas = pd.DataFrame(ringkas_rows).T
            label_col = [c for c in df_ringkas.columns if "Nilai Akhir" in c][0]
            df_ringkas = df_ringkas.sort_values(by=label_col, ascending=False)
            st.dataframe(beautify(df_ringkas))
            
            with st.expander(f"Lihat Rincian ({cat})"):
                for opsi, (summary, breakdown) in all_results[cat].items():
                    st.write(f"#### Rincian {opsi}")
                    
                    labels = list(portfolio_options[cat][opsi].keys())
                    sizes = list(portfolio_options[cat][opsi].values())
                    
                    fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
                    ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
                    ax_pie.axis('equal')
                    ax_pie.set_title(f"Alokasi Aset {opsi}")
                    st.pyplot(fig_pie)
                    
                    st.dataframe(beautify(breakdown))

            fig, ax = plt.subplots(figsize=(9, 5))
            vals = df_ringkas[label_col].sort_values(ascending=False)
            ax.bar(vals.index, vals.values, color='#2c5ba3')
            ax.set_title(f"Perbandingan Nilai Akhir - Risiko {cat} (Hold {hold_thn} thn, Modal {fmt_money(modal_baru)})")
            ax.set_ylabel("Nilai Akhir (Rp)")
            plt.xticks(rotation=0)
            st.pyplot(fig)

with tab3:
    st.subheader("❓ Tanya Jawab Investasi")
    st.info("Pilih topik di bawah ini untuk mendapatkan jawaban cepat dan akurat.")

    # --- Opsi 1: Pertanyaan Spesifik dengan Jawaban Langsung ---
    faqs = {
        "Apa itu saham?": "Saham adalah bukti kepemilikan Anda terhadap sebuah perusahaan. Ketika Anda membeli saham, Anda menjadi salah satu pemiliknya dan berhak atas sebagian keuntungan (dividen) serta kenaikan nilai perusahaan.",
        "Apa itu obligasi?": "Obligasi adalah surat utang yang diterbitkan oleh pemerintah atau perusahaan. Ketika Anda membeli obligasi, Anda meminjamkan uang kepada penerbit dan akan mendapatkan bunga (kupon) secara berkala.",
        "Apa bedanya saham dan obligasi?": "Saham adalah bukti kepemilikan, sementara obligasi adalah surat utang. Saham memiliki risiko lebih tinggi namun potensi keuntungan lebih besar. Obligasi lebih stabil namun keuntungannya lebih terbatas.",
        "Apa itu CAGR?": "CAGR adalah singkatan dari Compound Annual Growth Rate, atau Tingkat Pertumbuhan Tahunan Majemuk. Ini adalah rata-rata tingkat pertumbuhan tahunan yang dihitung dari suatu investasi dalam periode waktu tertentu. CAGR membantu mengukur seberapa efektif investasi tumbuh dari waktu ke waktu.",
        "Apa itu Inflasi?": "Inflasi adalah kenaikan harga barang dan jasa secara umum dan terus-menerus. Inflasi dapat mengurangi daya beli uang, yang berarti nilai riil investasi Anda juga bisa berkurang jika keuntungannya lebih kecil dari tingkat inflasi.",
        "Urutan investasi dari risiko rendah ke tinggi?": "Secara umum, urutan investasi dari risiko rendah ke tinggi adalah: **Deposito** → **Reksadana Pasar Uang** → **Obligasi Pemerintah** → **Reksadana Pendapatan Tetap** → **Emas** → **Properti** → **Reksadana Campuran** → **Reksadana Saham** → **Saham** → **Crypto**.",
        "Berapa dana darurat yang ideal?": "Dana darurat yang ideal adalah dana yang bisa menutupi biaya hidup Anda selama **3 hingga 6 bulan**, atau bahkan lebih, tergantung pekerjaan dan tanggungan Anda. Dana ini harus disimpan di instrumen yang mudah dicairkan seperti tabungan atau reksadana pasar uang.",
        "Kenapa investasi saham berisiko?": "Investasi saham berisiko karena nilainya bisa berfluktuasi tajam. Performa perusahaan, kondisi ekonomi, dan sentimen pasar dapat memengaruhi harga saham, yang bisa menyebabkan kerugian jika Anda menjual saat harga sedang turun.",
        "Apa itu diversifikasi?": "Diversifikasi adalah strategi mengalokasikan investasi ke berbagai jenis aset untuk mengurangi risiko. Tujuannya adalah agar kerugian di satu aset dapat diimbangi oleh keuntungan di aset lain.",
        "Apakah berinvestasi di crypto itu aman?": "Berinvestasi di crypto memiliki risiko yang sangat tinggi karena harganya sangat fluktuatif. Keuntungannya bisa sangat besar, tetapi potensi kerugiannya juga tinggi. Investasi ini cocok untuk investor dengan profil risiko tinggi."
    }

    # Tampilkan tombol-tombol pertanyaan
    cols = st.columns(2)
    current_col = 0
    if 'answer' not in st.session_state:
        st.session_state['answer'] = None
    
    for question, answer in faqs.items():
        with cols[current_col]:
            if st.button(question, use_container_width=True):
                st.session_state['answer'] = answer
        current_col = (current_col + 1) % 2
    
    st.markdown("---")
    
    # Tampilkan jawaban jika tombol diklik
    if st.session_state['answer']:
        st.success(f"**Jawaban:**\n\n{st.session_state['answer']}")
    
    # --- Opsi 2: Arahkan ke AI Fleksibel (Gemini) ---
    st.markdown("---")
    st.subheader("Butuh jawaban yang lebih fleksibel?")
    st.write("Jika pertanyaan Anda tidak ada di daftar, Anda bisa menggunakan AI lain untuk bantuan.")
    st.markdown("[Klik di sini untuk mengakses Google Gemini](https://gemini.google.com/app)", unsafe_allow_html=True)
    st.markdown("[Klik di sini untuk mengakses IBM Granite Playground](https://www.ibm.com/granite/playground/)", unsafe_allow_html=True)
    st.info("*(Tautan ini akan membuka halaman AI di tab baru. Anda bisa bertanya apa saja, termasuk topik investasi.)*")
