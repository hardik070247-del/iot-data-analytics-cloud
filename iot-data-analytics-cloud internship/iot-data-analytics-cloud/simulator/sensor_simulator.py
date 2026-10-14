#!/usr/bin/env python3
"""IoT sensor simulator.

Generates realistic temperature / humidity / pressure / battery readings for
several virtual devices and either:
  --mode local : appends JSON lines to a file (no cloud needed, good for testing)
  --mode aws   : publishes over MQTT (mutual TLS) to AWS IoT Core
"""
import argparse
import json
import math
import os
import random
import time
from datetime import datetime, timezone

LOCATIONS = ["lab", "warehouse", "server-room", "office", "outdoor"]


class Device:
    def __init__(self, idx: int):
        self.device_id = f"sensor-{idx:03d}"
        self.location = LOCATIONS[idx % len(LOCATIONS)]
        self.base_temp = random.uniform(22, 30)
        self.base_hum = random.uniform(40, 60)
        self.battery = 100.0

    def read(self, anomaly_rate: float) -> dict:
        now = datetime.now(timezone.utc)
        hour = now.hour + now.minute / 60
        diurnal = math.sin((hour - 9) / 24 * 2 * math.pi)  # day/night cycle

        temp = self.base_temp + 3 * diurnal + random.gauss(0, 0.4)
        hum = self.base_hum - 8 * diurnal + random.gauss(0, 1.2)
        pressure = 1013 + random.gauss(0, 1.5)
        self.battery = max(0.0, self.battery - random.uniform(0.001, 0.02))

        if random.random() < anomaly_rate:  # inject an anomaly spike
            temp += random.choice([-1, 1]) * random.uniform(12, 20)

        return {
            "device_id": self.device_id,
            "event_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "temperature_c": round(temp, 2),
            "humidity_pct": round(min(100, max(0, hum)), 2),
            "pressure_hpa": round(pressure, 2),
            "battery_pct": round(self.battery, 2),
            "location": self.location,
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["local", "aws"], default="local")
    p.add_argument("--devices", type=int, default=5)
    p.add_argument("--interval", type=float, default=2.0, help="seconds between rounds")
    p.add_argument("--count", type=int, default=0, help="rounds to run (0 = forever)")
    p.add_argument("--anomaly-rate", type=float, default=0.02)
    p.add_argument("--out", default="data/readings.jsonl", help="local mode output file")
    p.add_argument("--topic", default="iot/sensors/data")
    p.add_argument("--endpoint", help="AWS IoT endpoint (xxxx-ats.iot.<region>.amazonaws.com)")
    p.add_argument("--cert", default="certs/device.pem.crt")
    p.add_argument("--key", default="certs/private.pem.key")
    p.add_argument("--ca", default="certs/AmazonRootCA1.pem")
    p.add_argument("--client-id", default="iot-sim-publisher")
    a = p.parse_args()

    devices = [Device(i) for i in range(a.devices)]
    conn = None
    f = None

    if a.mode == "aws":
        from awscrt import mqtt
        from awsiot import mqtt_connection_builder

        if not a.endpoint:
            raise SystemExit("--endpoint is required in aws mode")
        conn = mqtt_connection_builder.mtls_from_path(
            endpoint=a.endpoint,
            cert_filepath=a.cert,
            pri_key_filepath=a.key,
            ca_filepath=a.ca,
            client_id=a.client_id,
            clean_session=False,
            keep_alive_secs=30,
        )
        print(f"Connecting to {a.endpoint} ...")
        conn.connect().result()
        print("Connected.")
    else:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        f = open(a.out, "a", buffering=1)

    n = 0
    try:
        while a.count == 0 or n < a.count:
            for d in devices:
                rec = d.read(a.anomaly_rate)
                payload = json.dumps(rec)
                if conn:
                    conn.publish(topic=a.topic, payload=payload, qos=mqtt.QoS.AT_LEAST_ONCE)
                else:
                    f.write(payload + "\n")
                print(payload)
            n += 1
            time.sleep(a.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if conn:
            conn.disconnect().result()
        if f:
            f.close()


if __name__ == "__main__":
    main()
