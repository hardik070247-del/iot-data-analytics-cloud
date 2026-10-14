-- 1. Latest reading per device
SELECT device_id, event_time, temperature_c, humidity_pct, battery_pct
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY event_time DESC) rn
  FROM iot_readings
) WHERE rn = 1;

-- 2. Hourly averages per location
SELECT location,
       DATE_TRUNC('hour', event_time) AS hour,
       ROUND(AVG(temperature_c), 2) AS avg_temp,
       ROUND(AVG(humidity_pct), 2)  AS avg_humidity,
       COUNT(*) AS readings
FROM iot_readings
GROUP BY 1, 2
ORDER BY 2 DESC, 1;

-- 3. Anomaly detection: temperature more than 3 std-devs from the device mean
WITH stats AS (
  SELECT device_id, AVG(temperature_c) mu, STDDEV(temperature_c) sd
  FROM iot_readings GROUP BY device_id
)
SELECT r.device_id, r.event_time, r.temperature_c,
       ROUND((r.temperature_c - s.mu) / NULLIF(s.sd, 0), 2) AS z_score
FROM iot_readings r JOIN stats s USING (device_id)
WHERE ABS((r.temperature_c - s.mu) / NULLIF(s.sd, 0)) > 3
ORDER BY r.event_time DESC;

-- 4. Rolling 10-reading moving average of temperature
SELECT device_id, event_time, temperature_c,
       ROUND(AVG(temperature_c) OVER (
         PARTITION BY device_id ORDER BY event_time
         ROWS BETWEEN 9 PRECEDING AND CURRENT ROW), 2) AS moving_avg
FROM iot_readings
ORDER BY device_id, event_time;

-- 5. Devices with low battery
SELECT device_id, MIN(battery_pct) AS min_battery
FROM iot_readings GROUP BY device_id HAVING MIN(battery_pct) < 20;

-- 6. Data freshness (is the pipeline alive?)
SELECT MAX(event_time) AS last_event,
       DATEDIFF(second, MAX(event_time), GETDATE()) AS seconds_ago
FROM iot_readings;
