import streamlit as st

from components.notifikasi import tampilkan_banner, tampilkan_riwayat
from core.model import muat_info


def _langkah(nomor, judul, ket):
    return (f'<div class="langkah"><div class="no">{nomor}</div>'
            f'<div class="isi"><b>{judul}</b><span>{ket}</span></div></div>')


def render_beranda() -> None:
    info = muat_info()
    recall = next((m["recall"] for m in info["metrik"] if m["model"] == info["nama_model"]), None)

    st.markdown("""
    <div class="hero">
        <h1>❄️ Prediksi Potensi Embun Beku Dieng</h1>
        <p>Sistem peringatan dini berbasis data historis AWS Batur. Petugas mengunggah data AWS
        sekali setiap malam, lalu sistem memprediksi apakah <b>dini hari besok</b> berpotensi embun beku
        dan menampilkan dashboard serta notifikasi peringatan.</p>
    </div>
    """, unsafe_allow_html=True)

    hasil = st.session_state.get("hasil_terakhir")
    if hasil:
        st.markdown("##### Prediksi terakhir pada sesi ini")
        tampilkan_banner(hasil)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Model", info["nama_model"])
    with k2:
        st.metric("Data latih", f"{info['jumlah_hari_model']:,} hari")
    with k3:
        st.metric("Hari berpotensi di data", f"{info['hari_berpotensi']} hari")
    with k4:
        st.metric("Recall (validasi per tahun)", f"{recall:.0%}" if recall is not None else "-")

    kiri, kanan = st.columns(2)
    with kiri:
        st.markdown(
            '<div class="kartu"><div class="kartu-judul">🏗️ Alur penggunaan</div>'
            + _langkah(1, "Unggah file AWS tiap malam", "Setelah pukul 21.00 WIB, file CSV/Excel hasil ekspor AWS Batur")
            + _langkah(2, "Sistem membersihkan data", "Konversi UTC ke WIB, buang nilai error, hitung titik embun (Magnus-Tetens)")
            + _langkah(3, "Model memprediksi", "Memakai data 15.00-21.00 WIB untuk menebak dini hari besok (00.00-08.00 WIB)")
            + _langkah(4, "Notifikasi muncul", "Banner, pop-up, dan pesan siap salin untuk grup petani")
            + _langkah(5, "Dashboard", "Grafik 10 menit dan nilai puncak harian, mingguan, bulanan, tahunan")
            + "</div>", unsafe_allow_html=True)
    with kanan:
        st.markdown(
            '<div class="kartu"><div class="kartu-judul">🛎️ Dua lapis peringatan</div>'
            + _langkah("A", "Prediksi (model ML)", "Dijalankan malam hari. Menjawab: besok dini hari berpotensi atau tidak, lengkap dengan tingkat risiko.")
            + _langkah("B", "Pemantauan langsung (aturan jurnal)",
                       "Setiap data 10 menit dicek: suhu ≤ 2°C = Waspada, + angin ≤ 5 m/s = Siaga, + RH ≥ 60% = Awas.")
            + "</div>", unsafe_allow_html=True)
        st.info("Gunakan menu **Prediksi** di sidebar untuk mulai. Belum punya file? Di sana tersedia "
                "contoh file dan mode simulasi dari data historis.")

    st.markdown("##### Riwayat prediksi sesi ini")
    tampilkan_riwayat()
