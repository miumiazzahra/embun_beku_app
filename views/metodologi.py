import pandas as pd
import streamlit as st

from components.charts import grafik_batang_horizontal
from core.model import muat_info

DESKRIPSI_FITUR = {
    "T_15": "Suhu pukul 15.00 WIB",
    "T_21": "Suhu pukul ±21.00 WIB (data terakhir di jendela sore)",
    "T_min_sore": "Suhu minimum 15.00-21.00 WIB",
    "T_mean_sore": "Suhu rata-rata 15.00-21.00 WIB",
    "RH_21": "Kelembapan pukul ±21.00 WIB",
    "RH_mean_sore": "Kelembapan rata-rata 15.00-21.00 WIB",
    "WS_21": "Kecepatan angin pukul ±21.00 WIB",
    "WS_mean_sore": "Kecepatan angin rata-rata 15.00-21.00 WIB",
    "Td_21": "Titik embun (Magnus-Tetens) pukul ±21.00 WIB",
    "T_turun_3jam": "Penurunan suhu 18.00 → 21.00 WIB",
    "T_turun_sore": "Penurunan suhu 15.00 → 21.00 WIB",
    "Selisih_T_Td": "Suhu dikurangi titik embun pukul 21.00 (kecil = udara hampir jenuh)",
    "T_max_siang": "Suhu maksimum 09.00-15.00 WIB",
    "SR_mean_siang": "Radiasi matahari rata-rata 09.00-15.00 WIB (penanda hari cerah)",
    "rentang_harian": "Suhu maksimum siang dikurangi suhu 21.00",
    "T_min_dini_hari_ini": "Suhu minimum dini hari tadi (00.00-07.50 WIB)",
    "bulan": "Bulan (menangkap musim kemarau)",
}


