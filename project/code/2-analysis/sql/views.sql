-- View KPI push test (Project 20). Cpk = MIN(USL - mean, mean - LSL) / (3 x stdev sampel). Hanya hasil ukur valid (0 < nilai <= kapasitas).
CREATE OR REPLACE VIEW v_measure AS
SELECT r.run_id, r.file_name, r.machine_id, r.model, r.condition, r.shift, r.test_datetime, m.seq, m.force_g, m.judgement,
       s.lsl_g, s.usl_g, STRFTIME(r.test_datetime, '%G-W%V') AS iso_week
FROM measurement m JOIN test_run r USING (run_id) JOIN spec s ON s.model = r.model AND s.test_type = r.test_type
WHERE m.is_valid;

CREATE OR REPLACE VIEW v_kpi_group AS
SELECT model, condition, COUNT(DISTINCT run_id) AS sesi, COUNT(*) AS n, AVG(force_g) AS mean_g, MIN(force_g) AS min_g, MAX(force_g) AS max_g,
       STDDEV_SAMP(force_g) AS sd_g, ANY_VALUE(lsl_g) AS lsl_g, ANY_VALUE(usl_g) AS usl_g,
       (ANY_VALUE(usl_g) - AVG(force_g)) / (3 * STDDEV_SAMP(force_g)) AS cpu,
       (AVG(force_g) - ANY_VALUE(lsl_g)) / (3 * STDDEV_SAMP(force_g)) AS cpl,
       LEAST((ANY_VALUE(usl_g) - AVG(force_g)), (AVG(force_g) - ANY_VALUE(lsl_g))) / (3 * STDDEV_SAMP(force_g)) AS cpk,
       AVG(CASE WHEN force_g < lsl_g OR force_g > usl_g THEN 1.0 ELSE 0.0 END) AS oos_rate
FROM v_measure GROUP BY model, condition;

CREATE OR REPLACE VIEW v_kpi_machine_shift AS
SELECT machine_id, shift, COUNT(*) AS n, AVG(force_g) AS mean_g, STDDEV_SAMP(force_g) AS sd_g, MEDIAN(force_g) AS median_g
FROM v_measure GROUP BY machine_id, shift;

CREATE OR REPLACE VIEW v_kpi_weekly AS
SELECT iso_week, machine_id, COUNT(*) AS n, AVG(force_g) AS mean_g, STDDEV_SAMP(force_g) AS sd_g
FROM v_measure GROUP BY iso_week, machine_id;

CREATE OR REPLACE VIEW v_kpi_run AS
SELECT run_id, file_name, model, condition, machine_id, shift, test_datetime, COUNT(*) AS n, AVG(force_g) AS mean_g, MIN(force_g) AS min_g, MAX(force_g) AS max_g, STDDEV_SAMP(force_g) AS sd_g
FROM v_measure GROUP BY run_id, file_name, model, condition, machine_id, shift, test_datetime;
