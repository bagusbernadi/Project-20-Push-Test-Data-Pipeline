[← Back to portfolio](https://bagusbernadi.github.io/)

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

- Data simulasi (100% karangan), dibuat `00_generate_csv.py` (seed 20260401): 1.200 file unik ditambah 14 salinan, 14.476 hasil ukur dimuat. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`01_verify_fingerprint.py`).
- Tabel: `test_run`, `measurement`, `spec`, `ingest_log`. Kamus data: `project/docs/data_dictionary.md`.

## 3. Analysis

Pipeline: hash isi, baca format, validasi, karantina, muat ke DuckDB; KPI lewat view SQL (`project/code/2-analysis/sql/views.sql`). Definisi dan asumsi: `project/docs/definitions.md`.

- 1.159 dari 1.200 file unik dimuat (96,6%); 41 masuk karantina dengan alasan; percobaan kedua menambah 0 baris test_run dan 0 baris measurement.
- Macro lama (ditiru) salah membaca 436 nilai (3,0%) di 36 file.
- Cpk per model dan kondisi (semua di atas 1,33; spesifikasi lebar):

| Kombinasi | Hasil ukur | Cpk (CI 95%) | Out-of-spec |
|---|---|---|---|
| Model B before_oven | 3.507 | 1,95 (1,90 sampai 2,00) | 0,00% |
| Model A before_oven | 3.854 | 2,06 (2,01 sampai 2,11) | 0,00% |
| Model B after_oven | 3.584 | 2,45 (2,39 sampai 2,51) | 0,00% |
| Model A after_oven | 3.531 | 2,58 (2,52 sampai 2,65) | 0,00% |

- Pergeseran rata-rata mesin PT-02 terdeteksi mulai 2026-05-23 (-8,3%); tanggal sama dengan yang ditanam.

## 4. Recommendation

Jalankan pipeline terjadwal dan tinjau folder karantina; tambahkan aturan untuk format mesin baru; selidiki kalibrasi mesin PT-02; pantau jarak rata-rata ke LSL karena spesifikasi lebar.

## 5. Impact

Estimasi (`estimated`): sekitar 387 jam kerja manual per tahun (5 menit per file x 4.649 file per tahun; menit per file adalah asumsi).

```
jam hemat per tahun = file dimuat per tahun x menit manual per file / 60
```

## Batasan

- **Data adalah simulasi**; angka menggambarkan simulasi, bukan lini produksi.
- Macro lama ditiru dari deskripsi rancangan; workbook asli tidak tersedia. Menit manual per file, kapasitas mesin, dan aturan baca angka adalah asumsi.
- Fakta rancangan hanya sebagian ditanam: tidak ada Cpk di bawah 1,33, tidak ada nilai tidak wajar, tidak ada jenis uji shear; pergeseran mesin permanen, bukan sekitar 1 minggu.
- Dashboard belum di-deploy (diuji AppTest: 13 dari 13 lulus) dan success criteria "orang awam menyebut kombinasi Cpk terendah dalam 1 menit" belum diuji; slide dan file contoh di data/samples tidak dibuat; branch belum di-merge ke main.
- Cek silang: 5.989 dari 199 cocok; pytest 11 dari 11 lulus.

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
  code/                        common.py, ingest_lib.py; 1-data-preparation/{python,sql} (00 sampai 02); 2-analysis/{python,sql} (03 sampai 08); 3-presentation/{python,streamlit} (09 sampai 12)
  config.yaml                  alamat folder dan spesifikasi
  tests/                       test_ingest.py (pytest)
  results/                     1-data-preparation/ 2-analysis/ 3-presentation/ (CSV hasil, analysis.ipynb)
  outputs/                     reconciliation.xlsx
  data/                        README.md (data tidak di-commit)
  docs/                        data_dictionary.md, old_process.md, definitions.md, simulation_spec.md, datacenter_fingerprint.csv
  run20.sh, requirements.txt
```
