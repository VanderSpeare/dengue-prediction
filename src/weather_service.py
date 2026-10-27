"""
weather_service.py — Open-Meteo Historical Weather API Client
=============================================================
Thu thap du lieu khi hau thang (luong mua, nhiet do, do am) cho tung
Tinh/Thanh theo toa do trung tam. Khong yeu cau API key.

API endpoint:  https://archive-api.open-meteo.com/v1/archive
Documentation: https://open-meteo.com/en/docs/historical-weather-api
"""

import logging
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import pandas as pd
import json

try:
    import urllib.request
    import urllib.parse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

try:
    from . import paths
    from .mongo_data_service import mongo_data_service
except ImportError:
    import paths
    try:
        from mongo_data_service import mongo_data_service
    except ImportError:
        mongo_data_service = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Toa do trung tam 34 Tinh/Thanh
# ---------------------------------------------------------------------------
PROVINCE_COORDS = {
    'Tuyen Quang':      {'lat': 21.8236, 'lon': 105.2144},
    'Lao Cai':          {'lat': 22.3364, 'lon': 103.9753},
    'Thai Nguyen':      {'lat': 21.5942, 'lon': 105.8480},
    'Hai Phong':        {'lat': 20.8449, 'lon': 106.6881},
    'TP. Ho Chi Minh':  {'lat': 10.7769, 'lon': 106.7009},
    'Phu Tho':          {'lat': 21.3683, 'lon': 105.2018},
    'Bac Ninh':         {'lat': 21.1861, 'lon': 106.0763},
    'Hung Yen':         {'lat': 20.6465, 'lon': 106.0511},
    'Ninh Binh':        {'lat': 20.2506, 'lon': 105.9745},
    'Quang Tri':        {'lat': 16.7500, 'lon': 107.1853},
    'Da Nang':          {'lat': 16.0544, 'lon': 108.2022},
    'Quang Ngai':       {'lat': 15.1214, 'lon': 108.8044},
    'Gia Lai':          {'lat': 13.9833, 'lon': 108.0000},
    'Khanh Hoa':        {'lat': 12.2388, 'lon': 109.1967},
    'Lam Dong':         {'lat': 11.9404, 'lon': 108.4583},
    'Dak Lak':          {'lat': 12.7100, 'lon': 108.2378},
    'Dong Nai':         {'lat': 10.9453, 'lon': 107.2536},
    'Tay Ninh':         {'lat': 11.3351, 'lon': 106.1099},
    'Can Tho':          {'lat': 10.0341, 'lon': 105.7876},
    'Vinh Long':        {'lat': 10.2397, 'lon': 105.9570},
    'Dong Thap':        {'lat': 10.4900, 'lon': 105.6882},
    'Ca Mau':           {'lat':  9.1769, 'lon': 105.1500},
    'An Giang':         {'lat': 10.5215, 'lon': 105.1259},
    'Ha Noi':           {'lat': 21.0245, 'lon': 105.8412},
    'Hue':              {'lat': 16.4637, 'lon': 107.5909},
    'Lai Chau':         {'lat': 22.3964, 'lon': 103.4319},
    'Dien Bien':        {'lat': 21.3860, 'lon': 103.0230},
    'Son La':           {'lat': 21.3272, 'lon': 103.9144},
    'Lang Son':         {'lat': 21.8537, 'lon': 106.7611},
    'Quang Ninh':       {'lat': 21.0062, 'lon': 107.2925},
    'Thanh Hoa':        {'lat': 19.8068, 'lon': 105.7852},
    'Nghe An':          {'lat': 18.6696, 'lon': 105.6813},
    'Ha Tinh':          {'lat': 18.3428, 'lon': 105.9057},
    'Cao Bang':         {'lat': 22.6666, 'lon': 106.2637},
}

