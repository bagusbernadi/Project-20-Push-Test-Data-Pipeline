"""Generator Report v2 (Project 20). Dijalankan paling akhir, setelah seluruh pipeline dijalankan ulang dari nol.

Input : design-and-report/src/page_v1.html (rancangan, pane Design TIDAK diubah), project/results/*.
Output: design-and-report/index.html
Angka di teks Report berasal dari CSV lewat helper report_lib (I, D, P, cs). audit() memeriksa token angka tak terdaftar.
"""
import math
import re
import sys
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO / "project"
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(HERE))
import pandas as pd
import common as C
import report_lib as R
from report_lib import I, D, P, cs, pill, BLUE, GREY, table, qa, legend, bars, gbars, lines, audit

SRC = (HERE / "page_v1.html").read_text(encoding="utf-8")
CSS_EXTRA = (HERE / "report.css").read_text(encoding="utf-8")
r1, r2, r3 = C.RES1, C.RES2, C.RES3
rd = lambda d, n, **k: pd.read_csv(d / n, **k)

att = rd(r1, "ingest_attempts.csv").set_index("percobaan"); ilog = rd(r1, "ingest_log.csv"); dbt = rd(r1, "db_tables.csv"); fp = rd(r1, "fingerprint_check.csv")
cpk = rd(r2, "cpk_group.csv"); kg = rd(r2, "kpi_group.csv"); kms = rd(r2, "kpi_machine_shift.csv"); kw = rd(r2, "kpi_weekly.csv"); kr = rd(r2, "kpi_run.csv")
wa = rd(r2, "weekly_all.csv"); wm = rd(r2, "weekly_machine.csv"); cp = rd(r2, "changepoint.csv").set_index("machine_id"); smt = rd(r2, "shift_machine_test.csv").set_index("faktor")
ms = rd(r2, "macro_summary.csv").iloc[0]; mgc = rd(r2, "macro_group_compare.csv"); msc = rd(r2, "macro_session_compare.csv").set_index("ukuran")
imp = rd(r2, "impact.csv"); cx = rd(r2, "crosscheck.csv"); fct = rd(r2, "design_facts.csv").set_index("fakta"); gtf = rd(r2, "ground_truth_files.csv")
gtn = rd(r2, "ground_truth_normal.csv").iloc[0]; gts = rd(r2, "ground_truth_shift.csv").iloc[0]; idem = rd(r2, "idempotency.csv").set_index("tabel"); pyt = rd(r2, "pytest_result.csv")
dtest = rd(r3, "dashboard_test.csv"); dst = rd(r3, "dashboard_status.csv")

a1, a2 = att.loc[1], att.loc[2]
uniq = int(a1.loaded + a1.quarantined)
n_cx, n_cx_ok = len(cx), int(cx.cocok.sum())
n_fp, n_fp_ok = int(fp.berkas.sum()), int(fp.cocok.sum())
n_py, n_py_ok = len(pyt), int((pyt.hasil == "lulus").sum())
n_dt, n_dt_ok = len(dtest), int((dtest.hasil == "lulus").sum())
meas = int(dbt[(dbt.percobaan == 1) & (dbt.tabel == "measurement")].baris.iloc[0])
runs = int(dbt[(dbt.percobaan == 1) & (dbt.tabel == "test_run")].baris.iloc[0])
LSL, USL = C.LSL, C.USL


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, ps[i] * (len(ps) - r)))
        adj[i] = run
    return adj


def pv(p):
    p = float(p)
    return "< 0,001" if p < 0.001 else D(p, 3)


def kp(v, l, d, color):
    return f'<div class="card kpi" style="--h:var(--{color})"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'


gname = lambda r: f"{r.model} {r.condition.replace('_', ' ')}"
ph = holm([float(smt.loc["shift", "p_mannwhitney"]), float(smt.loc["machine_id", "p_mannwhitney"])])
p_shift, p_mach = float(smt.loc["shift", "p_mannwhitney"]), float(smt.loc["machine_id", "p_mannwhitney"])
ph_shift, ph_mach = ph
# ---------- nilai turunan ----------
err = ilog[(ilog.attempt == 1) & (ilog.status != "loaded")].groupby(["status", "error_type"]).size().reset_index(name="file")
errd = {(r.status, r.error_type): int(r.file) for r in err.itertuples()}
q_trunc, q_fmt, d_dup = errd[("quarantined", "terpotong")], errd[("quarantined", "format_mesin_baru")], errd[("skipped", "duplikat_isi")]
q_empty, q_hdr = errd[("quarantined", "file_kosong")], errd[("quarantined", "header_tidak_lengkap")]
f1, f2, f3, f4, f5 = (fct.loc[i] for i in (1, 2, 3, 4, 5)); inv_pl = int(fct.loc[5, "kombinasi"]); n_below = int(cpk.di_bawah_cpk_target.sum())
sens = rd(r2, "dip_sensitivity.csv"); C_WIN = int(sorted(set(sens.panjang_jendela_hari))[1])
wk_of = lambda t: f"{file_week(t).year}-W{file_week(t).week:02d}"
w_ok = wilson(int(a1.loaded), uniq)
low = cpk.sort_values("cpk").iloc[0]; high = cpk.sort_values("cpk").iloc[-1]
cpkmin_ci = (low.cpk_ci_low, low.cpk_ci_high)
cpg = lambda col: mgc[mgc.ukuran == col]
cp_rows = mgc[mgc.ukuran == "cpk"]
d_cpk = cp_rows.selisih.abs()
d_min = mgc[mgc.ukuran == "min_g"].selisih
mean_pipe, mean_mac = ms.rata_nilai_berubah_pipeline, ms.rata_nilai_berubah_macro
file_week = lambda t: pd.Timestamp(t).isocalendar()
cpw0, cpw1 = f"{file_week(cp.loc['PT-02', 'tanggal_mulai']).year}-W{file_week(cp.loc['PT-02', 'tanggal_mulai']).week:02d}", f"{file_week(cp.loc['PT-02', 'tanggal_selesai']).year}-W{file_week(cp.loc['PT-02', 'tanggal_selesai']).week:02d}"
wk_list = list(wa.iso_week)
imp5 = imp[imp.dasar == 1].iloc[0]
imp3 = imp[imp.menit_per_file == imp.menit_per_file.min()].iloc[0]; imp10 = imp[imp.menit_per_file == imp.menit_per_file.max()].iloc[0]
nonvalid = int(fct.loc[5, "nilai"])
gt_tot = int(gtf.ditanam.sum()); gt_det = int(gtf.terdeteksi.sum())
low_q = [f"Q{n}" for n in (1, 2, 3)]

# ---------- grafik ----------
st_items = [("Dimuat", int(a1.loaded), BLUE, f"dimuat: {I(a1.loaded)} file"), ("Terpotong", q_trunc, "#E8710A", f"karantina, terpotong: {I(q_trunc)} file"),
            ("Format mesin baru", q_fmt, "#E8710A", f"karantina, format mesin baru: {I(q_fmt)} file"), ("Header tidak lengkap", q_hdr, "#E8710A", f"karantina, header tidak lengkap: {I(q_hdr)} file"), ("File kosong", q_empty, "#E8710A", f"karantina, file kosong: {I(q_empty)} file"), ("Duplikat isi", d_dup, GREY, f"dilewati, duplikat isi: {I(d_dup)} file")]
chart_status = R.hbars(st_items, lambda v: I(v), "Grafik jumlah file per status pemuatan", 1300)
chart_cpk = bars([(gname(r), float(r.cpk), BLUE, f"{gname(r)}: Cpk {D(r.cpk, 2)} (CI {D(r.cpk_ci_low, 2)} sampai {D(r.cpk_ci_high, 2)})") for r in cpk.itertuples()], lambda v: D(v, 1),
                 "Grafik Cpk per model dan kondisi", rot=0, small=True)
