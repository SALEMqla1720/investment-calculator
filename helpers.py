import streamlit as st
import requests
import yfinance as yf
from datetime import datetime

# ==================== Helpers & UI Components ====================


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

