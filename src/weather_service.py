"""
weather_service.py — Hybrid Weather API Client (WeatherAPI + Open-Meteo Fallback)
==================================================================================
Thu thập dữ liệu khí hậu tháng (lượng mưa, nhiệt độ, độ ẩm) cho từng Tỉnh/Thành.

Ưu tiên nguồn:
  1. WeatherAPI.com (endpoint history.json)  — cần WEATHERAPI_KEY trong .env
  2. Open-Meteo Archive API                  — miễn phí, không cần key (fallback)

Dữ liệu được lưu cache kép: MongoDB (nguồn chính) và CSV (local fallback).

Scheduler tích hợp (APScheduler):
  - Cập nhật hàng tuần: mỗi Thứ Hai 02:00 — đồng bộ dữ liệu tuần qua cho HCMC
  - Cập nhật hàng tháng: ngày 1 mỗi tháng lúc 03:00 — đồng bộ đầy đủ tất cả tỉnh
"""

import logging
import os
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional
import json
import pandas as pd

try:
    import urllib.request
    import urllib.parse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from . import paths
    from .mongo_data_service import mongo_data_service
except ImportError:
    import paths
    try:
        from mongo_data_service import mongo_data_service
    except ImportError:
        mongo_data_service = None

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv(paths.PROJECT_ROOT / ".env", override=False)
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WeatherAPI config
# ---------------------------------------------------------------------------
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY") or os.getenv("WEATHER_API_KEY")
WEATHERAPI_HISTORY_URL = "https://api.weatherapi.com/v1/history.json"

# ---------------------------------------------------------------------------
# Tọa độ trung tâm 34 Tỉnh/Thành và query name cho WeatherAPI
# ---------------------------------------------------------------------------
PROVINCE_COORDS = {
    'Tuyen Quang':      {'lat': 21.8236, 'lon': 105.2144, 'wapi_q': 'Tuyen Quang'},
    'Lao Cai':          {'lat': 22.3364, 'lon': 103.9753, 'wapi_q': 'Lao Cai'},
    'Thai Nguyen':      {'lat': 21.5942, 'lon': 105.8480, 'wapi_q': 'Thai Nguyen'},
    'Hai Phong':        {'lat': 20.8449, 'lon': 106.6881, 'wapi_q': 'Hai Phong'},
    'TP. Ho Chi Minh':  {'lat': 10.7769, 'lon': 106.7009, 'wapi_q': 'Ho Chi Minh'},
    'Phu Tho':          {'lat': 21.3683, 'lon': 105.2018, 'wapi_q': 'Phu Tho'},
    'Bac Ninh':         {'lat': 21.1861, 'lon': 106.0763, 'wapi_q': 'Bac Ninh'},
    'Hung Yen':         {'lat': 20.6465, 'lon': 106.0511, 'wapi_q': 'Hung Yen'},
    'Ninh Binh':        {'lat': 20.2506, 'lon': 105.9745, 'wapi_q': 'Ninh Binh'},
    'Quang Tri':        {'lat': 16.7500, 'lon': 107.1853, 'wapi_q': 'Quang Tri'},
    'Da Nang':          {'lat': 16.0544, 'lon': 108.2022, 'wapi_q': 'Da Nang'},
    'Quang Ngai':       {'lat': 15.1214, 'lon': 108.8044, 'wapi_q': 'Quang Ngai'},
    'Gia Lai':          {'lat': 13.9833, 'lon': 108.0000, 'wapi_q': 'Gia Lai'},
    'Khanh Hoa':        {'lat': 12.2388, 'lon': 109.1967, 'wapi_q': 'Nha Trang'},
    'Lam Dong':         {'lat': 11.9404, 'lon': 108.4583, 'wapi_q': 'Da Lat'},
    'Dak Lak':          {'lat': 12.7100, 'lon': 108.2378, 'wapi_q': 'Buon Ma Thuot'},
    'Dong Nai':         {'lat': 10.9453, 'lon': 107.2536, 'wapi_q': 'Bien Hoa'},
    'Tay Ninh':         {'lat': 11.3351, 'lon': 106.1099, 'wapi_q': 'Tay Ninh'},
    'Can Tho':          {'lat': 10.0341, 'lon': 105.7876, 'wapi_q': 'Can Tho'},
    'Vinh Long':        {'lat': 10.2397, 'lon': 105.9570, 'wapi_q': 'Vinh Long'},
    'Dong Thap':        {'lat': 10.4900, 'lon': 105.6882, 'wapi_q': 'Cao Lanh'},
    'Ca Mau':           {'lat':  9.1769, 'lon': 105.1500, 'wapi_q': 'Ca Mau'},
    'An Giang':         {'lat': 10.5215, 'lon': 105.1259, 'wapi_q': 'Long Xuyen'},
    'Ha Noi':           {'lat': 21.0245, 'lon': 105.8412, 'wapi_q': 'Hanoi'},
    'Hue':              {'lat': 16.4637, 'lon': 107.5909, 'wapi_q': 'Hue'},
    'Lai Chau':         {'lat': 22.3964, 'lon': 103.4319, 'wapi_q': 'Lai Chau'},
    'Dien Bien':        {'lat': 21.3860, 'lon': 103.0230, 'wapi_q': 'Dien Bien Phu'},
    'Son La':           {'lat': 21.3272, 'lon': 103.9144, 'wapi_q': 'Son La'},
    'Lang Son':         {'lat': 21.8537, 'lon': 106.7611, 'wapi_q': 'Lang Son'},
    'Quang Ninh':       {'lat': 21.0062, 'lon': 107.2925, 'wapi_q': 'Ha Long'},
    'Thanh Hoa':        {'lat': 19.8068, 'lon': 105.7852, 'wapi_q': 'Thanh Hoa'},
    'Nghe An':          {'lat': 18.6696, 'lon': 105.6813, 'wapi_q': 'Vinh'},
    'Ha Tinh':          {'lat': 18.3428, 'lon': 105.9057, 'wapi_q': 'Ha Tinh'},
    'Cao Bang':         {'lat': 22.6666, 'lon': 106.2637, 'wapi_q': 'Cao Bang'},
}

