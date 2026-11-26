import pandas as pd
import streamlit as st

from components.charts import grafik_10menit, grafik_agregat, grafik_batang_hari
from components.notifikasi import BULAN, tgl_id
from core import arsip as ar
from core import data as dt
from core import pipeline as pl
from core.model import muat_info

NAMA_KOLOM = {
    "T_min": "Suhu min (°C)", "T_max": "Suhu maks (°C)", "T_mean": "Suhu rata-rata (°C)",
    "Td_min": "Titik embun min malam (°C)", "RH_mean": "RH rata-rata (%)", "WS_max": "Angin maks (m/s)",
    "jam_T_min": "Jam suhu min", "jam_Td_min": "Jam titik embun min",
    "hari_berpotensi": "Hari berpotensi", "berpotensi_aktual": "Dini hari ≤ ambang",
    "T_min_dini": "Suhu min dini hari (°C)", "n_data": "Jumlah data",
}


def _tampilkan_tabel(tabel, format_tanggal, kolom=None):
    t = tabel.copy()
    if kolom:
        t = t[kolom]
    t.index = t.index.strftime(format_tanggal)
    if "berpotensi_aktual" in t.columns:
        t["berpotensi_aktual"] = t["berpotensi_aktual"].map({1.0: "Ya", 0.0: "Tidak"}).fillna("-")
    st.dataframe(t.rename(columns=NAMA_KOLOM), use_container_width=True)


def _filter_tahun_bulan(tabel, kunci, dengan_bulan):
    kiri, kanan, _ = st.columns([1, 1, 2])
    with kiri:
        tahun = st.selectbox("Tahun", ["Semua"] + [int(y) for y in sorted(set(tabel.index.year))], key=f"th_{kunci}")
    bulan = "Semua"
    if dengan_bulan:
        with kanan:
            bulan = st.selectbox("Bulan", ["Semua"] + BULAN, key=f"bl_{kunci}")
    hasil = tabel
    if tahun != "Semua":
        hasil = hasil[hasil.index.year == tahun]
    if bulan != "Semua":
        hasil = hasil[hasil.index.month == BULAN.index(bulan) + 1]
    return hasil


def _tab_agregat(nama, tabel, ambang, kunci, format_tanggal, harian=False, dengan_filter=True):
    if dengan_filter:
        tabel = _filter_tahun_bulan(tabel, kunci, dengan_bulan=harian)
    tabel = tabel.dropna(subset=["T_min"])
    if tabel.empty:
        st.warning("Tidak ada data pada filter ini.")
        return

    idx = tabel["T_min"].idxmin()
    a, b, c = st.columns(3)
    with a:
        ket = f" · {tabel.loc[idx, 'jam_T_min']} WIB" if harian else ""
        st.metric(f"Suhu terendah ({nama})", f"{tabel.loc[idx, 'T_min']:.1f} °C")
        st.caption(f"{idx.strftime(format_tanggal)}{ket}")
    with b:
        st.metric("Titik embun terendah malam-pagi", f"{tabel['Td_min'].min():.1f} °C")
    with c:
        kolom_hari = "berpotensi_aktual" if harian else "hari_berpotensi"
        st.metric("Hari berpotensi embun beku", f"{int(tabel[kolom_hari].sum())} hari")

    merah = tabel[tabel["berpotensi_aktual"] == 1] if harian else None
    st.plotly_chart(grafik_agregat(tabel, ambang, merah), use_container_width=True)
    if not harian:
        st.plotly_chart(grafik_batang_hari(tabel), use_container_width=True)

    st.markdown(f"**10 {nama} dengan suhu terendah**")
    kolom = ["T_min", "jam_T_min", "Td_min", "jam_Td_min", "berpotensi_aktual"] if harian else \
            ["T_min", "Td_min", "T_max", "RH_mean", "hari_berpotensi"]
    _tampilkan_tabel(tabel.nsmallest(10, "T_min"), format_tanggal, kolom)
    with st.expander("Lihat semua data"):
        _tampilkan_tabel(tabel, format_tanggal)
        st.download_button("⬇️ Unduh tabel (CSV)", data=tabel.to_csv(), file_name=f"agregasi_{kunci}.csv",
                           mime="text/csv", key=f"unduh_{kunci}")


