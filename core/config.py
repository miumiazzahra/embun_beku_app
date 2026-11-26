"""Lokasi file-file yang dipakai aplikasi."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_FILE = BASE_DIR / "model" / "model_embun_beku.joblib"
INFO_FILE = BASE_DIR / "model" / "info_model.json"
DATA_FILE = BASE_DIR / "data" / "data_bersih_10menit.csv.gz"
CONTOH_DIR = BASE_DIR / "contoh"
ARSIP_FILE = BASE_DIR / "data" / "arsip_unggahan.csv.gz"
