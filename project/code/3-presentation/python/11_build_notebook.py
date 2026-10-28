"""11: Notebook analisis Q1-Q12 (analysis.ipynb), dieksekusi tanpa error. Membaca CSV hasil."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import nbformat as nbf
from nbclient import NotebookClient
import common as CM

nb = nbf.v4.new_notebook()
md = lambda t: nbf.v4.new_markdown_cell(t); code = lambda t: nbf.v4.new_code_cell(t)
cells = [md("# Project 20: Push Test Data Pipeline + Dashboard\nData simulasi. Notebook membaca CSV hasil pipeline; angka tidak dihitung ulang."),
         code("from pathlib import Path\nimport pandas as pd\nR1 = Path('..') / '1-data-preparation'\nR2 = Path('..') / '2-analysis'\nrd = lambda n, d=R2: pd.read_csv(d / n)\n")]
SEC = [("Q1 dan Q11: pemuatan file dan ground truth", [("ingest_attempts.csv", "R1"), ("ground_truth_files.csv", "R2"), ("ground_truth_normal.csv", "R2")]),
       ("Q2 dan Q3: rekonsiliasi dengan proses lama", [("macro_summary.csv", "R2"), ("macro_group_compare.csv", "R2"), ("macro_session_compare.csv", "R2")]),
       ("Q4 dan Q5: Cpk dan out-of-spec", [("cpk_group.csv", "R2"), ("kpi_group.csv", "R2")]),
       ("Q6 sampai Q8: shift, mesin, tren, pergeseran", [("shift_machine_test.csv", "R2"), ("weekly_all.csv", "R2"), ("changepoint.csv", "R2")]),
       ("Q9 dan Q10: waktu dihemat (estimated)", [("impact.csv", "R2")]),
       ("Q12: idempoten dan tes", [("idempotency.csv", "R2"), ("pytest_result.csv", "R2")]),
       ("Cek silang dan lima fakta rancangan", [("crosscheck.csv", "R2"), ("design_facts.csv", "R2")])]
for t, files in SEC:
    cells.append(md(f"## {t}"))
    for f, d in files:
        cells.append(code(f"print('{f}'); display(rd('{f}', {d}))"))
cells.append(md("Rata-rata mingguan semua mesin"))
cells.append(code("import matplotlib.pyplot as plt\nd = rd('weekly_machine.csv'); [plt.plot(g.iso_week, g.mean_g, label=m) for m, g in d.groupby('machine_id')]\nplt.xticks(rotation=90); plt.legend(); plt.ylabel('g'); plt.show()"))
nb.cells = cells
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(CM.RES3)}}).execute()
nbf.write(nb, CM.RES3 / "analysis.ipynb")
print("notebook ditulis")
