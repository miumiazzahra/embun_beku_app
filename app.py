import streamlit as st

from components.sidebar import render_sidebar
from styles.theme import apply_theme
from views.beranda import render_beranda
from views.dashboard import render_dashboard
from views.metodologi import render_metodologi
from views.prediksi import render_prediksi

st.set_page_config(
    page_title="Prediksi Embun Beku Dieng",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


def main() -> None:
    halaman = render_sidebar()
    if "Beranda" in halaman:
        render_beranda()
    elif "Prediksi" in halaman:
        render_prediksi()
    elif "Dashboard" in halaman:
        render_dashboard()
    elif "Metodologi" in halaman:
        render_metodologi()


if __name__ == "__main__":
    main()
