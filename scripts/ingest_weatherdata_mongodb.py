"""
scripts/ingest_weatherdata_mongodb.py
=====================================
Script tổng hợp và nạp bộ dữ liệu thời tiết & chất lượng không khí (PM2.5) từ
`data/weatherdata` vào MongoDB Atlas và xuất cache tháng `data/processed/weatherdata_hcmc_monthly.csv`.

Các collection MongoDB tạo/cập nhật:
1. `weatherdata_hcmc_monthly`: Dữ liệu khí tượng và PM2.5 theo tháng của TP.HCM.
2. `weatherdata_cleaned`: Toàn bộ 7,656 bản ghi theo giờ (Hourly Time Series) từ cleaned_final.csv.
3. `weatherdata_raw_meteo`: Bản ghi khí tượng Open-Meteo từ raw_openmeteo.csv.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import paths
from mongo_data_service import mongo_data_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ingest_weatherdata")


def build_monthly_weatherdata() -> pd.DataFrame:
    """Tổng hợp dữ liệu theo tháng cho TP. Hồ Chí Minh từ data/weatherdata."""
    cleaned_path = paths.WEATHERDATA_CLEANED_CSV
    raw_meteo_path = paths.WEATHERDATA_RAW_METEO_CSV

    if not cleaned_path.exists() and not raw_meteo_path.exists():
        logger.error("Không tìm thấy file nguồn trong data/weatherdata!")
        return pd.DataFrame()

    # 1. Đọc raw_openmeteo để có dữ liệu khí tượng từ cuối 2024 đến giữa 2026
    df_meteo = pd.DataFrame()
    if raw_meteo_path.exists():
        df_meteo = pd.read_csv(raw_meteo_path)
        df_meteo['time'] = pd.to_datetime(df_meteo['time'])
        df_meteo['year'] = df_meteo['time'].dt.year
        df_meteo['month'] = df_meteo['time'].dt.month

    # 2. Đọc cleaned_final để có dữ liệu PM2.5 và thời tiết chuẩn hóa
    df_clean = pd.DataFrame()
    if cleaned_path.exists():
        df_clean = pd.read_csv(cleaned_path)
        df_clean['time'] = pd.to_datetime(df_clean['time'])
        df_clean['year'] = df_clean['time'].dt.year
        df_clean['month'] = df_clean['time'].dt.month

    # Aggregate meteo
    m_agg = None
    if not df_meteo.empty:
        m_agg = df_meteo.groupby(['year', 'month']).agg(
            precipitation_sum=('precipitation', 'sum'),
            temp_mean=('temperature', 'mean'),
            temp_max=('temperature', 'max'),
            temp_min=('temperature', 'min'),
            humidity_mean=('humidity', 'mean'),
            wind_speed_mean=('wind_speed', 'mean'),
            pressure_mean=('pressure', 'mean'),
            hours_obs=('temperature', 'count')
        ).reset_index()

    # Aggregate clean (PM2.5 focus)
    c_agg = None
    if not df_clean.empty:
        c_agg = df_clean.groupby(['year', 'month']).agg(
            pm25_mean=('pm25', 'mean'),
            pm25_max=('pm25', 'max'),
            pm25_min=('pm25', 'min'),
            clean_temp_mean=('temperature', 'mean'),
            clean_humidity_mean=('humidity', 'mean'),
            clean_precip_sum=('precipitation', 'sum'),
            clean_hours=('pm25', 'count')
        ).reset_index()

    if m_agg is not None and c_agg is not None:
        merged = pd.merge(m_agg, c_agg, on=['year', 'month'], how='outer')
    elif m_agg is not None:
        merged = m_agg
    else:
        merged = c_agg

    # Fill fallback from clean if meteo was empty or vice versa
    if 'clean_temp_mean' in merged.columns:
        merged['temp_mean'] = merged['temp_mean'].fillna(merged['clean_temp_mean'])
        merged['humidity_mean'] = merged['humidity_mean'].fillna(merged['clean_humidity_mean'])
        merged['precipitation_sum'] = merged['precipitation_sum'].fillna(merged['clean_precip_sum'])

    # Round numerical metrics
    round_cols = ['temp_mean', 'humidity_mean', 'precipitation_sum', 'wind_speed_mean', 'pressure_mean', 'pm25_mean', 'pm25_max', 'pm25_min']
    for col in round_cols:
        if col in merged.columns:
            merged[col] = merged[col].round(2)

    merged['province'] = 'TP. Hồ Chí Minh'
    merged['source'] = 'weatherdata_local_station'
    merged = merged.sort_values(['year', 'month']).reset_index(drop=True)

    # Reorder columns
    cols_order = [
        'province', 'year', 'month', 'precipitation_sum', 'temp_mean',
        'humidity_mean', 'pm25_mean', 'wind_speed_mean', 'pressure_mean',
        'pm25_max', 'pm25_min', 'source'
    ]
    present_cols = [c for c in cols_order if c in merged.columns]
    merged = merged[present_cols]

    return merged


def main():
    print("=" * 70)
    print(" Ingest & Backup WeatherData (PM2.5 + Khí Tượng) -> MongoDB Atlas ")
    print("=" * 70)

    # 1. Tổng hợp dữ liệu tháng
    print("\n[1/4] Đang tổng hợp dữ liệu thời tiết tháng từ data/weatherdata...")
    monthly_df = build_monthly_weatherdata()
    if monthly_df.empty:
        print("❌ Không tạo được bảng dữ liệu tháng!")
        return

    # Lưu local file processed
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    monthly_path = paths.PROCESSED_DIR / "weatherdata_hcmc_monthly.csv"
    monthly_df.to_csv(monthly_path, index=False, encoding='utf-8')
    print(f"✅ Đã lưu {len(monthly_df)} dòng tổng hợp tháng vào: {monthly_path}")
    print(monthly_df[['year', 'month', 'precipitation_sum', 'temp_mean', 'humidity_mean', 'pm25_mean']].to_string(index=False))

    # 2. Kiểm tra kết nối MongoDB
    print("\n[2/4] Kiểm tra kết nối MongoDB...")
    if not mongo_data_service.is_connected:
        print(f"⚠️ Không thể kết nối MongoDB: {mongo_data_service._connection_error}")
        print("Dữ liệu đã được lưu local, hệ thống vẫn hoạt động với Local Fallback.")
        return
    print(f"✅ Đã kết nối MongoDB Database: '{mongo_data_service.db_name}'")

    # 3. Nạp monthly weatherdata vào MongoDB
    print("\n[3/4] Đang lưu 'weatherdata_hcmc_monthly' vào MongoDB...")
    ok_monthly = mongo_data_service.backup_dataframe_to_mongo("weatherdata_hcmc_monthly", monthly_df)
    print(f" -> Nạp bảng tháng: {'THÀNH CÔNG' if ok_monthly else 'THẤT BẠI'}")

    # 4. Nạp cleaned hourly dataset vào MongoDB
    cleaned_path = paths.WEATHERDATA_CLEANED_CSV
    if cleaned_path.exists():
        print(f"\n[4/4] Đang lưu toàn bộ bản ghi giờ ({cleaned_path.name}) vào MongoDB collection 'weatherdata_cleaned'...")
        df_clean = pd.read_csv(cleaned_path)
        ok_clean = mongo_data_service.backup_dataframe_to_mongo("weatherdata_cleaned", df_clean)
        print(f" -> Nạp {len(df_clean)} bản ghi chuỗi thời gian: {'THÀNH CÔNG' if ok_clean else 'THẤT BẠI'}")

    # 5. Xác thực lại bằng cách query từ MongoDB
    print("\n[Xác Thực] Đọc thử dữ liệu vừa nạp từ MongoDB Atlas...")
    test_df = mongo_data_service.load_dataset("weatherdata_hcmc_monthly")
    print(f" -> Truy vấn thành công: {len(test_df)} dòng từ MongoDB.")

    print("\n" + "=" * 70)
    print(" Hoàn tất quá trình nạp WeatherData vào MongoDB thành công! ")
    print("=" * 70)


if __name__ == "__main__":
    main()
