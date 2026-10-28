"""Project 20: file CSV simulasi mesin push/shear test untuk pipeline. Seed tetap.

+-1.200 file, +-15.000 baris hasil ukur; 2 model x 2 kondisi (sebelum/sesudah oven) x 2 mesin x 2 shift, +-3 bulan.
Hasil (data/sim/incoming/): CSV mesin (beberapa rusak, beda format angka, ganda, format mesin baru),
data/sim/ground_truth.json (daftar file bermasalah dan pergeseran). Jalankan: python3 code/1-data-preparation/python/00_generate_csv.py dari folder project/ (versi data: v1)
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from common import SIM as OUT
SEED = 20260401
DATA_VERSION = "v1"
LSL, USL = 1500.0, 19000.0
START = date(2026, 4, 1)
N_DAYS = 91
N_FILES = 1200
MODELS = ["Model A", "Model B"]
CONDS = ["before_oven", "after_oven"]
MACHINES = ["PT-01", "PT-02"]
SHIFTS = ["Shift 1", "Shift 2"]
BASE = {("Model A", "before_oven"): 7200.0, ("Model A", "after_oven"): 8600.0,
        ("Model B", "before_oven"): 6800.0, ("Model B", "after_oven"): 8300.0}
UNIT_SD = 850.0
SHIFT_DAY, SHIFT_MACHINE, SHIFT_FRAC = 52, "PT-02", -0.08      # pergeseran rata-rata -8% setelah kalibrasi (hari ke-52)
BAD_RATES = dict(corrupt=0.02, number_format=0.03, duplicate=0.012, new_format=0.015)

rng = np.random.default_rng(SEED)
ROWS_PER_FILE = lambda: int(rng.integers(9, 17))   # rata-rata 12,5 baris -> +-15.000 baris


def fmt_id(x):
    return f"{x:.1f}".replace(".", ",")


specs = []
for i in range(N_FILES):
    specs.append(dict(i=i, day=int(rng.integers(0, N_DAYS)), model=MODELS[int(rng.integers(0, 2))],
                      cond=CONDS[int(rng.integers(0, 2))], machine=MACHINES[int(rng.integers(0, 2))],
                      shift=SHIFTS[int(rng.integers(0, 2))], n=ROWS_PER_FILE()))
specs.sort(key=lambda s: (s["day"], s["i"]))

pick = lambda frac: set(int(k) for k in rng.choice(N_FILES, int(round(frac * N_FILES)), replace=False))
corrupt, numfmt, dup, newfmt = (pick(BAD_RATES[k]) for k in ("corrupt", "number_format", "duplicate", "new_format"))
(OUT / "incoming").mkdir(parents=True, exist_ok=True)
bad = {"corrupt": [], "number_format": [], "duplicate": [], "new_format": []}
rows_total, written = 0, []
for pos, s in enumerate(specs):
    mu = BASE[(s["model"], s["cond"])] + rng.normal(0, 150)
    if s["machine"] == SHIFT_MACHINE and s["day"] >= SHIFT_DAY:
        mu *= 1 + SHIFT_FRAC
    vals = np.round(rng.normal(mu, UNIT_SD, s["n"]), 1)
    rows_total += s["n"]
    d = START + timedelta(days=s["day"])
    name = f"{s['machine']}_{d.strftime('%Y%m%d')}_{s['shift'].replace(' ', '')}_{s['model'].replace(' ', '')}_{s['cond']}_{pos + 1:04d}.csv"
    fmt = fmt_id
    if pos in numfmt:                                  # desimal titik dan pemisah ribuan koma pada sebagian file
        fmt = lambda x: f"{x:,.1f}"
        bad["number_format"].append(name)
    if pos in newfmt:                                  # format mesin baru: header berbeda, dipisah koma
        text = "\n".join([f"# Machine,{s['machine']},FW 2.1", f"Date,{d.isoformat()}", f"Model,{s['model']}",
                          f"Cond,{s['cond']}", "idx,force_gf"] + [f"{j + 1},{v}" for j, v in enumerate(vals)]) + "\n"
        bad["new_format"].append(name)
    else:
        lines = ["Test Program;DS20KG", f"Test Date;{d.strftime('%d/%m/%Y')}", f"Shift;{s['shift']}",
                 f"Machine;{s['machine']}", f"Model;{s['model']}", f"Condition;{s['cond']}",
                 f"LSL (g);{fmt_id(LSL)}", f"USL (g);{fmt_id(USL)}", "Sample No;Force (g)"]
        lines += [f"{j + 1};{fmt(v)}" for j, v in enumerate(vals)]
        text = "\n".join(lines) + "\n"
    if pos in corrupt:                                 # file rusak: terpotong di tengah baris
        text = text[: int(len(text) * rng.uniform(0.35, 0.8))]
        bad["corrupt"].append(name)
    (OUT / "incoming" / name).write_text(text, encoding="utf-8")
    written.append((name, text))
    if pos in dup:                                     # file yang sama masuk dua kali dengan nama berbeda
        (OUT / "incoming" / ("copy_of_" + name)).write_text(text, encoding="utf-8")
        bad["duplicate"].append(name)

gt = {"seed": SEED, "version": DATA_VERSION, "n_files_base": N_FILES, "n_rows_clean": rows_total,
      "lsl_g": LSL, "usl_g": USL,
      "mean_shift": {"machine": SHIFT_MACHINE, "from": str(START + timedelta(days=SHIFT_DAY)), "fraction": SHIFT_FRAC,
                     "note": "kalibrasi mesin"},
      "bad_files": bad}
(OUT / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{N_FILES} file + {len(bad['duplicate'])} salinan, {rows_total} baris; rusak {len(bad['corrupt'])}, "
      f"format angka {len(bad['number_format'])}, format baru {len(bad['new_format'])}")
