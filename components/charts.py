"""Grafik Plotly yang dipakai di beberapa halaman."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BIRU, UNGU, MERAH, HIJAU, ABU = "#2563eb", "#7c3aed", "#dc2626", "#059669", "#64748b"


def _iso(ts):
    return pd.Timestamp(ts).isoformat()


def _blok_waktu(fig, x0, x1, warna, teks):
    """Blok transparan di area grafik untuk menandai jendela waktu."""
    fig.add_shape(type="rect", xref="x", yref="paper", x0=_iso(x0), x1=_iso(x1), y0=0, y1=1,
                  fillcolor=warna, opacity=0.12, line_width=0, layer="below")
    fig.add_annotation(x=_iso(x0), xref="x", y=1, yref="paper", text=teks, showarrow=False,
                       xanchor="left", yanchor="bottom", font=dict(size=11, color=ABU))


def gauge_skor(p, ambang, warna):
    nilai = p * 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=nilai,
        number={"suffix": "%", "valueformat": ".0f"},
        title={"text": "Skor risiko model"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": warna},
            "steps": [{"range": [0, ambang * 100], "color": "rgba(5,150,105,0.15)"},
                      {"range": [ambang * 100, 100], "color": "rgba(220,38,38,0.12)"}],
            "threshold": {"line": {"color": "#0f172a", "width": 3}, "thickness": 0.85,
                          "value": ambang * 100},
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=60, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def grafik_hari(df, tanggal, ambang_suhu, sampai_besok=False):
    """Suhu dan titik embun satu hari; opsional diperpanjang sampai dini hari besok (untuk simulasi)."""
    t0 = pd.Timestamp(tanggal).normalize()
    t1 = t0 + (pd.Timedelta(days=1, hours=7, minutes=50) if sampai_besok else pd.Timedelta(hours=23, minutes=50))
    d = df.loc[t0:t1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d.index, y=d["T"], name="Suhu udara", line=dict(color=BIRU, width=2)))
    fig.add_trace(go.Scatter(x=d.index, y=d["Td"], name="Titik embun", line=dict(color=UNGU, width=1.5, dash="dot")))
    fig.add_hline(y=ambang_suhu, line_dash="dash", line_color=MERAH,
                  annotation_text=f"Ambang {ambang_suhu:g}°C", annotation_position="top left")
    _blok_waktu(fig, t0 + pd.Timedelta(hours=15), t0 + pd.Timedelta(hours=21), BIRU, "Data yang dipakai model")
    if sampai_besok:
        _blok_waktu(fig, t0 + pd.Timedelta(days=1), t0 + pd.Timedelta(days=1, hours=7, minutes=50), MERAH,
                    "Dini hari yang diprediksi")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
                      yaxis_title="°C", legend=dict(orientation="h", y=-0.15))
    return fig


def grafik_10menit(d, ambang_suhu):
    """Tiga panel: suhu & titik embun, kelembapan, kecepatan angin (resolusi 10 menit)."""
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=("Suhu udara & titik embun (°C)", "Kelembapan relatif (%)", "Kecepatan angin (m/s)"))
    fig.add_trace(go.Scatter(x=d.index, y=d["T"], name="Suhu udara", line=dict(color=BIRU)), row=1, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=d["Td"], name="Titik embun", line=dict(color=UNGU, dash="dot")), row=1, col=1)
    fig.add_hline(y=ambang_suhu, line_dash="dash", line_color=MERAH, row=1, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=d["RH"], name="RH", line=dict(color=HIJAU)), row=2, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=d["WS"], name="Angin", line=dict(color=ABU)), row=3, col=1)

    suhu = d["T"].dropna()
    if len(suhu):
        t_min = suhu.idxmin()
        fig.add_trace(go.Scatter(x=[t_min], y=[suhu.min()], mode="markers+text", name="Suhu terendah",
                                 text=[f"{suhu.min():.1f}°C ({t_min:%H:%M})"], textposition="bottom center",
                                 marker=dict(color=MERAH, size=10)), row=1, col=1)
    fig.update_layout(height=620, margin=dict(l=10, r=10, t=40, b=10), hovermode="x unified",
                      showlegend=False)
    return fig


def grafik_agregat(tabel, ambang_suhu, titik_merah=None):
    """Suhu minimum dan titik embun minimum per periode (harian/mingguan/bulanan/tahunan)."""
    mode = "lines+markers" if len(tabel) <= 60 else "lines"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tabel.index, y=tabel["T_min"], name="Suhu minimum", mode=mode, line=dict(color=BIRU)))
    fig.add_trace(go.Scatter(x=tabel.index, y=tabel["Td_min"], name="Titik embun minimum (malam-pagi)",
                             mode=mode, line=dict(color=UNGU, dash="dot")))
    if titik_merah is not None and len(titik_merah):
        fig.add_trace(go.Scatter(x=titik_merah.index, y=titik_merah["T_min"], mode="markers",
                                 name="Hari berpotensi embun beku", marker=dict(color=MERAH, size=9)))
    fig.add_hline(y=ambang_suhu, line_dash="dash", line_color=MERAH,
                  annotation_text=f"Ambang {ambang_suhu:g}°C", annotation_position="top left")
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
                      yaxis_title="°C", legend=dict(orientation="h", y=-0.2))
    return fig


def grafik_batang_hari(tabel):
    """Jumlah hari berpotensi embun beku per periode."""
    fig = go.Figure(go.Bar(x=tabel.index, y=tabel["hari_berpotensi"], marker_color=MERAH))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Hari berpotensi")
    return fig


def grafik_batang_horizontal(seri, judul):
    s = seri.sort_values()
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h", marker_color=HIJAU))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10), title=judul)
    return fig
