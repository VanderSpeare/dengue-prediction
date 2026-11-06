"""
ai_prediction_service.py — AI-Powered Dengue Evaluation & Predictive Intelligence
==================================================================================
Tích hợp Google Gemini AI API từ .env để:
1. Đánh giá dịch tễ học và dự báo số ca nhiễm dựa trên DỮ LIỆU HIỆN CÓ
   (Số liệu ca bệnh lịch sử, trạm quan trắc thời tiết & PM2.5, dự báo nền tảng XGBoost).
2. Đánh giá và mô phỏng dự báo dựa trên DỮ LIỆU TỰ THỐNG KÊ (Custom Statistics / Scenarios)
   (Cho phép chuyên gia/người dùng nhập giả định về lượng mưa, nhiệt độ, độ ẩm, chỉ số bọ gậy BI, can thiệp cộng đồng).
3. Hoàn toàn độc lập, không làm ảnh hưởng đến các service hay mô hình hiện có.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Path setup
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_ROOT))

import paths

try:
    from config import settings
    GEMINI_API_KEY = settings.GEMINI_API_KEY
    GEMINI_MODEL = settings.GEMINI_MODEL
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# MongoDB service
try:
    from mongo_data_service import mongo_data_service
except ImportError:
    from src.mongo_data_service import mongo_data_service

# Weather service
try:
    import weather_service
except ImportError:
    from src import weather_service

logger = logging.getLogger("ai_prediction_service")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

_client = None
CACHE_FILE = paths.PROCESSED_DIR / "ai_evaluation_cache.json"


def load_cached_existing_prediction() -> Optional[Dict[str, Any]]:
    """Tải kết quả đánh giá AI đã lưu trước đó từ MongoDB hoặc file JSON cục bộ."""
    if mongo_data_service and mongo_data_service.is_connected:
        try:
            coll = mongo_data_service.db["ai_evaluation_cache"]
            doc = coll.find_one({"key": "existing_data_eval"}, {"_id": 0})
            if doc and "data" in doc:
                logger.info("Đã tải kết quả đánh giá AI từ MongoDB collection 'ai_evaluation_cache'.")
                return doc["data"]
        except Exception:
            pass

    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info("Đã tải kết quả đánh giá AI từ file cache JSON.")
                return data
        except Exception:
            pass
    return None


def save_cached_existing_prediction(data: Dict[str, Any]) -> None:
    """Lưu kết quả đánh giá AI vào MongoDB và file JSON cục bộ."""
    try:
        paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Lỗi lưu file cache AI: {e}")

    if mongo_data_service and mongo_data_service.is_connected:
        try:
            coll = mongo_data_service.db["ai_evaluation_cache"]
            coll.replace_one(
                {"key": "existing_data_eval"},
                {"key": "existing_data_eval", "data": data, "updated_at": datetime.now().isoformat()},
                upsert=True
            )
            logger.info("Đã lưu kết quả đánh giá AI vào MongoDB collection 'ai_evaluation_cache'.")
        except Exception as e:
            logger.warning(f"Lỗi lưu MongoDB cache AI: {e}")


def _get_gemini_client():
    """Khởi tạo Google GenAI Client nếu chưa có."""
    global _client
    if _client is not None:
        return _client
    key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not key or key == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=key)
        return _client
    except Exception as e:
        logger.warning(f"Lỗi khởi tạo Gemini Client: {e}")
        return None


def get_current_dengue_weather_context(province: str = "TP. Hồ Chí Minh") -> Dict[str, Any]:
    """
    Trích xuất và tổng hợp ngữ cảnh số liệu thực tế gồm:
    - Số ca SXH 2024 và 2025 theo từng tháng
    - Số liệu khí tượng & PM2.5 tháng
    - Dự báo nền của XGBoost
    """
    # 1. Đọc dữ liệu lịch sử SXH
    dengue_df = pd.DataFrame()
    if mongo_data_service and mongo_data_service.is_connected:
        dengue_df = mongo_data_service.load_dataset("historical", paths.HISTORICAL_CSV)
    elif paths.HISTORICAL_CSV.exists():
        dengue_df = pd.read_csv(paths.HISTORICAL_CSV)

    hcm_df = pd.DataFrame()
    if not dengue_df.empty and 'province' in dengue_df.columns:
        hcm_df = dengue_df[dengue_df['province'].str.contains('Hồ Chí Minh|HCM', na=False, case=False)].copy()

    cases_2024 = {}
    cases_2025 = {}
    if not hcm_df.empty and 'year' in hcm_df.columns and 'month' in hcm_df.columns:
        s24 = hcm_df[hcm_df['year'] == 2024].groupby('month')['cases'].sum()
        s25 = hcm_df[hcm_df['year'] == 2025].groupby('month')['cases'].sum()
        cases_2024 = {int(m): int(c) for m, c in s24.items()}
        cases_2025 = {int(m): int(c) for m, c in s25.items()}

    # 2. Đọc thời tiết tháng từ trạm quan trắc địa phương / MongoDB
    weather_df = pd.DataFrame()
    if hasattr(weather_service, 'load_local_weatherdata_monthly'):
        weather_df = weather_service.load_local_weatherdata_monthly()
    elif getattr(paths, 'WEATHERDATA_MONTHLY_CSV', None) and paths.WEATHERDATA_MONTHLY_CSV.exists():
        weather_df = pd.read_csv(paths.WEATHERDATA_MONTHLY_CSV)

    weather_summary_2025 = []
    if not weather_df.empty:
        w25 = weather_df[weather_df['year'] == 2025].sort_values('month')
        for _, r in w25.iterrows():
            m = int(r['month'])
            weather_summary_2025.append({
                "month": m,
                "cases": cases_2025.get(m, 0),
                "precipitation_mm": float(r.get('precipitation_sum', 0)),
                "temp_c": float(r.get('temp_mean', 0)),
                "humidity_pct": float(r.get('humidity_mean', 0)),
                "pm25": float(r.get('pm25_mean', 0)) if pd.notna(r.get('pm25_mean')) else None
            })

    # 3. XGBoost predictions
    preds_df = pd.DataFrame()
    if mongo_data_service and mongo_data_service.is_connected:
        preds_df = mongo_data_service.load_dataset("latest_predictions", paths.PREDICTIONS_CSV)
    elif paths.PREDICTIONS_CSV.exists():
        preds_df = pd.read_csv(paths.PREDICTIONS_CSV)

    xgb_preds = []
    if not preds_df.empty and 'province' in preds_df.columns:
        p_hcm = preds_df[preds_df['province'].str.contains('Hồ Chí Minh|HCM', na=False, case=False)].sort_values(['year', 'month']).head(3)
        for _, r in p_hcm.iterrows():
            xgb_preds.append({
                "month": f"Tháng {int(r['month']):02d}/{int(r['year'])}",
                "xgb_cases": float(r.get('predicted_cases', 0))
            })

    return {
        "province": province,
        "cases_2024_total": sum(cases_2024.values()),
        "cases_2025_total": sum(cases_2025.values()),
        "cases_2024": cases_2024,
        "cases_2025": cases_2025,
        "weather_dengue_2025": weather_summary_2025,
        "xgb_baseline_predictions": xgb_preds,
        "latest_actual_cases": cases_2025.get(12, 205)
    }


def predict_from_existing_data(province: str = "TP. Hồ Chí Minh", force_refresh: bool = False) -> Dict[str, Any]:
    """
    Gửi request tới Gemini AI để:
    1. Phân tích, đánh giá dịch tễ tổng quan theo dữ liệu hiện có (2024-2025 và khí tượng trạm quan trắc).
    2. Dự báo số ca nhiễm sốt xuất huyết 3 tháng đầu năm 2026.
    3. Đưa ra khuyến nghị can thiệp dựa trên tương quan khí hậu - ổ dịch.
    """
    if not force_refresh:
        cached = load_cached_existing_prediction()
        if cached:
            return cached

    ctx = get_current_dengue_weather_context(province)
    client = _get_gemini_client()

    prompt = f"""
