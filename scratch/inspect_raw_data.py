import sys
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

raw_dir = Path("data/raw")
for f in sorted(raw_dir.glob("*.xlsx")):
    print(f"\n==================== {f.name} ====================")
    try:
        xls = pd.ExcelFile(f)
        print("Sheets:", xls.sheet_names)
        for s in xls.sheet_names:
            df = pd.read_excel(f, sheet_name=s)
            print(f"\n--- Sheet: '{s}' (Rows: {len(df)}) ---")
            print("Columns:", list(df.columns))
            print("Sample head:")
            print(df.head(2))
    except Exception as e:
        print(f"Error reading {f.name}: {e}")