def render_metodologi() -> None:
    info = muat_info()
    st.markdown("## 📘 Metodologi")
    st.caption("Penjelasan singkat cara kerja sistem, evaluasi model, dan keterbatasannya.")

    st.markdown("### 1. Definisi label")
    st.markdown(
        f"- **Berpotensi embun beku** = suhu udara minimum pada **00.00-07.50 WIB** hari berikutnya "
        f"**≤ {info['ambang_suhu']:g}°C** (mengikuti ambang status Waspada pada Jufri dkk., 2024).\n"
        f"- Model memakai data **15.00-21.00 WIB hari ini** untuk menebak label tersebut, jadi ini prediksi ke depan.\n"
        f"- Dari {info['jumlah_hari_model']:,} hari yang bisa dipakai, **{info['hari_berpotensi']} hari** berlabel berpotensi "
        f"({info['hari_berpotensi'] / info['jumlah_hari_model']:.1%}). Kelasnya sangat timpang, jadi accuracy tidak dipakai sebagai ukuran.")

    st.markdown("### 2. Alur data")
    st.code("File AWS (10 menit, UTC)\n"
            "  → ubah ke WIB, buang nilai error sensor, isi celah ≤ 30 menit\n"
            "  → hitung titik embun (Magnus-Tetens)\n"
            "  → ringkas jendela 15.00-21.00 WIB menjadi 17 fitur\n"
            f"  → {info['nama_model']} → skor 0-1\n"
            f"  → skor ≥ {info['ambang_prob']:.2f} = Berpotensi → tingkat Waspada / Siaga / Awas", language=None)

    st.markdown("### 3. Fitur model")
    with st.expander(f"Lihat {len(info['fitur'])} fitur yang dipakai model"):
        tabel_fitur = pd.DataFrame({"Fitur": info["fitur"], "Arti": [DESKRIPSI_FITUR.get(k, "") for k in info["fitur"]]})
        st.dataframe(tabel_fitur, use_container_width=True, hide_index=True, height=35 * (len(tabel_fitur) + 1) + 3)

    st.markdown("### 4. Evaluasi (validasi leave-one-year-out)")
    st.markdown("Model dilatih pada 4 tahun dan diuji pada 1 tahun yang tidak ikut dilatih, diulang untuk tiap tahun. "
                "Baseline = \"kalau dini hari tadi sudah dingin, besok diprediksi dingin juga\".")
    metrik = pd.DataFrame(info["metrik"]).rename(columns={
        "model": "Model", "recall": "Recall", "precision": "Precision", "ambang_prob": "Ambang skor"})
    st.dataframe(metrik[["Model", "Recall", "Precision", "F1", "PR-AUC", "Ambang skor"]],
                 use_container_width=True, hide_index=True)
    st.caption("Recall = kejadian nyata yang tertangkap. Precision = alarm yang benar-benar diikuti kejadian.")

    kiri, kanan = st.columns(2)
    with kiri:
        st.markdown("**Hari berpotensi per tahun**")
        per_tahun = pd.DataFrame(info["per_tahun"]).T.rename(columns={"hari": "Hari valid", "berpotensi": "Hari berpotensi"})
        st.dataframe(per_tahun, use_container_width=True)
    with kanan:
        st.markdown("**Kejadian tertangkap per tahun uji**")
        kinerja = pd.DataFrame(info["kinerja_per_tahun"]).rename(
            columns={"tahun": "Tahun", "kejadian": "Kejadian", "tertangkap": "Tertangkap", "alarm": "Total alarm"})
        st.dataframe(kinerja, use_container_width=True, hide_index=True)

    st.plotly_chart(grafik_batang_horizontal(pd.Series(info["pentingnya_fitur"]).head(10),
                                             "10 fitur terpenting (Random Forest)"), use_container_width=True)

    st.markdown("### 5. Pencocokan dengan tanggal berita")
    berita = pd.DataFrame(info["cek_berita"])
    ada_data = berita[berita["prediksi_model"] != "tidak ada data"]
    ditandai = int((ada_data["prediksi_model"] == "Berpotensi").sum())
    st.markdown(f"Dari **{len(ada_data)} tanggal berita** yang punya data AWS, model menandai **{ditandai}** sebagai berpotensi "
                f"(prediksi dibuat dari data malam sebelumnya, validasi per tahun).")
    with st.expander("Lihat tabel per tanggal"):
        tampil = ada_data.rename(columns={
            "tanggal_berita": "Tanggal berita", "T_min_dini_AWS": "Suhu min dini hari AWS (°C)",
            "probabilitas": "Skor model malam sebelumnya", "prediksi_model": "Prediksi"})
        st.dataframe(tampil, use_container_width=True, hide_index=True, height=35 * (len(tampil) + 1) + 3)
        st.caption("AWS Batur hanya satu titik. Berita sering menyebut lokasi lain di Dieng yang lebih dingin, "
                   "jadi tanggal berita tidak selalu terlihat dingin di AWS. Tanggal tanpa data AWS tidak ditampilkan.")

    st.markdown("### 6. Keterbatasan")
    st.markdown(
        "- **Kejadian sedikit** (30 hari berlabel). Angka performa bisa berubah bila data bertambah.\n"
        "- **Nama stasiun berubah di pertengahan 2023** (AWS Batur → AWS Batur Dieng). Hampir semua kejadian ada di 2023-2024; "
        "kemungkinan ada pergantian sensor yang perlu dikonfirmasi.\n"
        "- **Sensor RH bermasalah** pada beberapa periode (misal Desember 2024 - Maret 2025). Nilai RH di bawah 20% dibuang, "
        "tapi nilai 20-30% pada periode itu masih mencurigakan.\n"
        "- **Satu titik pengamatan.** Embun beku di lahan terbuka bisa lebih dingin daripada AWS.\n"
        "- **Skor model bukan peluang** yang sudah dikalibrasi, dan tingkat Waspada/Siaga/Awas pada prediksi adalah "
        "pembagian skor, **bukan standar resmi BMKG**. Status Waspada/Siaga/Awas pada pemantauan langsung memakai aturan jurnal.\n"
        "- Hasil ini adalah alat bantu, bukan peringatan resmi BMKG.")

    st.markdown("### 7. Referensi")
    st.markdown(
        "- Jufri dkk. (2024). Rancangan dan Implementasi Sistem Monitoring Bencana Frost (Embun Beku). *ELKOMIKA* 12(2), 288-302.\n"
        "- Camuffo (2019). Rumus Magnus-Tetens untuk titik embun.\n"
        "- Moeletsi dkk. (2016). Kategori light / medium / heavy frost.")
