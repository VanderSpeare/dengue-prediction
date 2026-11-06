"""
tests/test_weatherapi.py - Kịch bản kiểm tra độc lập API Weather từ WeatherAPI.com.

Hỗ trợ:
1. Lấy thông tin thời tiết hiện tại (Current Weather).
2. Lấy dữ liệu thời tiết lịch sử trong 7 ngày qua (Past Week).
3. Lấy dữ liệu thời tiết lịch sử trong 30 ngày qua (Past Month).

File này hoàn toàn độc lập, không can thiệp hay làm ảnh hưởng đến mã nguồn chính của project.
Chạy trực tiếp file này bằng lệnh:
    python tests/test_weatherapi.py
"""
import os
import sys
from datetime import date, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# Đảm bảo hiển thị tiếng Việt mượt mà trên console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Đọc file .env ở thư mục gốc dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def get_weatherapi_key() -> str | None:
    """Lấy API key từ biến môi trường WEATHERAPI_KEY hoặc WEATHER_API_KEY."""
    return os.getenv("WEATHERAPI_KEY") or os.getenv("WEATHER_API_KEY")


def fetch_current_weather(location: str = "Ho Chi Minh", api_key: str | None = None) -> dict:
    """
    Hàm gọi WeatherAPI để lấy thông tin thời tiết hiện tại theo địa điểm.

    Args:
        location: Tên thành phố / tỉnh / tọa độ (ví dụ: "Ho Chi Minh", "Hanoi", "Da Nang").
        api_key: WeatherAPI key (nếu None sẽ tự lấy từ file .env).

    Returns:
        dict: Kết quả thời tiết đã được chuẩn hóa hoặc thông báo lỗi.
    """
    key = api_key or get_weatherapi_key()
    if not key:
        return {
            "success": False,
            "error": "Không tìm thấy API Key trong file .env (biến WEATHERAPI_KEY).",
            "data": None,
        }

    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": key,
        "q": location,
        "aqi": "no",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200:
            current = data.get("current", {})
            loc = data.get("location", {})

            return {
                "success": True,
                "error": None,
                "location": {
                    "name": loc.get("name"),
                    "region": loc.get("region"),
                    "country": loc.get("country"),
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon"),
                    "localtime": loc.get("localtime"),
                },
                "weather": {
                    "temp_c": current.get("temp_c"),
                    "feelslike_c": current.get("feelslike_c"),
                    "humidity": current.get("humidity"),  # %
                    "condition": current.get("condition", {}).get("text"),
                    "precip_mm": current.get("precip_mm"),  # mm mưa
                    "wind_kph": current.get("wind_kph"),
                    "uv": current.get("uv"),
                },
                "raw": data,
            }
        else:
            err_msg = data.get("error", {}).get("message", f"HTTP Error {response.status_code}")
            return {
                "success": False,
                "error": f"Lỗi từ WeatherAPI ({response.status_code}): {err_msg}",
                "data": None,
            }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Lỗi kết nối mạng: {str(e)}",
            "data": None,
        }


def fetch_historical_weather(
    location: str = "Ho Chi Minh",
    start_date: str | None = None,
    end_date: str | None = None,
    api_key: str | None = None,
) -> dict:
    """
    Gọi endpoint history.json để lấy thông tin thời tiết lịch sử theo ngày hoặc khoảng ngày.

    Args:
        location: Tên địa điểm ("Ho Chi Minh", "Hanoi", ...).
        start_date: Ngày bắt đầu định dạng YYYY-MM-DD.
        end_date: Ngày kết thúc định dạng YYYY-MM-DD (tùy chọn, tối đa 30 ngày/request).
        api_key: WeatherAPI key.

    Returns:
        dict: Danh sách thời tiết theo từng ngày (nhiệt độ tb, max, min, độ ẩm tb, lượng mưa mm).
    """
    key = api_key or get_weatherapi_key()
    if not key:
        return {"success": False, "error": "Chưa cấu hình WEATHERAPI_KEY trong .env"}

    url = "https://api.weatherapi.com/v1/history.json"
    params = {
        "key": key,
        "q": location,
        "dt": start_date,
    }
    if end_date:
        params["end_dt"] = end_date

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        if response.status_code == 200:
            forecast_days = data.get("forecast", {}).get("forecastday", [])
            daily_records = []

            for item in forecast_days:
                day_info = item.get("day", {})
                daily_records.append({
                    "date": item.get("date"),
                    "avgtemp_c": day_info.get("avgtemp_c"),
                    "maxtemp_c": day_info.get("maxtemp_c"),
                    "mintemp_c": day_info.get("mintemp_c"),
                    "avghumidity": day_info.get("avghumidity"),      # Độ ẩm trung bình (%)
                    "totalprecip_mm": day_info.get("totalprecip_mm"),  # Tổng lượng mưa trong ngày (mm)
                    "maxwind_kph": day_info.get("maxwind_kph"),
                    "condition": day_info.get("condition", {}).get("text"),
                    "uv": day_info.get("uv"),
                })

            return {
                "success": True,
                "location": data.get("location", {}).get("name"),
                "total_days": len(daily_records),
                "history": daily_records,
                "error": None,
            }
        else:
            err_msg = data.get("error", {}).get("message", f"HTTP Error {response.status_code}")
            return {"success": False, "error": f"Lỗi ({response.status_code}): {err_msg}"}

    except requests.RequestException as e:
        return {"success": False, "error": f"Lỗi mạng: {str(e)}"}


