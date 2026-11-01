"""Memuat model dan info evaluasi (di-cache supaya tidak dibaca ulang tiap interaksi)."""
import json

import joblib
import streamlit as st

from core.config import INFO_FILE, MODEL_FILE


@st.cache_resource(show_spinner="Memuat model...")
def muat_model():
    return joblib.load(MODEL_FILE)


@st.cache_data
def muat_info():
    with open(INFO_FILE, encoding="utf-8") as fh:
        return json.load(fh)