# Mapping: tên tiếng Việt → key ASCII trong PROVINCE_COORDS
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

# Danh sách tỉnh ưu tiên (HCMC luôn đứng đầu)
PRIORITY_PROVINCES = ['TP. Ho Chi Minh', 'Ha Noi', 'Da Nang', 'Dong Nai', 'Binh Duong']

WEATHER_CACHE_CSV = paths.PROCESSED_DIR / "weather_cache.csv"
OPENMETEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_VARIABLES = [
    "precipitation_sum",
    "temperature_2m_mean",
    "relative_humidity_2m_mean"
]


# ===========================================================================
# HELPER: Tìm thông tin tỉnh
# ===========================================================================
def _get_province_info(province_vn: str) -> Optional[dict]:
    """Trả về dict gồm lat, lon, wapi_q cho một tỉnh (hỗ trợ cả ASCII và tiếng Việt)."""
    if province_vn in PROVINCE_COORDS:
        info = PROVINCE_COORDS[province_vn].copy()
        info['ascii_key'] = province_vn
        return info
    key = PROVINCE_NAME_TO_KEY.get(province_vn)
    if key and key in PROVINCE_COORDS:
        info = PROVINCE_COORDS[key].copy()
        info['ascii_key'] = key
        return info
    return None


# ===========================================================================
# NGUỒN 1: WeatherAPI.com — history.json (lấy theo khoảng ngày)
# ===========================================================================
def _fetch_weatherapi_range(wapi_q: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Gọi WeatherAPI history.json cho khoảng ngày [start_date, end_date] (YYYY-MM-DD).
    Trả về DataFrame daily: date, precipitation_mm, temp_c, humidity_pct.
    Trả về DataFrame rỗng nếu không có key hoặc lỗi.
    """
    if not WEATHERAPI_KEY or not HAS_REQUESTS:
        return pd.DataFrame()

    try:
        resp = _requests.get(
            WEATHERAPI_HISTORY_URL,
            params={"key": WEATHERAPI_KEY, "q": wapi_q, "dt": start_date, "end_dt": end_date, "aqi": "no"},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"WeatherAPI [{wapi_q}] HTTP {resp.status_code}: {resp.text[:200]}")
            return pd.DataFrame()

        forecast_days = resp.json().get("forecast", {}).get("forecastday", [])
        rows = []
        for item in forecast_days:
            d = item.get("day", {})
            rows.append({
                "date": item.get("date"),
                "precipitation": d.get("totalprecip_mm", 0.0),
                "temperature": d.get("avgtemp_c"),
                "humidity": d.get("avghumidity"),
            })
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        return df

    except Exception as e:
        logger.warning(f"WeatherAPI lỗi [{wapi_q}]: {e}")
        return pd.DataFrame()


# ===========================================================================
# NGUỒN 2: Open-Meteo Archive API (fallback, tọa độ)
# ===========================================================================
def _fetch_openmeteo_range(lat: float, lon: float, start_date: str, end_date: str,
                           retries: int = 3) -> pd.DataFrame:
    """Gọi Open-Meteo Archive API. Trả về DataFrame daily."""
    if not HAS_URLLIB:
        return pd.DataFrame()

    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start_date, "end_date": end_date,
        "daily": ",".join(WEATHER_VARIABLES),
        "timezone": "Asia/Ho_Chi_Minh",
    }
    url = OPENMETEO_ARCHIVE_URL + "?" + urllib.parse.urlencode(params)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                raw = json.loads(r.read().decode("utf-8"))
            time_list = raw.get("daily", {}).get("time", [])
            if not time_list:
                return pd.DataFrame()
            n = len(time_list)
            df = pd.DataFrame({
                "date": pd.to_datetime(time_list),
                "precipitation": raw["daily"].get("precipitation_sum", [None] * n),
                "temperature": raw["daily"].get("temperature_2m_mean", [None] * n),
                "humidity": raw["daily"].get("relative_humidity_2m_mean", [None] * n),
            })
            return df
        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"Open-Meteo attempt {attempt+1}/{retries} failed: {e}. Wait {wait}s…")
            time.sleep(wait)
    return pd.DataFrame()


# ===========================================================================
# LOGIC TỔNG HỢP: Lấy dữ liệu daily, rồi gom nhóm theo tháng
# ===========================================================================
def _daily_to_monthly(df_daily: pd.DataFrame, province_key: str) -> pd.DataFrame:
    """Gom nhóm DataFrame daily → monthly aggregate."""
    if df_daily.empty:
        return pd.DataFrame()
    df = df_daily.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    monthly = df.groupby(["year", "month"]).agg(
        precipitation_sum=("precipitation", "sum"),
        temp_mean=("temperature", "mean"),
        humidity_mean=("humidity", "mean"),
    ).reset_index()
    monthly["province"] = province_key
    return monthly[["province", "year", "month", "precipitation_sum", "temp_mean", "humidity_mean"]]


def fetch_province_weather(province: str,
                           start_year: int = 2020,
                           end_year: Optional[int] = None) -> pd.DataFrame:
    """
    Lấy dữ liệu thời tiết tháng cho 1 tỉnh.
    Thử WeatherAPI trước, nếu thất bại thì fallback sang Open-Meteo.

    Returns: DataFrame có cột [province, year, month, precipitation_sum, temp_mean, humidity_mean]
    """
    info = _get_province_info(province)
    if info is None:
        logger.warning(f"Không có tọa độ cho '{province}' — bỏ qua.")
        return pd.DataFrame()

    today = date.today()
    if end_year is None:
        end_year = today.year

    start_date = f"{start_year}-01-01"
    end_date = min(f"{end_year}-12-31", today.isoformat())
    if start_date > end_date:
        start_date = f"{today.year}-01-01"

    province_key = info.get("ascii_key", province)
    logger.info(f"  → Đang lấy thời tiết: {province_key} ({start_date} ~ {end_date})")

    # --- Thử nguồn 1: WeatherAPI ---
    df_daily = pd.DataFrame()
    if WEATHERAPI_KEY and HAS_REQUESTS:
        df_daily = _fetch_weatherapi_range(info["wapi_q"], start_date, end_date)
        if not df_daily.empty:
            logger.info(f"    [WeatherAPI OK] {len(df_daily)} ngày")

    # --- Fallback nguồn 2: Open-Meteo ---
    if df_daily.empty:
        logger.info(f"    [Fallback Open-Meteo] {province_key}")
        df_daily = _fetch_openmeteo_range(info["lat"], info["lon"], start_date, end_date)
        if not df_daily.empty:
            logger.info(f"    [Open-Meteo OK] {len(df_daily)} ngày")

    return _daily_to_monthly(df_daily, province_key)


# ===========================================================================
# HÀM LẤY DỮ LIỆU CHO NHIỀU TỈNH
# ===========================================================================
def fetch_all_provinces_weather(provinces=None,
                                start_year: int = 2020,
                                end_year: Optional[int] = None,
                                delay_between: float = 0.5) -> pd.DataFrame:
    """Thu thập thời tiết cho danh sách tỉnh (mặc định: toàn bộ 34 tỉnh, HCMC ưu tiên đầu)."""
    if provinces is None:
        # HCMC luôn đầu tiên, sau đó toàn bộ
        all_keys = list(PROVINCE_COORDS.keys())
        rest = [p for p in all_keys if p not in PRIORITY_PROVINCES]
        provinces = PRIORITY_PROVINCES + rest

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


# ===========================================================================
# CACHE: load / save
# ===========================================================================
def load_weather_cache() -> pd.DataFrame:
    """Đọc cache thời tiết từ MongoDB (ưu tiên) hoặc CSV (fallback)."""
    if mongo_data_service:
        df = mongo_data_service.load_dataset("weather_cache", WEATHER_CACHE_CSV)
        if not df.empty:
            logger.info(f"Cache thời tiết loaded: {len(df)} dòng (MongoDB)")
            return df
    if WEATHER_CACHE_CSV.exists():
        df = pd.read_csv(WEATHER_CACHE_CSV)
        logger.info(f"Cache thời tiết loaded: {len(df)} dòng (local CSV)")
        return df
    return pd.DataFrame()


def save_weather_cache(df: pd.DataFrame) -> None:
    """Lưu cache thời tiết ra MongoDB và CSV."""
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if mongo_data_service:
        mongo_data_service.save_dataset("weather_cache", df, WEATHER_CACHE_CSV)
    else:
        df.to_csv(WEATHER_CACHE_CSV, index=False)
    logger.info(f"Cache thời tiết saved: {len(df)} dòng → {WEATHER_CACHE_CSV}")


# ===========================================================================
# SMART SYNC: chỉ fetch dữ liệu còn thiếu (delta) hoặc làm mới hoàn toàn
# ===========================================================================
def _merge_and_deduplicate(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Gộp two DataFrames và loại bỏ trùng lặp (ưu tiên dữ liệu mới hơn)."""
    combined = pd.concat([old, new], ignore_index=True)
    return combined.drop_duplicates(subset=["province", "year", "month"], keep="last").reset_index(drop=True)


def sync_weather_delta(provinces=None, force_refresh: bool = False) -> pd.DataFrame:
    """
    Đồng bộ thông minh: chỉ fetch các tháng còn thiếu hoặc chưa được lưu.
    - Nếu cache rỗng hoặc force_refresh=True: fetch full từ 2020.
    - Nếu cache đã có nhưng thiếu tháng gần nhất: fetch delta.
    - Luôn ưu tiên HCMC.

    Returns: DataFrame cache đã cập nhật.
    """
    today = date.today()
    current_year = today.year

    if not force_refresh:
        cached = load_weather_cache()
        if not cached.empty:
            max_year = int(cached["year"].max())
            max_month_in_max_year = int(cached.loc[cached["year"] == max_year, "month"].max())

            # Kiểm tra xem có tháng mới nào chưa có không
            last_full_month = (today.replace(day=1) - timedelta(days=1))
            cache_up_to = date(max_year, max_month_in_max_year, 1)

            if cache_up_to >= last_full_month.replace(day=1):
                logger.info(f"Cache đã cập nhật đến {max_year}/{max_month_in_max_year:02d}. Bỏ qua.")
                return cached

            # Fetch delta từ năm thiếu trở đi
            delta_start_year = max_year if max_month_in_max_year < 12 else max_year + 1
            logger.info(f"Đang fetch delta thời tiết từ năm {delta_start_year}…")
            new_data = fetch_all_provinces_weather(
                provinces=provinces, start_year=delta_start_year, end_year=current_year
            )
            if not new_data.empty:
                merged = _merge_and_deduplicate(cached, new_data)
                save_weather_cache(merged)
                return merged
            return cached

    # Full fetch
    logger.info("Bắt đầu fetch toàn bộ thời tiết (2020 → nay)…")
    all_data = fetch_all_provinces_weather(provinces=provinces, start_year=2020, end_year=current_year)
    if not all_data.empty:
        save_weather_cache(all_data)
    return all_data


def sync_hcmc_weekly() -> pd.DataFrame:
    """
    Đồng bộ nhanh: chỉ lấy 30 ngày gần nhất của TP. Hồ Chí Minh.
    Dùng cho scheduler hàng tuần.
    Returns: cache đã cập nhật.
    """
    today = date.today()
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    logger.info(f"[Weekly Sync] Đồng bộ HCMC: {start_date} ~ {end_date}")
    info = _get_province_info("TP. Ho Chi Minh")
    if not info:
        return load_weather_cache()

    # Lấy daily từ WeatherAPI (ưu tiên) hoặc Open-Meteo
    df_daily = pd.DataFrame()
    if WEATHERAPI_KEY and HAS_REQUESTS:
        df_daily = _fetch_weatherapi_range(info["wapi_q"], start_date, end_date)
    if df_daily.empty:
        df_daily = _fetch_openmeteo_range(info["lat"], info["lon"], start_date, end_date)

    if df_daily.empty:
        logger.warning("[Weekly Sync] Không lấy được dữ liệu HCMC.")
        return load_weather_cache()

    new_monthly = _daily_to_monthly(df_daily, "TP. Ho Chi Minh")
    cached = load_weather_cache()
    if cached.empty:
        save_weather_cache(new_monthly)
        return new_monthly

    merged = _merge_and_deduplicate(cached, new_monthly)
    save_weather_cache(merged)
    logger.info(f"[Weekly Sync] Cập nhật {len(new_monthly)} bản ghi HCMC. Tổng cache: {len(merged)} dòng.")
    return merged


def get_weather_safe(provinces=None, start_year: int = 2020,
                     end_year: Optional[int] = None) -> pd.DataFrame:
    """
    Wrapper an toàn: không crash nếu mất mạng / lỗi API.
    Dùng trong pipeline chính.
    """
    try:
        return sync_weather_delta(provinces=provinces)
    except Exception as e:
        logger.warning(f"Weather service không khả dụng ({e}). Thử đọc cache cục bộ…")
        try:
            return load_weather_cache()
        except Exception:
            return pd.DataFrame()


# ===========================================================================
# SCHEDULER: tự động đồng bộ hàng tuần & hàng tháng (APScheduler)
# ===========================================================================
_scheduler = None


def start_weather_scheduler() -> None:
    """
    Khởi động APScheduler chạy ngầm:
    - Hàng tuần (Thứ Hai 02:00): đồng bộ 30 ngày gần nhất của HCMC.
    - Hàng tháng (ngày 1 lúc 03:00): đồng bộ đầy đủ toàn bộ 34 tỉnh.
    Gọi hàm này một lần khi khởi động ứng dụng.
    """
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        logger.info("Scheduler thời tiết đã chạy, bỏ qua.")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler chưa được cài đặt. Chạy: pip install apscheduler")
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh", daemon=True)

    # Job 1: Hàng tuần — Thứ Hai 02:00 sáng — đồng bộ nhanh HCMC
    _scheduler.add_job(
        func=sync_hcmc_weekly,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=0, timezone="Asia/Ho_Chi_Minh"),
        id="weekly_hcmc_sync",
        name="[Weekly] Đồng bộ thời tiết HCMC 30 ngày qua",
        replace_existing=True,
        misfire_grace_time=3600,  # cho phép trễ tối đa 1 giờ
    )

    # Job 2: Hàng tháng — Ngày 1 lúc 03:00 sáng — đồng bộ đầy đủ tất cả tỉnh
    _scheduler.add_job(
        func=lambda: sync_weather_delta(force_refresh=False),
        trigger=CronTrigger(day=1, hour=3, minute=0, timezone="Asia/Ho_Chi_Minh"),
        id="monthly_all_provinces_sync",
        name="[Monthly] Đồng bộ đầy đủ thời tiết 34 tỉnh",
        replace_existing=True,
        misfire_grace_time=7200,  # cho phép trễ tối đa 2 giờ
    )

    _scheduler.start()
    next_weekly = _scheduler.get_job("weekly_hcmc_sync").next_run_time
    next_monthly = _scheduler.get_job("monthly_all_provinces_sync").next_run_time
    logger.info("✅ Weather Scheduler đã khởi động!")
    logger.info(f"   • Weekly  (HCMC)   lần tới: {next_weekly}")
    logger.info(f"   • Monthly (all)    lần tới: {next_monthly}")


