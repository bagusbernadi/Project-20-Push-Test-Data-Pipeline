# Spesifikasi simulasi

Generator `00_generate_csv.py` (seed 20260401, versi data v1): 1.200 file CSV mesin push test (91 hari, 2 model, 2 kondisi, 2 mesin, 2 shift, 9 sampai 16 hasil ukur per file) ditambah 14 salinan ganda. Hasil ukur ~ Normal(rata-rata dasar + derau sesi N(0, 150), 850 g); rata-rata dasar 6.800 sampai 8.600 g. Ground truth di `data/sim/ground_truth.json`, hanya dibaca `08_ground_truth_check.py`.

Ditanam: pergeseran rata-rata PT-02 -8% mulai hari ke-52 (permanen); 2% file terpotong; 3% file berformat angka titik desimal dan koma ribuan; 1,2% file disalin; 1,5% file berformat mesin baru.

Tidak ditanam, berbeda dari rancangan: Cpk di bawah 1,33 untuk satu kombinasi, nilai tidak wajar (0, negatif, di atas kapasitas), jenis uji shear, file kosong dan kolom hilang. Pergeseran PT-02 permanen, bukan sekitar 1 minggu.
