-- Skema database push test (empat tabel rancangan). Dipakai 03_ingest.py.
CREATE TABLE IF NOT EXISTS spec (model VARCHAR, test_type VARCHAR, lsl_g DOUBLE, usl_g DOUBLE);
CREATE TABLE IF NOT EXISTS test_run (
    run_id VARCHAR PRIMARY KEY, file_name VARCHAR, file_hash VARCHAR UNIQUE, machine_id VARCHAR, model VARCHAR,
    condition VARCHAR, test_type VARCHAR, shift VARCHAR, test_datetime DATE, number_format VARCHAR);
CREATE TABLE IF NOT EXISTS measurement (run_id VARCHAR, seq INTEGER, force_g DOUBLE, judgement VARCHAR, is_valid BOOLEAN);
CREATE TABLE IF NOT EXISTS ingest_log (
    attempt INTEGER, file_name VARCHAR, file_hash VARCHAR, status VARCHAR, error_type VARCHAR, rows_read INTEGER, rows_invalid INTEGER, run_id VARCHAR);
