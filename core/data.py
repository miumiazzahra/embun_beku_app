"""Pembacaan data: data historis bawaan dan file CSV/Excel yang diunggah petugas."""
import io

import pandas as pd
import streamlit as st

from core import pipeline as pl
from core.config import DATA_FILE


@st.cache_data(show_spinner="Memuat data historis...")
def muat_data_historis():
    df = pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
    df.index.name = "waktu_wib"
    return df


@st.cache_data(show_spinner="Menyiapkan fitur data historis...")
def fitur_historis():
    return pl.buat_fitur(muat_data_historis())


@st.cache_data(show_spinner="Menghitung agregasi dashboard...")
def agregasi_historis(ambang):
    return pl.buat_agregasi(muat_data_historis(), ambang)


@st.cache_data
def tabel_dini_historis(ambang):
    return pl.tabel_dini(muat_data_historis(), ambang)


def baca_file(isi: bytes, nama: str) -> pd.DataFrame:
    """Baca CSV (pemisah koma atau titik-koma) atau Excel dari isi file."""
    if nama.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(isi))
    raw = pd.read_csv(io.BytesIO(isi), low_memory=False)
    if raw.shape[1] == 1:                      # kemungkinan pemisah titik-koma
        raw = pd.read_csv(io.BytesIO(isi), sep=";", low_memory=False)
    return raw


@st.cache_data(show_spinner="Membersihkan data unggahan...")
def proses_unggahan(isi: bytes, nama: str, zona: str, ambang: float):
    """
    Hasil: (data bersih 10 menit, tabel fitur, laporan ringkas).
    Dicache berdasarkan isi file, jadi tidak diulang tiap kali halaman di-refresh.
    """
    raw = baca_file(isi, nama)
    bersih = pl.bersihkan_data(raw, zona=zona, ambang=ambang)
    fitur = pl.buat_fitur(bersih)
    laporan = {
        "baris_file": int(len(raw)),
        "awal": bersih.index.min(),
        "akhir": bersih.index.max(),
        "persen_suhu_valid": float(bersih["T"].notna().mean() * 100),
        "persen_rh_valid": float(bersih["RH"].notna().mean() * 100),
    }
    return bersih, fitur, laporan
