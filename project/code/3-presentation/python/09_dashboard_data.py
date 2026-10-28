"""09: Data dashboard: tren mingguan per model dan kondisi, histogram terhadap spesifikasi, status file. Dibulatkan 8 desimal."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import numpy as np
import pandas as pd
import common as CM

con = duckdb.connect(str(CM.DB_PATH))
con.execute((CM.SQL_DIR / "views.sql").read_text(encoding="utf-8"))
v = con.execute("SELECT * FROM v_measure").df()
con.close()
w = v.groupby(["model", "condition", "machine_id", "iso_week"]).force_g.agg(["count", "mean", "std"]).reset_index().rename(columns={"count": "n", "mean": "mean_g", "std": "sd_g"})
w.round(8).to_csv(CM.RES3 / "dashboard_weekly.csv", index=False)
edges = np.arange(2000, 14001, 250)
h = []
for (m, c), d in v.groupby(["model", "condition"]):
    cnt, _ = np.histogram(d.force_g, bins=edges)
    h += [dict(model=m, condition=c, bin_low=int(edges[i]), bin_high=int(edges[i + 1]), n=int(cnt[i])) for i in range(len(cnt))]
pd.DataFrame(h).to_csv(CM.RES3 / "dashboard_hist.csv", index=False)
log = pd.read_csv(CM.RES1 / "ingest_log.csv")
st = log.groupby(["status", "error_type"], dropna=False).size().reset_index(name="file")
st["error_type"] = st.error_type.fillna("-")
st.to_csv(CM.RES3 / "dashboard_status.csv", index=False)
q = log[log.status != "loaded"][["file_name", "status", "error_type"]]
q.to_csv(CM.RES3 / "dashboard_files_bermasalah.csv", index=False)
print(len(w), len(h), len(st), len(q))
