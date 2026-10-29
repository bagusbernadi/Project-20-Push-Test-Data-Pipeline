# Kamus data

| Tabel | Isi (1 baris = ...) | Kolom |
|---|---|---|
| `test_run` | satu file CSV yang dimuat | run_id, file_name, file_hash (SHA-256), machine_id, model, condition, test_type, shift, test_datetime, number_format (ID atau US) |
| `measurement` | satu hasil ukur | run_id, seq, force_g, judgement (OK atau NG menurut tabel spec), is_valid (0 < nilai <= kapasitas) |
| `spec` | batas spesifikasi per model dan jenis uji | model, test_type, lsl_g, usl_g (dari config.yaml) |
| `ingest_log` | satu percobaan memuat satu file | attempt, file_name, file_hash, status (loaded, skipped, quarantined), error_type, rows_read, rows_invalid, run_id |

Database `pushtest.duckdb` tidak di-commit; dibuat ulang oleh `02_ingest.py`. View KPI ada di `code/2-analysis/sql/views.sql`.

## Definisi KPI
- Max, Min, rata-rata, simpangan baku sampel: dari hasil ukur valid per kelompok.
- Cpk = min(USL - rata-rata, rata-rata - LSL) / (3 x simpangan baku). CI 95% dengan bootstrap hasil ukur.
- Out-of-spec rate = hasil ukur di luar LSL dan USL / hasil ukur valid.
- Parse success rate = file dimuat / file unik (tanpa salinan).
- Menit manual per file: asumsi (lihat definitions.md).

## Aturan validasi file (`code/ingest_lib.py`)
Hash isi sudah ada (duplikat_isi atau sudah_dimuat_sebelumnya, lewati); isi kosong (file_kosong); baris pertama `# Machine,` (format_mesin_baru); bukan header `Test Program;` (format_tidak_dikenal); nama program bukan PUSH-DS20KG atau SHEAR-DS20KG (jenis_uji_tidak_dikenal); tidak diakhiri baris baru (terpotong); header kurang (header_tidak_lengkap); baris data bukan `nomor;nilai` (baris_rusak); nilai bukan angka (nilai_bukan_angka); tanggal tidak valid; model tanpa spesifikasi. Nilai <= 0 atau di atas kapasitas ditandai tidak valid (file tetap dimuat). File gagal disalin ke karantina bersama alasan.
