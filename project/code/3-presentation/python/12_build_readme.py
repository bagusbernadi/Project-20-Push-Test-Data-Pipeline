"""12: README.md dari CSV hasil (angka tidak diketik). Dijalankan paling akhir sebelum build_report.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

R1, R2, R3 = CM.RES1, CM.RES2, CM.RES3
att = pd.read_csv(R1 / "ingest_attempts.csv"); cp = pd.read_csv(R2 / "cpk_group.csv"); imp = pd.read_csv(R2 / "impact.csv"); imp = imp[imp.dasar == 1].iloc[0]
n_below = int(cp.di_bawah_cpk_target.sum()); ms = pd.read_csv(R2 / "macro_summary.csv").iloc[0]; cx = pd.read_csv(R2 / "crosscheck.csv"); dt = pd.read_csv(R3 / "dashboard_test.csv"); pt = pd.read_csv(R2 / "pytest_result.csv")
gs = pd.read_csv(R2 / "ground_truth_shift.csv").iloc[0]; gf = pd.read_csv(R2 / "ground_truth_files.csv"); idem = pd.read_csv(R2 / "idempotency.csv").set_index("tabel"); db = pd.read_csv(R1 / "db_tables.csv")


def I(n): return f"{int(round(float(n))):,}".replace(",", ".")
def D(x, d=1): return f"{float(x):.{d}f}".replace(".", ",")
def P(x, d=1): return D(float(x) * 100, d) + "%"


a1 = att.iloc[0]; uniq = int(a1.loaded + a1.quarantined)
rows = "\n".join(f"| {r.model} {r.condition} | {I(r.n)} | {D(r.cpk, 2)} ({D(r.cpk_ci_low, 2)} sampai {D(r.cpk_ci_high, 2)}) | {P(r.oos_rate, 2)} |" for r in cp.itertuples())
txt = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 20: Push Test Data Pipeline + Dashboard

**Status: Selesai di branch `project-20-build` (belum di-merge ke `main`).** Halaman rancangan dan laporan: [`design-and-report/index.html`](design-and-report/index.html) (tab Design Project dan Report Project).

**Tujuan:** membangun pipeline yang membaca file CSV mesin push test secara otomatis, membersihkan angkanya, dan menyimpannya di database, sehingga Max, Min, rata-rata, dan Cpk kekuatan rekat per model dan kondisi bisa dipantau di dashboard tanpa macro VBA dan copy-paste manual.

| | |
|---|---|
| Kategori | Manufaktur (perakitan sepeda motor) |
| Tingkat | Menengah |
| Data | **Simulasi**: file CSV yang meniru keluaran mesin push test |
| Tools | Python (parser, pandas, SciPy), DuckDB + SQL, pytest, Streamlit + Plotly, Excel (cek silang, dihitung ulang LibreOffice) |

## 1. Problem

**Pertanyaan utama:** bagaimana mengganti macro VBA dan copy-paste manual agar data CSV mesin push test otomatis masuk database, terbaca dengan benar, dan siap dianalisis per model dan kondisi proses? Rancangan memecahnya menjadi 12 pertanyaan (8 Utama, 3 Pendukung, 1 Tambahan).

## 2. Data

- Data simulasi (100% karangan), dibuat `00_generate_csv.py` (seed 20260401): {I(uniq)} file unik ditambah {I(a1.skipped)} salinan, {I(db[(db.percobaan == 1) & (db.tabel == 'measurement')].baris.iloc[0])} hasil ukur dimuat. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`01_verify_fingerprint.py`).
- Tabel: `test_run`, `measurement`, `spec`, `ingest_log`. Kamus data: `project/docs/data_dictionary.md`.

## 3. Analysis

Pipeline: hash isi, baca format, validasi, karantina, muat ke DuckDB; KPI lewat view SQL (`project/code/2-analysis/sql/views.sql`). Definisi dan asumsi: `project/docs/definitions.md`.

- {I(a1.loaded)} dari {I(uniq)} file unik dimuat ({P(a1.loaded / uniq, 1)}); {I(a1.quarantined)} masuk karantina dengan alasan; percobaan kedua menambah {I(idem.loc['test_run', 'tambahan'])} baris test_run dan {I(idem.loc['measurement', 'tambahan'])} baris measurement.
- Macro lama (ditiru) salah membaca {I(ms.nilai_berubah)} nilai ({P(ms.persen_nilai_berubah, 1)}) di {I(ms.file_terdampak)} file.
- Cpk per model dan kondisi ({n_below} dari {len(cp)} kombinasi di bawah 1,33):

| Kombinasi | Hasil ukur | Cpk (CI 95%) | Out-of-spec |
|---|---|---|---|
{rows}

- Penurunan rata-rata mesin {gs.mesin_tertanam} terdeteksi {gs.tanggal_terdeteksi} sampai {gs.tanggal_terdeteksi_selesai} ({D(gs.selisih_terdeteksi_g, 0)} g, {P(gs.persen_terdeteksi, 1)}); tanggal mulai sama dengan yang ditanam (jendela 7 hari adalah asumsi).

## 4. Recommendation

Jalankan pipeline terjadwal dan tinjau folder karantina; tambahkan aturan untuk format mesin baru; selidiki kalibrasi mesin {gs.mesin_tertanam}; turunkan variasi kombinasi dengan Cpk di bawah 1,33 dan pantau jarak rata-rata ke LSL.

## 5. Impact

Estimasi (`estimated`): sekitar {D(imp.jam_hemat_per_tahun, 0)} jam kerja manual per tahun ({D(imp.menit_per_file, 0)} menit per file x {I(imp.file_per_tahun)} file per tahun; menit per file adalah asumsi).

```
jam hemat per tahun = file dimuat per tahun x menit manual per file / 60
```

## Batasan

- **Data adalah simulasi**; angka menggambarkan simulasi, bukan lini produksi.
- Macro lama ditiru dari deskripsi rancangan; workbook asli tidak tersedia. Menit manual per file, kapasitas mesin, dan aturan baca angka adalah asumsi.
- Lima fakta data rancangan ditanam dan terdeteksi. Aliran shear test ditambahkan dengan nilai dasar dan spesifikasi asumsi; analisis Cpk, tren, dan dashboard hanya untuk push test. Generator dan pipeline ditulis oleh orang yang sama, jadi uji pemulihan optimistis.
- Dashboard belum di-deploy (diuji AppTest: {I((dt.hasil == 'lulus').sum())} dari {I(len(dt))} lulus) dan success criteria "orang awam menyebut kombinasi Cpk terendah dalam 1 menit" belum diuji; slide dan file contoh di data/samples tidak dibuat; branch belum di-merge ke main.
- Cek silang: {I(cx.cocok.sum())} dari {I(len(cx))} cocok; pytest {I((pt.hasil == 'lulus').sum())} dari {I(len(pt))} lulus.

## Menjalankan

Dari folder `project/`:

```
pip install -r requirements.txt
bash run20.sh
streamlit run code/3-presentation/streamlit/app.py
```

## Struktur repository

```
README.md
index.html                     pengalihan ke design-and-report/
design-and-report/             index.html (tab Design + Report), src/ (page_v1.html, report.css, report_lib.py, build_report.py)
project/
  code/                        common.py, ingest_lib.py; 1-data-preparation/{{python,sql}} (00 sampai 02); 2-analysis/{{python,sql}} (03 sampai 08); 3-presentation/{{python,streamlit}} (09 sampai 12)
  config.yaml                  alamat folder dan spesifikasi
  tests/                       test_ingest.py (pytest)
  results/                     1-data-preparation/ 2-analysis/ 3-presentation/ (CSV hasil, analysis.ipynb)
  outputs/                     reconciliation.xlsx
  data/                        README.md (data tidak di-commit)
  docs/                        data_dictionary.md, old_process.md, definitions.md, simulation_spec.md, datacenter_fingerprint.csv
  run20.sh, requirements.txt
```
"""
(CM.ROOT.parent / "README.md").write_text(txt, encoding="utf-8")
print("README ditulis")
