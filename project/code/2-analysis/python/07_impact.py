"""07: Waktu kerja manual yang digantikan pipeline (Q9) dan jam per tahun (Q10). Semua angka waktu adalah ASUMSI (estimated), bukan pengukuran.

Menit manual per file proses lama = CM.MANUAL_MIN_PER_FILE. Pipeline berjalan otomatis (0 menit per file); file yang masuk karantina tetap ditangani manual
dengan waktu sama. Volume tahunan = file dasar per periode data dianualkan (periode data 91 hari kalender).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

log = pd.read_csv(CM.RES1 / "ingest_log.csv")
n_base = int(((log.status != "skipped") | (log.error_type != "duplikat_isi")).sum())
n_loaded = int((log.status == "loaded").sum()); n_q = int((log.status == "quarantined").sum()); n_dup = int((log.error_type == "duplikat_isi").sum())
DAYS = 91
rows = []
for m in (3.0, CM.MANUAL_MIN_PER_FILE, 10.0):
    per_year = n_loaded * 365 / DAYS
    rows.append(dict(menit_per_file=m, dasar=int(m == CM.MANUAL_MIN_PER_FILE), file_dimuat_periode=n_loaded, file_karantina_periode=n_q, file_per_tahun=per_year, menit_dihemat_per_file=m,
                     menit_hemat_periode=n_loaded * m, jam_hemat_periode=n_loaded * m / 60, jam_hemat_per_tahun=per_year * m / 60, label="estimated"))
pd.DataFrame(rows).to_csv(CM.RES2 / "impact.csv", index=False, float_format="%.10g")
print(pd.DataFrame(rows).T)
