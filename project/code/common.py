"""Konstanta dan path bersama Project 20 (Push Test Data Pipeline + Dashboard).

ROOT = folder project/. Semua skrip memakai path dari sini. Folder hasil dibuat otomatis.
Definisi yang tidak ada di rancangan ditulis di project/docs/definitions.md dengan label asumsi.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SIM = DATA / "sim"                         # hasil generator: folder incoming dan ground truth (tidak di-commit)
INCOMING = SIM / "incoming"
QUARANTINE = SIM / "quarantine"            # dibuat pipeline (tidak di-commit)
DB_PATH = ROOT / "pushtest.duckdb"         # tidak di-commit
CONFIG = ROOT / "config.yaml"
RES1 = ROOT / "results" / "1-data-preparation"
RES2 = ROOT / "results" / "2-analysis"
RES3 = ROOT / "results" / "3-presentation"
SQL_DIR = ROOT / "code" / "2-analysis" / "sql"
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"
TESTS = ROOT / "tests"
for _d in (DATA, SIM, RES1, RES2, RES3, OUTPUTS):
    _d.mkdir(parents=True, exist_ok=True)

SEED = 20
ALPHA = 0.05
BOOT_B = 2000
CPK_TARGET = 1.33              # rancangan: Cpk di bawah 1,33 dianggap kurang
MIN_N_CPK = 30                 # rancangan: Cpk dari < ±30 hasil ukur tidak stabil
LSL, USL = 1500.0, 19000.0     # rancangan: spesifikasi 1.500 sampai 19.000 g (disimpan di tabel spec)
SHEAR_LSL, SHEAR_USL = 800.0, 11000.0   # ASUMSI: spesifikasi shear test (rancangan hanya menyebut spec per model dan jenis uji)
CAPACITY_G = 20000.0           # ASUMSI: kapasitas mesin DS20KG
MODELS = ["Model A", "Model B"]
CONDITIONS = ["before_oven", "after_oven"]
MACHINES = ["PT-01", "PT-02"]
SHIFTS = ["Shift 1", "Shift 2"]
MANUAL_MIN_PER_FILE = 5.0      # ASUMSI: menit kerja manual per file di proses lama (macro + copy-paste)
OPS_DAYS_PER_YEAR = 260        # ASUMSI: hari kerja per tahun untuk anualisasi
MACRO_MIN_FILES_NOTE = "format mesin baru ditolak macro lama (ASUMSI: macro hanya menerima format machine_v1)"
