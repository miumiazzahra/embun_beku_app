"""
Logika inti (TANPA Streamlit): cleaning, fitur, label, agregasi.

Isinya sama persis dengan notebook Pipeline_Embun_Beku.ipynb. Kalau kamu mengubah
aturan di notebook (misal ambang atau jam jendela), ubah juga di sini.
"""
import numpy as np
import pandas as pd

AMBANG_SUHU_DEFAULT = 2.0
JAM_DINI = ("00:00", "07:50")      # jendela dini hari yang dilabeli (WIB)
JAM_SORE = ("15:00", "21:00")      # jendela data yang dipakai untuk memprediksi (WIB)
MIN_DATA_DINI = 30
RH_MIN_VALID = 20
MIN_DATA_SORE_APP = 30             # aplikasi minta minimal 30 dari 37 data sore agar prediksi layak

KOLOM = {"tt_air_avg": "T",        # suhu udara (°C)
         "rh_avg": "RH",           # kelembapan (%)
         "ws_avg": "WS",           # kecepatan angin (m/s)
         "wd_avg": "WD",           # arah angin (derajat)
         "sr_avg": "SR",           # radiasi matahari
         "rr": "RR"}               # curah hujan
KOLOM_WAJIB = ["Tanggal", "tt_air_avg", "rh_avg", "ws_avg"]


# ---------------------------------------------------------------- rumus dasar
def titik_embun(T, RH):
    """Titik embun (Magnus-Tetens, bentuk standar). T dalam °C, RH dalam %."""
    a, b = 17.625, 243.04
    gamma = np.log(RH / 100) + a * T / (b + T)
    return b * gamma / (a - gamma)


def hitung_status_jurnal(df, ambang=AMBANG_SUHU_DEFAULT):
    """Status pemantauan langsung ala jurnal ELKOMIKA (kondisi SAAT INI, bukan prediksi)."""
    dingin = df["T"] <= ambang
    status = np.select(
        [dingin & (df["WS"] <= 5) & (df["RH"] >= 60), dingin & (df["WS"] <= 5), dingin],
        ["Awas", "Siaga", "Waspada"], default="Normal")
    status = pd.Series(status, index=df.index)
    status[df["T"].isna()] = "Tidak ada data"
    return status


def tingkat_risiko(p, ambang):
    """Bagi rentang [ambang, 1] menjadi 3 tingkat. Ini tingkat risiko dari model, bukan standar resmi BMKG."""
    if p < ambang:
        return "Tidak berpotensi"
    batas = (1 - ambang) / 3
    if p < ambang + batas:
        return "Waspada"
    if p < ambang + 2 * batas:
        return "Siaga"
    return "Awas"