chart_wk = lines([w[-3:] for w in wk_list], [("PT-01", GREY, 2, [float(wm[(wm.machine_id == "PT-01") & (wm.iso_week == w)].mean_g.iloc[0]) for w in wk_list]),
                                              ("PT-02", BLUE, 2, [float(wm[(wm.machine_id == "PT-02") & (wm.iso_week == w)].mean_g.iloc[0]) for w in wk_list])],
                 lambda v: I(v), "Grafik rata-rata kekuatan rekat per minggu, per mesin", h=260,
                 bands=[i for i, w in enumerate(wk_list) if cpw0 <= w <= cpw1], band_label="jendela penurunan PT-02, minggu")
chart_cpkw = lines([w[-3:] for w in wk_list], [("Cpk", BLUE, 2, [float(v) for v in wa.cpk])], lambda v: D(v, 1), "Grafik Cpk gabungan per minggu", h=240, zero=True)

# ---------- pertanyaan ----------
QS = [
    (1, "Berapa persen file CSV yang berhasil dibaca otomatis, dan apa penyebab file yang gagal?", "Utama"),
    (2, "Berapa banyak nilai yang berubah karena salah baca pemisah ribuan dan desimal di proses lama?", "Utama"),
    (3, "Apakah Max, Min, rata-rata, dan Cpk hasil hitung ulang sama dengan angka di workbook lama?", "Utama"),
    (4, "Berapa Cpk kekuatan rekat per model dan kondisi (sebelum dan sesudah oven), dan mana yang di bawah 1,33?", "Utama"),
    (5, "Berapa persen hasil ukur di luar spesifikasi per model dan kondisi?", "Utama"),
    (6, "Apakah hasil berbeda antar shift atau antar mesin uji?", "Pendukung"),
    (7, "Bagaimana tren rata-rata kekuatan rekat dan Cpk per minggu, dan adakah pergeseran?", "Utama"),
    (8, "Apakah pergeseran terjadi setelah kalibrasi mesin atau penggantian lot lem?", "Pendukung"),
    (9, "Berapa menit kerja manual per file yang digantikan pipeline?", "Utama"),
    (10, "Berapa jam kerja per tahun yang bisa dihemat?", "Tambahan"),
    (11, "Apakah pipeline menangkap semua file rusak dan nilai aneh yang sengaja ditanam?", "Utama"),
    (12, "Apakah file yang sama tidak pernah masuk dua kali walaupun pipeline dijalankan ulang?", "Pendukung"),
]
WARN = {1, 2, 3, 4, 5, 6, 8, 9, 10, 11}
ANS = {
    1: (f"Dari {I(uniq)} file unik, {I(a1.loaded)} dimuat: parse success rate {P(a1.loaded / uniq, 1)} (CI Wilson {D(w_ok[0] * 100, 1)}% sampai {D(w_ok[1] * 100, 1)}%). {I(a1.quarantined)} file masuk karantina dengan alasan: "
        f"{I(q_trunc)} terpotong (tidak berakhir baris baru), {I(q_hdr)} header tidak lengkap (kolom hilang), {I(q_empty)} kosong, dan {I(q_fmt)} berformat mesin baru; {I(d_dup)} salinan dilewati karena isi sama (hash). Aturan terpotong adalah asumsi (docs/definitions.md); data adalah simulasi."),
    2: (f"Macro lama (ditiru dari deskripsi rancangan) salah membaca {I(ms.nilai_berubah)} dari {I(ms.nilai_pipeline)} nilai ({P(ms.persen_nilai_berubah, 1)}) di {I(ms.file_terdampak)} file; rata-rata nilai yang berubah {D(mean_mac, 2)} g di macro vs {D(mean_pipe, 0)} g di pipeline. "
        f"Penyebabnya file berformat titik desimal yang dibaca sebagai ribuan. Macro tiruan juga gagal membaca {I(ms.file_macro_gagal_format_baru)} file format baru, membaca {I(ms.file_salinan_terbaca_dua_kali)} salinan dua kali, dan membaca {I(ms.file_terpotong_terbaca_sebagian)} file terpotong sebagian. Workbook asli tidak tersedia, jadi angka ini bergantung pada tiruan macro."),
    3: (f"Tidak sama. Pada {I(msc.loc['mean', 'sesi'])} sesi, {I(msc.loc['mean', 'sesi_beda'])} sesi ({P(msc.loc['mean', 'persen'], 1)}) punya rata-rata, Min, dan Max berbeda (selisih rata-rata terbesar {D(msc.loc['mean', 'selisih_abs_maks'], 0)} g). "
        f"Per model dan kondisi, Cpk macro lebih rendah {D(d_cpk.min(), 2)} sampai {D(d_cpk.max(), 2)} dan Min turun hingga {D(d_min.abs().max(), 0)} g (Tabel 2.2c). Rekonsiliasi memakai macro tiruan karena workbook lama tidak ada (asumsi)."),
    4: (f"{I(n_below)} dari {I(len(cpk))} kombinasi di bawah 1,33 (target): terendah {gname(low)} {D(low.cpk, 2)} (CI {D(cpkmin_ci[0], 2)} sampai {D(cpkmin_ci[1], 2)}), tertinggi {gname(high)} {D(high.cpk, 2)}; kombinasi lain di atas 1,33. Variasi besar pada satu kombinasi memang ditanam (rancangan fakta 1). "
        f"Cpk dihitung dari hasil ukur valid digabung per kelompok (asumsi), n antara {I(cpk.n.min())} dan {I(cpk.n.max())}, cukup besar. Spesifikasi lebar ({I(LSL)} sampai {I(USL)} g) membuat Cpk ditentukan batas bawah."),
    5: (f"{I(cpk.oos_n.sum())} dari {I(cpk.n.sum())} hasil ukur valid di luar spesifikasi, seluruhnya pada {gname(low)} ({I(low.oos_n)} dari {I(low.n)}, CI Wilson {P(low.oos_ci_low, 2)} sampai {P(low.oos_ci_high, 2)}); kombinasi lain nol (batas atas CI {P(cpk[cpk.oos_n == 0].oos_ci_high.min(), 2)} sampai {P(cpk[cpk.oos_n == 0].oos_ci_high.max(), 2)}, bukan bukti nol mutlak). "
        f"Nilai tidak wajar (0, negatif, di atas kapasitas {I(C.CAPACITY_G)} g) ditanam {I(inv_pl)} baris dan {I(nonvalid)} terdeteksi ({P(f5.nilai2, 1)} hasil ukur file dimuat); baris itu ditandai tidak valid dan tidak masuk Cpk atau out-of-spec."),
    6: (f"Mesin berbeda: PT-02 lebih rendah {D(abs(smt.loc['machine_id', 'selisih_rata_g']), 0)} g dari PT-01 pada rata-rata sesi (Mann-Whitney p {pv(p_mach)}, p Holm {pv(ph_mach)}), terutama karena pergeseran PT-02 (Q7). "
        f"Shift berbeda kecil: Shift 2 lebih tinggi {D(smt.loc['shift', 'selisih_rata_g'], 0)} g (p {pv(p_shift)}, p Holm {pv(ph_shift)}); signifikan secara statistik tetapi selisihnya kecil terhadap sebaran. Mesin dan shift tidak dipisah dari waktu, jadi perancu belum dikendalikan."),
    7: (f"Rata-rata mingguan gabungan stabil sekitar {I(wa.mean_g.mean())} g dan Cpk mingguan antara {D(wa.cpk.min(), 2)} dan {D(wa.cpk.max(), 2)} ({I(len(wk_list))} minggu). Penurunan ada di mesin PT-02: jendela {cp.loc['PT-02', 'tanggal_mulai']} sampai {cp.loc['PT-02', 'tanggal_selesai']}, rata-rata turun {D(abs(cp.loc['PT-02', 'selisih_g']), 0)} g ({P(abs(cp.loc['PT-02', 'persen_dari_rata']), 1)}), p permutasi {pv(cp.loc['PT-02', 'p_permutasi'])}. "
       f"PT-01 tidak punya jendela penurunan (p {pv(cp.loc['PT-01', 'p_permutasi'])}). Jendela {I(C_WIN)} hari adalah asumsi (rancangan: sekitar 1 minggu); jendela {I(sens.panjang_jendela_hari.min())} dan {I(sens.panjang_jendela_hari.max())} hari memberi selisih {D(sens[(sens.machine_id == 'PT-02') & (sens.panjang_jendela_hari == sens.panjang_jendela_hari.min())].selisih_g.iloc[0], 0)} dan {D(sens[(sens.machine_id == 'PT-02') & (sens.panjang_jendela_hari == sens.panjang_jendela_hari.max())].selisih_g.iloc[0], 0)} g (Tabel 2.4f)."),
    8: (f"Penurunan PT-02 terjadi {cp.loc['PT-02', 'tanggal_mulai']} sampai {cp.loc['PT-02', 'tanggal_selesai']} dan tidak muncul di PT-01. Data tidak memuat catatan kalibrasi atau lot lem, sehingga penyebabnya tidak dapat dipastikan dari data; pada simulasi pergeseran ditanam sebagai kalibrasi mesin. Pergeseran belum tentu sebab kalibrasi dan perlu dicek di lapangan."),
    9: (f"Asumsi dasar {I(imp5.menit_per_file)} menit manual per file (salin dengan macro dan copy-paste), dibanding pipeline otomatis. Untuk {I(imp5.file_dimuat_periode)} file pada periode data, penghematan {D(imp5.jam_hemat_periode, 1)} jam. Menit per file tidak diukur; sensitivitas {I(imp3.menit_per_file)} dan {I(imp10.menit_per_file)} menit di Tabel 2.4a."),
    10: (f"Sekitar {D(imp5.jam_hemat_per_tahun, 0)} jam per tahun (estimated): {I(imp5.file_per_tahun)} file per tahun x {I(imp5.menit_per_file)} menit / 60. Sensitivitas: {D(imp3.jam_hemat_per_tahun, 0)} jam pada {I(imp3.menit_per_file)} menit dan {D(imp10.jam_hemat_per_tahun, 0)} jam pada {I(imp10.menit_per_file)} menit. Volume tahunan diekstrapolasi dari periode data (asumsi)."),
    11: (f"Semua kategori file rusak yang ditanam tertangkap: {I(gt_det)} dari {I(gt_tot)} pemeriksaan kategori (Tabel 2.5a); {I(gtn.file_normal_salah_karantina)} dari {I(gtn.file_normal)} file normal salah dikarantina. {I(gtn.file_dikarantina)} file rusak masuk karantina dan {I(gtn.file_rusak_lolos_dimuat)} lolos dimuat. "
         f"Nilai tidak wajar: {I(nonvalid)} dari {I(inv_pl)} yang ditanam terdeteksi. Kategori hanya dari yang ditanam generator; aturan juga diuji pytest ({I(n_py_ok)} dari {I(n_py)} lulus)."),
    12: (f"Ya. Pipeline dijalankan dua kali: percobaan kedua memuat {I(a2.loaded)} file dan melewati {I(a2.skipped)}; baris test_run tetap {I(idem.loc['test_run', 'setelah_percobaan_2'])} (tambahan {I(idem.loc['test_run', 'tambahan'])}) dan measurement tetap {I(idem.loc['measurement', 'setelah_percobaan_2'])} (tambahan {I(idem.loc['measurement', 'tambahan'])}). "
         f"{I(d_dup)} salinan dalam folder yang sama juga dilewati lewat hash isi."),
}
n_ans = len(QS)


