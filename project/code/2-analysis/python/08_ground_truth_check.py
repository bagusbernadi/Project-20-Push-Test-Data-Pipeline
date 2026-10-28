"""08: Uji pemulihan fakta yang ditanam (Q11), uji idempoten (Q12), hasil pytest, dan lima fakta data rancangan.

Ground truth (data/sim/ground_truth.json) hanya dibaca di skrip ini, bukan di analisis. Alasan dianggap benar:
format baru -> format_mesin_baru; file terpotong -> alasan terpotong atau header/baris rusak; salinan -> duplikat_isi; format angka -> dimuat dengan number_format US.
"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import pandas as pd
import common as CM

gt = json.loads((CM.SIM / "ground_truth.json").read_text(encoding="utf-8"))
bad = gt["bad_files"]
log = pd.read_csv(CM.RES1 / "ingest_log.csv").set_index("file_name")
con = duckdb.connect(str(CM.DB_PATH), read_only=True)
fmt = dict(con.execute("SELECT file_name, number_format FROM test_run").fetchall())
con.close()
TRUNC_OK = {"terpotong", "header_tidak_lengkap", "baris_rusak", "nilai_bukan_angka", "tanggal_tidak_valid"}
newf, corr, dup, numf = set(bad["new_format"]), set(bad["corrupt"]), set(bad["duplicate"]), set(bad["number_format"])
rows = []
def add(kat, names, check):
    ok = sum(1 for n in names if check(n))
    rows.append(dict(jenis=kat, ditanam=len(names), terdeteksi=ok, tidak_terdeteksi=len(names) - ok))
add("format mesin baru", sorted(newf), lambda n: log.loc[n, "status"] == "quarantined" and log.loc[n, "error_type"] == "format_mesin_baru")
add("file terpotong (bukan format baru)", sorted(corr - newf), lambda n: log.loc[n, "status"] == "quarantined" and log.loc[n, "error_type"] in TRUNC_OK)
add("file terpotong yang juga format baru", sorted(corr & newf), lambda n: log.loc[n, "status"] == "quarantined")
add("salinan ganda (nama copy_of_)", sorted("copy_of_" + n for n in dup), lambda n: log.loc[n, "status"] == "skipped" and log.loc[n, "error_type"] == "duplikat_isi")
add("format angka titik/koma lain (tidak rusak)", sorted(numf - corr - newf), lambda n: log.loc[n, "status"] == "loaded" and fmt.get(n) == "US")
gtd = pd.DataFrame(rows)
gtd.to_csv(CM.RES2 / "ground_truth_files.csv", index=False)
all_bad = newf | corr
normal = [n for n in log.index if not n.startswith("copy_of_") and n not in all_bad]
n_loaded_normal = sum(1 for n in normal if log.loc[n, "status"] == "loaded")
false_q = [n for n in normal if log.loc[n, "status"] == "quarantined"]
extra = dict(file_normal=len(normal), file_normal_dimuat=n_loaded_normal, file_normal_salah_karantina=len(false_q), file_rusak_ditanam=len(all_bad),
             file_rusak_lolos_dimuat=int(sum(1 for n in all_bad if log.loc[n, "status"] == "loaded")), file_dikarantina=int((log.status == "quarantined").sum()))
pd.DataFrame([extra]).to_csv(CM.RES2 / "ground_truth_normal.csv", index=False)

# fakta rancangan: nilai tak wajar, Cpk, dan pergeseran
cpk = pd.read_csv(CM.RES2 / "cpk_group.csv"); cp = pd.read_csv(CM.RES2 / "changepoint.csv").set_index("machine_id")
bad_vals = int(log.rows_invalid.sum())
ms = gt["mean_shift"]
shift_row = cp.loc[ms["machine"]]
other = [m for m in cp.index if m != ms["machine"]][0]
facts = pd.DataFrame([
    dict(fakta=1, rancangan="satu kombinasi dibuat bervariasi besar sehingga Cpk < 1,33", ukuran="Cpk terendah", nilai=cpk.cpk.min(), nilai2=float(cpk.di_bawah_cpk_target.sum()), keterangan="kombinasi di bawah 1,33"),
    dict(fakta=2, rancangan="rata-rata satu mesin turun sekitar 800 g selama sekitar 1 minggu setelah kalibrasi", ukuran="selisih rata-rata mesin PT-02 setelah titik ubah (g)", nilai=shift_row.selisih_g,
         nilai2=float(pd.Timestamp(shift_row.tanggal_titik_ubah) == pd.Timestamp(ms["from"])), keterangan="tanggal titik ubah sama dengan tanggal tertanam"),
    dict(fakta=3, rancangan="sekitar 3% file berformat titik ribuan dan koma desimal", ukuran="persen file dengan format angka lain", nilai=len(numf) / gt["n_files_base"], nilai2=float(len(numf)), keterangan="file tertanam"),
    dict(fakta=4, rancangan="file bermasalah: header berbeda, kolom hilang, file kosong, file ganda", ukuran="jenis file bermasalah tertanam", nilai=float(len(newf) + len(corr) + len(dup)), nilai2=float(len(dup)), keterangan="file bermasalah tertanam (salinan)"),
    dict(fakta=5, rancangan="2% sampai 3% nilai tidak wajar (0, negatif, di atas kapasitas)", ukuran="hasil ukur tidak valid di data", nilai=float(bad_vals), nilai2=float(bad_vals) / 14990, keterangan="baris tidak valid"),
])
facts.to_csv(CM.RES2 / "design_facts.csv", index=False, float_format="%.10g")
cpd = pd.DataFrame([dict(mesin_tertanam=ms["machine"], tanggal_tertanam=ms["from"], persen_tertanam=ms["fraction"], tanggal_terdeteksi=shift_row.tanggal_titik_ubah, persen_terdeteksi=shift_row.persen_dari_rata,
                         p_permutasi=shift_row.p_permutasi, mesin_lain=other, p_permutasi_mesin_lain=cp.loc[other].p_permutasi)])
cpd.to_csv(CM.RES2 / "ground_truth_shift.csv", index=False, float_format="%.10g")

# idempoten
att = pd.read_csv(CM.RES1 / "ingest_attempts.csv"); tb = pd.read_csv(CM.RES1 / "db_tables.csv")
p = tb.pivot(index="tabel", columns="percobaan", values="baris")
idem = pd.DataFrame([dict(tabel=t, setelah_percobaan_1=int(p.loc[t, 1]), setelah_percobaan_2=int(p.loc[t, 2]), tambahan=int(p.loc[t, 2] - p.loc[t, 1])) for t in ("test_run", "measurement", "ingest_log")])
idem.to_csv(CM.RES2 / "idempotency.csv", index=False)

# pytest
xml = CM.RES2 / "_pytest.xml"
subprocess.run([sys.executable, "-m", "pytest", "-q", str(CM.TESTS), f"--junitxml={xml}", "-p", "no:cacheprovider"], check=True, capture_output=True, cwd=CM.ROOT)
root = ET.parse(xml).getroot()
tc = [dict(tes=c.get("name"), hasil="gagal" if (c.find("failure") is not None or c.find("error") is not None) else "lulus") for c in root.iter("testcase")]
xml.unlink()
pd.DataFrame(tc).to_csv(CM.RES2 / "pytest_result.csv", index=False)
print(gtd.to_string(index=False)); print(pd.DataFrame([extra]).T); print(facts.to_string()); print(cpd.T); print(idem); print(pd.DataFrame(tc).hasil.value_counts())