def render_dashboard() -> None:
    info = muat_info()
    ambang = info["ambang_suhu"]
    st.markdown("## 📊 Dashboard")

    pilihan = ["Data historis AWS Batur 2021-2025"]
    ringkas = ar.ringkas_arsip()
    versi = dt.versi_arsip()
    if ringkas["baris"]:
        pilihan.append(f"Historis + arsip unggahan ({ringkas['hari']} hari baru)")
    if "df_unggahan" in st.session_state:
        pilihan.append(f"File unggahan: {st.session_state.get('nama_unggahan', '')}")
    sumber = st.radio("Sumber data", pilihan, horizontal=True)

    if sumber.startswith("Data historis"):
        historis = True
        df = dt.muat_data_historis()
        harian, mingguan, bulanan, tahunan = dt.agregasi_historis(ambang)
        kunci = "hist"
    elif sumber.startswith("Historis + arsip"):
        historis = True
        df = dt.data_gabungan(versi)
        harian, mingguan, bulanan, tahunan = dt.agregasi_gabungan(ambang, versi)
        kunci = "gabung"
    else:
        historis = False
        df = st.session_state["df_unggahan"]
        harian, mingguan, bulanan, tahunan = pl.buat_agregasi(df, ambang)
        kunci = "unggah"

    if harian.empty or harian["T_min"].isna().all():
        st.warning("Tidak ada data suhu yang valid untuk ditampilkan.")
        return

    idx = harian["T_min"].idxmin()
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Rentang data", f"{harian.index.min():%d/%m/%Y}")
        st.caption(f"sampai {harian.index.max():%d/%m/%Y}")
    with r2:
        st.metric("Suhu terendah", f"{harian.loc[idx, 'T_min']:.1f} °C")
        st.caption(f"{tgl_id(idx)} · {harian.loc[idx, 'jam_T_min']} WIB")
    with r3:
        st.metric("Jumlah hari data", f"{len(harian):,} hari")
    with r4:
        st.metric(f"Dini hari ≤ {ambang:g}°C", f"{int(harian['berpotensi_aktual'].sum())} hari")
    st.caption("Catatan: titik embun dihitung dari suhu dan RH. Nilai yang sangat rendah biasanya tanda sensor RH bermasalah "
               "(misal Desember 2024 - Maret 2025), bukan kondisi nyata. Suhu udara lebih bisa diandalkan.")

    t10, th, tm, tb, tt = st.tabs(["📈 Per 10 menit", "📅 Harian", "🗓️ Mingguan", "🗒️ Bulanan", "📊 Tahunan"])

    with t10:
        bawaan = idx if historis else harian.index.max()
        tgl = st.date_input("Tanggal", value=bawaan.date(), min_value=df.index.min().date(),
                            max_value=df.index.max().date(), key=f"tgl10_{kunci}")
        t0 = pd.Timestamp(tgl)
        d = df.loc[t0: t0 + pd.Timedelta(hours=23, minutes=50)]
        if d["T"].notna().sum() == 0:
            st.warning("Tidak ada data suhu pada tanggal ini.")
        else:
            t_min = d["T"].idxmin()
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Suhu terendah", f"{d['T'].min():.1f} °C")
                st.caption(f"pukul {t_min:%H:%M} WIB")
            with m2:
                st.metric("Suhu tertinggi", f"{d['T'].max():.1f} °C")
            with m3:
                st.metric("RH tertinggi", f"{d['RH'].max():.0f} %")
            with m4:
                st.metric("Angin maksimum", f"{d['WS'].max():.1f} m/s")
            st.plotly_chart(grafik_10menit(d, ambang), use_container_width=True)
            hitung = d["status_jurnal"].value_counts()
            ringkas = ", ".join(f"{k}: {hitung[k]}" for k in ("Awas", "Siaga", "Waspada") if k in hitung)
            st.caption("Status aturan jurnal pada hari ini (jumlah data 10 menit): " + (ringkas if ringkas else "tidak ada kondisi di bawah ambang."))

    with th:
        _tab_agregat("hari", harian, ambang, f"harian_{kunci}", "%d/%m/%Y", harian=True)
    with tm:
        _tab_agregat("minggu", mingguan, ambang, f"mingguan_{kunci}", "minggu s.d. %d/%m/%Y")
    with tb:
        _tab_agregat("bulan", bulanan, ambang, f"bulanan_{kunci}", "%Y-%m", dengan_filter=False)
    with tt:
        _tab_agregat("tahun", tahunan, ambang, f"tahunan_{kunci}", "%Y", dengan_filter=False)

    with st.expander("🗂️ Kelola arsip unggahan"):
        r = ar.ringkas_arsip()
        if r["baris"] == 0:
            st.caption("Arsip masih kosong. Simpan data dari menu Prediksi (tombol \"Simpan data ini ke arsip\").")
        else:
            st.write(f"Arsip berisi {r['hari']} hari ({r['baris']:,} data 10 menit), "
                     f"{r['awal']:%d/%m/%Y} sampai {r['akhir']:%d/%m/%Y}.")
            yakin = st.checkbox("Saya yakin ingin mengosongkan arsip", key="yakin_kosongkan")
            if st.button("🗑️ Kosongkan arsip", key="kosongkan_arsip") and yakin:
                ar.kosongkan_arsip()
                st.rerun()
