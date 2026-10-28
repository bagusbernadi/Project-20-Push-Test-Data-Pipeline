# Proses lama (macro VBA dan copy-paste)

Workbook dan macro asli tidak tersedia di project ini. Macro lama ditiru di `05_reconcile_macro.py` berdasarkan deskripsi rancangan (ASUMSI):

- Macro membaca semua `*.csv` di folder, melewati 9 baris header, mengambil kolom kedua.
- Angka diubah dengan aturan lokal Indonesia: titik dianggap pemisah ribuan (dihapus), koma dianggap desimal. Nilai `8,245.6` terbaca `8,2456`.
- Format mesin baru (header berbeda) tidak terbaca.
- File terpotong dibaca sebagian; file salinan terbaca dua kali.
- Waktu manual per file 5 menit (asumsi, sensitivitas 3 dan 10 menit).
