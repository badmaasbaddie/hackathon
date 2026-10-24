import os
import pandas as pd

DATA_DIR = r"C:\Users\ambuj kumar\.gemini\antigravity\scratch\swasthyasetu-ai\dataset_extracted"

for fname in ["appointments.csv", "followups.csv", "health_worker_tasks.csv", "sample_reports.csv", "medicine_inventory.csv", "diagnostic_tests.csv"]:
    df = pd.read_csv(os.path.join(DATA_DIR, fname))
    print(f"\n=== {fname} ===")
    for col in df.columns:
        if "date" in col or "time" in col:
            print(f"  {col}: min={df[col].dropna().min()}, max={df[col].dropna().max()}")
        elif "status" in col or "priority" in col or "type" in col or "care" in col or "available" in col:
            print(f"  {col} counts:\n{df[col].value_counts(dropna=False)}")
