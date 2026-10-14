-- Run in Redshift (Query Editor v2) before starting the pipeline.
-- Column names MUST match the JSON keys sent by the simulator (COPY ... json 'auto').
CREATE TABLE IF NOT EXISTS iot_readings (
    device_id     VARCHAR(32),
    event_time    TIMESTAMP,
    temperature_c DOUBLE PRECISION,
    humidity_pct  DOUBLE PRECISION,
    pressure_hpa  DOUBLE PRECISION,
    battery_pct   DOUBLE PRECISION,
    location      VARCHAR(32)
)
DISTKEY(device_id)
SORTKEY(event_time);
