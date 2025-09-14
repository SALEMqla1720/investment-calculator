import streamlit as st
import requests
import yfinance as yf
from datetime import datetime

# ==================== Helpers & UI Components ====================

def analyze_with_granite(text):
    """
    Simulasi fungsi analisis AI (dari IBM Granite)
    Menganalisis sentimen dari teks input.
    """
    text_lower = text.lower()
    if any(word in text_lower for word in ['naik', 'untung', 'profit', 'membeli', 'bagus', 'bertahan']):
        sentiment = "Positif 😊"
    elif any(word in text_lower for word in ['turun', 'rugi', 'jual', 'fluktuasi', 'resiko']):
        sentiment = "Negatif 😕"
    else:
        sentiment = "Netral 😐"
    words = text.split()
    summary = " ".join(words[:20]) + "..." if len(words) > 20 else text
    return {"sentimen": sentiment, "ringkasan": summary}

def fmt_money(x):
    """
    Fungsi untuk memformat angka menjadi format mata uang Rupiah.
    """
    try:
        return f"Rp{x:,.0f}"
    except:
        return x

def fmt_pct(x):
    """
    Fungsi untuk memformat angka desimal menjadi persentase.
    """
    try:
        return f"{x*100:.2f}%"
    except:
        return x

def beautify(df):
    """
    Fungsi untuk memformat DataFrame menjadi tampilan yang lebih rapi
    dengan format mata uang dan persentase.
    """
    out = df.copy()
    money_cols = [c for c in out.columns if ("Rp" in c) or ("Nilai" in c) or ("Pajak" in c) or (c in ["Real (setelah inflasi)", "Setelah Pajak", "Profit (Rp)"])]
    pct_cols = [c for c in out.columns if ("(%)" in c) or ("Rate (%)" in c)]
    for c in money_cols:
        if c in out.columns:
            out[c] = out[c].apply(lambda v: fmt_money(v))
    for c in pct_cols:
        if c in out.columns:
            out[c] = out[c].apply(lambda v: fmt_pct(v/100.0) if "Rate" in c or "CAGR" in c else fmt_pct(v))
    return out

def proj(h0, r, t):
    """
    Fungsi proyeksi nilai nominal (future value) investasi.
    """
    return h0 * ((1 + r) ** t)

def realval(n, t, inflasi):
    """
    Fungsi menghitung nilai real (setelah inflasi) dari nilai nominal.
    """
    return n / ((1 + inflasi) ** t)

def cagr(h0, hN, t):
    """
    Fungsi menghitung Compound Annual Growth Rate (CAGR).
    """
    if t <= 0 or h0 <= 0:
        return 0.0
    return (hN / h0) ** (1 / t) - 1

@st.cache_data(ttl=3600)
def fetch_usd_idr():
    """Mengambil kurs USD ke IDR dari API eksternal."""
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=IDR", timeout=10)
        r.raise_for_status()
        return float(r.json()["rates"]["IDR"]), "exchangerate.host"
    except Exception:
        return None, None

@st.cache_data(ttl=3600)
def fetch_crypto_usd(ids):
    """Mengambil harga crypto dalam USD dari CoinGecko API."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        r = requests.get(url, params={"ids": ",".join(ids), "vs_currencies": "usd"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        out = {}
        for i in ids:
            if i in data and "usd" in data[i]:
                out[i] = float(data[i]["usd"])
        return out, "CoinGecko"
    except Exception:
        return {}, None

@st.cache_data(ttl=3600)
def fetch_yahoo_last_price(ticker):
    """Mengambil harga penutupan terakhir saham/ETF dari Yahoo Finance."""
    try:
        px = yf.Ticker(ticker).history(period="5d")["Close"]
        return float(px.dropna().iloc[-1]), "Yahoo Finance"
    except Exception:
        return None, None
