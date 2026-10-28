"""10: Uji dashboard dengan Streamlit AppTest: tiap halaman berjalan tanpa exception dan angka tampil sama dengan CSV."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from streamlit.testing.v1 import AppTest
import common as CM

APP = CM.ROOT / "code" / "3-presentation" / "streamlit" / "app.py"
cp = pd.read_csv(CM.RES2 / "cpk_group.csv"); att = pd.read_csv(CM.RES1 / "ingest_attempts.csv").iloc[0]; bad = pd.read_csv(CM.RES3 / "dashboard_files_bermasalah.csv")
res = {}
at = AppTest.from_file(str(APP), default_timeout=90).run()
res["halaman Ringkasan Cpk tanpa error"] = not at.exception
m = {x.label: x.value for x in at.metric}
res["Cpk terendah sama dengan CSV"] = m["Cpk terendah"] == f"{cp.cpk.iloc[0]:.2f}"
res["kombinasi terendah sama dengan CSV"] = m["Kombinasi terendah"] == f"{cp.model.iloc[0]} {cp.condition.iloc[0]}"
res["kombinasi di bawah 1,33 sama dengan CSV"] = m["Kombinasi di bawah 1,33"] == str(int(cp.di_bawah_cpk_target.sum()))
at.sidebar.radio[0].set_value("Detail model dan kondisi").run()
res["halaman Detail tanpa error"] = not at.exception
at.selectbox[0].set_value("Model B").run(); at.selectbox[1].set_value("after_oven").run()
r = cp[(cp.model == "Model B") & (cp.condition == "after_oven")].iloc[0]
res["ganti model dan kondisi tanpa error"] = not at.exception
res["kalimat Cpk detail sama dengan CSV"] = any(f"Cpk {r.cpk:.2f} dari {int(r.n)} hasil ukur" in x.value for x in at.markdown)
at.multiselect[0].set_value(["PT-02"]).run()
res["filter mesin tanpa error"] = not at.exception
at.sidebar.radio[0].set_value("Status file").run()
res["halaman Status file tanpa error"] = not at.exception
m = {x.label: x.value for x in at.metric}
res["file dimuat sama dengan CSV"] = m["File dimuat"] == f"{int(att.loaded):,}".replace(",", ".")
res["file dikarantina sama dengan CSV"] = m["File dikarantina"] == str(int(att.quarantined))
at.selectbox[0].set_value("terpotong").run()
res["filter alasan tanpa error"] = not at.exception
res["jumlah file terpotong sama dengan CSV"] = any(f"{int((bad.error_type == 'terpotong').sum())} file" == x.value for x in at.markdown)
out = pd.DataFrame(list(res.items()), columns=["pemeriksaan", "hasil"])
out["hasil"] = out.hasil.map({True: "lulus", False: "gagal"})
out.to_csv(CM.RES3 / "dashboard_test.csv", index=False)
print(out.to_string(index=False))
assert (out.hasil == "lulus").all(), "uji dashboard gagal"
