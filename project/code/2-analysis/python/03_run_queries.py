"""03: Jalankan view SQL KPI (sql/views.sql) pada pushtest.duckdb dan simpan hasilnya. Hasil dibulatkan 8 desimal."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import common as CM

con = duckdb.connect(str(CM.DB_PATH))
con.execute((CM.SQL_DIR / "views.sql").read_text(encoding="utf-8"))
for view, out, order in (("v_kpi_group", "kpi_group", "model, condition"), ("v_kpi_machine_shift", "kpi_machine_shift", "machine_id, shift"),
                         ("v_kpi_weekly", "kpi_weekly", "iso_week, machine_id"), ("v_kpi_run", "kpi_run", "run_id")):
    df = con.execute(f"SELECT * FROM {view} ORDER BY {order}").df()
    for c in df.select_dtypes("float").columns:
        df[c] = df[c].round(8)
    df.to_csv(CM.RES2 / f"{out}.csv", index=False)
    print(out, len(df))
