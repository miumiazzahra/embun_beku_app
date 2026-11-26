"""Notifikasi peringatan: banner, toast, pesan siap salin, dan riwayat sesi."""
import textwrap
import pandas as pd
import streamlit as st

BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]

WARNA = {"Tidak berpotensi": "#059669", "Waspada": "#d97706", "Siaga": "#ea580c", "Awas": "#dc2626"}
IKON = {"Tidak berpotensi": "🟢", "Waspada": "🟡", "Siaga": "🟠", "Awas": "🔴"}

REKOMENDASI = {
    "Tidak berpotensi": "Tidak ada tindakan khusus. Tetap pantau data pada malam berikutnya.",
    "Waspada": "Pantau kondisi menjelang subuh dan beri tahu kelompok tani. Periksa lapangan bila suhu mendekati 2°C.",
    "Siaga": "Sebarkan peringatan ke petani/kelompok tani. Siapkan penutup atau perlindungan tanaman dan penyiraman manual sebelum subuh.",
    "Awas": "Segera informasikan petani dan pihak terkait. Lakukan pemeriksaan lapangan dini hari dan lindungi tanaman (penutupan, penyiraman manual) sesuai saran jurnal ELKOMIKA 2024.",
}


def tgl_id(ts) -> str:
    ts = pd.Timestamp(ts)
    return f"{ts.day} {BULAN[ts.month - 1]} {ts.year}"


def pesan_peringatan(hasil) -> str:
    baris = [
        "⚠️ PERINGATAN DINI POTENSI EMBUN BEKU - DIENG",
        f"Tingkat risiko (model): {hasil['tingkat'].upper()}",
        f"Berpotensi pada dini hari {tgl_id(hasil['untuk_dini_hari'])} (00.00-08.00 WIB).",
        f"Kondisi {tgl_id(hasil['tanggal_data'])} sekitar pukul 21.00 WIB: "
        f"suhu {hasil['T_21']:.1f}°C, RH {hasil['RH_21']:.0f}%.",
        f"Saran: {REKOMENDASI[hasil['tingkat']]}",
        "(Prediksi model berbasis data AWS Batur, bukan peringatan resmi BMKG)",
    ]
    return "\n".join(textwrap.fill(b, width=62) for b in baris)


def tampilkan_banner(hasil) -> None:
    tingkat = hasil["tingkat"]
    tgl = tgl_id(hasil["untuk_dini_hari"])
    skor = f"{hasil['probabilitas']:.0%}"
    if tingkat == "Awas":
        st.error(f"🔴 **AWAS** · Dini hari {tgl} berpotensi embun beku (skor model {skor}).")
    elif tingkat == "Siaga":
        st.warning(f"🟠 **SIAGA** · Dini hari {tgl} berpotensi embun beku (skor model {skor}).")
    elif tingkat == "Waspada":
        st.warning(f"🟡 **WASPADA** · Dini hari {tgl} berpotensi embun beku (skor model {skor}).")
    else:
        st.success(f"🟢 Dini hari {tgl} diprediksi **tidak berpotensi** embun beku (skor model {skor}).")


def catat_riwayat(hasil) -> bool:
    """Simpan ke riwayat sesi. Mengembalikan True kalau ini hasil baru (bukan refresh halaman yang sama)."""
    riwayat = st.session_state.setdefault("riwayat", [])
    kunci = (hasil["sumber"], str(hasil["tanggal_data"]), round(hasil["probabilitas"], 4))
    if riwayat and riwayat[-1]["kunci"] == kunci:
        return False
    riwayat.append({
        "kunci": kunci,
        "Sumber": hasil["sumber"],
        "Data tanggal": tgl_id(hasil["tanggal_data"]),
        "Untuk dini hari": tgl_id(hasil["untuk_dini_hari"]),
        "Skor model": f"{hasil['probabilitas']:.0%}",
        "Hasil": hasil["prediksi"],
        "Tingkat": hasil["tingkat"],
    })
    return True


def tampilkan_riwayat() -> None:
    riwayat = st.session_state.get("riwayat", [])
    if not riwayat:
        st.caption("Belum ada prediksi pada sesi ini.")
        return
    tabel = pd.DataFrame(riwayat).drop(columns="kunci").iloc[::-1]
    st.dataframe(tabel, use_container_width=True, hide_index=True)
