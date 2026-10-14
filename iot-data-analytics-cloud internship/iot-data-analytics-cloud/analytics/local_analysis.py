#!/usr/bin/env python3
"""Offline analysis of simulator output (same logic as sql/analytics.sql)."""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/readings.jsonl")
    p.add_argument("--outdir", default="output")
    a = p.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    df = pd.read_json(a.input, lines=True)
    df["event_time"] = pd.to_datetime(df["event_time"])

    # z-score anomalies per device
    g = df.groupby("device_id")["temperature_c"]
    df["z"] = (df["temperature_c"] - g.transform("mean")) / g.transform("std")
    anomalies = df[df["z"].abs() > 3]
    anomalies.to_csv(f"{a.outdir}/anomalies.csv", index=False)

    summary = df.groupby("location")[["temperature_c", "humidity_pct", "battery_pct"]].agg(["mean", "min", "max"]).round(2)
    summary.to_csv(f"{a.outdir}/summary_by_location.csv")
    print(summary, "\n")
    print(f"{len(df)} readings, {len(anomalies)} anomalies")

    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for dev, d in df.groupby("device_id"):
        ax[0].plot(d["event_time"], d["temperature_c"], label=dev)
        ax[1].plot(d["event_time"], d["humidity_pct"], label=dev)
    ax[0].scatter(anomalies["event_time"], anomalies["temperature_c"], c="red", marker="x", s=60, zorder=5, label="anomaly")
    ax[0].set_ylabel("Temperature (°C)")
    ax[1].set_ylabel("Humidity (%)")
    ax[0].legend(ncol=3, fontsize=8)
    ax[0].set_title("IoT sensor readings")
    plt.tight_layout()
    plt.savefig(f"{a.outdir}/sensor_dashboard.png", dpi=150)
    print(f"Saved chart to {a.outdir}/sensor_dashboard.png")


if __name__ == "__main__":
    main()