def stop_weather_scheduler() -> None:
    """Dừng scheduler nếu đang chạy."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Weather Scheduler đã dừng.")


def get_scheduler_status() -> dict:
    """Trả về trạng thái scheduler và thời điểm chạy kế tiếp."""
    if _scheduler is None or not _scheduler.running:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time),
        })
    return {"running": True, "jobs": jobs}


# ===========================================================================
# NGUỒN DỮ LIỆU SONG SONG: LOCAL WEATHERDATA & CHẤT LƯỢNG KHÔNG KHÍ (PM2.5)
# ===========================================================================
DATA_SOURCE_API_CACHE = "api_cache"
DATA_SOURCE_LOCAL_WEATHERDATA = "local_weatherdata"


def load_local_weatherdata_monthly() -> pd.DataFrame:
    """
    Tải dữ liệu thời tiết & PM2.5 tháng cho TP. Hồ Chí Minh từ data/weatherdata.
    Ưu tiên nguồn MongoDB collection 'weatherdata_hcmc_monthly' (với Fallback về CSV).
    Hoàn toàn độc lập, chạy song song và KHÔNG làm ảnh hưởng đến cache của WeatherAPI/Open-Meteo.
    """
    monthly_csv = getattr(paths, 'WEATHERDATA_MONTHLY_CSV', paths.PROCESSED_DIR / "weatherdata_hcmc_monthly.csv")

    if mongo_data_service:
        df = mongo_data_service.load_dataset("weatherdata_hcmc_monthly", monthly_csv)
        if not df.empty:
            logger.info(f"[Parallel Source] Đã tải {len(df)} dòng weatherdata monthly từ MongoDB.")
            return df

    if monthly_csv.exists():
        try:
            df = pd.read_csv(monthly_csv)
            logger.info(f"[Parallel Source] Đã tải {len(df)} dòng weatherdata monthly từ local CSV.")
            return df
        except Exception as e:
            logger.error(f"Lỗi đọc {monthly_csv}: {e}")

    return pd.DataFrame()


def load_local_weatherdata_hourly(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Tải dữ liệu chuỗi thời gian hourly (PM2.5, nhiệt độ, độ ẩm, áp suất, gió, lượng mưa).
    Ưu tiên tải từ MongoDB collection 'weatherdata_cleaned', fallback về cleaned_final.csv.
    """
    cleaned_csv = getattr(paths, 'WEATHERDATA_CLEANED_CSV', paths.DATA_DIR / "weatherdata" / "processed" / "cleaned_final.csv")

    if mongo_data_service and mongo_data_service.is_connected:
        try:
            coll = mongo_data_service.db["weatherdata_cleaned"]
            cursor = coll.find({}, {"_id": 0})
            if limit:
                cursor = cursor.limit(limit)
            records = list(cursor)
            if records:
                df = pd.DataFrame(records)
                logger.info(f"[Parallel Source] Đã tải {len(df)} bản ghi hourly từ MongoDB.")
                return df
        except Exception as e:
            logger.warning(f"Không thể đọc hourly từ MongoDB: {e}")

    if cleaned_csv.exists():
        try:
            df = pd.read_csv(cleaned_csv, nrows=limit)
            return df
        except Exception as e:
            logger.error(f"Lỗi đọc {cleaned_csv}: {e}")

    return pd.DataFrame()


