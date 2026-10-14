# IoT Data Analytics on Cloud

A real-time IoT data pipeline: simulated sensors publish telemetry over MQTT to **AWS IoT Core**, which streams it through **Kinesis Data Firehose** into **Amazon Redshift**, where it is analysed with SQL.

## Architecture

```
Python simulator --MQTT/TLS--> AWS IoT Core --Rule--> Kinesis Firehose --> S3 (staging) --COPY--> Redshift --> SQL analytics
 (5 virtual sensors)         (topic iot/sensors/data)                                                (BI / dashboards)
```

## Features
- Simulates temperature, humidity, pressure and battery data with day/night cycles and injected anomalies
- Secure device connectivity using X.509 certificates (mutual TLS) and a least-privilege IoT policy
- Infrastructure as code (CloudFormation) for the Rule, Firehose, S3 staging bucket and IAM roles
- Redshift schema + analytics queries (hourly aggregates, z-score anomaly detection, moving average, low-battery alerts, data freshness)
- **Local mode** to test everything without an AWS account, plus a pandas/matplotlib report

## Project structure
```
simulator/sensor_simulator.py   # data generator (local or AWS mode)
infra/template.yaml             # CloudFormation: IoT rule, Firehose, S3, IAM, IoT policy
scripts/provision_device.sh     # creates Thing + certs
sql/schema.sql                  # Redshift table
sql/analytics.sql               # analytics queries
analytics/local_analysis.py     # offline analysis + chart
```

## Quick start (no cloud needed)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python simulator/sensor_simulator.py --mode local --count 60 --interval 0.2
python analytics/local_analysis.py        # writes output/sensor_dashboard.png
```

## Deploy on AWS
1. **Redshift:** create a Redshift Serverless workgroup (or cluster), make it publicly accessible, and in its security group allow inbound port 5439 from the Kinesis Data Firehose IP range for your region (AWS docs: *Grant Firehose access to an Amazon Redshift destination*). Run `sql/schema.sql` in Query Editor v2.
2. **Deploy the stack:**
   ```bash
   aws cloudformation deploy --stack-name iot-analytics --template-file infra/template.yaml \
     --capabilities CAPABILITY_IAM \
     --parameter-overrides RedshiftJdbcUrl=jdbc:redshift://<host>:5439/dev RedshiftUser=<user> RedshiftPassword=<password>
   ```
3. **Provision a device and get the endpoint:** `./scripts/provision_device.sh`
4. **Start streaming:**
   ```bash
   python simulator/sensor_simulator.py --mode aws --endpoint <endpoint-from-step-3>
   ```
5. Verify in the IoT Core **MQTT test client** (subscribe to `iot/sensors/#`), then after ~1 minute run the queries in `sql/analytics.sql`.

## Variants
- **Azure:** swap IoT Core for Azure IoT Hub (azure-iot-device SDK) + Stream Analytics.
- **BigQuery:** IoT Core -> Kinesis/Lambda -> BigQuery streaming insert, or Azure IoT Hub -> Event Hub -> Stream Analytics -> BigQuery.

## Cost / cleanup
Pause Redshift when idle and delete the stack: `aws cloudformation delete-stack --stack-name iot-analytics` (empty the S3 bucket first).

## Security notes
Never commit `certs/` or passwords (already in `.gitignore`). Use AWS Secrets Manager for the Redshift password in production.

## Future work
Grafana/QuickSight dashboard, SNS alerts on anomalies, Parquet + Redshift Spectrum for cold data.
