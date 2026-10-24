import os
import glob
import pandas as pd

DATA_DIR = r"C:\Users\ambuj kumar\.gemini\antigravity\scratch\swasthyasetu-ai\dataset_extracted"

csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
print(f"Found {len(csv_files)} CSV files:")

for f in sorted(csv_files):
    name = os.path.basename(f)
    try:
        df = pd.read_csv(f)
        print(f"\n--- {name} ---")
        print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        print(f"Columns: {list(df.columns)}")
        print("First 2 rows:")
        for idx, row in df.head(2).iterrows():
            print(dict(row))
    except Exception as e:
        print(f"Error reading {name}: {e}")