def get_parallel_weather_monthly(province: str = "TP. Hồ Chí Minh",
                                 year: Optional[int] = None) -> dict:
    """
    Truy xuất đồng thời 2 nguồn dữ liệu khí tượng song song:
      1. 'api_cache': Từ API trực tuyến & cache tổng hợp (weather_cache)
      2. 'local_weatherdata': Từ trạm quan trắc địa phương & PM2.5 (weatherdata_hcmc_monthly)

    Returns:
        dict: {
            "api_cache": DataFrame,
            "local_weatherdata": DataFrame,
            "province": province
        }
    """
    api_df = load_weather_cache()
    if not api_df.empty and 'province' in api_df.columns:
        api_df = api_df[api_df['province'].str.contains('Hồ Chí Minh|HCM', na=False, case=False)]
        if year and 'year' in api_df.columns:
            api_df = api_df[api_df['year'] == int(year)]

    local_df = load_local_weatherdata_monthly()
    if not local_df.empty and year and 'year' in local_df.columns:
        local_df = local_df[local_df['year'] == int(year)]

    return {
        "api_cache": api_df.reset_index(drop=True) if not api_df.empty else pd.DataFrame(),
        "local_weatherdata": local_df.reset_index(drop=True) if not local_df.empty else pd.DataFrame(),
        "province": province
    }


