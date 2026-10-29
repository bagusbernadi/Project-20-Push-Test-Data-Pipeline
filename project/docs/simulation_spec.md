# Spesifikasi simulasi

Generator `00_generate_csv.py` (seed 20260401, versi data v3): 1.200 file CSV mesin push test (91 hari, 2 model, 2 kondisi, 2 mesin, 2 shift, 9 sampai 16 hasil ukur per file) ditambah 14 salinan ganda dan 300 file shear test (lihat bawah). Hasil ukur ~ Normal(rata-rata dasar + derau sesi N(0, 150), 850 g); rata-rata dasar 6.800 sampai 8.600 g. Ground truth di `data/sim/ground_truth.json`, hanya dibaca `08_ground_truth_check.py`.

Ditanam (lima fakta data rancangan, semuanya pada aliran push test):
- Fakta 1: Model B sebelum oven memakai simpangan baku 1.700 g (kombinasi lain 850 g) sehingga Cpk di bawah 1,33.
- Fakta 2: rata-rata PT-02 turun 800 g selama 7 hari (hari ke-52 sampai 58), lalu kembali normal.
- Fakta 3: 3% file berformat angka titik desimal dan koma ribuan.
- Fakta 4: 2% file terpotong, 1,2% disalin, 1,5% berformat mesin baru, 0,8% kosong, 0,8% kolom Force hilang (kosong dan kolom hilang tidak bertumpuk dengan masalah lain).
- Fakta 5: 2,5% hasil ukur diganti nilai tidak wajar (sepertiga nol, sepertiga negatif, sepertiga di atas kapasitas 20.000 g); daftar per file ada di ground truth.

Jenis uji shear (rancangan: test_type push / shear), ditambahkan di v3 dengan rng terpisah (seed 20260402) sehingga data push tidak berubah: 300 file bersih dari file rusak (tanpa salinan, format angka lain, atau pergeseran mesin), 9 sampai 16 hasil ukur per file, Normal(rata-rata dasar + derau sesi N(0, 100), 600 g); rata-rata dasar 3.900 sampai 5.100 g; nilai tidak wajar sama (2,5%). Angka dasar dan spesifikasi shear 800 sampai 11.000 g adalah ASUMSI karena rancangan tidak memberinya. Jenis uji dibedakan lewat nama program mesin (`PUSH-DS20KG` atau `SHEAR-DS20KG`) di baris pertama file.

Parameter (laju, simpangan baku, durasi) disetel agar fakta cukup besar untuk terdeteksi; jendela penurunan 7 hari saat analisis adalah asumsi analis, bukan dibaca dari ground truth.