Bạn là Chuyên gia Cao cấp về Dịch tễ học và Y tế Dự phòng (AI Senior Epidemiologist).
Nhiệm vụ của bạn: Phân tích đánh giá dịch tễ và dự báo số ca nhiễm Sốt xuất huyết Dengue cho {province} dựa trên dữ liệu chuẩn xác sau:

=== DỮ LIỆU DỊCH TỄ VÀ KHÍ TƯỢNG HIỆN CÓ ===
1. Tổng quan số ca:
- Tổng ca năm 2024: {ctx['cases_2024_total']} ca
- Tổng ca năm 2025: {ctx['cases_2025_total']} ca (tăng mạnh so với 2024)
- Ca bệnh thực tế tháng 12/2025 gần nhất: {ctx['latest_actual_cases']} ca

2. Diễn biến chi tiết 12 tháng năm 2025 (Ca bệnh & Khí tượng Trạm quan trắc TP.HCM):
{json.dumps(ctx['weather_dengue_2025'], indent=2, ensure_ascii=False)}

3. Dự báo tham chiếu từ mô hình Machine Learning XGBoost:
{json.dumps(ctx['xgb_baseline_predictions'], indent=2, ensure_ascii=False)}

=== YÊU CẦU ĐÁNH GIÁ & DỰ BÁO ===
Hãy phân tích mối tương quan giữa mùa mưa (đỉnh mưa tháng 8-9 vượt 450mm), độ ẩm (>85%) và đỉnh dịch tháng 10 (227 ca).
Sau đó đưa ra dự báo số ca cho 3 tháng tiếp theo: Tháng 01/2026, Tháng 02/2026, Tháng 03/2026.
Trả về DUY NHẤT một chuỗi JSON hợp lệ không có markdown code blocks bao bọc (hoặc chuẩn json) với các khóa sau:
{{
  "evaluation_title": "tiêu đề tóm tắt đánh giá",
  "executive_summary": "đoạn văn đánh giá dịch tễ chuyên sâu (khoảng 150-200 từ)",
  "epidemiological_risk_level": "Nguy cơ Rất cao | Nguy cơ Cao | Nguy cơ Trung bình | Nguy cơ Thấp",
  "climate_correlation_insight": "nhận định cụ thể về tác động của lượng mưa, độ ẩm, PM2.5 đến chu kỳ muỗi Aedes",
  "monthly_predictions": [
    {{
      "month_label": "Tháng 01/2026",
      "predicted_cases": 182,
      "lower_bound": 160,
      "upper_bound": 205,
      "trend": "Giảm dần theo mùa khô",
      "risk_level": "Nguy cơ Cao",
      "rationale": "Lý do dự báo dựa trên lượng mưa giảm còn 17mm nhưng mật độ muỗi từ mùa mưa vẫn còn tồn lưu"
    }},
    {{
      "month_label": "Tháng 02/2026",
      "predicted_cases": 158,
      "lower_bound": 135,
      "upper_bound": 180,
      "trend": "Giảm",
      "risk_level": "Nguy cơ Trung bình",
      "rationale": "Mùa khô cao điểm, độ ẩm giảm xuống 68%, hạn chế ổ bọ gậy tự nhiên"
    }},
    {{
      "month_label": "Tháng 03/2026",
      "predicted_cases": 139,
      "lower_bound": 115,
      "upper_bound": 165,
      "trend": "Chạm đáy mùa khô",
      "risk_level": "Nguy cơ Trung bình",
      "rationale": "Nhiệt độ tăng cao (28-30°C) kết hợp mưa thấp làm giảm vòng đời muỗi"
    }}
  ],
  "recommendations": [
    "khuyến cáo can thiệp y tế dự phòng 1",
    "khuyến cáo can thiệp 2",
    "khuyến cáo can thiệp 3"
  ]
}}
"""

    if client:
        try:
            from google.genai import types
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            raw_text = resp.text.strip()
            # Clean markdown formatting if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("\n", 1)[0]
            data = json.loads(raw_text)
            data["success"] = True
            data["source"] = f"Google Gemini ({model_name})"
            data["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            save_cached_existing_prediction(data)
            return data
        except Exception as e:
            logger.warning(f"Lỗi gọi Gemini API (Existing Data): {e}. Kích hoạt AI Fallback.")

    # Rule-based fallback if API is unreachable
    return _fallback_existing_prediction(ctx)


def predict_from_custom_statistics(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gửi request tới Gemini AI để đánh giá và dự báo theo DỮ LIỆU TỰ THỐNG KÊ (Scenario Simulation).
    
    Các tham số do người dùng/chuyên gia tự thiết lập:
    - target_month: Tháng muốn giả định (ví dụ: 'Tháng 06/2026 (Đầu mùa mưa)')
    - custom_rainfall: Lượng mưa giả định (mm)
    - custom_humidity: Độ ẩm giả định (%)
    - custom_temp: Nhiệt độ trung bình (°C)
    - custom_pm25: Bụi mịn PM2.5 (µg/m³)
    - mosquito_bi: Chỉ số bọ gậy / lăng quăng Breteau Index (BI)
    - intervention_effort: 'Quyết liệt (Chiến dịch diệt lăng quăng toàn thành)', 'Trung bình (Phun thuốc định kỳ)', 'Thấp (Chưa can thiệp diện rộng)'
    - baseline_cases: Số ca nền của tháng liền kề trước đó
    """
    client = _get_gemini_client()

    target_month = scenario.get("target_month", "Tháng giả định")
    rain = float(scenario.get("custom_rainfall", 320.0))
    humidity = float(scenario.get("custom_humidity", 85.0))
    temp = float(scenario.get("custom_temp", 28.5))
    pm25 = float(scenario.get("custom_pm25", 30.0))
    bi = float(scenario.get("mosquito_bi", 35.0))
    intervention = scenario.get("intervention_effort", "Trung bình (Phun thuốc định kỳ)")
    baseline_cases = float(scenario.get("baseline_cases", 150))

    prompt = f"""
Bạn là Chuyên gia Dịch tễ học AI lượng giá tác động can thiệp và biến đổi môi trường đến Sốt xuất huyết.
Hãy đánh giá và dự báo số ca nhiễm Sốt xuất huyết Dengue theo DỮ LIỆU TỰ THỐNG KÊ / KỊCH BẢN GIẢ ĐỊNH sau:

=== KỊCH BẢN TỰ THỐNG KÊ (CUSTOM SCENARIO) ===
- Thời điểm kịch bản: {target_month}
- Số ca mắc nền tháng trước: {baseline_cases:.0f} ca
- Lượng mưa dự kiến: {rain:.1f} mm
- Độ ẩm không khí dự kiến: {humidity:.1f} %
- Nhiệt độ trung bình: {temp:.1f} °C
- Nồng độ Bụi mịn PM2.5: {pm25:.1f} µg/m³
- Chỉ số bọ gậy Breteau Index (BI): {bi:.1f} (BI > 20 là ngưỡng nguy cơ dịch rất cao)
- Mức độ can thiệp dập dịch: {intervention}

=== QUY TẮC DỊCH TỄ HỌC CẦN ÁP DỤNG ===
1. Mưa nhiều (>300mm) và độ ẩm cao (>80%) làm tăng nơi sinh sản của muỗi Aedes.
2. Chỉ số BI cao (>30) làm tăng số ca dự báo đột biến.
3. Can thiệp "Quyết liệt" có thể kìm hãm số ca từ 25% - 40%; Can thiệp "Thấp" khiến số ca bùng phát mạnh (tăng 30% - 60% so với ca nền).

Hãy tính toán dự báo số ca nhiễm và trả về DUY NHẤT một chuỗi JSON hợp lệ không có markdown code blocks bao bọc với định dạng:
{{
  "scenario_name": "{target_month}",
  "predicted_cases": 195,
  "lower_bound": 170,
  "upper_bound": 225,
  "delta_cases_from_baseline": 45,
  "delta_pct_from_baseline": 30.0,
  "risk_level": "Nguy cơ Rất cao | Nguy cơ Cao | Nguy cơ Trung bình | Nguy cơ Thấp",
  "epidemiological_assessment": "Phân tích tác động tổng hòa giữa khí hậu, chỉ số bọ gậy và mức độ can thiệp",
  "climate_vector_synergy": "Nhận định tương quan yếu tố mưa/ẩm và chỉ số BI",
  "intervention_effectiveness": "Đánh giá mức độ hiệu quả của phương án can thiệp đã chọn",
  "recommended_actions": [
    "Hành động kiểm soát cụ thể 1",
    "Hành động kiểm soát cụ thể 2",
    "Hành động kiểm soát cụ thể 3"
  ]
}}
"""

    if client:
        try:
            from google.genai import types
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            raw_text = resp.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("\n", 1)[0]
            data = json.loads(raw_text)
            data["success"] = True
            data["source"] = f"Google Gemini ({model_name})"
            data["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            save_cached_existing_prediction(data)
            return data
        except Exception as e:
            logger.warning(f"Lỗi gọi Gemini API (Custom Scenario): {e}. Kích hoạt AI Fallback.")

    return _fallback_custom_prediction(scenario)


def _fallback_existing_prediction(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback dự báo khi mất mạng hoặc không có API key."""
    base_cases = ctx.get("latest_actual_cases", 205)
    # Regression reduction in dry season
    p1 = max(int(base_cases * 0.88), 170)
    p2 = max(int(p1 * 0.85), 145)
    p3 = max(int(p2 * 0.90), 125)

    return {
        "success": False,
        "is_fallback": True,
        "evaluation_title": "Đánh Giá Dịch Tễ Học TP.HCM (Thuật Toán Hồi Quy Môi Trường Offline)",
        "executive_summary": (
            "Dữ liệu năm 2025 ghi nhận đỉnh dịch bùng phát vào tháng 10 với 227 ca bệnh, diễn ra ngay sau đỉnh "
            "lượng mưa tháng 09 (470.9 mm) và độ ẩm đạt 87.6%. Khi TP.HCM bước vào các tháng mùa khô đầu năm 2026, "
            "lượng mưa giảm rõ rệt (< 25 mm/tháng), môi trường sinh sản của muỗi Aedes thu hẹp, dẫn đến số ca mắc có xu hướng hạ nhiệt."
        ),
        "epidemiological_risk_level": "Nguy cơ Cao (Chuyển mùa)",
        "climate_correlation_insight": "Độ trễ dịch tễ học giữa lượng mưa cực đại và đỉnh ca bệnh là 3-4 tuần. Mùa khô làm giảm số ca nhưng mật độ lưu hành mầm bệnh trong cộng đồng vẫn ở mức cảnh báo.",
        "monthly_predictions": [
            {
                "month_label": "Tháng 01/2026",
                "predicted_cases": p1,
                "lower_bound": int(p1 * 0.88),
                "upper_bound": int(p1 * 1.12),
                "trend": "Giảm dần",
                "risk_level": "Nguy cơ Cao",
                "rationale": "Lượng mưa giảm nhanh nhưng các ổ bọ gậy tồn dư từ cuối mùa mưa vẫn phát tán muỗi trưởng thành."
            },
            {
                "month_label": "Tháng 02/2026",
                "predicted_cases": p2,
                "lower_bound": int(p2 * 0.88),
                "upper_bound": int(p2 * 1.12),
                "trend": "Giảm sâu",
                "risk_level": "Nguy cơ Trung bình",
                "rationale": "Mùa khô rõ rệt, độ ẩm không khí thấp (67-68%) làm giảm tỷ lệ sống sót của muỗi truyền bệnh."
            },
            {
                "month_label": "Tháng 03/2026",
                "predicted_cases": p3,
                "lower_bound": int(p3 * 0.88),
                "upper_bound": int(p3 * 1.12),
                "trend": "Chạm đáy mùa khô",
                "risk_level": "Nguy cơ Kiểm soát",
                "rationale": "Nhiệt độ ấm lên, thời tiết nắng ráo kéo dài giúp kiểm soát số ca nhiễm."
            }
        ],
        "recommendations": [
            "Tập trung rà soát và loại bỏ các vật dụng chứa nước nhân tạo quanh nhà dân trong các tháng mùa khô.",
            "Duy trì hoạt động giám sát ca sốt phát ban nghi ngờ tại các phòng khám và bệnh viện tuyến quận/huyện.",
            "Chuẩn bị vật tư, hóa chất diệt muỗi dự phòng trước khi mùa mưa 2026 bắt đầu."
        ],
        "source": "Mô hình Phân Tích Thống Kê Dịch Tễ (Offline Fallback)",
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
    }


def _fallback_custom_prediction(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback tính toán kịch bản tự thống kê khi không có kết nối API."""
    target_month = scenario.get("target_month", "Tháng kịch bản")
    rain = float(scenario.get("custom_rainfall", 300.0))
    humidity = float(scenario.get("custom_humidity", 80.0))
    bi = float(scenario.get("mosquito_bi", 30.0))
    intervention = scenario.get("intervention_effort", "Trung bình")
    baseline = float(scenario.get("baseline_cases", 150))

    # Weight factors
    factor_rain = (rain / 250.0) * 0.25
    factor_humidity = (humidity / 75.0) * 0.25
    factor_bi = (bi / 20.0) * 0.35

    if "Quyết liệt" in intervention:
        factor_interv = -0.30
    elif "Thấp" in intervention:
        factor_interv = 0.25
    else:
        factor_interv = -0.05

    delta_pct = (factor_rain + factor_humidity + factor_bi + factor_interv - 0.70) * 100
    delta_pct = max(min(delta_pct, 120.0), -60.0)
    pred_cases = max(int(baseline * (1 + delta_pct / 100)), 10)
    delta_c = pred_cases - baseline

    risk = "Nguy cơ Rất cao" if pred_cases > 200 else ("Nguy cơ Cao" if pred_cases > 130 else "Nguy cơ Trung bình")

    return {
        "success": False,
        "is_fallback": True,
        "scenario_name": target_month,
        "predicted_cases": pred_cases,
        "lower_bound": int(pred_cases * 0.85),
        "upper_bound": int(pred_cases * 1.15),
        "delta_cases_from_baseline": delta_c,
        "delta_pct_from_baseline": round(delta_pct, 1),
        "risk_level": risk,
        "epidemiological_assessment": f"Kịch bản với lượng mưa {rain}mm và chỉ số bọ gậy BI={bi} kết hợp nỗ lực can thiệp '{intervention}'.",
        "climate_vector_synergy": f"Lượng mưa và độ ẩm tạo điều kiện cho lăng quăng phát triển với hệ số tác động tổng hợp {delta_pct:+.1f}%.",
        "intervention_effectiveness": f"Phương án can thiệp '{intervention}' đóng góp điều chỉnh số ca mắc.",
        "recommended_actions": [
            "Tổ chức tổng vệ sinh môi trường, diệt lăng quăng hàng tuần tại các khu phố trọng điểm.",
            "Xử lý dập dịch bán kính 200m ngay khi phát hiện ca bệnh đầu tiên.",
            "Tăng cường truyền thông phòng chống muỗi đốt cho người dân trong khu vực."
        ],
        "source": "Mô phỏng Thống Kê Toán Học (Offline Fallback)",
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
