[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 20: Push Test Data Pipeline + Dashboard

**Status: Design (rancangan).**

**Tujuan:** Membangun pipeline yang membaca file CSV mesin push test secara otomatis, membersihkan angkanya, dan menyimpannya di database, sehingga Max, Min, rata-rata, dan Cpk kekuatan rekat per model dan kondisi proses bisa dipantau di dashboard tanpa macro VBA dan copy-paste manual.


| | |
|---|---|
| Kategori | Manufaktur (perakitan lampu depan sepeda motor) |
| Tingkat | Menengah |
| Data | Simulasi: file CSV mesin push/shear test (perekatan lensa lampu depan sepeda motor, Model A/B, sebelum/sesudah oven) |
| Tools | Python (pandas), DuckDB + SQL, Streamlit + Plotly, pytest, Excel (cek silang), GitHub |

## 1. Problem
Bagaimana mengganti macro VBA dan copy-paste manual agar data CSV mesin push test otomatis masuk database, terbaca dengan benar, dan siap dianalisis per model dan kondisi proses?

## 2. Data
Data simulasi buatan sendiri, dibuat oleh `scripts/generate_csv.py` (seed tetap). Perkiraan ±1.200 file CSV dan ±15.000 baris hasil ukur (2 model, 2 kondisi, 2 mesin, 2 shift, ±3 bulan). File rusak, salah format angka, dan pergeseran sengaja ditanam sebagai ground truth. Tidak memakai data perusahaan.

## 3. Analysis
Rencana: parse success rate, rekonsiliasi dengan workbook lama, Max/Min/rata-rata/Cpk dan out-of-spec rate per model dan kondisi, tren mingguan. Belum dikerjakan.

## 4. Recommendation
Belum dikerjakan.

## 5. Impact
Belum dikerjakan. Angka dampak akan diberi label `estimated` / `simulated`.

## Batasan yang sudah diketahui
- Cpk dari kurang dari ±30 hasil ukur tidak stabil.
- Rentang spesifikasi 1.500–19.000 g lebar, sehingga Cpk lebih ditentukan batas bawah.
- Format mesin baru masuk karantina sampai aturannya ditambahkan.
- Waktu manual per file adalah estimasi.

## Struktur repository (rencana)
```
docs/            # proses lama, kamus data, definisi KPI
scripts/         # generator CSV simulasi
pipeline/        # parser, validasi, pemuatan ke DuckDB
sql/             # view KPI
tests/           # tes parser
notebooks/       # analisis
dashboard/       # aplikasi Streamlit
index.html       # halaman rancangan (GitHub Pages)
README.md
```