def get_weather_dengue_combined_series(dengue_df: Optional[pd.DataFrame] = None,
                                       province: str = "TP. Hồ Chí Minh",
                                       weather_source: str = DATA_SOURCE_LOCAL_WEATHERDATA) -> pd.DataFrame:
    """
    Kết hợp số ca sốt xuất huyết và số liệu thời tiết song song theo từng tháng.
    Hỗ trợ chuyển đổi linh hoạt nguồn thời tiết ('local_weatherdata' hoặc 'api_cache').

    Returns:
        DataFrame các cột: [year, month, month_label, cases, precipitation_sum, temp_mean, humidity_mean, pm25_mean]
    """
    # 1. Lấy dữ liệu SXH
    if dengue_df is None or dengue_df.empty:
        if mongo_data_service:
            dengue_df = mongo_data_service.load_dataset("historical", paths.HISTORICAL_CSV)
        elif paths.HISTORICAL_CSV.exists():
            dengue_df = pd.read_csv(paths.HISTORICAL_CSV)
        else:
            dengue_df = pd.DataFrame()

    d_prov = pd.DataFrame()
    if not dengue_df.empty and 'province' in dengue_df.columns:
        d_prov = dengue_df[dengue_df['province'].str.contains('Hồ Chí Minh|HCM', na=False, case=False)].copy()
        if 'cases' in d_prov.columns:
            d_prov = d_prov.groupby(['year', 'month'])['cases'].sum().reset_index()

    # 2. Lấy dữ liệu thời tiết theo nguồn được chọn
    if weather_source == DATA_SOURCE_LOCAL_WEATHERDATA:
        w_df = load_local_weatherdata_monthly()
    else:
        w_df = load_weather_cache()
        if not w_df.empty and 'province' in w_df.columns:
            w_df = w_df[w_df['province'].str.contains('Hồ Chí Minh|HCM', na=False, case=False)]

    if w_df.empty and d_prov.empty:
        return pd.DataFrame()

    if w_df.empty:
        merged = d_prov
        for c in ['precipitation_sum', 'temp_mean', 'humidity_mean', 'pm25_mean']:
            merged[c] = None
    elif d_prov.empty:
        merged = w_df
        merged['cases'] = 0
    else:
        merged = pd.merge(d_prov, w_df, on=['year', 'month'], how='outer')

    merged = merged.sort_values(['year', 'month']).reset_index(drop=True)
    merged['month_label'] = merged.apply(lambda r: f"Tháng {int(r['month']):02d}/{int(r['year'])}", axis=1)

    return merged


# ===========================================================================
# TEST CHẠY TRỰC TIẾP
# ===========================================================================
if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=== Test: Đồng bộ thời tiết HCMC (30 ngày qua) ===")
    df = sync_hcmc_weekly()
    if not df.empty:
        hcmc = df[df["province"] == "TP. Ho Chi Minh"].tail(3)
        print(hcmc.to_string(index=False))
    else:
        print("Không có dữ liệu.")
