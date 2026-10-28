"""05: Rekonsiliasi dengan proses lama (Q2, Q3). Workbook lama tidak tersedia, jadi macro lama ditiru (ASUMSI, docs/definitions.md):
macro membaca semua *.csv di folder (termasuk salinan), melewati 9 baris header, mengambil kolom kedua, dan mengubah angka dengan aturan lokal Indonesia
(titik = ribuan dihapus, koma = desimal). Format mesin baru tidak terbaca. File terpotong dibaca sebagian dan baris yang bukan angka dilewati.
Hasil: macro_summary.csv, macro_group_compare.csv, macro_session_compare.csv, outputs/reconciliation.xlsx.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import numpy as np
import openpyxl
import pandas as pd
import common as CM

con = duckdb.connect(str(CM.DB_PATH))
con.execute((CM.SQL_DIR / "views.sql").read_text(encoding="utf-8"))
pipe = con.execute("SELECT file_name, model, condition, seq, force_g FROM v_measure").df()
con.close()
ing = pd.read_csv(CM.RES1 / "ingest_log.csv")


def macro_value(s):
    try:
        return float(s.strip().replace(".", "").replace(",", "."))
    except ValueError:
        return None


def name_info(n):
    base = n.replace("copy_of_", "")
    parts = base[:-4].split("_")
    model = parts[3].replace("Model", "Model ")
    cond = "_".join(parts[4:6])
    return model, cond


rows, failed, partial, copies = [], [], [], []
for f in sorted(CM.INCOMING.glob("*.csv")):
    text = f.read_text(encoding="utf-8")
    if text.startswith("# Machine,"):
        failed.append(f.name); continue
    model, cond = name_info(f.name)
    if not text.endswith("\n"):
        partial.append(f.name)
    if f.name.startswith("copy_of_"):
        copies.append(f.name)
    for i, l in enumerate(text.split("\n")[9:], 1):
        p = l.split(";")
        if len(p) == 2:
            v = macro_value(p[1])
            if v is not None:
                rows.append(dict(file_name=f.name, model=model, condition=cond, seq=i, macro_g=v, raw=p[1]))
mac = pd.DataFrame(rows)
mac["fmt_us"] = mac.raw.str.contains(r"\.")
# Q2: nilai yang berubah (pipeline vs macro) untuk file yang dimuat pipeline
cmp_ = pipe.merge(mac[["file_name", "seq", "macro_g", "fmt_us"]], on=["file_name", "seq"], how="left")
cmp_["berubah"] = ~np.isclose(cmp_.force_g, cmp_.macro_g, atol=1e-6)
files_aff = cmp_[cmp_.berubah].file_name.nunique()
summ = dict(file_di_folder=len(list(CM.INCOMING.glob("*.csv"))), file_macro_gagal_format_baru=len(failed), file_terpotong_terbaca_sebagian=len(partial), file_salinan_terbaca_dua_kali=len(copies),
            nilai_pipeline=len(cmp_), nilai_berubah=int(cmp_.berubah.sum()), persen_nilai_berubah=cmp_.berubah.mean(), file_terdampak=files_aff, file_dimuat_pipeline=cmp_.file_name.nunique(),
            nilai_macro_total=len(mac), nilai_macro_dari_salinan=int(mac.file_name.str.startswith("copy_of_").sum()),
            nilai_macro_dari_file_terpotong=int(mac.file_name.isin(partial).sum()), selisih_nilai_macro_vs_pipeline=len(mac) - len(cmp_),
            rata_nilai_berubah_macro=float(cmp_[cmp_.berubah].macro_g.mean()), rata_nilai_berubah_pipeline=float(cmp_[cmp_.berubah].force_g.mean()))
pd.DataFrame([summ]).to_csv(CM.RES2 / "macro_summary.csv", index=False, float_format="%.10g")

# Q3: KPI kelompok, pipeline vs workbook macro
def kpis(d, col):
    v = d[col]; m, s = v.mean(), v.std(ddof=1)
    return dict(n=len(v), mean_g=m, min_g=v.min(), max_g=v.max(), cpk=min(CM.USL - m, m - CM.LSL) / (3 * s), oos_rate=float(((v < CM.LSL) | (v > CM.USL)).mean()))
gr = []
for (m, c), d in mac.groupby(["model", "condition"]):
    a = kpis(pipe[(pipe.model == m) & (pipe.condition == c)], "force_g"); b = kpis(d, "macro_g")
    for k in a:
        gr.append(dict(model=m, condition=c, ukuran=k, pipeline=a[k], macro=b[k], selisih=b[k] - a[k]))
grd = pd.DataFrame(gr)
grd.to_csv(CM.RES2 / "macro_group_compare.csv", index=False, float_format="%.10g")
ses = pipe.groupby("file_name").agg(mean_p=("force_g", "mean"), min_p=("force_g", "min"), max_p=("force_g", "max")).join(
    cmp_.groupby("file_name").agg(mean_m=("macro_g", "mean"), min_m=("macro_g", "min"), max_m=("macro_g", "max")))
sc = []
for k in ("mean", "min", "max"):
    d = ~np.isclose(ses[f"{k}_p"], ses[f"{k}_m"], atol=1e-6)
    sc.append(dict(ukuran=k, sesi=len(ses), sesi_beda=int(d.sum()), persen=float(d.mean()), selisih_abs_maks=float((ses[f"{k}_m"] - ses[f"{k}_p"]).abs().max())))
pd.DataFrame(sc).to_csv(CM.RES2 / "macro_session_compare.csv", index=False, float_format="%.10g")

wb = openpyxl.Workbook(); w = wb.active; w.title = "group"
w.append(["model", "condition", "ukuran", "pipeline", "macro_lama", "selisih"])
for r in grd.itertuples():
    w.append([r.model, r.condition, r.ukuran, float(r.pipeline), float(r.macro), float(r.selisih)])
w2 = wb.create_sheet("session_beda"); w2.append(["file", "mean_pipeline", "mean_macro", "selisih"])
bd = ses[~np.isclose(ses.mean_p, ses.mean_m, atol=1e-6)].reset_index()
for r in bd.itertuples():
    w2.append([r.file_name, float(r.mean_p), float(r.mean_m), float(r.mean_m - r.mean_p)])
wb.save(CM.OUTPUTS / "reconciliation.xlsx")
print(pd.DataFrame([summ]).T); print(grd.pivot_table(index=["model", "condition"], columns="ukuran", values="selisih").round(2)); print(pd.DataFrame(sc))
