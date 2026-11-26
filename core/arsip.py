import pandas as pd

from core.config import ARSIP_FILE

KOLOM_ARSIP = ["T", "RH", "WS", "WD", "SR", "RR", "Td", "status_jurnal"]


def muat_arsip():
    if not ARSIP_FILE.exists():
        return pd.DataFrame(columns=KOLOM_ARSIP, index=pd.DatetimeIndex([], name="waktu_wib"))
    df = pd.read_csv(ARSIP_FILE, index_col=0, parse_dates=True)
    df.index.name = "waktu_wib"
    return df


def simpan_ke_arsip(bersih):
    """Tambahkan data bersih ke arsip. Waktu yang sama ditimpa data terbaru. Hasil: (data baru, total data)."""
    baru = bersih.loc[bersih["T"].notna(), KOLOM_ARSIP]
    lama = muat_arsip()
    if lama.empty:
        gabung = baru
        jumlah_baru = len(baru)
    else:
        jumlah_baru = int((~baru.index.isin(lama.index)).sum())
        gabung = pd.concat([lama, baru])
    gabung = gabung[~gabung.index.duplicated(keep="last")].sort_index()
    ARSIP_FILE.parent.mkdir(parents=True, exist_ok=True)
    gabung.round(3).to_csv(ARSIP_FILE)
    return jumlah_baru, len(gabung)


def kosongkan_arsip():
    if ARSIP_FILE.exists():
        ARSIP_FILE.unlink()


def ringkas_arsip():
    arsip = muat_arsip()
    if arsip.empty:
        return {"baris": 0, "hari": 0, "awal": None, "akhir": None}
    return {"baris": int(len(arsip)), "hari": int(arsip.index.normalize().nunique()),
            "awal": arsip.index.min(), "akhir": arsip.index.max()}
