import sys
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Import data_processor functions
sys.path.insert(0, "src")
from data_processor import extract_province, extract_district, REQUIRED_COLUMNS

raw_dir = Path("data/raw")
all_dfs = []

for file_path in sorted(raw_dir.glob("*.xlsx")):
    xls = pd.ExcelFile(file_path)
    print(f"\nProcessing file: {file_path.name}")
    
    # Check sheets
    for sheet in xls.sheet_names:
        if sheet.lower().startswith("ma icd"):
            continue
            
        df = pd.read_excel(file_path, sheet_name=sheet)
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            print(f"  Sheet '{sheet}' missing {missing} -> skipped")
            continue
            
        col_map = {
            'NgayVao': 'date',
            'NgayRa': 'discharge_date',
            'Diachi': 'address',
            'NamSinh': 'birth_year',
            'Maicd': 'icd_code',
            'TenBenhNhan': 'patient_name'
        }
        df = df.rename(columns=col_map)
        df = df.dropna(subset=['date'])
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        
        # Filter ICD if general fever
        sheet_or_file = f"{file_path.stem} {sheet}".lower()
        is_dedicated = any(k in sheet_or_file for k in ['xuất huyết', 'xuat huyet', 'data'])
        if not is_dedicated and 'icd_code' in df.columns:
            df['icd_code'] = df['icd_code'].astype(str)
            df = df[df['icd_code'].str.contains('A90|A97', na=False)]
            
        df['source_file'] = file_path.name
        df['source_sheet'] = sheet
        print(f"  Sheet '{sheet}' valid filtered rows: {len(df)}")
        all_dfs.append(df)

if all_dfs:
    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"\nTotal concatenated rows across all files: {len(combined)}")
    
    # Deduplicate based on core patient fields
    dedup_cols = ['patient_name', 'birth_year', 'address', 'date']
    avail_dedup = [c for c in dedup_cols if c in combined.columns]
    deduped = combined.drop_duplicates(subset=avail_dedup)
    print(f"Total unique patient records after deduplication: {len(deduped)}")
    
    deduped['province'] = deduped['address'].apply(extract_province)
    deduped['district'] = deduped['address'].apply(extract_district)
    deduped = deduped.dropna(subset=['province'])
    print(f"Valid mapped provinces: {deduped['province'].nunique()} provinces, {len(deduped)} cases.")
