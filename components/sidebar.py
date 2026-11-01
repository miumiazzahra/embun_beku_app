import streamlit as st

from core.model import muat_info

HALAMAN = ["🏠  Beranda", "🔍  Prediksi", "📊  Dashboard", "📘  Metodologi"]


def render_sidebar() -> str:
    info = muat_info()
    with st.sidebar:
        st.markdown("""
        <div class="nav-nama">❄️ Embun Beku Dieng</div>
        <div class="nav-tag">Prediksi potensi embun beku<br>AWS Batur · BMKG Stasiun Klimatologi Semarang</div>
        <hr/>
        """, unsafe_allow_html=True)

        halaman = st.radio("Menu", HALAMAN, label_visibility="collapsed")

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.caption("STATUS MODEL")
        st.markdown(
            f"**{info['nama_model']}**  \n"
            f"Ambang suhu: ≤ {info['ambang_suhu']:g}°C  \n"
            f"Ambang skor: {info['ambang_prob']:.2f}  \n"
            f"Data latih: {info['jumlah_hari_model']:,} hari"
        )
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.caption("Proyek magang · Data AWS Batur 2021-2025")
    return halaman