def qchip(n, t):
    return f'<a class="qc{" w" if n in WARN else ""}" href="#sec2{n}" title="{esc(t)}">Q{n}</a>'


def block(qs):
    return "".join(f'<span id="sec2{n}"></span>' + qa(f"Q{n}", t, p, ANS[n], status="Dengan catatan" if n in WARN else "Terjawab", warn=n in WARN) for n, t, p in QS if n in qs)


n_main = sum(1 for q in QS if q[2] == "Utama"); n_sup = sum(1 for q in QS if q[2] == "Pendukung"); n_add = sum(1 for q in QS if q[2] == "Tambahan")
sec2 = []
sec2.append(f'<div class="card"><h3>Jawaban singkat</h3><p>Semua {I(n_ans)} pertanyaan terjawab dengan angka dari data ({I(n_main)} Utama, {I(n_sup)} Pendukung, {I(n_add)} Tambahan). {I(len(WARN))} pertanyaan diberi catatan kuning '
            f'(asumsi definisi, macro tiruan, atau estimasi). Pertanyaan utama project dijawab di bagian 7. Rancangan tidak memuat hipotesis formal; lima fakta data diuji di bagian 3.</p>'
            f'<p class="how">Klik nomor pertanyaan untuk melompat. Q hijau = terjawab. Q kuning = terjawab dengan catatan.</p><div class="qchips">' + "".join(qchip(n, t) for n, t, _ in QS) + '</div></div>')
sec2.append('<h3>2.1 Pemuatan file dan penyebab kegagalan</h3><div class="card"><p>Grafik 2.1a: jumlah file per status pemuatan, percobaan pertama.</p>' + chart_status
            + '<p>Tabel 2.1b: status file menurut penyebab.</p>'
            + table(["Status", "Penyebab", "File"], [["dimuat", "-", I(a1.loaded)], ["karantina", "terpotong", I(q_trunc)], ["karantina", "format mesin baru", I(q_fmt)], ["dilewati", "duplikat isi", I(d_dup)]])
            + '<p>Tabel 2.1c: percobaan pemuatan.</p>' + table(["Percobaan", "File dibaca", "Dimuat", "Karantina", "Dilewati"], [[I(k), I(r.file_dibaca), I(r.loaded), I(r.quarantined), I(r.skipped)] for k, r in att.iterrows()]) + '</div>')
sec2.append(block([1]))
sec2.append('<h3>2.2 Proses lama (macro tiruan) vs pipeline</h3><div class="card"><p>Tabel 2.2a: ringkasan selisih macro lama (tiruan) terhadap pipeline.</p>'
            + table(["Ukuran", "Nilai"], [["Nilai hasil ukur di pipeline", I(ms.nilai_pipeline)], ["Nilai berubah di macro", f"{I(ms.nilai_berubah)} ({P(ms.persen_nilai_berubah, 1)})"], ["File terdampak", I(ms.file_terdampak)],
                                          ["File format baru gagal dibaca macro", I(ms.file_macro_gagal_format_baru)], ["Salinan terbaca dua kali", I(ms.file_salinan_terbaca_dua_kali)], ["File terpotong terbaca sebagian", I(ms.file_terpotong_terbaca_sebagian)],
                                          ["Nilai macro dari salinan", I(ms.nilai_macro_dari_salinan)], ["Nilai macro dari file terpotong", I(ms.nilai_macro_dari_file_terpotong)]])
            + '<p>Tabel 2.2b: sesi uji yang berbeda, per ukuran.</p>'
            + table(["Ukuran", "Sesi", "Sesi beda", "Persen", "Selisih abs terbesar (g)"], [[k, I(r.sesi), I(r.sesi_beda), P(r.persen, 1), D(r.selisih_abs_maks, 0)] for k, r in msc.iterrows()])
            + '<p>Tabel 2.2c: Cpk dan Min per model dan kondisi, pipeline vs macro tiruan.</p>'
            + table(["Kelompok", "Cpk pipeline", "Cpk macro", "Min pipeline (g)", "Min macro (g)", "Rata-rata pipeline (g)", "Rata-rata macro (g)"],
                    [[f"{m} {c.replace('_', ' ')}"] + [D(g[g.ukuran == u][col].iloc[0], d) for u, col, d in (("cpk", "pipeline", 2), ("cpk", "macro", 2), ("min_g", "pipeline", 0), ("min_g", "macro", 0), ("mean_g", "pipeline", 0), ("mean_g", "macro", 0))]
                     for (m, c), g in mgc.groupby(["model", "condition"])]) + '</div>')
