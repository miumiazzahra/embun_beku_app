from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from components.charts import gauge_skor, grafik_hari
from components.notifikasi import (IKON, REKOMENDASI, WARNA, catat_riwayat, pesan_peringatan,
                                   tampilkan_banner, tgl_id)
from core import data as dt
from core import pipeline as pl
from core.config import CONTOH_DIR
from core.model import muat_model


# ----------------------------------------------------------------------------- tampilan hasil
def _hitung_dan_tampil(df, f, tanggal, paket, sumber, sampai_besok=False):
    ambang_suhu = paket["ambang_suhu"]
    hasil = pl.prediksi(f, tanggal, paket)
    hasil["sumber"] = sumber

    terakhir = pl.waktu_data_sore_terakhir(df, tanggal)
    if terakhir is not None and (terakhir.hour * 60 + terakhir.minute) < 20 * 60 + 30:
        st.warning(f"Data sore terakhir hanya sampai pukul {terakhir:%H:%M} WIB. Prediksi paling akurat bila data "
                   f"sudah sampai sekitar 21.00 WIB (model memakai suhu/RH pukul 21.00).")

    st.session_state["hasil_terakhir"] = hasil
    baru = catat_riwayat(hasil)

    st.markdown("### Hasil prediksi")
    tampilkan_banner(hasil)
    if baru and hasil["tingkat"] != "Tidak berpotensi":
        st.toast(f"Peringatan: potensi embun beku dini hari {tgl_id(hasil['untuk_dini_hari'])} "
                 f"({hasil['tingkat'].upper()})", icon="⚠️")

    warna = WARNA[hasil["tingkat"]]
    kiri, tengah, kanan = st.columns([1, 1, 1])
    with kiri:
        st.plotly_chart(gauge_skor(hasil["probabilitas"], hasil["ambang"], warna),
                        use_container_width=True, config={"displayModeBar": False})
        st.caption(f"Garis hitam = ambang skor ({hasil['ambang']:.2f}). Skor adalah keluaran model, "
                   f"bukan peluang kejadian yang sudah dikalibrasi.")
    with tengah:
        st.markdown(f"""
        <div class="hasil" style="border-color:{warna}; background:{warna}14;">
            <div class="judul">Prediksi dini hari {tgl_id(hasil['untuk_dini_hari'])}</div>
            <div class="nilai" style="color:{warna};">{IKON[hasil['tingkat']]} {hasil['prediksi'].upper()}</div>
            <div class="ket">Tingkat risiko (model): <b>{hasil['tingkat']}</b></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        st.info(f"**Saran:** {REKOMENDASI[hasil['tingkat']]}")
    with kanan:
        st.markdown(f"**Kondisi {tgl_id(hasil['tanggal_data'])}, sekitar 21.00 WIB**")
        a, b = st.columns(2)
        with a:
            st.metric("Suhu", f"{hasil['T_21']:.1f} °C")
            st.metric("Angin", "-" if hasil["WS_21"] is None else f"{hasil['WS_21']:.1f} m/s")
        with b:
            st.metric("Kelembapan", f"{hasil['RH_21']:.0f} %")
            st.metric("Titik embun", "-" if hasil["Td_21"] is None else f"{hasil['Td_21']:.1f} °C")

    st.plotly_chart(grafik_hari(df, tanggal, ambang_suhu, sampai_besok), use_container_width=True)

    if hasil["prediksi"] == "Berpotensi":
        with st.expander("📋 Pesan peringatan siap salin (untuk grup petani / WhatsApp)"):
            st.code(pesan_peringatan(hasil), language=None)

    unduh = {k: (str(v) if isinstance(v, pd.Timestamp) else v) for k, v in hasil.items()}
    st.download_button("⬇️ Unduh hasil (CSV)", data=pd.DataFrame([unduh]).to_csv(index=False),
                       file_name=f"prediksi_{hasil['tanggal_data']:%Y-%m-%d}.csv", mime="text/csv")
    return hasil


def _pemantauan_langsung(df, ambang_suhu):
    """Lapis B: status ala jurnal ELKOMIKA dari data 10 menit terbaru (kondisi saat ini)."""
    st.markdown("### Pemantauan langsung (aturan jurnal)")
    valid = df["T"].dropna()
    if valid.empty:
        st.caption("Tidak ada data suhu valid di file ini.")
        return
    t_akhir = valid.index[-1]
    baris = df.loc[t_akhir]
    status = baris["status_jurnal"]
    rincian = (f"Data terakhir {t_akhir:%d/%m/%Y %H:%M} WIB: suhu {baris['T']:.1f}°C, "
               f"RH {baris['RH']:.0f}%, angin {baris['WS']:.1f} m/s")
    if status == "Awas":
        st.error(f"🔴 **AWAS** (suhu ≤ {ambang_suhu:g}°C, angin ≤ 5 m/s, RH ≥ 60%). {rincian}")
    elif status in ("Siaga", "Waspada"):
        st.warning(f"🟠 **{status.upper()}**. {rincian}")
    else:
        st.success(f"🟢 Normal. {rincian}")

    jendela = df.loc[t_akhir - pd.Timedelta(hours=24): t_akhir, "status_jurnal"].value_counts()
    ringkas = ", ".join(f"{k}: {v}" for k, v in jendela.items() if k in ("Waspada", "Siaga", "Awas"))
    st.caption("24 jam terakhir di file: " + (ringkas + " (jumlah data 10 menit)" if ringkas else "tidak ada kondisi di bawah ambang."))
    st.caption(f"Aturan (Jufri dkk., 2024): Waspada = suhu ≤ {ambang_suhu:g}°C; Siaga = + angin ≤ 5 m/s; "
               f"Awas = + RH ≥ 60%. Ini kondisi yang sedang terjadi, bukan prediksi.")


# ----------------------------------------------------------------------------- mode unggah
def _mode_unggah(paket):
    ambang_suhu = paket["ambang_suhu"]
    st.markdown("Unggah file hasil ekspor AWS Batur **sekali setiap malam, setelah pukul 21.00 WIB**. "
                "Isinya data 10 menit, minimal dari 00.00 sampai ±21.00 WIB. Titik embun dan semua fitur "
                "dihitung otomatis, petugas tidak perlu mengisi apa pun.")

    kiri, kanan = st.columns([2, 1])
    with kanan:
        zona = st.radio("Zona waktu kolom Tanggal", ["UTC", "WIB"],
                        help="Ekspor AWS biasanya berformat UTC (ada '+00' di belakang jam). Pilih WIB bila jam sudah WIB.")
        st.caption("Contoh file untuk mencoba:")
        for nama, label in [("contoh_malam_berpotensi_2023-08-10.csv", "⬇️ Contoh malam dingin (10 Agu 2023)"),
                            ("contoh_malam_aman_2024-02-15.csv", "⬇️ Contoh malam aman (15 Feb 2024)")]:
            berkas = CONTOH_DIR / nama
            if berkas.exists():
                st.download_button(label, data=berkas.read_bytes(), file_name=nama, mime="text/csv", key=f"dl_{nama}")
    with kiri:
        berkas = st.file_uploader("Pilih file CSV atau Excel", type=["csv", "xlsx", "xls"])

    if berkas is None:
        with st.expander("Format file yang diterima"):
            st.markdown(
                "- **Kolom wajib:** `Tanggal`, `tt_air_avg` (suhu), `rh_avg` (kelembapan), `ws_avg` (kecepatan angin)\n"
                "- **Kolom opsional:** `sr_avg` (radiasi), `wd_avg`, `rr`\n"
                "- Satu baris = satu pengamatan 10 menit. File boleh berisi banyak hari.\n"
                "- Format `Tanggal` seperti `2023-08-09 17:00:00+00` (UTC).")
        return

    try:
        bersih, fitur, lap = dt.proses_unggahan(berkas.getvalue(), berkas.name, zona, ambang_suhu)
    except Exception as exc:
        st.error(f"File tidak bisa diproses: {exc}")
        return

    st.session_state["df_unggahan"] = bersih
    st.session_state["nama_unggahan"] = berkas.name
    st.caption(f"📄 {berkas.name} · {lap['baris_file']:,} baris · {lap['awal']:%d/%m/%Y %H:%M} sampai "
               f"{lap['akhir']:%d/%m/%Y %H:%M} WIB · suhu valid {lap['persen_suhu_valid']:.0f}% · "
               f"RH valid {lap['persen_rh_valid']:.0f}%")

    siap = pl.hari_siap(fitur)
    if siap.empty:
        st.warning("Belum ada tanggal dengan data sore (15.00-21.00 WIB) yang cukup. Pastikan file berisi data "
                   "sampai sekitar pukul 21.00 WIB dan zona waktu sudah benar.")
        _pemantauan_langsung(bersih, ambang_suhu)
        return

    terakhir = bersih["T"].dropna().index.max()
    if terakhir.normalize() > siap.index.max() and terakhir.hour >= 15:
        st.info(f"Data tanggal {tgl_id(terakhir)} baru sampai pukul {terakhir:%H:%M} WIB, belum cukup untuk "
                f"prediksi. Prediksi memakai tanggal lengkap terakhir.")

    opsi = list(siap.index[::-1])      # terbaru di atas
    tanggal = st.selectbox("Tanggal data yang dipakai memprediksi (default: terbaru)", opsi,
                           format_func=tgl_id)
    _hitung_dan_tampil(bersih, fitur, tanggal, paket, "Unggahan", sampai_besok=False)
    _pemantauan_langsung(bersih, ambang_suhu)


# ----------------------------------------------------------------------------- mode simulasi
def _mode_simulasi(paket):
    ambang_suhu = paket["ambang_suhu"]
    st.info("Mode simulasi memakai data historis AWS Batur 2021-2025. **Model ini dilatih dengan data yang sama**, "
            "jadi hasil simulasi cenderung lebih bagus daripada kondisi nyata. Untuk performa yang jujur, "
            "lihat halaman Metodologi (validasi leave-one-year-out).")
    df = dt.muat_data_historis()
    f = dt.fitur_historis()
    siap = pl.hari_siap(f)

    awal, akhir = siap.index.min().date(), siap.index.max().date()
    bawaan = date(2023, 8, 10)
    if not (awal <= bawaan <= akhir):
        bawaan = akhir
    tgl = st.date_input("Tanggal data (hari sebelum kejadian yang mau diprediksi)", value=bawaan,
                        min_value=awal, max_value=akhir)
    tanggal = pd.Timestamp(tgl)
    if tanggal not in siap.index:
        st.warning("Tanggal ini tidak punya data sore yang cukup. Coba tanggal lain.")
        return

    hasil = _hitung_dan_tampil(df, f, tanggal, paket, "Simulasi", sampai_besok=True)

    st.markdown("### Kenyataan dini hari berikutnya")
    dini = dt.tabel_dini_historis(ambang_suhu)
    aktual = dini["T_min_dini"].get(hasil["untuk_dini_hari"], np.nan)
    if pd.isna(aktual):
        st.caption("Data dini hari berikutnya tidak lengkap, tidak bisa dibandingkan.")
        return
    nyata = aktual <= ambang_suhu
    prediksi_ya = hasil["prediksi"] == "Berpotensi"
    ringkas = f"Suhu minimum dini hari {tgl_id(hasil['untuk_dini_hari'])}: **{aktual:.1f}°C** " \
              f"({'di bawah' if nyata else 'di atas'} ambang {ambang_suhu:g}°C)."
    if nyata and prediksi_ya:
        st.success(ringkas + " ✅ Model menangkap kejadian ini.")
    elif nyata and not prediksi_ya:
        st.error(ringkas + " ❌ Kejadian terlewat oleh model.")
    elif prediksi_ya:
        st.warning(ringkas + " ⚠️ Alarm meleset (model memprediksi berpotensi, tapi tidak terjadi).")
    else:
        st.success(ringkas + " ✅ Model benar: tidak ada kejadian.")


# ----------------------------------------------------------------------------- halaman
def render_prediksi() -> None:
    paket = muat_model()
    st.markdown("## 🔍 Prediksi Potensi Embun Beku")
    mode = st.radio("Sumber data", ["📤 Unggah file AWS", "🧪 Simulasi dari data historis"], horizontal=True)
    st.markdown("---")
    if mode.startswith("📤"):
        _mode_unggah(paket)
    else:
        _mode_simulasi(paket)
