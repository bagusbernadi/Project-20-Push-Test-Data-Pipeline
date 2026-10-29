# Definisi dan asumsi (label ASUMSI = tidak ada di rancangan)

- **ASUMSI** Kapasitas mesin 20.000 g (nama program PUSH-DS20KG dan SHEAR-DS20KG); nilai <= 0 atau di atas kapasitas tidak valid.
- **ASUMSI** Format angka: bila ada koma dan titik, simbol paling kanan desimal; hanya koma desimal koma; hanya titik desimal titik. File berformat titik desimal diberi number_format US.
- **ASUMSI** File yang tidak diakhiri baris baru dianggap terpotong.
- **ASUMSI** Macro lama ditiru seperti di old_process.md; angka rekonsiliasi bergantung pada tiruan ini.
- **ASUMSI** 5 menit manual per file (sensitivitas 3 dan 10) dan volume tahunan = file dimuat periode data x 365 / 91; hasil berlabel estimated.
- **ASUMSI** Cpk dihitung dari hasil ukur valid yang digabung per model dan kondisi (bukan per sesi); minimal 30 hasil ukur (rancangan).
- **ASUMSI** Kelompok shift dan mesin diuji pada rata-rata sesi dikurangi rata-rata model x kondisi (Mann-Whitney, Holm atas dua uji).
- **ASUMSI** Titik ubah: pindai pada 15% sampai 85% sesi per mesin; uji permutasi 300 kali atas |t Welch| maksimum.
- **ASUMSI** Shear test: spesifikasi 800 sampai 11.000 g dan nilai dasar simulasi karangan; jenis uji dibaca dari nama program mesin (program lain masuk karantina jenis_uji_tidak_dikenal). Analisis Cpk, tren, rekonsiliasi macro, dan dashboard hanya untuk push test; shear hanya punya `v_kpi_shear` dan cek silangnya.
- Data lot lem tidak ada di data; Q8 hanya bisa menunjukkan tanggal pergeseran, bukan penyebabnya.
- Alpha 0,05; bootstrap 2.000; seed 20.
