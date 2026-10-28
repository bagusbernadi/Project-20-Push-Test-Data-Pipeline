"""04: Cek silang KPI. (a) SQL vs pandas dengan parser independen (regex, tanpa ingest_lib) untuk 1.159 sesi dan 4 kelompok,
(b) SQL vs Excel (rumus AVERAGEIFS, MAXIFS, MINIFS, simpangan baku dari jumlah kuadrat; dihitung ulang LibreOffice) pada 4 kelompok dan 30 sesi sampel.
"""
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import openpyxl
import pandas as pd
import common as CM

runs = pd.read_csv(CM.RES2 / "kpi_run.csv"); grp = pd.read_csv(CM.RES2 / "kpi_group.csv")
import duckdb
con = duckdb.connect(str(CM.DB_PATH), read_only=True)
meas = con.execute("SELECT r.file_name, r.model, r.condition, m.seq, m.force_g FROM measurement m JOIN test_run r USING (run_id) WHERE m.is_valid ORDER BY r.run_id, m.seq").df()
con.close()

# (a) parser independen: baca file yang dimuat (nama dari test_run), tanpa ingest_lib
def num(s):
    s = s.strip()
    if "," in s and "." in s:
        return float(s.replace(",", "")) if s.rfind(".") > s.rfind(",") else float(s.replace(".", "").replace(",", "."))
    return float(s.replace(",", ".")) if "," in s else float(s)

rows = []
for name, g in meas.groupby("file_name"):
    lines = (CM.INCOMING / name).read_text(encoding="utf-8").strip().split("\n")[9:]
    v = np.array([num(l.split(";")[1]) for l in lines])
    v = v[(v > 0) & (v <= CM.CAPACITY_G)]
    rows.append(dict(file_name=name, n=len(v), mean_g=v.mean(), min_g=v.min(), max_g=v.max(), sd_g=v.std(ddof=1)))
pdf = pd.DataFrame(rows).merge(runs[["file_name", "model", "condition", "n", "mean_g", "min_g", "max_g", "sd_g"]], on="file_name", suffixes=("_pd", "_sql"))
res = []
for f in ("n", "mean_g", "min_g", "max_g", "sd_g"):
    ok = np.isclose(pdf[f + "_pd"], pdf[f + "_sql"], atol=1e-6)
    res.append(dict(cek="SQL vs pandas (parser independen)", item=f"per sesi: {f}", dibandingkan=len(pdf), cocok=int(ok.sum())))
allv = pd.concat([pd.DataFrame({"model": m, "condition": c, "v": [num(l.split(';')[1]) for l in (CM.INCOMING / n).read_text().strip().split("\n")[9:]]}) for n, m, c in meas.drop_duplicates("file_name")[["file_name", "model", "condition"]].itertuples(index=False)])
allv = allv[(allv.v > 0) & (allv.v <= CM.CAPACITY_G)]
for r in grp.itertuples():
    d = allv[(allv.model == r.model) & (allv.condition == r.condition)].v
    cpk = min(CM.USL - d.mean(), d.mean() - CM.LSL) / (3 * d.std(ddof=1))
    for f, a, b in (("n", len(d), r.n), ("mean_g", d.mean(), r.mean_g), ("sd_g", d.std(ddof=1), r.sd_g), ("cpk", cpk, r.cpk), ("oos_rate", ((d < CM.LSL) | (d > CM.USL)).mean(), r.oos_rate)):
        res.append(dict(cek="SQL vs pandas (parser independen)", item=f"{r.model} {r.condition}: {f}", dibandingkan=1, cocok=int(np.isclose(a, b, atol=1e-6))))

# (b) Excel
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "data"
ws.append(["model", "condition", "file", "value", "value2"])
for i, r in enumerate(meas.itertuples(), 2):
    ws.append([r.model, r.condition, r.file_name, r.force_g, f"=D{i}^2"])
n_last = len(meas) + 1
g = wb.create_sheet("group"); g.append(["model", "condition", "n", "mean", "min", "max", "sd", "cpk"])
for i, r in enumerate(grp.itertuples(), 2):
    c = f"data!$A$2:$A${n_last},$A{i},data!$B$2:$B${n_last},$B{i}"
    g.append([r.model, r.condition, f"=COUNTIFS({c})", f"=AVERAGEIFS(data!$D$2:$D${n_last},{c})", f"=_xlfn.MINIFS(data!$D$2:$D${n_last},{c})", f"=_xlfn.MAXIFS(data!$D$2:$D${n_last},{c})",
              f"=SQRT((SUMIFS(data!$E$2:$E${n_last},{c})-C{i}*D{i}^2)/(C{i}-1))", f"=MIN({CM.USL}-D{i},D{i}-{CM.LSL})/(3*G{i})"])
samp = runs.iloc[::max(1, len(runs) // 30)].head(30)
s = wb.create_sheet("session"); s.append(["file", "n", "mean", "min", "max", "sd"])
for i, r in enumerate(samp.itertuples(), 2):
    c = f"data!$C$2:$C${n_last},$A{i}"
    s.append([r.file_name, f"=COUNTIFS({c})", f"=AVERAGEIFS(data!$D$2:$D${n_last},{c})", f"=_xlfn.MINIFS(data!$D$2:$D${n_last},{c})", f"=_xlfn.MAXIFS(data!$D$2:$D${n_last},{c})",
              f"=SQRT((SUMIFS(data!$E$2:$E${n_last},{c})-B{i}*C{i}^2)/(B{i}-1))"])
tmp = Path(tempfile.mkdtemp()); src = tmp / "x.xlsx"; wb.save(src); (tmp / "o").mkdir()
subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(tmp / "o"), str(src)], check=True, capture_output=True, timeout=900)
v = openpyxl.load_workbook(tmp / "o" / "x.xlsx", data_only=True)
vg, vs = v["group"], v["session"]
for i, r in enumerate(grp.itertuples(), 2):
    for col, f, ref in (("C", "n", r.n), ("D", "mean_g", r.mean_g), ("E", "min_g", r.min_g), ("F", "max_g", r.max_g), ("G", "sd_g", r.sd_g), ("H", "cpk", r.cpk)):
        res.append(dict(cek="SQL vs Excel (LibreOffice)", item=f"{r.model} {r.condition}: {f}", dibandingkan=1, cocok=int(np.isclose(float(vg[f"{col}{i}"].value), ref, rtol=1e-9, atol=1e-6))))
for i, r in enumerate(samp.itertuples(), 2):
    for col, f in (("B", "n"), ("C", "mean_g"), ("D", "min_g"), ("E", "max_g"), ("F", "sd_g")):
        res.append(dict(cek="SQL vs Excel (LibreOffice)", item=f"sesi {r.file_name[:30]}: {f}", dibandingkan=1, cocok=int(np.isclose(float(vs[f"{col}{i}"].value), getattr(r, f), rtol=1e-9, atol=1e-6))))
out = pd.DataFrame(res)
out.to_csv(CM.RES2 / "crosscheck.csv", index=False)
summ = out.groupby("cek").agg(item=("item", "size"), cocok=("cocok", "sum"))
print(summ)
assert (out.cocok == out.dibandingkan).all(), out[out.cocok != out.dibandingkan]