sec2.append(block([2, 3]))
sec2.append('<h3>2.3 Cpk dan out-of-spec</h3><div class="card"><p>Grafik 2.3a: Cpk per model dan kondisi (target 1,33).</p>' + chart_cpk
            + '<p>Tabel 2.3b: KPI per model dan kondisi dari view SQL (spesifikasi 1.500 sampai 19.000 g).</p>'
            + table(["Kelompok", "Sesi", "Hasil ukur", "Rata-rata (g)", "Min (g)", "Max (g)", "Simpangan baku (g)", "Cpk", "CI 95% Cpk"],
                    [[gname(r), I(r.sesi), I(r.n), D(r.mean_g, 0), D(r.min_g, 0), D(r.max_g, 0), D(r.sd_g, 0), D(r.cpk, 2), f"{D(c.cpk_ci_low, 2)} sampai {D(c.cpk_ci_high, 2)}"]
                     for r, c in zip(kg.sort_values("cpk").itertuples(), cpk.itertuples())])
            + '<p>Tabel 2.3c: out-of-spec dan jarak ke batas bawah.</p>'
            + table(["Kelompok", "Di luar spesifikasi", "Persen", "Batas atas CI 95%", "Batas atas (aturan tiga)", "Jarak rata-rata ke LSL (simpangan baku)"],
                    [[gname(r), I(r.oos_n), P(r.oos_rate, 2), P(r.oos_ci_high, 2), P(r.batas_atas_aturan_tiga, 2), D(r.jarak_ke_lsl_sd, 1)] for r in cpk.itertuples()]) + '</div>')
sec2.append(block([4, 5]))
sec2.append('<h3>2.4 Shift, mesin, tren mingguan, dan waktu</h3><div class="card"><p>Grafik 2.4a: rata-rata kekuatan rekat per minggu per mesin (latar kuning = minggu jendela penurunan PT-02).</p>' + chart_wk + legend([(GREY, "PT-01"), (BLUE, "PT-02")])
            + '<p>Grafik 2.4b: Cpk gabungan per minggu.</p>' + chart_cpkw
            + '<p>Tabel 2.4c: perbandingan shift dan mesin (rata-rata sesi dikurangi rata-rata model x kondisi, Mann-Whitney, Holm atas dua uji).</p>'
            + table(["Faktor", "Kelompok A", "Kelompok B", "Sesi A", "Sesi B", "Selisih rata-rata (g)", "p", "p Holm"],
                    [[f, r.kelompok_a, r.kelompok_b, I(r.sesi_a), I(r.sesi_b), D(r.selisih_rata_g, 0), pv(r.p_mannwhitney), pv(h)] for (f, r), h in zip(smt.iterrows(), (ph_shift, ph_mach))])
            + '<p>Tabel 2.4d: jendela penurunan per mesin (pindai jendela 7 hari, uji permutasi; panjang jendela adalah asumsi).</p>'
            + table(["Mesin", "Sesi", "Mulai", "Selesai", "Rata-rata di luar jendela (selisih ke model)", "Rata-rata di jendela", "Selisih (g)", "Persen", "p permutasi"],
                    [[m, I(r.sesi), r.tanggal_mulai, r.tanggal_selesai, D(r.rata_luar_resid, 0), D(r.rata_jendela_resid, 0), D(r.selisih_g, 0), P(r.persen_dari_rata, 1), pv(r.p_permutasi)] for m, r in cp.iterrows()])
            + '<p>Tabel 2.4f: sensitivitas panjang jendela penurunan (5, 7, 10 hari).</p>'
            + table(["Mesin", "Jendela (hari)", "Mulai", "Selesai", "Selisih (g)", "p permutasi"], [[r.machine_id, I(r.panjang_jendela_hari), r.tanggal_mulai, r.tanggal_selesai, D(r.selisih_g, 0), pv(r.p_permutasi)] for r in sens.itertuples()])
            + '<p>Tabel 2.4e: estimasi waktu yang dihemat (estimated; menit per file adalah asumsi).</p>'
            + table(["Menit per file", "File per tahun", "Jam hemat pada periode data", "Jam hemat per tahun", "Label"], [[I(r.menit_per_file), I(r.file_per_tahun), D(r.jam_hemat_periode, 1), D(r.jam_hemat_per_tahun, 0), r.label] for r in imp.itertuples()]) + '</div>')
sec2.append(block([6, 7, 8, 9, 10]))
sec2.append('<h3>2.5 Validasi: ground truth, idempoten, dan uji</h3><div class="card"><p>Tabel 2.5a: file bermasalah yang ditanam dan yang terdeteksi.</p>'
            + table(["Jenis", "Ditanam", "Terdeteksi", "Tidak terdeteksi"], [[r.jenis, I(r.ditanam), I(r.terdeteksi), I(r.tidak_terdeteksi)] for r in gtf.itertuples()])
            + '<p>Tabel 2.5b: file normal dan file rusak.</p>'
            + table(["File normal", "Dimuat", "Salah karantina", "File rusak ditanam", "Rusak lolos dimuat", "Dikarantina"], [[I(gtn.file_normal), I(gtn.file_normal_dimuat), I(gtn.file_normal_salah_karantina), I(gtn.file_rusak_ditanam), I(gtn.file_rusak_lolos_dimuat), I(gtn.file_dikarantina)]])
            + '<p>Tabel 2.5c: pergeseran PT-02, ditanam vs terdeteksi.</p>'
            + table(["Mesin", "Ditanam mulai", "Ditanam selesai", "Selisih ditanam (g)", "Terdeteksi mulai", "Terdeteksi selesai", "Selisih terdeteksi (g)", "p permutasi", "Mesin lain", "p mesin lain"],
                    [[gts.mesin_tertanam, gts.tanggal_tertanam, gts.tanggal_tertanam_selesai, D(gts.selisih_tertanam_g, 0), gts.tanggal_terdeteksi, gts.tanggal_terdeteksi_selesai, D(gts.selisih_terdeteksi_g, 0), pv(gts.p_permutasi), gts.mesin_lain, pv(gts.p_permutasi_mesin_lain)]])
            + '<p>Tabel 2.5d: uji idempoten, jumlah baris setelah dua kali pemuatan.</p>'
            + table(["Tabel", "Setelah percobaan 1", "Setelah percobaan 2", "Tambahan"], [[t, I(r.setelah_percobaan_1), I(r.setelah_percobaan_2), I(r.tambahan)] for t, r in idem.iterrows()])
            + '<p>Tabel 2.5e: uji pytest parser.</p>' + table(["Tes", "Hasil"], [[r.tes, pill("lulus") if r.hasil == "lulus" else pill(r.hasil, "d")] for r in pyt.itertuples()])
            + '<p>Tabel 2.5f: cek silang.</p>' + table(["Pembanding", "Dibandingkan", "Cocok"], [[g, I(len(d)), I(d.cocok.sum())] for g, d in cx.groupby("cek")]) + '</div>')
sec2.append(block([11, 12]))

