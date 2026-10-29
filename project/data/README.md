# Data

Semua data di project ini simulasi (karangan), dibuat oleh generator dengan seed tetap. Tidak ada dataset publik atau data perusahaan, jadi tidak ada masalah lisensi.

| | |
|---|---|
| Versi data | v2 (v1 tidak menanam Cpk rendah, nilai tidak wajar, file kosong, kolom hilang; penurunan PT-02 permanen) |
| Tanggal dibuat | v1: 28 Okt 2026, v2: 29 Okt 2026 |
| Seed | 20260401 |
| Cara membuat ulang | `python3 code/1-data-preparation/python/00_generate_csv.py` (dari folder project) |
| Hasil v2 | 1.200 file CSV unik + 14 salinan ganda (14.990 baris hasil ukur di semua file; 14.253 dimuat ke database setelah 59 file dikarantina dan 14 salinan dilewati) |

Isi folder ini tidak di-commit (lihat `.gitignore`). Jejak pembuatan (seed, commit, SHA-256 hasil) dicatat di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) dan diverifikasi oleh `01_verify_fingerprint.py` terhadap `project/docs/datacenter_fingerprint.csv`. Jika generator, seed, atau versi library berubah, hasil berubah dan versi data harus dinaikkan.
