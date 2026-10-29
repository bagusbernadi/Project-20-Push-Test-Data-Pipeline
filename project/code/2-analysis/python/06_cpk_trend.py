"""06: Cpk, out-of-spec, shift dan mesin, tren mingguan, dan pergeseran (Q4 sampai Q8). Memakai view SQL dan tabel DuckDB.

Cpk = min(USL - mean, mean - LSL) / (3 s), s simpangan baku sampel. CI Cpk: bootstrap hasil ukur (B dan seed dari common.py).
Pergeseran: pindai jendela 7 hari per mesin (ASUMSI, sensitivitas 5 dan 10 hari) pada rata-rata sesi (selisih dari rata-rata model dan kondisi); uji permutasi atas nilai maksimum |t Welch|.
Ground truth tidak dibaca di sini (hanya di 08_ground_truth_check.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import numpy as np
import pandas as pd
from scipy import stats
import common as CM

con = duckdb.connect(str(CM.DB_PATH))
con.execute((CM.SQL_DIR / "views.sql").read_text(encoding="utf-8"))
v = con.execute("SELECT * FROM v_measure ORDER BY run_id, seq").df(); runs = con.execute("SELECT * FROM v_kpi_run ORDER BY run_id").df()
con.close()
rng = np.random.default_rng(CM.SEED)


def cpk(x):
    m, s = x.mean(), x.std(ddof=1)
    return min(CM.USL - m, m - CM.LSL) / (3 * s)


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0, c - h / d), min(1, c + h / d)


rows = []
for (m, c), d in v.groupby(["model", "condition"]):
    x = d.force_g.values
    bs = np.array([cpk(rng.choice(x, len(x))) for _ in range(CM.BOOT_B)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    below, above = int((x < CM.LSL).sum()), int((x > CM.USL).sum())
    wl, wh = wilson(below + above, len(x))
    rows.append(dict(model=m, condition=c, n=len(x), sesi=d.run_id.nunique(), mean_g=x.mean(), sd_g=x.std(ddof=1), cpk=cpk(x), cpk_ci_low=lo, cpk_ci_high=hi,
                     jarak_ke_lsl_sd=(x.mean() - CM.LSL) / x.std(ddof=1), di_bawah_cpk_target=int(cpk(x) < CM.CPK_TARGET), n_cukup=int(len(x) >= CM.MIN_N_CPK),
                     oos_n=below + above, oos_rate=(below + above) / len(x), oos_ci_low=wl, oos_ci_high=wh, batas_atas_aturan_tiga=3 / len(x)))
cp = pd.DataFrame(rows).sort_values(["cpk", "model", "condition"]).reset_index(drop=True)
cp.insert(0, "peringkat", range(1, len(cp) + 1))
cp.to_csv(CM.RES2 / "cpk_group.csv", index=False, float_format="%.10g")

runs["resid"] = runs.mean_g - runs.groupby(["model", "condition"]).mean_g.transform("mean")
runs["date"] = pd.to_datetime(runs.test_datetime)
sm = []
for f, a, b in (("shift", "Shift 1", "Shift 2"), ("machine_id", "PT-01", "PT-02")):
    x, y = runs[runs[f] == a].resid, runs[runs[f] == b].resid
    u, p = stats.mannwhitneyu(x, y)
    sm.append(dict(faktor=f, kelompok_a=a, kelompok_b=b, sesi_a=len(x), sesi_b=len(y), median_resid_a=x.median(), median_resid_b=y.median(), selisih_rata_g=y.mean() - x.mean(), p_mannwhitney=p))
pd.DataFrame(sm).to_csv(CM.RES2 / "shift_machine_test.csv", index=False, float_format="%.10g")

wall = v.groupby("iso_week").force_g.agg(["count", "mean", "std"]).reset_index().rename(columns={"count": "n", "mean": "mean_g", "std": "sd_g"})
wall["cpk"] = [min(CM.USL - r.mean_g, r.mean_g - CM.LSL) / (3 * r.sd_g) for r in wall.itertuples()]
wall["n_cukup"] = (wall.n >= CM.MIN_N_CPK).astype(int)
wall.to_csv(CM.RES2 / "weekly_all.csv", index=False, float_format="%.10g")
wm = v.groupby(["iso_week", "machine_id"]).force_g.agg(["count", "mean"]).reset_index().rename(columns={"count": "n", "mean": "mean_g"})
wm.to_csv(CM.RES2 / "weekly_machine.csv", index=False, float_format="%.10g")

WIN_DAYS = 7          # ASUMSI: panjang jendela penurunan 7 hari kalender (rancangan: sekitar 1 minggu); sensitivitas 5 dan 10 hari
MIN_IN = 3            # ASUMSI: minimal 3 sesi di dalam jendela dan di luar jendela


def dip_scan(day, r, L):
    """Pindai jendela L hari: statistik |t Welch| rata-rata sesi di dalam vs di luar jendela; kembalikan (t, hari mulai) terbesar."""
    nd = int(day.max()) + 1; N = len(r)
    c = np.concatenate([[0], np.bincount(day, minlength=nd).cumsum()])
    a = np.concatenate([[0.0], np.bincount(day, r, nd).cumsum()])
    b = np.concatenate([[0.0], np.bincount(day, r * r, nd).cumsum()])
    best = (0.0, 0)
    for st in range(0, nd - L + 1):
        n1 = c[st + L] - c[st]; n2 = N - n1
        if n1 < MIN_IN or n2 < MIN_IN:
            continue
        s1, q1 = a[st + L] - a[st], b[st + L] - b[st]
        m1, m2 = s1 / n1, (a[-1] - s1) / n2
        v1, v2 = (q1 - n1 * m1 ** 2) / (n1 - 1), ((b[-1] - q1) - n2 * m2 ** 2) / (n2 - 1)
        t = abs(m1 - m2) / np.sqrt(v1 / n1 + v2 / n2)
        if t > best[0]:
            best = (t, st)
    return best


def scan_machine(d, L, n_perm=1000):
    d = d.sort_values(["date", "run_id"]).reset_index(drop=True)
    day = (d.date - d.date.min()).dt.days.values; r = d.resid.values
    t, st = dip_scan(day, r, L)
    pr = np.random.default_rng(CM.SEED + 1)
    perm = [dip_scan(day, pr.permutation(r), L)[0] for _ in range(n_perm)]
    inw = (day >= st) & (day < st + L)
    start = d.date.min() + pd.Timedelta(days=int(st))
    return dict(sesi=len(d), tanggal_mulai=start.date().isoformat(), tanggal_selesai=(start + pd.Timedelta(days=L - 1)).date().isoformat(), sesi_di_luar=int((~inw).sum()), sesi_di_jendela=int(inw.sum()),
                rata_luar_resid=r[~inw].mean(), rata_jendela_resid=r[inw].mean(), selisih_g=r[inw].mean() - r[~inw].mean(), persen_dari_rata=(r[inw].mean() - r[~inw].mean()) / d.mean_g.mean(),
                t_welch=t, p_permutasi=(1 + sum(p >= t for p in perm)) / (len(perm) + 1))


cps = [dict(machine_id=mc, **scan_machine(d, WIN_DAYS)) for mc, d in runs.groupby("machine_id")]
pd.DataFrame(cps).to_csv(CM.RES2 / "changepoint.csv", index=False, float_format="%.10g")
sens = [dict(machine_id=mc, panjang_jendela_hari=L, **{k: v for k, v in scan_machine(d, L, 300).items() if k in ("tanggal_mulai", "tanggal_selesai", "selisih_g", "p_permutasi")})
        for L in (5, WIN_DAYS, 10) for mc, d in runs.groupby("machine_id")]
pd.DataFrame(sens).to_csv(CM.RES2 / "dip_sensitivity.csv", index=False, float_format="%.10g")
print(cp[["peringkat", "model", "condition", "n", "cpk", "cpk_ci_low", "cpk_ci_high", "oos_rate"]]); print(pd.DataFrame(sm)); print(pd.DataFrame(cps).T)