REP = []
REP.append('<div class="callout a"><h4>Data project ini adalah simulasi</h4>File CSV dibuat generator dengan file rusak dan pergeseran mesin tertanam (lihat docs/simulation_spec.md). Angka menggambarkan simulasi, bukan lini produksi. Macro lama ditiru dari deskripsi rancangan karena workbook asli tidak tersedia.</div>')
REP.append('<h2 id="rp1">1. Data yang berhasil didapatkan<small>Isi data mentah, tabel di database, dan data hasil analisis</small></h2>')
REP.append('<div class="kpis">' + kp(I(a1.file_dibaca), "file dibaca", f"{I(uniq)} unik dan {I(d_dup)} salinan.", "navyH") + kp(I(a1.loaded), "file dimuat", f"Parse success rate {P(a1.loaded / uniq, 1)}.", "tealH")
           + kp(I(meas), "hasil ukur", f"Di {I(runs)} sesi uji (test_run).", "amberH") + kp(I(a1.quarantined), "file karantina", "Terpotong atau format mesin baru.", "plumH")
           + kp(I(n_cx), "cek silang", f"{I(n_cx_ok)} cocok.", "roseH") + kp(I(n_fp_ok), "sidik jari cocok", f"Dari {I(n_fp)} berkas, dicocokkan dengan repo DataCenter.", "skyH") + '</div>')
sample = kr.head(5)
REP.append('<h3>1.1 Data mentah</h3><div class="card"><p>Tabel 1.1a: lima sesi uji pertama (satu baris per file CSV; ringkasan hasil ukur).</p>'
           + table(["Run", "File", "Model", "Kondisi", "Mesin", "Shift", "Tanggal", "Hasil ukur", "Rata-rata (g)", "Min (g)", "Max (g)"],
                   [[r.run_id, esc(cs(r.file_name)), r.model, r.condition.replace("_", " "), r.machine_id, r.shift, r.test_datetime, I(r.n), D(r.mean_g, 0), D(r.min_g, 0), D(r.max_g, 0)] for r in sample.itertuples()])
           + '<p>Tabel 1.1b: format file mesin (data simulasi).</p>' + table(["Ciri", "Isi"], [["Pemisah kolom", "titik koma"], ["Header", "sembilan baris keterangan mesin"], ["Format angka", f"titik ribuan dan koma desimal; {I(fct.loc[3, 'nilai2'])} file berformat titik desimal"],
                                                                                          ["Format mesin baru", f"{I(q_fmt)} file dengan header berbeda"], ["File terpotong", f"{I(q_trunc)} file tidak berakhir baris baru"]]) + '</div>')
FILES = {
    "changepoint.csv": "jendela penurunan rata-rata per mesin", "dip_sensitivity.csv": "sensitivitas panjang jendela penurunan", "cpk_group.csv": "Cpk dan out-of-spec per model dan kondisi", "crosscheck.csv": "cek silang SQL, pandas, Excel", "design_facts.csv": "lima fakta data rancangan terhadap hasil",
    "ground_truth_files.csv": "file rusak ditanam vs terdeteksi", "ground_truth_normal.csv": "file normal dan rusak", "ground_truth_shift.csv": "pergeseran ditanam vs terdeteksi", "idempotency.csv": "uji pemuatan dua kali",
    "impact.csv": "estimasi jam dihemat (estimated)", "kpi_group.csv": "KPI per model dan kondisi", "kpi_machine_shift.csv": "KPI per mesin dan shift", "kpi_run.csv": "KPI per sesi uji", "kpi_weekly.csv": "KPI per minggu dan mesin",
    "macro_group_compare.csv": "pipeline vs macro per kelompok", "macro_session_compare.csv": "pipeline vs macro per sesi", "macro_summary.csv": "ringkasan selisih macro tiruan", "pytest_result.csv": "hasil pytest parser",
    "shift_machine_test.csv": "uji shift dan mesin", "weekly_all.csv": "Cpk dan rata-rata mingguan gabungan", "weekly_machine.csv": "rata-rata mingguan per mesin"}
real = sorted(p.name for p in r2.glob("*.csv"))
assert set(real) == set(FILES), ("CSV belum terdokumentasi / tidak ada:", set(real) ^ set(FILES))
REP.append('<h3>1.2 Tabel hasil</h3><div class="card"><p>Tabel 1.2a: tabel di database DuckDB (percobaan pertama dan kedua).</p>'
           + table(["Tabel", "Setelah percobaan 1", "Setelah percobaan 2"], [[t, I(dbt[(dbt.percobaan == 1) & (dbt.tabel == t)].baris.iloc[0]), I(dbt[(dbt.percobaan == 2) & (dbt.tabel == t)].baris.iloc[0])] for t in dbt.tabel.unique()])
           + f'<p>Tabel 1.2b: uji otomatis. pytest {I(n_py_ok)} dari {I(n_py)} lulus; dashboard AppTest {I(n_dt_ok)} dari {I(n_dt)} lulus.</p>'
           + table(["Pemeriksaan dashboard", "Hasil"], [[esc(r.pemeriksaan), pill("lulus") if r.hasil == "lulus" else pill(r.hasil, "d")] for r in dtest.itertuples()])
           + f'<p>Tabel 1.2c: {I(len(FILES))} file hasil analisis di results/2-analysis.</p>' + table(["File", "Isi"], [[f, FILES[f]] for f in sorted(FILES)]) + '</div>')
REP.append('<h3>1.3 Angka kunci (KPI)</h3><div class="card"><p>Tabel 1.3: lima KPI.</p>'
           + table(["KPI", "Rumus ringkas", "Hasil", "Jumlah data"], [
               ["Parse success rate", "file dimuat / file unik", P(a1.loaded / uniq, 1), f"{I(uniq)} file"],
               ["Cpk terendah", "min((USL - rata-rata), (rata-rata - LSL)) / (3 x simpangan baku)", f"{D(low.cpk, 2)} ({gname(low)})", f"{I(low.n)} hasil ukur"],
               ["Out-of-spec rate", "hasil ukur di luar 1.500 sampai 19.000 g / hasil ukur", P(cpk.oos_n.sum() / cpk.n.sum(), 2), f"{I(cpk.n.sum())} hasil ukur"],
               ["Pergeseran rata-rata PT-02", "rata-rata di jendela dikurangi di luar jendela", f"{D(cp.loc['PT-02', 'selisih_g'], 0)} g ({P(cp.loc['PT-02', 'persen_dari_rata'], 1)})", f"{I(cp.loc['PT-02', 'sesi'])} sesi"],
               ["Menit manual per file", "asumsi, bukan pengukuran", f"{I(imp5.menit_per_file)} menit (estimated)", f"{I(imp5.file_dimuat_periode)} file"]]) + '</div>')
REP.append('<h2 id="rp2">2. Apakah business question terjawab?<small>' + f'{I(n_ans)} pertanyaan pada Design Project, dijawab dengan data' + '</small></h2>')
REP.extend(sec2)

