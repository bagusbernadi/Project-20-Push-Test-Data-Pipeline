"""Dashboard Push Test Data Pipeline (Streamlit + Plotly). 3 halaman: Ringkasan Cpk, Detail model dan kondisi, Status file.
Data dibaca dari results (dibuat pipeline). Data simulasi; angka menggambarkan simulasi, bukan pabrik.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RES = Path(__file__).resolve().parents[3] / "results"


@st.cache_data
def load(folder, name):
    return pd.read_csv(RES / folder / name)


cp = load("2-analysis", "cpk_group.csv")
wk, hist = load("3-presentation", "dashboard_weekly.csv"), load("3-presentation", "dashboard_hist.csv")
stat, bad = load("3-presentation", "dashboard_status.csv"), load("3-presentation", "dashboard_files_bermasalah.csv")
att = load("1-data-preparation", "ingest_attempts.csv")
LSL, USL, TARGET = 1500, 19000, 1.33

st.set_page_config(page_title="Push Test Pipeline", layout="wide")
st.title("Push Test Data Pipeline: Cpk kekuatan rekat")
st.caption("Data simulasi. Spesifikasi 1.500 sampai 19.000 g (lebar), sehingga Cpk ditentukan batas bawah. Cpk dari kurang dari 30 hasil ukur tidak stabil; jumlah data ditampilkan di samping Cpk.")
page = st.sidebar.radio("Halaman", ["Ringkasan Cpk", "Detail model dan kondisi", "Status file"])

if page == "Ringkasan Cpk":
    low = cp.iloc[0]
    a, b, c = st.columns(3)
    a.metric("Cpk terendah", f"{low.cpk:.2f}")
    b.metric("Kombinasi terendah", f"{low.model} {low.condition}")
    c.metric("Kombinasi di bawah 1,33", str(int(cp.di_bawah_cpk_target.sum())))
    cp["kombinasi"] = cp.model + " " + cp.condition
    f = go.Figure(go.Bar(x=cp.kombinasi, y=cp.cpk, error_y=dict(type="data", symmetric=False, array=cp.cpk_ci_high - cp.cpk, arrayminus=cp.cpk - cp.cpk_ci_low), marker_color="#1A73E8"))
    f.add_hline(y=TARGET, line_dash="dash", line_color="#D93025", annotation_text="Cpk 1,33")
    f.update_layout(yaxis_title="Cpk (CI 95% bootstrap)", height=380)
    st.plotly_chart(f, width="stretch")
    st.dataframe(cp[["peringkat", "model", "condition", "n", "mean_g", "sd_g", "cpk", "jarak_ke_lsl_sd", "oos_rate"]], hide_index=True, width="stretch")

elif page == "Detail model dan kondisi":
    model = st.selectbox("Model", sorted(wk.model.unique()))
    cond = st.selectbox("Kondisi", sorted(wk.condition.unique()))
    mach = st.multiselect("Mesin", sorted(wk.machine_id.unique()), default=sorted(wk.machine_id.unique()))
    d = wk[(wk.model == model) & (wk.condition == cond) & (wk.machine_id.isin(mach))]
    f = px.line(d, x="iso_week", y="mean_g", color="machine_id", markers=True)
    f.update_layout(yaxis_title="Rata-rata kekuatan rekat (g)", height=330)
    st.plotly_chart(f, width="stretch")
    h = hist[(hist.model == model) & (hist.condition == cond)]
    f2 = px.bar(h, x="bin_low", y="n")
    f2.add_vline(x=LSL, line_color="#D93025", annotation_text="LSL 1.500 g")
    f2.update_layout(xaxis_title="Kekuatan rekat (g)", yaxis_title="Hasil ukur", height=330)
    st.plotly_chart(f2, width="stretch")
    row = cp[(cp.model == model) & (cp.condition == cond)].iloc[0]
    st.write(f"Cpk {row.cpk:.2f} dari {int(row.n)} hasil ukur; jarak rata-rata ke LSL {row.jarak_ke_lsl_sd:.1f} simpangan baku; out-of-spec {row.oos_rate * 100:.2f}%.")

else:
    last = att.iloc[0]
    a, b, c = st.columns(3)
    a.metric("File dimuat", f"{int(last.loaded):,}".replace(",", "."))
    b.metric("File dikarantina", str(int(last.quarantined)))
    c.metric("File duplikat dilewati", str(int(last.skipped)))
    st.dataframe(stat, hide_index=True, width="stretch")
    et = st.selectbox("Alasan", ["semua"] + sorted(bad.error_type.unique()))
    d = bad if et == "semua" else bad[bad.error_type == et]
    st.write(f"{len(d)} file")
    st.dataframe(d, hide_index=True, width="stretch")
