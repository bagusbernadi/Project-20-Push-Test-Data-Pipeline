"""Tes otomatis parser dan pemuatan (pytest): file normal, format angka, header berbeda, file kosong, terpotong, nilai aneh, duplikat, idempoten."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import pytest
import ingest_lib as IL

GOOD = ("Test Program;DS20KG\nTest Date;01/04/2026\nShift;Shift 1\nMachine;PT-01\nModel;Model A\nCondition;before_oven\n"
        "LSL (g);1500,0\nUSL (g);19000,0\nSample No;Force (g)\n{rows}\n")


def mk(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def rows(*vals):
    return "\n".join(f"{i + 1};{v}" for i, v in enumerate(vals))


def test_normal_file(tmp_path):
    r = IL.parse_file(mk(tmp_path, "a.csv", GOOD.format(rows=rows(*"7200,5\n8100,0".split("\n")))))
    assert r["status"] == "ok" and r["values"] == [(1, 7200.5), (2, 8100.0)] and r["number_format"] == "ID"


def test_thousand_separator_us_format(tmp_path):
    r = IL.parse_file(mk(tmp_path, "a.csv", GOOD.format(rows=rows(*"8,245.6\n950.2".split("\n")))))
    assert r["status"] == "ok" and r["values"][0][1] == 8245.6 and r["values"][1][1] == 950.2 and r["number_format"] == "US"


def test_dot_thousand_comma_decimal(tmp_path):
    assert IL.parse_number("8.245,6")[0] == 8245.6


def test_new_machine_format_goes_to_quarantine(tmp_path):
    r = IL.parse_file(mk(tmp_path, "a.csv", "# Machine,PT-01,FW 2.1\nDate,2026-04-01\nidx,force_gf\n1,7000.0\n"))
    assert r["status"] == "gagal" and r["error_type"] == "format_mesin_baru"


def test_empty_file(tmp_path):
    assert IL.parse_file(mk(tmp_path, "a.csv", ""))["error_type"] == "file_kosong"


def test_truncated_file(tmp_path):
    t = GOOD.format(rows=rows(*"7200,5\n8100,0".split("\n")))[:-6]
    assert IL.parse_file(mk(tmp_path, "a.csv", t))["error_type"] == "terpotong"


def test_missing_header_field(tmp_path):
    t = GOOD.replace("Machine;PT-01\n", "").format(rows="7200,5")
    assert IL.parse_file(mk(tmp_path, "a.csv", t))["error_type"] == "header_tidak_lengkap"


def test_non_numeric_value(tmp_path):
    assert IL.parse_file(mk(tmp_path, "a.csv", GOOD.format(rows=rows(*"abc".split("\n")))))["error_type"] == "nilai_bukan_angka"


def test_out_of_range_values_flagged(tmp_path):
    r = IL.parse_file(mk(tmp_path, "a.csv", GOOD.format(rows=rows(*"0,0\n-5,0\n25000,0\n7000,0".split("\n")))))
    assert r["status"] == "ok" and r["rows_invalid"] == 3


@pytest.fixture
def cfg():
    return dict(spec=[dict(model="Model A", test_type="push", lsl_g=1500.0, usl_g=19000.0)], capacity_g=20000.0, min_rows=1)


def test_duplicate_and_idempotent(tmp_path, cfg):
    inc, q = tmp_path / "in", tmp_path / "q"
    inc.mkdir()
    text = GOOD.format(rows=rows(*"7200,5\n8100,0".split("\n")))
    mk(inc, "a.csv", text); mk(inc, "copy_of_a.csv", text); mk(inc, "bad.csv", "")
    con = IL.connect(tmp_path / "t.duckdb")
    l1 = IL.ingest(con, inc, q, cfg)
    assert sorted(l1.status) == ["loaded", "quarantined", "skipped"]
    n1 = con.execute("SELECT COUNT(*) FROM test_run").fetchone()[0], con.execute("SELECT COUNT(*) FROM measurement").fetchone()[0]
    l2 = IL.ingest(con, inc, q, cfg)
    n2 = con.execute("SELECT COUNT(*) FROM test_run").fetchone()[0], con.execute("SELECT COUNT(*) FROM measurement").fetchone()[0]
    assert n1 == n2 == (1, 2) and set(l2.status) == {"skipped"}
    assert (q / "bad.csv.reason.txt").read_text().strip() == "file_kosong"


def test_judgement_uses_spec(tmp_path, cfg):
    inc = tmp_path / "in"; inc.mkdir()
    mk(inc, "a.csv", GOOD.format(rows=rows(*"1000,0\n7000,0\n19500,0".split("\n"))))
    con = IL.connect(tmp_path / "t.duckdb")
    IL.ingest(con, inc, tmp_path / "q", cfg)
    assert [r[0] for r in con.execute("SELECT judgement FROM measurement ORDER BY seq").fetchall()] == ["NG", "OK", "NG"]
