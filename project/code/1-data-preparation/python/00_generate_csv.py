"""Project 20: file CSV simulasi mesin push/shear test untuk pipeline. Seed tetap.

+-1.200 file push test (+ 300 file shear test), +-15.000 baris hasil ukur; 2 model x 2 kondisi (sebelum/sesudah oven) x 2 mesin x 2 shift, +-3 bulan.
Hasil (data/sim/incoming/): CSV mesin (beberapa rusak, beda format angka, ganda, format mesin baru),
data/sim/ground_truth.json (daftar file bermasalah dan pergeseran). Jalankan: python3 code/1-data-preparation/python/00_generate_csv.py dari folder project/ (versi data: v3)
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from common import SIM as OUT
SEED = 20260401
DATA_VERSION = "v3"
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
UNIT_SD = {k: 850.0 for k in BASE}
UNIT_SD[("Model B", "before_oven")] = 1700.0                   # rancangan fakta 1: variasi besar sehingga Cpk di bawah 1,33
SHIFT_DAY, SHIFT_DAYS, SHIFT_MACHINE, SHIFT_G = 52, 7, "PT-02", -800.0   # rancangan fakta 2: -800 g selama 1 minggu (hari ke-52 sampai 58)
INVALID_RATE = 0.025                                           # rancangan fakta 5: 2% sampai 3% nilai tidak wajar
N_SHEAR = 300                                                 # rancangan: jenis uji shear (ASUMSI: 300 file, bersih dari file rusak, rng terpisah agar data push tidak berubah)
SHEAR_LSL, SHEAR_USL = 800.0, 11000.0
SHEAR_BASE = {("Model A", "before_oven"): 4200.0, ("Model A", "after_oven"): 5100.0, ("Model B", "before_oven"): 3900.0, ("Model B", "after_oven"): 4900.0}
SHEAR_SD = 600.0
BAD_RATES = dict(corrupt=0.02, number_format=0.03, duplicate=0.012, new_format=0.015, empty=0.008, missing_column=0.008)

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
avail = sorted(set(range(N_FILES)) - corrupt - numfmt - dup - newfmt)          # file kosong dan kolom hilang tidak bertumpuk dengan masalah lain
empty = set(int(k) for k in rng.choice(avail, int(round(BAD_RATES["empty"] * N_FILES)), replace=False))
avail = sorted(set(avail) - empty)
nocol = set(int(k) for k in rng.choice(avail, int(round(BAD_RATES["missing_column"] * N_FILES)), replace=False))
(OUT / "incoming").mkdir(parents=True, exist_ok=True)
bad = {"corrupt": [], "number_format": [], "duplicate": [], "new_format": [], "empty": [], "missing_column": []}
rows_total, written, invalid_by_file = 0, [], {}
for pos, s in enumerate(specs):
    mu = BASE[(s["model"], s["cond"])] + rng.normal(0, 150)
    if s["machine"] == SHIFT_MACHINE and SHIFT_DAY <= s["day"] < SHIFT_DAY + SHIFT_DAYS:
        mu += SHIFT_G
    vals = np.round(rng.normal(mu, UNIT_SD[(s["model"], s["cond"])], s["n"]), 1)
    bad_mask = rng.random(s["n"]) < INVALID_RATE                  # nilai tidak wajar: 0, negatif, atau di atas kapasitas mesin
    if bad_mask.any():
        kinds = rng.integers(0, 3, int(bad_mask.sum()))
        vals[bad_mask] = np.where(kinds == 0, 0.0, np.where(kinds == 1, -np.round(rng.uniform(10, 500, len(kinds)), 1), np.round(rng.uniform(20500, 30000, len(kinds)), 1)))
    n_invalid_this = int(bad_mask.sum())
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
        lines = ["Test Program;PUSH-DS20KG", f"Test Date;{d.strftime('%d/%m/%Y')}", f"Shift;{s['shift']}",
                 f"Machine;{s['machine']}", f"Model;{s['model']}", f"Condition;{s['cond']}",
                 f"LSL (g);{fmt_id(LSL)}", f"USL (g);{fmt_id(USL)}", "Sample No;Force (g)"]
        lines += [f"{j + 1};{fmt(v)}" for j, v in enumerate(vals)]
        text = "\n".join(lines) + "\n"
    if pos in empty:                                   # file kosong (isi hanya baris kosong; panjang beda agar isi tidak identik)
        text = "\n" * (len(bad["empty"]) + 1)
        bad["empty"].append(name)
    elif pos in nocol:                                 # kolom hilang: kolom Force (g) tidak ada
        text = "\n".join(l.split(";")[0] if i >= 8 else l for i, l in enumerate(text.rstrip("\n").split("\n"))) + "\n"
        bad["missing_column"].append(name)
    if pos in corrupt:                                 # file rusak: terpotong di tengah baris
        text = text[: int(len(text) * rng.uniform(0.35, 0.8))]
        bad["corrupt"].append(name)
    if n_invalid_this:
        invalid_by_file[name] = n_invalid_this
    (OUT / "incoming" / name).write_text(text, encoding="utf-8")
    written.append((name, text))
    if pos in dup:                                     # file yang sama masuk dua kali dengan nama berbeda
        (OUT / "incoming" / ("copy_of_" + name)).write_text(text, encoding="utf-8")
        bad["duplicate"].append(name)

# shear test: aliran terpisah dengan rng sendiri (data push tidak berubah). Tidak terkena pergeseran mesin dan tidak ada file rusak; nilai tak wajar sama.
rng_s = np.random.default_rng(SEED + 1)
shear_files = []
for k in range(N_SHEAR):
    day, model, cond = int(rng_s.integers(0, N_DAYS)), MODELS[int(rng_s.integers(0, 2))], CONDS[int(rng_s.integers(0, 2))]
    machine, shift, n = MACHINES[int(rng_s.integers(0, 2))], SHIFTS[int(rng_s.integers(0, 2))], int(rng_s.integers(9, 17))
    vals = np.round(rng_s.normal(SHEAR_BASE[(model, cond)] + rng_s.normal(0, 100), SHEAR_SD, n), 1)
    bm = rng_s.random(n) < INVALID_RATE
    if bm.any():
        kd = rng_s.integers(0, 3, int(bm.sum()))
        vals[bm] = np.where(kd == 0, 0.0, np.where(kd == 1, -np.round(rng_s.uniform(10, 500, len(kd)), 1), np.round(rng_s.uniform(20500, 30000, len(kd)), 1)))
    d = START + timedelta(days=day)
    name = f"{machine}_{d.strftime('%Y%m%d')}_{shift.replace(' ', '')}_{model.replace(' ', '')}_{cond}_{N_FILES + k + 1:04d}.csv"
    lines = ["Test Program;SHEAR-DS20KG", f"Test Date;{d.strftime('%d/%m/%Y')}", f"Shift;{shift}", f"Machine;{machine}", f"Model;{model}", f"Condition;{cond}",
             f"LSL (g);{fmt_id(SHEAR_LSL)}", f"USL (g);{fmt_id(SHEAR_USL)}", "Sample No;Force (g)"] + [f"{j + 1};{fmt_id(v)}" for j, v in enumerate(vals)]
    (OUT / "incoming" / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    shear_files.append(name); rows_total += n
    if int(bm.sum()):
        invalid_by_file[name] = int(bm.sum())

gt = {"seed": SEED, "version": DATA_VERSION, "n_files_base": N_FILES, "n_rows_clean": rows_total,
      "lsl_g": LSL, "usl_g": USL,
      "invalid_by_file": invalid_by_file, "shear_files": shear_files, "shear_spec": [SHEAR_LSL, SHEAR_USL],
      "mean_shift": {"machine": SHIFT_MACHINE, "from": str(START + timedelta(days=SHIFT_DAY)), "to": str(START + timedelta(days=SHIFT_DAY + SHIFT_DAYS - 1)),
                     "delta_g": SHIFT_G, "note": "kalibrasi mesin salah selama 1 minggu"},
      "bad_files": bad}
(OUT / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{N_FILES} file + {len(bad['duplicate'])} salinan, {rows_total} baris; rusak {len(bad['corrupt'])}, "
      f"format angka {len(bad['number_format'])}, format baru {len(bad['new_format'])}, kosong {len(bad['empty'])}, kolom hilang {len(bad['missing_column'])}, nilai tak wajar {sum(invalid_by_file.values())}")