# Province name mapping: Vietnamese name -> ASCII key in PROVINCE_COORDS
PROVINCE_NAME_TO_KEY = {
    'Tuyên Quang': 'Tuyen Quang',
    'Lào Cai': 'Lao Cai',
    'Thái Nguyên': 'Thai Nguyen',
    'Hải Phòng': 'Hai Phong',
    'TP. Hồ Chí Minh': 'TP. Ho Chi Minh',
    'Phú Thọ': 'Phu Tho',
    'Bắc Ninh': 'Bac Ninh',
    'Hưng Yên': 'Hung Yen',
    'Ninh Bình': 'Ninh Binh',
    'Quảng Trị': 'Quang Tri',
    'Đà Nẵng': 'Da Nang',
    'Quảng Ngãi': 'Quang Ngai',
    'Gia Lai': 'Gia Lai',
    'Khánh Hòa': 'Khanh Hoa',
    'Lâm Đồng': 'Lam Dong',
    'Đắk Lắk': 'Dak Lak',
    'Đồng Nai': 'Dong Nai',
    'Tây Ninh': 'Tay Ninh',
    'Cần Thơ': 'Can Tho',
    'Vĩnh Long': 'Vinh Long',
    'Đồng Tháp': 'Dong Thap',
    'Cà Mau': 'Ca Mau',
    'An Giang': 'An Giang',
    'Hà Nội': 'Ha Noi',
    'Huế': 'Hue',
    'Lai Châu': 'Lai Chau',
    'Điện Biên': 'Dien Bien',
    'Sơn La': 'Son La',
    'Lạng Sơn': 'Lang Son',
    'Quảng Ninh': 'Quang Ninh',
    'Thanh Hóa': 'Thanh Hoa',
    'Nghệ An': 'Nghe An',
    'Hà Tĩnh': 'Ha Tinh',
    'Cao Bằng': 'Cao Bang',
}

WEATHER_CACHE_CSV = paths.PROCESSED_DIR / "weather_cache.csv"
OPENMETEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_VARIABLES = [
    "precipitation_sum",
    "temperature_2m_mean",
    "relative_humidity_2m_mean"
]


def _get_coords(province_vn: str):
    """Tra toa do tu ten tinh tieng Viet hoac ASCII."""
    # Try direct ASCII key
    if province_vn in PROVINCE_COORDS:
        return PROVINCE_COORDS[province_vn]
    # Try Vietnamese name mapping
    key = PROVINCE_NAME_TO_KEY.get(province_vn)
    if key and key in PROVINCE_COORDS:
        return PROVINCE_COORDS[key]
    return None


def _fetch_daily_api(lat: float, lon: float,
                     start_date: str, end_date: str,
                     retries: int = 3):
    """Goi Open-Meteo Archive API va tra ve JSON."""
    if not HAS_URLLIB:
        return None

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(WEATHER_VARIABLES),
        "timezone": "Asia/Ho_Chi_Minh"
    }
    url = OPENMETEO_ARCHIVE_URL + "?" + urllib.parse.urlencode(params)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"API call attempt {attempt+1}/{retries} failed: {e}. Wait {wait}s…")
            time.sleep(wait)
    return None


def _daily_to_monthly(raw: dict) -> pd.DataFrame:
    """Chuyen daily JSON cua Open-Meteo thanh monthly aggregate DataFrame."""
    time_list = raw.get("daily", {}).get("time", [])
    if not time_list:
        return pd.DataFrame()

    n = len(time_list)
    df = pd.DataFrame({
        "date":          pd.to_datetime(time_list),
        "precipitation": raw["daily"].get("precipitation_sum", [None] * n),
        "temperature":   raw["daily"].get("temperature_2m_mean", [None] * n),
        "humidity":      raw["daily"].get("relative_humidity_2m_mean", [None] * n),
    })
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    monthly = df.groupby(["year", "month"]).agg(
        precipitation_sum=("precipitation", "sum"),
        temp_mean=("temperature", "mean"),
        humidity_mean=("humidity", "mean"),
    ).reset_index()
    return monthly


def fetch_province_weather(province: str,
                           start_year: int = 2023,
                           end_year: Optional[int] = None) -> pd.DataFrame:
    """
    Lay du lieu thoi tiet thang cho 1 tinh.
    Returns DataFrame: province, year, month, precipitation_sum, temp_mean, humidity_mean
    """
    coords = _get_coords(province)
    if coords is None:
        logger.warning(f"No coordinates for '{province}' — skipping.")
        return pd.DataFrame()

    today = date.today()
    if end_year is None:
        end_year = today.year

    # Archive API chỉ nhận ngày từ quá khứ đến hiện tại (không vượt quá hôm nay)
    start_date = f"{start_year}-01-01"
    target_end = f"{end_year}-12-31"
    today_str = today.isoformat()
    end_date = min(target_end, today_str)

    if start_date > end_date:
        start_date = f"{today.year}-01-01"

    logger.info(f"  Fetching weather: {province} ({start_date} to {end_date})")
    raw = _fetch_daily_api(coords["lat"], coords["lon"], start_date, end_date)
    if raw is None:
        logger.warning(f"  No API data for {province}.")
        return pd.DataFrame()

    monthly = _daily_to_monthly(raw)
    if monthly.empty:
        return pd.DataFrame()

    monthly["province"] = province
    return monthly[["province", "year", "month",
                    "precipitation_sum", "temp_mean", "humidity_mean"]]


