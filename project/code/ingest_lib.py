"""Parser, validasi, karantina, dan pemuatan file CSV mesin push test ke DuckDB (pengganti macro VBA).

Alur satu file: hash isi -> sudah pernah dilihat? (lewati) -> baca (format dikenali, header lengkap, tidak terpotong, angka terbaca) ->
validasi nilai (<= 0 atau > kapasitas ditandai tidak valid) -> muat, atau karantina dengan alasan. Alamat folder dan spesifikasi dari config.yaml.
"""
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import yaml

import common as CM

HEADER_KEYS = ["Test Date", "Shift", "Machine", "Model", "Condition", "LSL (g)", "USL (g)"]
DATA_HEADER = "Sample No;Force (g)"


def load_config(path=None):
    return yaml.safe_load(Path(path or CM.CONFIG).read_text(encoding="utf-8"))


def parse_number(s):
    """Baca angka dengan pemisah ribuan dan desimal campuran. Jika ada koma dan titik, simbol paling kanan adalah desimal;
    hanya koma -> desimal koma; hanya titik -> desimal titik. Mengembalikan (nilai, gaya) dengan gaya 'ID' atau 'US'."""
    s = s.strip()
    if not re.fullmatch(r"-?\d[\d.,]*", s):
        raise ValueError(s)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            return float(s.replace(".", "").replace(",", ".")), "ID"
        return float(s.replace(",", "")), "US"
    if "," in s:
        return float(s.replace(",", ".")), "ID"
    return float(s), "US"


def parse_file(path, capacity=None, min_rows=1):
    """Baca satu file. Hasil: dict status ('ok' atau 'gagal'), error_type, header, values, rows_invalid, file_hash."""
    path = Path(path)
    raw = path.read_bytes()
    out = dict(file_name=path.name, file_hash=hashlib.sha256(raw).hexdigest(), status="gagal", error_type="", header={}, values=[], rows_read=0, rows_invalid=0, number_format="")
    capacity = capacity or CM.CAPACITY_G
    if not raw.strip():
        out["error_type"] = "file_kosong"; return out
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        out["error_type"] = "bukan_teks"; return out
    lines = text.split("\n")
    if lines[0].startswith("# Machine,"):
        out["error_type"] = "format_mesin_baru"; return out
    if not lines[0].startswith("Test Program;"):
        out["error_type"] = "format_tidak_dikenal"; return out
    if not text.endswith("\n"):
        out["error_type"] = "terpotong"; return out
    lines = [l for l in lines if l != ""]
    hdr = {}
    for l in lines[1:8]:
        k, _, v = l.partition(";")
        hdr[k] = v
    if any(k not in hdr or hdr[k] == "" for k in HEADER_KEYS) or len(lines) < 9 or lines[8] != DATA_HEADER:
        out["error_type"] = "header_tidak_lengkap"; return out
    styles, values = set(), []
    for l in lines[9:]:
        parts = l.split(";")
        if len(parts) != 2 or not parts[0].isdigit():
            out["error_type"] = "baris_rusak"; return out
        try:
            v, st = parse_number(parts[1])
        except ValueError:
            out["error_type"] = "nilai_bukan_angka"; return out
        values.append((int(parts[0]), v)); styles.add(st)
    if len(values) < min_rows:
        out["error_type"] = "tanpa_hasil_ukur"; return out
    try:
        date = datetime.strptime(hdr["Test Date"], "%d/%m/%Y").date()
    except ValueError:
        out["error_type"] = "tanggal_tidak_valid"; return out
    out.update(status="ok", header=dict(machine=hdr["Machine"], model=hdr["Model"], condition=hdr["Condition"], shift=hdr["Shift"], date=date, lsl=parse_number(hdr["LSL (g)"])[0], usl=parse_number(hdr["USL (g)"])[0]),
               values=values, rows_read=len(values), rows_invalid=sum(1 for _, v in values if v <= 0 or v > capacity), number_format="US" if styles == {"US"} else "ID")
    return out


def connect(path=None):
    con = duckdb.connect(str(path or CM.DB_PATH))
    con.execute((CM.ROOT / "code" / "1-data-preparation" / "sql" / "schema.sql").read_text(encoding="utf-8"))
    return con


def load_spec(con, cfg):
    con.execute("DELETE FROM spec")
    for s in cfg["spec"]:
        con.execute("INSERT INTO spec VALUES (?,?,?,?)", [s["model"], s["test_type"], s["lsl_g"], s["usl_g"]])


def ingest(con, incoming, quarantine, cfg=None):
    """Muat file baru dari folder incoming. File yang hash-nya sudah ada (dimuat atau dikarantina) dilewati. Mengembalikan DataFrame ingest_log percobaan ini."""
    cfg = cfg or load_config()
    incoming, quarantine = Path(incoming), Path(quarantine)
    quarantine.mkdir(parents=True, exist_ok=True)
    load_spec(con, cfg)
    spec = {(r[0], r[1]): (r[2], r[3]) for r in con.execute("SELECT * FROM spec").fetchall()}
    seen = {r[0] for r in con.execute("SELECT file_hash FROM ingest_log WHERE status IN ('loaded','quarantined')").fetchall()}
    attempt = (con.execute("SELECT COALESCE(MAX(attempt),0) FROM ingest_log").fetchone()[0]) + 1
    n_run = con.execute("SELECT COUNT(*) FROM test_run").fetchone()[0]
    seen_before = set(seen)
    log = []
    for f in sorted(p for p in incoming.glob("*.csv")):
        r = parse_file(f, cfg.get("capacity_g"), cfg.get("min_rows", 1))
        row = dict(attempt=attempt, file_name=f.name, file_hash=r["file_hash"], status="", error_type="", rows_read=r["rows_read"], rows_invalid=r["rows_invalid"], run_id=None)
        if r["file_hash"] in seen:
            row.update(status="skipped", error_type="sudah_dimuat_sebelumnya" if r["file_hash"] in seen_before else "duplikat_isi", rows_read=0, rows_invalid=0)
        elif r["status"] != "ok":
            shutil.copy(f, quarantine / f.name)
            (quarantine / (f.name + ".reason.txt")).write_text(r["error_type"] + "\n", encoding="utf-8")
            row.update(status="quarantined", error_type=r["error_type"]); seen.add(r["file_hash"])
        else:
            h = r["header"]
            lo, hi = spec.get((h["model"], "push"), (None, None))
            if lo is None:
                shutil.copy(f, quarantine / f.name)
                row.update(status="quarantined", error_type="model_tanpa_spesifikasi"); seen.add(r["file_hash"])
                log.append(row); continue
            n_run += 1; run_id = f"R{n_run:04d}"
            con.execute("INSERT INTO test_run VALUES (?,?,?,?,?,?,?,?,?,?)", [run_id, f.name, r["file_hash"], h["machine"], h["model"], h["condition"], "push", h["shift"], h["date"], r["number_format"]])
            con.executemany("INSERT INTO measurement VALUES (?,?,?,?,?)", [(run_id, s, v, "OK" if lo <= v <= hi else "NG", bool(0 < v <= (cfg.get("capacity_g") or CM.CAPACITY_G))) for s, v in r["values"]])
            row.update(status="loaded", run_id=run_id); seen.add(r["file_hash"])
        log.append(row)
    df = pd.DataFrame(log, columns=["attempt", "file_name", "file_hash", "status", "error_type", "rows_read", "rows_invalid", "run_id"])
    if len(df):
        con.executemany("INSERT INTO ingest_log VALUES (?,?,?,?,?,?,?,?)", [tuple(None if pd.isna(v) else v for v in r) for r in df.itertuples(index=False)])
    return df
