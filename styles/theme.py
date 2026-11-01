import streamlit as st


def apply_theme() -> None:
    st.markdown("""
<style>
.main .block-container { padding-top: 1.6rem; max-width: 1300px; }
footer { visibility: hidden; }

.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #2563eb 100%);
    border-radius: 18px; padding: 1.8rem 2rem; color: #fff; margin-bottom: 1.2rem;
}
.hero h1 { color: #fff; font-size: 1.9rem; margin: 0 0 .3rem 0; }
.hero p  { color: #dbeafe; margin: 0; font-size: .95rem; line-height: 1.6; }

.kartu {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 1rem 1.2rem; margin-bottom: .8rem;
}
.kartu-judul { font-weight: 700; font-size: .95rem; color: #0f172a; margin-bottom: .5rem; }
.langkah { display: flex; gap: .7rem; align-items: flex-start; padding: .45rem 0; }
.langkah .no {
    min-width: 26px; height: 26px; border-radius: 50%; background: #2563eb; color: #fff;
    display: flex; align-items: center; justify-content: center; font-size: .75rem; font-weight: 700;
}
.langkah .isi b { color: #0f172a; font-size: .88rem; }
.langkah .isi span { display: block; color: #64748b; font-size: .78rem; }

.hasil { border-radius: 16px; padding: 1.2rem 1.4rem; text-align: center; border: 2px solid; }
.hasil .judul { font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; color: #64748b; }
.hasil .nilai { font-size: 2.2rem; font-weight: 800; margin: .2rem 0; }
.hasil .ket { font-size: .85rem; color: #334155; }
.nav-nama { font-weight: 800; font-size: 1.05rem; color: #0f172a; }
.nav-tag  { font-size: .75rem; color: #64748b; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)