# ---------- rp3 ----------
f1, f2, f3, f4, f5 = (fct.loc[i] for i in (1, 2, 3, 4, 5))
gtd = gtf.set_index("jenis")
REP.append('<h2 id="rp3">3. Apakah dataset sesuai dengan Design Project?<small>Perbandingan rancangan dengan realisasi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 3a. Rancangan dan realisasi dataset.</p>'
           + table(["Hal", "Rancangan", "Realisasi", "Verdict"], [
               ["Sumber data", "simulasi buatan sendiri dari scripts/generate_csv.py", f"00_generate_csv.py (seed tetap), dibuat ulang dan dicocokkan dengan sidik jari repo DataCenter ({I(n_fp_ok)} dari {I(n_fp)} berkas)", pill("Sesuai", "")],
               ["Ukuran", "±1.200 file, ±15.000 hasil ukur", f"{I(uniq)} file unik ditambah {I(d_dup)} salinan; {I(meas)} hasil ukur dimuat dari {I(runs)} file", pill("Sesuai", "")],
               ["Tabel", "test_run, measurement, spec, ingest_log", "empat tabel yang sama di DuckDB; kolom test_type tidak ada (jenis uji shear tidak ada di data)", pill("Sesuai + penyesuaian", "p")],
               ["Fakta 1: satu kombinasi dengan Cpk di bawah 1,33", "Cpk < 1,33", f"{f1.kombinasi} Cpk {D(f1.nilai, 2)}, satu-satunya kombinasi di bawah 1,33 ({I(f1.nilai2)} kombinasi)", pill("Sesuai", "")],
               ["Fakta 2: rata-rata satu mesin turun ±800 g selama ±1 minggu", "turun ±800 g, ±1 minggu", f"PT-02 turun {D(abs(f2.nilai), 0)} g ({P(abs(cp.loc['PT-02', 'persen_dari_rata']), 1)}) pada {cp.loc['PT-02', 'tanggal_mulai']} sampai {cp.loc['PT-02', 'tanggal_selesai']}; tanggal mulai terdeteksi sama dengan yang ditanam", pill("Sesuai", "")],
               ["Fakta 3: ±3% file berformat titik ribuan dan koma desimal", "±3% file", f"{I(f3.nilai2)} file ({P(f3.nilai, 1)}) berformat angka lain, semuanya terbaca benar oleh pipeline", pill("Sesuai", "")],
               ["Fakta 4: file bermasalah (header berbeda, kolom hilang, file kosong, file ganda)", "empat jenis", f"header berbeda (format mesin baru) {I(gtd.loc['format mesin baru', 'ditanam'])}, kolom hilang {I(gtd.loc['kolom hilang (tanpa kolom Force)', 'ditanam'])}, file kosong {I(gtd.loc['file kosong', 'ditanam'])}, salinan {I(gtd.loc['salinan ganda (nama copy_of_)', 'ditanam'])}, terpotong {I(gtd.loc['file terpotong (bukan format baru)', 'ditanam'])}", pill("Sesuai", "")],
               ["Fakta 5: 2% sampai 3% nilai tidak wajar", "0, negatif, di atas kapasitas", f"{I(inv_pl)} baris ditanam, {I(f5.nilai)} terdeteksi tidak valid ({P(f5.nilai2, 1)} hasil ukur file dimuat)", pill("Sesuai", "")],
               ["Jenis uji", "push dan shear", "hanya push test", pill("Berubah", "d")],
               ["Hipotesis", "tidak ada hipotesis formal pada rancangan", "lima fakta data di atas diperlakukan sebagai klaim yang diuji", pill("Tidak berlaku", "d")]]) + '</div>')

# ---------- rp4 ----------
REP.append('<h2 id="rp4">4. Apakah tools yang digunakan sesuai?<small>Perbandingan rancangan dengan eksekusi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 4a. Tools rancangan dan realisasi.</p>' + table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
    ["Python (pandas)", "parser CSV, validasi, karantina", f"parser sendiri (ingest_lib.py) dengan pandas dan SciPy; konfigurasi di project/config.yaml; {I(n_cx_ok)} dari {I(n_cx)} cek silang cocok", pill("Sesuai + tambahan", "")],
    ["DuckDB + SQL", "empat tabel dan view KPI", "empat tabel dan lima view (views.sql); file database tidak di-commit", pill("Sesuai", "")],
    ["Streamlit + Plotly", "dashboard di-deploy lewat link", f"aplikasi tiga halaman diuji AppTest ({I(n_dt_ok)} dari {I(n_dt)} lulus); belum di-deploy", pill("Sebagian", "p")],
    ["pytest", "tes parser", f"{I(n_py_ok)} dari {I(n_py)} tes lulus", pill("Sesuai", "")],
    ["Excel", "cek silang dengan workbook lama", "workbook lama tidak tersedia; macro ditiru, reconciliation.xlsx dibuat openpyxl dan cek silang rumus dihitung ulang LibreOffice (bukan Excel)", pill("Sesuai + penyesuaian", "p")],
    ["GitHub + Markdown", "kode, contoh CSV, README; GitHub Actions opsional", "repo dan README; GitHub Actions tidak dipakai; branch belum di-merge", pill("Sebagian", "p")]]) + '</div>')
STEPS = [("1", "Memetakan proses lama", "docs/old_process.md", "Sesuai", ""), ("2", "Merancang skema dan KPI", "docs/data_dictionary.md dan definitions.md", "Sesuai", ""),
         ("3", "Membuat CSV simulasi", "00_generate_csv.py dan sidik jari (01)", "Sesuai", ""), ("4", "Membangun parser", "ingest_lib.py dan tests/test_ingest.py", "Sesuai", ""),
         ("5", "Memuat ke database", "02_ingest.py", "Sesuai", ""), ("6", "Menulis query KPI", "views.sql dan 03_run_queries.py", "Sesuai", ""),
         ("7", "Rekonsiliasi dengan workbook lama", "05_reconcile_macro.py (macro ditiru)", "Sesuai + penyesuaian", "p"), ("8", "Menganalisis Cpk dan tren", "06_cpk_trend.py", "Sesuai", ""),
         ("9", "Menghitung waktu dihemat", "07_impact.py", "Sesuai", ""), ("10", "Mencocokkan fakta yang ditanam", "08_ground_truth_check.py", "Sesuai", ""),
         ("11", "Membuat dashboard", "streamlit/app.py, belum di-deploy", "Sebagian", "p"), ("12", "README dan finalisasi", "12_build_readme.py, build_report.py; branch belum di-merge", "Sebagian", "p")]
RENAMES = [("docs/old_process.md", ["project/docs/old_process.md"], True), ("docs/data_dictionary.md", ["project/docs/data_dictionary.md", "project/docs/definitions.md"], True),
           ("scripts/generate_csv.py", ["project/code/1-data-preparation/python/00_generate_csv.py"], True), ("data/raw/*.csv", ["project/data/sim/incoming"], False),
           ("data/ground_truth.json", ["project/data/sim/ground_truth.json"], False), ("pipeline/ingest.py", ["project/code/ingest_lib.py", "project/code/1-data-preparation/python/02_ingest.py"], True),
           ("pipeline/config.yaml", ["project/config.yaml"], True), ("tests/test_ingest.py", ["project/tests/test_ingest.py"], True), ("pushtest.duckdb", ["project/data/sim/pushtest.duckdb"], False),
           ("sql/", ["project/code/2-analysis/sql/views.sql", "project/code/1-data-preparation/sql/schema.sql"], True), ("outputs/reconciliation.xlsx", ["project/outputs/reconciliation.xlsx"], True),
           ("notebooks/analysis.ipynb", ["project/results/3-presentation/analysis.ipynb"], True), ("dashboard/app.py", ["project/code/3-presentation/streamlit/app.py"], True),
           ("requirements.txt", ["project/requirements.txt"], True), ("README.md", ["README.md"], True), ("index.html", ["design-and-report/index.html"], True),
           ("data/samples/", [], True), ("slides/presentation.pdf", [], True)]
for _, dest, committed in RENAMES:
    for d in dest:
        assert (REPO / d).exists() or d.endswith("index.html") or not committed, d