def fetch_all_provinces_weather(provinces=None,
                                start_year: int = 2023,
                                end_year: Optional[int] = None,
                                delay_between: float = 0.4) -> pd.DataFrame:
    """Thu thap thoi tiet cho tat ca (hoac danh sach) tinh."""
    if provinces is None:
        provinces = list(PROVINCE_NAME_TO_KEY.keys())

    results = []
    for i, prov in enumerate(provinces, 1):
        logger.info(f"[{i}/{len(provinces)}] {prov}")
        df = fetch_province_weather(prov, start_year=start_year, end_year=end_year)
        if not df.empty:
            results.append(df)
        if i < len(provinces):
            time.sleep(delay_between)

    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True)


def load_weather_cache() -> pd.DataFrame:
    if mongo_data_service:
        df = mongo_data_service.load_dataset("weather_cache", WEATHER_CACHE_CSV)
        if not df.empty:
            logger.info(f"Weather cache loaded: {len(df)} rows")
            return df
    elif WEATHER_CACHE_CSV.exists():
        df = pd.read_csv(WEATHER_CACHE_CSV)
        logger.info(f"Weather cache loaded: {len(df)} rows")
        return df
    return pd.DataFrame()


def save_weather_cache(df: pd.DataFrame) -> None:
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if mongo_data_service:
        mongo_data_service.save_dataset("weather_cache", df, WEATHER_CACHE_CSV)
    else:
        df.to_csv(WEATHER_CACHE_CSV, index=False)
    logger.info(f"Weather cache saved: {len(df)} rows -> {WEATHER_CACHE_CSV}")


def get_or_fetch_weather(provinces=None,
                         start_year: int = 2023,
                         end_year: Optional[int] = None,
                         force_refresh: bool = False) -> pd.DataFrame:
    """
    Uu tien doc cache. Neu thieu du lieu moi nhat thi fetch delta roi merge.
    """
    current_year = end_year or date.today().year

    if not force_refresh:
        cached = load_weather_cache()
        if not cached.empty:
            max_cached = int(cached["year"].max())
            if max_cached >= current_year:
                logger.info(f"Cache is up-to-date (max year: {max_cached}).")
                return cached
            # Fetch delta
            logger.info(f"Cache missing {max_cached+1}→{current_year}. Fetching delta…")
            new_data = fetch_all_provinces_weather(
                provinces=provinces, start_year=max_cached + 1, end_year=current_year
            )
            if not new_data.empty:
                merged = pd.concat([cached, new_data], ignore_index=True)
                merged = merged.drop_duplicates(subset=["province", "year", "month"], keep="last")
                save_weather_cache(merged)
                return merged
            return cached

    # Full fetch
    weather_df = fetch_all_provinces_weather(
        provinces=provinces, start_year=start_year, end_year=current_year
    )
    if not weather_df.empty:
        save_weather_cache(weather_df)
    return weather_df


def get_weather_safe(provinces=None,
                     start_year: int = 2023,
                     end_year: Optional[int] = None) -> pd.DataFrame:
    """
    Wrapper an toan: tra DataFrame rong neu mat mang / loi.
    Dung trong pipeline chinh de khong crash neu weather API khong kha dung.
    """
    try:
        return get_or_fetch_weather(provinces=provinces,
                                    start_year=start_year,
                                    end_year=end_year)
    except Exception as e:
        logger.warning(f"Weather service unavailable ({e}). Continuing without weather features.")
        return pd.DataFrame()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Test: fetch TP. Ho Chi Minh weather ===")
    df = fetch_province_weather("TP. Ho Chi Minh", start_year=2024, end_year=2025)
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("No data.")