# -------------------------------------------------------------------- cleaning
def bersihkan_data(raw, zona="UTC", ambang=AMBANG_SUHU_DEFAULT):
    """
    raw  : DataFrame hasil ekspor AWS (kolom Tanggal, tt_air_avg, rh_avg, ws_avg, ...)
    zona : zona waktu kolom Tanggal, "UTC" (default ekspor AWS) atau "WIB"
    Hasil: DataFrame index waktu WIB (grid 10 menit), kolom T, RH, WS, WD, SR, RR, Td, status_jurnal
    """
    hilang = [k for k in KOLOM_WAJIB if k not in raw.columns]
    if hilang:
        raise ValueError("Kolom wajib tidak ditemukan: " + ", ".join(hilang))

    ada = [k for k in KOLOM if k in raw.columns]
    d = raw[["Tanggal"] + ada].rename(columns=KOLOM)
    for kol in KOLOM.values():
        if kol not in d.columns:
            d[kol] = np.nan

    waktu = pd.to_datetime(d["Tanggal"].astype(str).str[:19], errors="coerce")
    if zona == "UTC":
        waktu = waktu + pd.Timedelta(hours=7)
    d = d.drop(columns="Tanggal")
    d["waktu_wib"] = waktu.dt.round("10min")
    d = d[d["waktu_wib"].notna()]
    if d.empty:
        raise ValueError("Kolom Tanggal tidak bisa dibaca sebagai tanggal-waktu.")

    for kol in KOLOM.values():
        d[kol] = pd.to_numeric(d[kol], errors="coerce")
    d = d.drop_duplicates("waktu_wib").sort_values("waktu_wib").set_index("waktu_wib")

    # grid 10 menit lengkap
    grid = pd.date_range(d.index.min().normalize(), d.index.max(), freq="10min")
    d = d.reindex(grid)
    d.index.name = "waktu_wib"

    # buang nilai error sensor
    d.loc[~d["T"].between(-5, 30), "T"] = np.nan
    siang_hari = (d.index.hour >= 9) & (d.index.hour <= 17)
    d.loc[siang_hari & (d["T"] < 6), "T"] = np.nan
    d.loc[d["RH"].between(100, 101), "RH"] = 100
    d.loc[~d["RH"].between(RH_MIN_VALID, 100), "RH"] = np.nan
    d.loc[~d["WS"].between(0, 30), "WS"] = np.nan
    d.loc[~d["WD"].between(0, 360), "WD"] = np.nan
    d.loc[~d["SR"].between(0, 1500), "SR"] = np.nan
    d.loc[~d["RR"].between(0, 100), "RR"] = np.nan

    median_lokal = d["T"].rolling(7, center=True, min_periods=3).median()
    d.loc[(d["T"] - median_lokal).abs() > 3, "T"] = np.nan

    # isi celah pendek (maks 30 menit)
    for kol in ["T", "RH", "WS", "SR"]:
        d[kol] = d[kol].interpolate(limit=3, limit_area="inside")

    d["Td"] = titik_embun(d["T"], d["RH"])
    d["status_jurnal"] = hitung_status_jurnal(d, ambang)
    return d


# ------------------------------------------------------- label & fitur (model)
def tabel_dini(df, ambang=AMBANG_SUHU_DEFAULT):
    """Suhu minimum dini hari per tanggal + label berpotensi (1/0, NaN kalau data kurang)."""
    dini = df.between_time(JAM_DINI[0], JAM_DINI[1])
    g = dini["T"].groupby(dini.index.normalize())
    hasil = pd.DataFrame({"T_min_dini": g.min(), "jml_data": g.count()})
    hasil.loc[hasil["jml_data"] < MIN_DATA_DINI, "T_min_dini"] = np.nan
    hasil["berpotensi"] = (hasil["T_min_dini"] <= ambang).astype(float)
    hasil.loc[hasil["T_min_dini"].isna(), "berpotensi"] = np.nan
    return hasil


def buat_fitur(d):
    """Ringkas data 10 menit (index = waktu WIB) menjadi satu baris fitur per tanggal."""
    sore = d.between_time(JAM_SORE[0], JAM_SORE[1])
    t = sore.index.normalize()
    f = pd.DataFrame({
        "T_15":         sore["T"].groupby(t).first(),
        "T_21":         sore["T"].groupby(t).last(),
        "T_min_sore":   sore["T"].groupby(t).min(),
        "T_mean_sore":  sore["T"].groupby(t).mean(),
        "RH_21":        sore["RH"].groupby(t).last(),
        "RH_mean_sore": sore["RH"].groupby(t).mean(),
        "WS_21":        sore["WS"].groupby(t).last(),
        "WS_mean_sore": sore["WS"].groupby(t).mean(),
        "Td_21":        sore["Td"].groupby(t).last(),
        "n_sore":       sore["T"].groupby(t).count(),
    })
    t18 = d.at_time("18:00")["T"]
    t18.index = t18.index.normalize()
    f["T_turun_3jam"] = t18 - f["T_21"]
    f["T_turun_sore"] = f["T_15"] - f["T_21"]
    f["Selisih_T_Td"] = f["T_21"] - f["Td_21"]

    siang = d.between_time("09:00", "15:00")
    ts = siang.index.normalize()
    f["T_max_siang"] = siang["T"].groupby(ts).max()
    f["SR_mean_siang"] = siang["SR"].groupby(ts).mean()
    f["rentang_harian"] = f["T_max_siang"] - f["T_21"]

    pagi = d.between_time(JAM_DINI[0], JAM_DINI[1])
    tp = pagi.index.normalize()
    f["T_min_dini_hari_ini"] = pagi["T"].groupby(tp).min()

    f["bulan"] = f.index.month
    return f[f["n_sore"] >= 20]