rn_rows = [[a, "(tidak dibuat)" if not dest else ", ".join(dest) + ("" if committed else " (tidak di-commit)")] for a, dest, committed in RENAMES]
REP.append('<h2 id="rp5">5. Apakah alur pengerjaan sesuai dengan Design Project?<small>' + f'{I(12)} langkah rancangan vs yang dijalankan' + '</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 5a. Dua belas langkah rancangan dan yang dijalankan.</p>' + table(["No", "Langkah rancangan", "Realisasi", "Verdict"], [[n, t, r, pill(v, k)] for n, t, r, v, k in STEPS])
           + '<p>Tabel 5b: penyesuaian dan improvisasi yang tidak ada di rancangan.</p>' + table(["Penyesuaian", "Alasan"], [
               ["Data simulasi dari repo DataCenter", "data dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256"],
               ["Macro lama ditiru", "workbook dan macro asli tidak tersedia; tiruan ditulis di docs/old_process.md dan angka rekonsiliasi bergantung padanya (asumsi)"],
               ["Aturan file terpotong, kapasitas mesin, aturan baca angka", "tidak ada di rancangan; asumsi di docs/definitions.md"],
               ["Menit manual per file dan volume tahunan", "tidak ada di rancangan; 5 menit dengan sensitivitas 3 dan 10 menit, hasil berlabel estimated"],
               ["Jendela penurunan dari data", "penurunan dicari lewat pindai jendela dan uji permutasi, tanggal tertanam hanya dibandingkan di skrip validasi"],
               ["Hash isi untuk file ganda", "satu mekanisme untuk salinan dalam folder yang sama dan pemuatan ulang"],
               ["Pindai jendela penurunan 7 hari", "rancangan menyebut sekitar 1 minggu; panjang jendela asumsi dengan sensitivitas 5 dan 10 hari (dip_sensitivity.csv)"]])
           + '<p>Tabel 5c: perubahan nama dan lokasi file terhadap rancangan.</p>' + table(["Rancangan", "Realisasi"], rn_rows) + '</div>')
docs_list = [(a, d[0] if d else "", c) for a, d, c in RENAMES if a != "index.html"]


def doc_status(a, committed, path):
    if not path:
        return pill("Tidak dibuat", "d")
    if not committed:
        return pill("Tidak di-commit", "d")
    return pill("Ada", "") if (REPO / path).exists() else pill("Belum ada", "d")


REP.append('<h2 id="rp6">6. Apakah project output tercapai?<small>Output pada Design Project, bagian 7</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 6a. Status output rancangan.</p>' + table(["Output", "Label", "Status", "Bukti"], [
    ["Pipeline pemuatan data", "Utama", pill("Tercapai", ""), "ingest_lib.py, 02_ingest.py, config.yaml"],
    ["Dashboard interaktif", "Utama", pill("Sebagian", "p"), f"streamlit/app.py diuji AppTest ({I(n_dt_ok)} dari {I(n_dt)}); belum di-deploy sebagai link publik"],
    ["Database dan query SQL", "Utama", pill("Tercapai", ""), "schema.sql, views.sql; file .duckdb tidak di-commit"],
    ["Pembuat file CSV simulasi", "Utama", pill("Tercapai", ""), "00_generate_csv.py, seed tetap"],
    ["Notebook analisis", "Utama", pill("Tercapai", ""), "results/3-presentation/analysis.ipynb"],
    ["Laporan temuan dan rekomendasi", "Utama", pill("Tercapai", ""), "README dan Report"],
    ["Repositori GitHub", "Utama", pill("Sebagian", "p"), "branch belum di-merge ke main"],
    ["Slide presentasi", "Opsional", pill("Tidak dibuat", "d"), "-"]])
    + '<p>Tabel 6b: daftar dokumen rancangan dan status pada repositori.</p>' + table(["Dokumen", "Status"], [[a, doc_status(a, c, p)] for a, p, c in docs_list]) + '</div>')

crit = [("Kedelapan pertanyaan Utama terjawab dengan angka dari data", "Terpenuhi", f"{I(n_main)} dari {I(n_main)} terjawab; beberapa dengan catatan asumsi"),
        ("Semua file normal termuat dan file rusak yang ditanam masuk karantina dengan alasan benar", "Terpenuhi", f"{I(gtn.file_normal_dimuat)} dari {I(gtn.file_normal)} file normal dimuat; {I(gtn.file_dikarantina)} dari {I(gtn.file_rusak_ditanam)} file rusak dikarantina"),
        ("Menjalankan pipeline dua kali tidak menambah satu baris pun", "Terpenuhi", f"tambahan {I(idem.loc['test_run', 'tambahan'])} baris test_run dan {I(idem.loc['measurement', 'tambahan'])} baris measurement"),
        ("Max, Min, rata-rata, dan Cpk dari SQL sama dengan hitungan Excel pada sampel", "Terpenuhi", f"{I(n_cx_ok)} dari {I(n_cx)} cek silang cocok (Excel dihitung ulang LibreOffice)"),
        ("Orang awam menyebut kombinasi Cpk terendah dari dashboard dalam 1 menit", "Belum diuji", "belum ada uji dengan pembaca awam; dashboard belum di-deploy"),
        ("Checklist standar terpenuhi", "Sebagian", "dashboard belum di-deploy; branch belum di-merge ke main")]
n_ok_crit = sum(1 for c in crit if c[1] == "Terpenuhi")
REP.append('<h2 id="rp7">7. Kesimpulan<small>Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan</small></h2>')
REP.append('<h4>7.1 Hasil analisis</h4><div class="card"><p><b>Pertanyaan utama:</b> bagaimana mengganti macro VBA dan copy-paste manual agar data CSV mesin push test otomatis masuk database, terbaca dengan benar, dan siap dianalisis per model dan kondisi proses?</p>'
           f'<p>Pipeline memuat {I(a1.loaded)} dari {I(uniq)} file unik ({P(a1.loaded / uniq, 1)}), mengarantina {I(a1.quarantined)} file rusak dengan alasan, dan tidak menambah baris saat dijalankan ulang. '
           f'Macro lama (tiruan) salah membaca {I(ms.nilai_berubah)} nilai ({P(ms.persen_nilai_berubah, 1)}) sehingga Cpk terlihat {D(d_cpk.min(), 2)} sampai {D(d_cpk.max(), 2)} lebih rendah. '
           f'Cpk {gname(low)} {D(low.cpk, 2)} di bawah 1,33 (kombinasi lain di atas) dengan {I(low.oos_n)} hasil ukur di luar spesifikasi. Rata-rata mesin PT-02 turun {D(abs(cp.loc["PT-02", "selisih_g"]), 0)} g pada {cp.loc["PT-02", "tanggal_mulai"]} sampai {cp.loc["PT-02", "tanggal_selesai"]} dan terdeteksi di tanggal yang ditanam. '
           f'Semua {I(gt_det)} kategori file rusak yang ditanam tertangkap, tanpa file normal salah karantina.</p></div>')
REP.append('<h4>7.2 Impact</h4><div class="card">' f'<p>Estimasi (estimated): sekitar {D(imp5.jam_hemat_per_tahun, 0)} jam kerja manual per tahun ({I(imp5.menit_per_file)} menit per file x {I(imp5.file_per_tahun)} file per tahun), dengan rentang {D(imp3.jam_hemat_per_tahun, 0)} sampai {D(imp10.jam_hemat_per_tahun, 0)} jam untuk {I(imp3.menit_per_file)} sampai {I(imp10.menit_per_file)} menit per file. '
           'Menit per file adalah asumsi, bukan pengukuran.</p><p>Nilai praktis: angka tidak lagi salah baca dan file rusak tidak masuk diam-diam. Nilai analitis: Cpk dan tren per model, kondisi, dan mesin dari satu sumber SQL. Nilai portofolio: pipeline dengan karantina, idempoten, dan uji ground truth. Belum terukur: dampak nyata di lini dan dalam rupiah.</p></div>')
