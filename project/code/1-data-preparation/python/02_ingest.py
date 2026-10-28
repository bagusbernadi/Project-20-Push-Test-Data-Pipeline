"""02: Jalankan pipeline pemuatan (parser, validasi, karantina, DuckDB) dua kali pada folder incoming.

Percobaan 1 memuat semua file; percobaan 2 harus melewati semuanya (idempoten, Q12). Hasil: results/1-data-preparation/ingest_log.csv
(percobaan 1), ingest_attempts.csv (ringkasan tiap percobaan), db_tables.csv (jumlah baris tabel setelah tiap percobaan).
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM
import ingest_lib as IL

for p in (CM.DB_PATH, CM.DB_PATH.with_suffix(".duckdb.wal")):
    p.unlink(missing_ok=True)
shutil.rmtree(CM.QUARANTINE, ignore_errors=True)
cfg = IL.load_config()
con = IL.connect()
counts, attempts = [], []
for k in (1, 2):
    log = IL.ingest(con, CM.INCOMING, CM.QUARANTINE, cfg)
    if k == 1:
        log.drop(columns="file_hash").to_csv(CM.RES1 / "ingest_log.csv", index=False)
    s = log.groupby("status").size().to_dict()
    attempts.append(dict(percobaan=k, file_dibaca=len(log), loaded=s.get("loaded", 0), quarantined=s.get("quarantined", 0), skipped=s.get("skipped", 0)))
    for t in ("test_run", "measurement", "ingest_log", "spec"):
        counts.append(dict(percobaan=k, tabel=t, baris=con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]))
pd.DataFrame(attempts).to_csv(CM.RES1 / "ingest_attempts.csv", index=False)
pd.DataFrame(counts).to_csv(CM.RES1 / "db_tables.csv", index=False)
con.close()
print(pd.DataFrame(attempts).to_string(index=False)); print(pd.DataFrame(counts).pivot(index="tabel", columns="percobaan", values="baris"))