def hari_siap(f):
    """Tanggal yang datanya cukup untuk dipakai memprediksi."""
    ok = (f["n_sore"] >= MIN_DATA_SORE_APP) & f["T_21"].notna() & f["RH_21"].notna()
    return f[ok]


def waktu_data_sore_terakhir(df, tanggal):
    """Waktu data suhu valid terakhir di jendela sore (untuk mendeteksi data yang belum sampai ~21.00)."""
    t0 = pd.Timestamp(tanggal).normalize()
    w = df.loc[t0 + pd.Timedelta(hours=15): t0 + pd.Timedelta(hours=21), "T"].dropna()
    return w.index.max() if len(w) else None


def prediksi(f, tanggal, paket):
    """Prediksi dini hari BESOK dari fitur tanggal `tanggal`."""
    tanggal = pd.Timestamp(tanggal).normalize()
    if tanggal not in f.index:
        raise KeyError("Tanggal tidak punya data sore yang cukup.")
    baris = f.loc[[tanggal], paket["fitur"]]
    p = float(paket["model"].predict_proba(baris)[0, 1])
    ambang = paket["ambang_prob"]
    r = f.loc[tanggal]
    return {
        "tanggal_data": tanggal,
        "untuk_dini_hari": tanggal + pd.Timedelta(days=1),
        "probabilitas": p,
        "ambang": ambang,
        "prediksi": "Berpotensi" if p >= ambang else "Tidak berpotensi",
        "tingkat": tingkat_risiko(p, ambang),
        "T_21": float(r["T_21"]), "RH_21": float(r["RH_21"]),
        "WS_21": None if pd.isna(r["WS_21"]) else float(r["WS_21"]),
        "Td_21": None if pd.isna(r["Td_21"]) else float(r["Td_21"]),
    }


# -------------------------------------------------------------- agregasi dashboard
def buat_agregasi(df, ambang=AMBANG_SUHU_DEFAULT):
    """Tabel harian, mingguan, bulanan, tahunan untuk dashboard (nilai ekstrem + jam kejadian)."""
    dini = tabel_dini(df, ambang)
    tgl = df.index.normalize()

    # titik embun hanya dilihat malam-pagi (18.00-07.50 WIB); siang hari RH kering membuatnya menyesatkan
    malam = (df.index.hour >= 18) | (df.index.hour <= 7)
    td_malam = df["Td"].where(malam)

    harian = df.groupby(tgl).agg(T_min=("T", "min"), T_max=("T", "max"), T_mean=("T", "mean"),
                                 RH_mean=("RH", "mean"), WS_max=("WS", "max"), n_data=("T", "count"))
    harian["Td_min"] = td_malam.groupby(tgl).min()

    t_valid = df["T"].dropna()
    td_valid = td_malam.dropna()
    harian["jam_T_min"] = t_valid.groupby(t_valid.index.normalize()).idxmin().dt.strftime("%H:%M")
    harian["jam_Td_min"] = td_valid.groupby(td_valid.index.normalize()).idxmin().dt.strftime("%H:%M")
    harian["T_min_dini"] = dini["T_min_dini"]
    harian["berpotensi_aktual"] = dini["berpotensi"]
    harian = harian[harian["n_data"] > 0]

    def rekap(h, aturan):
        r = h.resample(aturan).agg({"T_min": "min", "T_max": "max", "T_mean": "mean",
                                    "Td_min": "min", "RH_mean": "mean", "WS_max": "max"})
        r["hari_berpotensi"] = h["berpotensi_aktual"].resample(aturan).sum()
        return r.round(2)

    return (harian.round(2), rekap(harian, "W"), rekap(harian, "MS"), rekap(harian, "YS"))