REP.append('<h4>7.3 Success criteria</h4><div class="card">' + table(["Kriteria", "Status", "Bukti"], [[k, pill(s, "" if s == "Terpenuhi" else ("p" if s in ("Sebagian", "Belum diuji") else "d")), cs(b)] for k, s, b in crit]) + f'<p>Hasil: {I(n_ok_crit)} dari {I(len(crit))} kriteria tercapai.</p></div>')
REP.append('<h4>7.4 Rekomendasi</h4><div class="card"><ul class="tight">'
           '<li>Jalankan pipeline terjadwal dan tinjau folder karantina setiap hari; format mesin baru ditambahkan sebagai aturan sebelum file dimuat ulang.</li>'
           f'<li>Selidiki kalibrasi mesin PT-02: rata-rata turun {D(abs(cp.loc["PT-02", "selisih_g"]), 0)} g pada {cp.loc["PT-02", "tanggal_mulai"]} sampai {cp.loc["PT-02", "tanggal_selesai"]}.</li>'
           f'<li>Turunkan variasi {gname(low)} (Cpk di bawah 1,33) dan pantau jarak rata-rata ke LSL (dalam simpangan baku) selain Cpk.</li>'
           '<li>Hentikan macro lama setelah pipeline diverifikasi pada data nyata.</li></ul></div>')
REP.append('<h4>7.5 Saran perbaikan</h4><div class="card"><ul class="tight">'
           '<li>Deploy dashboard dan uji ke pembaca awam (kriteria 1 menit).</li><li>Uji pipeline pada file mesin nyata untuk memeriksa format angka dan jenis kerusakan yang tidak ada di simulasi.</li>'
           '<li>Ukur menit manual per file di lapangan untuk menggantikan asumsi.</li><li>Tambahkan catatan kalibrasi dan lot lem ke data agar penyebab pergeseran bisa diuji.</li></ul></div>')
REP.append('<h4>7.6 Batasan</h4><div class="card"><ul class="tight">'
           f'<li><b>Data adalah simulasi;</b> angka menggambarkan simulasi, bukan lini produksi. Semua {I(gt_det)} kategori file rusak yang ditanam terdeteksi, tetapi hanya untuk kategori yang ditanam generator.</li>'
           '<li>Macro lama ditiru dari deskripsi rancangan; workbook asli tidak tersedia, sehingga rekonsiliasi (Q2, Q3) bergantung pada tiruan itu.</li>'
           f'<li>Asumsi buatan sendiri: aturan file terpotong, kapasitas mesin, aturan baca angka, Cpk per kelompok gabungan, {I(imp5.menit_per_file)} menit per file, volume tahunan, uji shear dan mesin pada rata-rata sesi.</li>'
           f'<li>Kelima fakta data rancangan ditanam dan terdeteksi, kecuali jenis uji shear yang tidak ada di data. Generator, jenis kerusakan, dan jendela penurunan 7 hari ditulis oleh orang yang sama dengan pipeline, jadi uji pemulihan optimistis.</li>'
           f'<li>Perbedaan shift kecil tetapi signifikan (p Holm {pv(ph_shift)}); mesin dan shift tidak dipisah dari waktu. Penyebab pergeseran PT-02 tidak bisa dipastikan dari data.</li>'
           f'<li>Dashboard belum di-deploy; kriteria pembaca awam belum diuji; slide dan file contoh di data/samples tidak dibuat; branch belum di-merge ke main.</li>'
           '<li>Rumus Excel dihitung ulang LibreOffice, bukan Excel. Lisensi data tidak berlaku (data karangan).</li></ul></div>')

REPORT_PANE = ('<div class="pane" id="report" data-tab="report" hidden>\n<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4>'
               f'Cek silang: {I(n_cx_ok)} dari {I(n_cx)} cocok (SQL, pandas, Excel); pytest {I(n_py_ok)} dari {I(n_py)} lulus; dashboard AppTest {I(n_dt_ok)} dari {I(n_dt)}. Angka diaudit dari CSV hasil. <b>Data pada project ini adalah simulasi.</b></div>\n'
               + '<div class="card"><p class="how">Ringkasan tujuh pertanyaan evaluasi. Klik untuk melompat ke bagian.</p>' + table(["No", "Pertanyaan evaluasi", "Verdict", "Ringkasan"], [
                   [f'<span class="en">{i}</span>', f'<a href="#rp{i}">{t}</a>', pill(v[0], v[1]), v[2]] for i, (t, v) in enumerate([
                       ("Data yang berhasil didapatkan", ("Berhasil", "", f"{I(a1.loaded)} dari {I(uniq)} file dimuat, {I(meas)} hasil ukur")),
                       ("Apakah business question terjawab?", ("Sesuai", "", f"{I(n_ans)} dari {I(n_ans)} terjawab, {I(len(WARN))} dengan catatan")),
                       ("Apakah dataset sesuai dengan Design Project?", ("Sesuai + penyesuaian", "p", "lima fakta data ditanam dan terdeteksi; jenis uji shear tidak ada")),
                       ("Apakah tools yang digunakan sesuai?", ("Sesuai + penyesuaian", "p", "macro ditiru, dashboard belum di-deploy")),
                       ("Apakah alur pengerjaan sesuai dengan Design Project?", ("Sesuai + tambahan", "", "dua belas langkah dijalankan")),
                       ("Apakah project output tercapai?", ("Sebagian", "p", "dashboard belum di-deploy, slide tidak dibuat")),
                       ("Kesimpulan", ("Simulasi", "", f"{I(gt_det)} dari {I(gt_tot)} kategori file rusak terdeteksi"))], 1)]) + '</div>\n' + "\n".join(REP) + '\n</div>\n')

nav_src = SRC[SRC.index('<nav aria-label="Project navigation">'):SRC.index('</nav>') + 6]
btn_design = re.search(r'<button[^>]*data-t="design"[^>]*>.*?</button>', nav_src, re.S).group(0)
btn_report = re.search(r'<button[^>]*data-t="report"[^>]*>.*?</button>', nav_src, re.S).group(0)
links_design = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_src, re.S).group(0)
new_report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in enumerate(["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + '</div>')
nav_new = '<nav aria-label="Project navigation">' + btn_design + btn_report + links_design + new_report_links + '</nav>'
design_pane = SRC[SRC.index('<header class="banner">'):SRC.index('<div class="pane" id="report"')]
head_end = SRC.index('</style>'); body_start = SRC.index('<body>')
hub_link = SRC[body_start:SRC.index('<main>')]
html = SRC[:head_end] + CSS_EXTRA + "\n" + SRC[head_end:body_start] + hub_link + '<main>\n' + nav_new + '\n' + design_pane + REPORT_PANE + SRC[SRC.index('</main>'):]
assert design_pane in html, "pane Design berubah"

STATIC = {str(i) for i in range(0, 41)} | {"2026", "1.500", "19.000", "20.000", "1,33", "800", "1.200", "15.000", "3,0", "2,0", "60", "100", "1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5", "7.1", "7.2", "7.3", "7.4", "7.5", "7.6",
                                           "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "3a", "3b", "75", "5", "3", "50", "70", "0,05", "95"}
n_tok, bad = audit(REPORT_PANE, STATIC)
print(f"token angka diperiksa: {n_tok}; tidak terdaftar: {len(bad)}")
if bad:
    vt = R.visible_text(REPORT_PANE)
    print("TIDAK TERDAFTAR:", bad[:80])
    for t in bad[:40]:
        m = re.search(r"(?<![\d.,])" + re.escape(t) + r"(?![\d,])", vt)
        if m:
            print("  ", t, "|", vt[max(0, m.start() - 60):m.end() + 30].replace("\n", " "))
    raise SystemExit("audit gagal: ada angka yang tidak berasal dari data")
out = HERE.parent / "index.html"
out.write_text(html, encoding="utf-8")
print("written", out, len(html))