def fetch_past_week_weather(location: str = "Ho Chi Minh") -> dict:
    """Lấy dữ liệu thời tiết 7 ngày vừa qua (từ hôm qua trở về trước 7 ngày)."""
    today = date.today()
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    return fetch_historical_weather(location=location, start_date=start_date, end_date=end_date)


def fetch_past_month_weather(location: str = "Ho Chi Minh") -> dict:
    """Lấy dữ liệu thời tiết 30 ngày vừa qua (từ hôm qua trở về trước 30 ngày)."""
    today = date.today()
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    return fetch_historical_weather(location=location, start_date=start_date, end_date=end_date)


def run_tests():
    """Hàm chạy các bài kiểm thử toàn diện: Hiện tại, 7 ngày qua, và 30 ngày qua."""
    print("=" * 70)
    print("KIỂM TRA TÍNH NĂNG GỌI THỜI TIẾT LỊCH SỬ (WEATHERAPI.COM)")
    print("=" * 70)

    key = get_weatherapi_key()
    if not key:
        print("[-] THẤT BÀI: Chưa cấu hình WEATHERAPI_KEY trong .env!")
        return False

    masked_key = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
    print(f"[+] API Key phát hiện: {masked_key}")

    # ----------------------------------------------------
    # BÀI TEST 1: THỜI TIẾT 7 NGÀY QUA (TUẦN VỪA QUA)
    # ----------------------------------------------------
    location = "Ho Chi Minh"
    print(f"\n[1] Kiểm tra gọi thời tiết TUẦN VỪA QUA (7 ngày) tại '{location}':")
    week_res = fetch_past_week_weather(location)

    if week_res["success"]:
        print(f"  [OK] Lấy thành công dữ liệu {week_res['total_days']} ngày qua!")
        print(f"  {'Ngày':<12} | {'Nhiệt độ (TB)':<14} | {'Độ ẩm (TB)':<12} | {'Mưa (mm)':<10} | {'Thời tiết'}")
        print("  " + "-" * 65)
        for d in week_res["history"]:
            print(f"  {d['date']:<12} | {d['avgtemp_c']} °C ({d['mintemp_c']}-{d['maxtemp_c']})  | {d['avghumidity']:>4}%        | {d['totalprecip_mm']:>6} mm  | {d['condition']}")
    else:
        print(f"  [FAIL] Lỗi: {week_res['error']}")
        return False

    # ----------------------------------------------------
    # BÀI TEST 2: THỜI TIẾT 30 NGÀY QUA (THÁNG VỪA QUA)
    # ----------------------------------------------------
    print(f"\n[2] Kiểm tra gọi thời tiết THÁNG VỪA QUA (30 ngày) tại '{location}':")
    month_res = fetch_past_month_weather(location)

    if month_res["success"]:
        hist = month_res["history"]
        total_days = month_res["total_days"]
        avg_temp = sum(d["avgtemp_c"] for d in hist) / total_days if total_days else 0
        avg_humidity = sum(d["avghumidity"] for d in hist) / total_days if total_days else 0
        total_precip = sum(d["totalprecip_mm"] for d in hist)
        rainy_days = sum(1 for d in hist if d["totalprecip_mm"] > 0)

        print(f"  [OK] Lấy thành công dữ liệu {total_days} ngày trong tháng vừa qua!")
        print(f"       + Nhiệt độ trung bình tháng: {avg_temp:.1f} °C")
        print(f"       + Độ ẩm trung bình tháng   : {avg_humidity:.1f} %")
        print(f"       + Tổng lượng mưa tích lũy  : {total_precip:.1f} mm")
        print(f"       + Số ngày có mưa           : {rainy_days}/{total_days} ngày")
    else:
        print(f"  [FAIL] Lỗi: {month_res['error']}")
        return False

    print("\n" + "=" * 70)
    print("[KẾT LUẬN]: API HOÀN TOÀN HỖ TRỢ GỌI DỮ LIỆU CẢ TUẦN QUA VÀ THÁNG QUA!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
