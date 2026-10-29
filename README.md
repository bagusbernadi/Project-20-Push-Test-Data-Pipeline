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

- Data simulasi (100% karangan), dibuat `00_generate_csv.py` (seed 20260401): 1.500 file unik ditambah 14 salinan, 18.003 hasil ukur dimuat. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`01_verify_fingerprint.py`).
- Tabel: `test_run`, `measurement`, `spec`, `ingest_log`. Kamus data: `project/docs/data_dictionary.md`.

## 3. Analysis

Pipeline: hash isi, baca format, validasi, karantina, muat ke DuckDB; KPI lewat view SQL (`project/code/2-analysis/sql/views.sql`). Definisi dan asumsi: `project/docs/definitions.md`.

- 1.440 dari 1.500 file unik dimuat (96,0%); 60 masuk karantina dengan alasan; percobaan kedua menambah 0 baris test_run dan 0 baris measurement.
- Macro lama (ditiru) salah membaca 424 nilai (3,1%) di 36 file.
- Cpk per model dan kondisi (1 dari 4 kombinasi di bawah 1,33):

| Kombinasi | Hasil ukur | Cpk (CI 95%) | Out-of-spec |
|---|---|---|---|
| Model B before_oven | 3.359 | 1,04 (1,02 sampai 1,07) | 0,12% |
| Model A before_oven | 3.722 | 2,12 (2,07 sampai 2,18) | 0,00% |
| Model B after_oven | 3.412 | 2,56 (2,50 sampai 2,63) | 0,00% |
| Model A after_oven | 3.399 | 2,73 (2,67 sampai 2,80) | 0,00% |

- Penurunan rata-rata mesin PT-02 terdeteksi 2026-05-23 sampai 2026-05-29 (-808 g, -10,6%); tanggal mulai sama dengan yang ditanam (jendela 7 hari adalah asumsi).

## 4. Recommendation

Jalankan pipeline terjadwal dan tinjau folder karantina; tambahkan aturan untuk format mesin baru; selidiki kalibrasi mesin PT-02; turunkan variasi kombinasi dengan Cpk di bawah 1,33 dan pantau jarak rata-rata ke LSL.

## 5. Impact

Estimasi (`estimated`): sekitar 481 jam kerja manual per tahun (5 menit per file x 5.776 file per tahun; menit per file adalah asumsi).

```
jam hemat per tahun = file dimuat per tahun x menit manual per file / 60
```

## Batasan

- **Data adalah simulasi**; angka menggambarkan simulasi, bukan lini produksi.
- Macro lama ditiru dari deskripsi rancangan; workbook asli tidak tersedia. Menit manual per file, kapasitas mesin, dan aturan baca angka adalah asumsi.
- Lima fakta data rancangan ditanam dan terdeteksi. Aliran shear test ditambahkan dengan nilai dasar dan spesifikasi asumsi; analisis Cpk, tren, dan dashboard hanya untuk push test. Generator dan pipeline ditulis oleh orang yang sama, jadi uji pemulihan optimistis.
- Dashboard belum di-deploy (diuji AppTest: 13 dari 13 lulus) dan success criteria "orang awam menyebut kombinasi Cpk terendah dalam 1 menit" belum diuji; slide dan file contoh di data/samples tidak dibuat; branch belum di-merge ke main.
- Cek silang: 5.910 dari 215 cocok; pytest 13 dari 13 lulus.

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
