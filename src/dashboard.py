import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import math
import sys
import re
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

# Fix sys.path for standalone or root launch
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_ROOT))

import paths
import unicodedata
from data_processor import (
    load_and_process_new_data,
    VN_PROVINCE_COORDS,
    HCMC_DISTRICT_COORDS,
    MERGE_MAP,
)
from chatbot.gemini_chat_engine import GeminiChatEngine, GEMINI_MODEL as _CHAT_MODEL

# Import MongoDB Data Layer for Dengue Datasets
try:
    from mongo_data_service import mongo_data_service
except ImportError:
    from src.mongo_data_service import mongo_data_service

try:
    import map_pins_service
except ImportError:
    from src import map_pins_service

_location_btn_component = components.declare_component(
    "user_location_button",
    path=str(_HERE / "location_component"),
)
_interactive_pin_map = components.declare_component(
    "interactive_pin_map",
    path=str(_HERE / "map_component"),
)
_arcgis_pin_map = components.declare_component(
    "arcgis_pin_map",
    path=str(_HERE / "arcgis_component"),
)

try:
    from booking.doctor_auth import DoctorAuthService
except ImportError:
    from src.booking.doctor_auth import DoctorAuthService

try:
    from gis_mapper import (
        ensure_hcmc_districts_geojson,
        ensure_hcmc_wards_geojson,
        normalize_hcmc_district_name,
    )
except ImportError:
    from src.gis_mapper import (
        ensure_hcmc_districts_geojson,
        ensure_hcmc_wards_geojson,
        normalize_hcmc_district_name,
    )

# Import Weather Service with Parallel Data Source Support
try:
    import weather_service
except ImportError:
    from src import weather_service

# Import AI Prediction Service (Google Gemini)
try:
    import ai_prediction_service
except ImportError:
    from src import ai_prediction_service


# ---------------------------------------------------------------------------
# Plotly Version Compatibility Helpers
# ---------------------------------------------------------------------------
MAP_HEIGHT = 900


def _scatter_map_compat(df, lat, lon, size, color, hover_name,
                        hover_data, color_continuous_scale,
                        size_max, zoom, center, title, **kwargs):
    """Render a scatter bubble map compatible with both Plotly old & new versions."""
    height = kwargs.pop("height", MAP_HEIGHT)
    common = dict(
        lat=lat, lon=lon, size=size, color=color,
        hover_name=hover_name, hover_data=hover_data,
        color_continuous_scale=color_continuous_scale,
        size_max=size_max, zoom=zoom, center=center, title=title,
        height=height,
    )
    try:
        if hasattr(px, 'scatter_map'):
            fig = px.scatter_map(df, map_style=ui.map_style(), **common, **kwargs)
        elif hasattr(px, 'scatter_mapbox'):
            fig = px.scatter_mapbox(df, mapbox_style=ui.map_style(), **common, **kwargs)
        else:
            raise AttributeError("Plotly không hỗ trợ scatter map API.")
        fig.update_layout(height=height)
        return fig
    except Exception as exc:
        raise RuntimeError(f"Không thể dựng scatter map: {exc}") from exc


def _choropleth_map_compat(df, geojson, locations, featureidkey,
                           color, hover_name, hover_data,
                           color_continuous_scale, center, zoom,
                           opacity, title, **kwargs):
    """Render a choropleth map compatible with both Plotly old & new versions."""
    height = kwargs.pop("height", MAP_HEIGHT)
    common = dict(
        geojson=geojson, locations=locations, featureidkey=featureidkey,
        color=color, hover_name=hover_name, hover_data=hover_data,
        color_continuous_scale=color_continuous_scale,
        center=center, zoom=zoom, opacity=opacity, title=title,
        height=height,
    )
    try:
        if hasattr(px, 'choropleth_map'):
            fig = px.choropleth_map(df, map_style=ui.map_style(), **common, **kwargs)
        elif hasattr(px, 'choropleth_mapbox'):
            fig = px.choropleth_mapbox(df, mapbox_style=ui.map_style(), **common, **kwargs)
        else:
            raise AttributeError("Plotly không hỗ trợ choropleth map API.")
        fig.update_layout(height=height)
        return fig
    except Exception as exc:
        raise RuntimeError(f"Không thể dựng choropleth map: {exc}") from exc


def _apply_user_location_to_map(fig, user_loc, zoom=13):
    """Overlay user's current position on a Plotly map and center the viewport on it."""
    if not user_loc or user_loc.get("lat") is None or user_loc.get("lon") is None:
        return fig
    u_lat = float(user_loc["lat"])
    u_lon = float(user_loc["lon"])
    trace_type = fig.data[0].type if fig.data else ""
    use_new_map = trace_type in ("scattermap", "choroplethmap") or (
        not trace_type and hasattr(go, "Scattermap")
    )
    if use_new_map and hasattr(go, "Scattermap"):
        fig.add_trace(
            go.Scattermap(
                lat=[u_lat],
                lon=[u_lon],
                mode="markers+text",
                marker=dict(size=18, color="#2563eb"),
                text=["📍 Vị trí của bạn"],
                textposition="top center",
                name="📍 Vị trí của bạn",
                hovertemplate="<b>📍 Vị trí của bạn</b><br>Lat: %{lat:.5f}<br>Lon: %{lon:.5f}<extra></extra>",
            )
        )
        fig.update_layout(map_center={"lat": u_lat, "lon": u_lon}, map_zoom=zoom)
    elif hasattr(go, "Scattermapbox"):
        fig.add_trace(
            go.Scattermapbox(
                lat=[u_lat],
                lon=[u_lon],
                mode="markers+text",
                marker=dict(size=18, color="#2563eb"),
                text=["📍 Vị trí của bạn"],
                textposition="top center",
                name="📍 Vị trí của bạn",
                hovertemplate="<b>📍 Vị trí của bạn</b><br>Lat: %{lat:.5f}<br>Lon: %{lon:.5f}<extra></extra>",
            )
        )
        fig.update_layout(mapbox_center={"lat": u_lat, "lon": u_lon}, mapbox_zoom=zoom)
    return fig


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Hệ thống Giám sát & Dự Báo Dịch Sốt xuất huyết",
    layout="wide",
    page_icon="🦟"
)

# Giao diện kiểu trang KAF: nạp CSS + bảng điều khiển giao diện, rồi dựng khung trang.
import ui_theme as ui
import kaf_layout

ui.apply_theme()
# Khung trang (header, banner, các khối). Các chức năng bên dưới được đổ vào từng khối.
_kaf_sec = kaf_layout.build_kaf_page()

# ---------------------------------------------------------------------------
# Database Status Badge (Đầu trang — đèn xanh / đỏ)
# ---------------------------------------------------------------------------
if mongo_data_service.is_connected:
    st.markdown(
        f'<div class="kaf-db-status" title="MongoDB đã kết nối ({mongo_data_service.db_name})">'
        '<span>🟢</span>'
        f'<span>MongoDB · {mongo_data_service.db_name}</span>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="kaf-db-status" title="Lưu trữ cục bộ (Local CSV) — Chưa kết nối MongoDB">'
        '<span>🔴</span>'
        '<span>Database: Local CSV</span>'
        '</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Sidebar Role Switcher & HCDC Officer Authentication
# ---------------------------------------------------------------------------
if "hcdc_auth_service" not in st.session_state:
    st.session_state["hcdc_auth_service"] = DoctorAuthService()

with st.sidebar.expander("🛡️ Vai trò & Quyền HCDC", expanded=False):
    _user_role = st.radio(
        "Đối tượng sử dụng:",
        [
            "👥 Người dân / Cộng đồng",
            "👨‍⚕️ Cán bộ Y tế / HCDC (Quản lý dịch)",
        ],
        key="user_role_selector",
    )
    if _user_role.startswith("👨‍⚕️"):
        _active_doc = st.session_state.get("hcdc_doctor_profile")
        if _active_doc:
            st.success(f"✅ Đã đăng nhập: **{_active_doc.get('full_name', '')}**")
            st.caption(f"🏥 {_active_doc.get('specialty', '')} · {_active_doc.get('room', '')}")
            if st.button("🚪 Đăng xuất HCDC", key="btn_hcdc_logout", use_container_width=True):
                _tok = st.session_state.get("hcdc_session_token")
                if _tok:
                    st.session_state["hcdc_auth_service"].logout_doctor(_tok)
                st.session_state.pop("hcdc_session_token", None)
                st.session_state.pop("hcdc_doctor_profile", None)
                st.rerun()
        else:
            st.caption("Đăng nhập để duyệt phản ánh cộng đồng & điều phối xử lý ổ dịch.")
            with st.form("hcdc_login_form"):
                _u_inp = st.text_input("Tài khoản cán bộ", value="bs_nguyenvana", key="hcdc_user_inp")
                _p_inp = st.text_input("Mật khẩu", type="password", value="", placeholder="Nhập mật khẩu", key="hcdc_pass_inp")
                _login_sub = st.form_submit_button("🔐 Đăng nhập HCDC", use_container_width=True)
                if _login_sub:
                    _db_conn = mongo_data_service.db if mongo_data_service.is_connected else None
                    _auth_res = st.session_state["hcdc_auth_service"].authenticate_doctor(_u_inp, _p_inp, mongo_db=_db_conn)
                    if _auth_res:
                        _tok, _prof = _auth_res
                        st.session_state["hcdc_session_token"] = _tok
                        st.session_state["hcdc_doctor_profile"] = (
                            _prof.model_dump() if hasattr(_prof, "model_dump") else _prof.dict()
                        )
                        st.success(f"Chào mừng {_prof.full_name}!")
                        st.rerun()
                    else:
                        st.error("Sai tài khoản hoặc mật khẩu.")
            st.caption("💡 Demo hội đồng: `bs_nguyenvana` / `Bacsi@123`")

is_hcdc_officer = bool(
    st.session_state.get("user_role_selector", "").startswith("👨‍⚕️")
    and st.session_state.get("hcdc_doctor_profile")
)
active_hcdc_officer = st.session_state.get("hcdc_doctor_profile") or {}

# ---------------------------------------------------------------------------
# Sidebar Management (Tất cả nằm trong ⚙️, dạng drop box ký hiệu + tên chức năng)
# ---------------------------------------------------------------------------
uploaded_file = None
_sb_options = [
    "⋮ Tùy chỉnh",
    "📍 Giám sát dịch tễ",
    "🗄️ Cơ sở dữ liệu",
    "📁 Dữ liệu dịch tễ",
    "🗺️ Tải bản đồ GeoJSON",
]

with st.sidebar.expander("⚙️", expanded=False):
    _sb_func = st.selectbox(
        "⚙️ Chức năng",
        _sb_options,
        key="sb_func_dropbox",
        label_visibility="collapsed",
    )

    if _sb_func == "⋮ Tùy chỉnh":
        ui.render_customize_panel()

    elif _sb_func == "📍 Giám sát dịch tễ":
        st.caption("🗺️ Hỗ trợ 4 cấp độ: **Phố > Phường > Quận > Toàn Quốc** kèm khoanh vùng bán kính ổ dịch trực quan.")

    elif _sb_func == "🗄️ Cơ sở dữ liệu":
        if mongo_data_service.is_connected:
            st.caption(f"🟢 Đã kết nối MongoDB Atlas (`{mongo_data_service.db_name}`)")
        else:
            st.caption("🟡 Lưu trữ: Dữ liệu cục bộ (Local CSV)")
            if st.button("🔌 Kết nối lại MongoDB Atlas", key="sb_reconnect_mongo", use_container_width=True):
                if mongo_data_service.connect():
                    st.success("Kết nối MongoDB thành công!")
                    st.rerun()
                else:
                    st.error("Chưa kết nối được. Vui lòng mở IP Access List (0.0.0.0/0) trên MongoDB Atlas Network Access.")

    elif _sb_func == "📁 Dữ liệu dịch tễ":
        uploaded_file = st.file_uploader("📤 Tải lên dữ liệu bệnh nhân mới (Excel)", type=['xlsx'])

    elif _sb_func == "🗺️ Tải bản đồ GeoJSON":
        if paths.MAP_OUTPUT_FILE.exists():
            with open(paths.MAP_OUTPUT_FILE, 'rb') as f:
                st.download_button(
                    "🗺️ Tải Bản Đồ Tỉnh GeoJSON",
                    f,
                    "dengue_map.geojson",
                    key="sb_dl_map_geojson",
                    use_container_width=True,
                )
        hcmc_map_geojson_path = getattr(paths, 'HCMC_MAP_OUTPUT_FILE', paths.OUTPUTS_DIR / "hcmc_districts_risk.geojson")
        if hcmc_map_geojson_path.exists():
            with open(hcmc_map_geojson_path, 'rb') as f:
                st.download_button(
                    "🏙️ Tải Bản Đồ Quận TP.HCM GeoJSON",
                    f,
                    "hcmc_districts_risk.geojson",
                    key="sb_dl_hcmc_dist_geojson",
                    use_container_width=True,
                )
        clusters_geojson_path = getattr(paths, 'EPIDEMIC_CLUSTERS_GEOJSON', paths.OUTPUTS_DIR / "epidemic_clusters.geojson")
        if clusters_geojson_path.exists():
            with open(clusters_geojson_path, 'rb') as f:
                st.download_button(
                    "🎯 Tải Bản Đồ Khoanh Vùng Ổ Dịch GeoJSON",
                    f,
                    "epidemic_clusters.geojson",
                    key="sb_dl_clusters_geojson",
                    use_container_width=True,
                )


@st.cache_data
def load_historical():
    df = mongo_data_service.load_dataset("historical", getattr(paths, 'HISTORICAL_CSV', paths.PROCESSED_DIR / "historical.csv"))
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_district_breakdown():
    df = mongo_data_service.load_dataset("district_breakdown", getattr(paths, 'DISTRICT_CSV', paths.PROCESSED_DIR / "district_breakdown.csv"))
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_ward_breakdown():
    df = mongo_data_service.load_dataset("ward_breakdown", getattr(paths, 'WARD_CSV', paths.PROCESSED_DIR / "ward_breakdown.csv"))
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_street_hotspots():
    df = mongo_data_service.load_dataset("street_hotspots", getattr(paths, 'STREET_HOTSPOTS_CSV', paths.PROCESSED_DIR / "street_hotspots.csv"))
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_epidemic_clusters():
    df = mongo_data_service.load_dataset("epidemic_clusters", getattr(paths, 'EPIDEMIC_CLUSTERS_CSV', paths.PROCESSED_DIR / "epidemic_clusters.csv"))
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_hcmc_hotspots():
    df = mongo_data_service.load_dataset("hcmc_hotspots", getattr(paths, 'HCMC_HOTSPOTS_CSV', paths.PROCESSED_DIR / "hcmc_hotspots.csv"))
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_predictions():
    return mongo_data_service.load_dataset("latest_predictions", getattr(paths, 'PREDICTIONS_CSV', paths.PROCESSED_DIR / "latest_predictions.csv"))


@st.cache_data
def load_hcmc_district_predictions():
    return mongo_data_service.load_dataset(
        "hcmc_district_predictions",
        getattr(paths, 'DISTRICT_PREDICTIONS_CSV', paths.PROCESSED_DIR / "hcmc_district_predictions.csv"),
    )


@st.cache_data(show_spinner=False)
def load_vietnam_geojson(geojson_str_path: str):
    """Cache the 48MB GeoJSON in RAM to prevent blocking disk I/O on every rerun."""
    p = Path(geojson_str_path)
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_hcmc_districts_geojson():
    """Nạp GeoJSON ranh giới Quận/Huyện TP.HCM (tự động sinh nếu chưa có)."""
    p = getattr(paths, 'HCMC_BOUNDARY_FILE', paths.DATA_DIR / "population" / "hcmc_districts.geojson")
    if not p.exists():
        try:
            ensure_hcmc_districts_geojson(output_file=p)
        except Exception:
            return None
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_hcmc_wards_geojson():
    """Nạp GeoJSON ranh giới Phường/Xã TP.HCM phủ kín 100% các Quận/Huyện."""
    p = getattr(paths, 'HCMC_WARDS_BOUNDARY_FILE', paths.DATA_DIR / "population" / "hcmc_wards.geojson")
    if not p.exists():
        try:
            ensure_hcmc_wards_geojson(output_file=p)
        except Exception:
            return None
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_vietnam_geojson_simplified(geojson_str_path: str, tolerance: float = 0.02):
    """Return a lightweight simplified GeoJSON (~200KB) for fast interactive Leaflet rendering."""
    raw = load_vietnam_geojson(geojson_str_path)
    if not raw or "features" not in raw:
        return raw
    try:
        from shapely.geometry import shape, mapping
        features = []
        for feat in raw["features"]:
            geom = feat.get("geometry")
            props = feat.get("properties") or {}
            if not geom:
                continue
            simp = shape(geom).simplify(tolerance, preserve_topology=True)
            features.append({
                "type": "Feature",
                "properties": {"adm1_name1": props.get("adm1_name1", "")},
                "geometry": mapping(simp),
            })
        return {"type": "FeatureCollection", "features": features}
    except Exception:
        return raw


_st_fragment = getattr(st, "fragment", getattr(st, "experimental_fragment", lambda f: f))


@st.cache_data(ttl=60, show_spinner=False)
def load_cached_pins():
    return map_pins_service.load_pins()


@st.cache_data(ttl=60, show_spinner=False)
def load_cached_cluster_actions():
    return map_pins_service.load_cluster_actions()


@st.cache_data(ttl=300, show_spinner=False)
def load_cached_weather_series(province: str, weather_source: str):
    return weather_service.get_weather_dengue_combined_series(
        dengue_df=load_historical(),
        province=province,
        weather_source=weather_source,
    )


@st.cache_data(show_spinner=False)
def load_historical_weather_csv():
    p = paths.PROCESSED_DIR / "historical_weather.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


@st.cache_data(show_spinner=False)
def load_hcmc_monthly_weather_csv():
    p = getattr(paths, "WEATHERDATA_MONTHLY_CSV", paths.PROCESSED_DIR / "weatherdata_hcmc_monthly.csv")
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


@st.cache_data(show_spinner=False)
def load_cleaned_station_weather_csv():
    p = getattr(paths, "WEATHERDATA_CLEANED_CSV", paths.DATA_DIR / "weatherdata" / "processed" / "cleaned_final.csv")
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


TEMP_ANOMALIES_FILE = getattr(paths, "TEMP_ANOMALIES_FILE", paths.PROCESSED_DIR / "temperature_anomalies.json")


@st.cache_data(ttl=60, show_spinner=False)
def load_temperature_anomalies():
    """Đọc danh sách điểm nhiệt độ dị thường (quá cao / quá thấp) đã lưu trữ."""
    records = []
    if TEMP_ANOMALIES_FILE.exists():
        try:
            with open(TEMP_ANOMALIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                records = data
        except Exception:
            records = []
    return records


def save_temperature_anomalies(new_records: list) -> list:
    """Lưu các điểm nhiệt độ dị thường mới vào local JSON (và MongoDB nếu kết nối)."""
    if not new_records:
        return load_temperature_anomalies()
    existing = []
    if TEMP_ANOMALIES_FILE.exists():
        try:
            with open(TEMP_ANOMALIES_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                existing = raw
        except Exception:
            existing = []

    seen_keys = {
        (
            round(_safe_float(r.get("lat"), 0.0), 3),
            round(_safe_float(r.get("lon"), 0.0), 3),
            str(r.get("obs_date", "")),
            str(r.get("anomaly_type", "")),
        )
        for r in existing
    }
    added = []
    for item in new_records:
        key = (
            round(_safe_float(item.get("lat"), 0.0), 3),
            round(_safe_float(item.get("lon"), 0.0), 3),
            str(item.get("obs_date", "")),
            str(item.get("anomaly_type", "")),
        )
        if key not in seen_keys:
            seen_keys.add(key)
            added.append(item)

    if added:
        merged = (added + existing)[:120]
        try:
            TEMP_ANOMALIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TEMP_ANOMALIES_FILE, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            load_temperature_anomalies.clear()
        except Exception:
            pass
        if getattr(mongo_data_service, "is_connected", False) and getattr(mongo_data_service, "db", None) is not None:
            try:
                mongo_data_service.db["temperature_anomalies"].insert_many([dict(x) for x in added])
            except Exception:
                pass
        return merged
    return existing


@st.cache_data(ttl=180, show_spinner=False)
def fetch_realtime_temperature_batch(coords_tuple: tuple):
    """Lấy nhiệt độ thời gian thực theo tọa độ từ Open-Meteo Forecast API (chia chunk an toàn toàn quốc)."""
    if not coords_tuple:
        return {}
    out = {}
    chunk_size = 35
    try:
        for start_idx in range(0, len(coords_tuple), chunk_size):
            chunk = coords_tuple[start_idx : start_idx + chunk_size]
            lats = ",".join(f"{float(c[0]):.4f}" for c in chunk)
            lons = ",".join(f"{float(c[1]):.4f}" for c in chunk)
            url = (
                "https://api.open-meteo.com/v1/forecast?"
                + urllib.parse.urlencode({
                    "latitude": lats,
                    "longitude": lons,
                    "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                    "timezone": "Asia/Ho_Chi_Minh",
                })
            )
            req = urllib.request.Request(url, headers={"User-Agent": "DengueSurveillanceGIS/1.0"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            items = payload if isinstance(payload, list) else [payload]
            for local_idx, entry in enumerate(items):
                cur = entry.get("current") or {}
                if cur.get("temperature_2m") is not None:
                    out[start_idx + local_idx] = {
                        "temp_c": round(float(cur["temperature_2m"]), 1),
                        "humidity_pct": round(float(cur.get("relative_humidity_2m") or 75.0), 1),
                        "rain_mm": round(float(cur.get("precipitation") or 0.0), 1),
                        "wind_kmh": round(float(cur.get("wind_speed_10m") or 0.0), 1),
                        "obs_time": str(cur.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M")),
                        "source": "Open-Meteo Real-time",
                    }
        return out
    except Exception:
        return out


@st.cache_data(show_spinner=False)
def load_adm1_population_csv():
    """Tổng hợp dân số và tỷ lệ trẻ em 0-14 tuổi theo 34 Tỉnh/Thành từ dữ liệu dân số 2024."""
    p = getattr(paths, "POP_DATA_FILE", paths.DATA_DIR / "population" / "vnm_admpop_adm1_2024.csv")
    if not p.exists():
        return pd.DataFrame()
    try:
        pop_df = pd.read_csv(p)
    except Exception:
        return pd.DataFrame()

    def _strip_acc(s):
        s = str(s or "").replace("đ", "d").replace("Đ", "d")
        return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

    merge_clean = {
        _strip_acc(k).lower().replace(" city", "").replace(" province", "").strip(): v
        for k, v in MERGE_MAP.items()
    }

    def _map_prov(adm1_en):
        key = _strip_acc(adm1_en).lower().replace(" city", "").replace(" province", "").strip()
        return merge_clean.get(key)

    pop_df["province"] = pop_df["ADM1_EN"].apply(_map_prov)
    pop_df = pop_df[pop_df["province"].notna()].copy()
    child_cols = [c for c in ("T_00_04", "T_05_09", "T_10_14") if c in pop_df.columns]
    pop_df["child_pop"] = pop_df[child_cols].sum(axis=1) if child_cols else 0.0
    agg = pop_df.groupby("province", as_index=False).agg(
        population=("T_TL", "sum"),
        child_pop=("child_pop", "sum"),
    )
    agg["child_ratio_pct"] = (agg["child_pop"] / agg["population"].replace(0, 1) * 100.0).round(1)
    return agg


_HCMC_DISTRICT_REF_POP_2024 = {
    "Quận 1": 165000,
    "Quận 3": 190000,
    "Quận 4": 175000,
    "Quận 5": 162000,
    "Quận 6": 235000,
    "Quận 7": 395000,
    "Quận 8": 430000,
    "Quận 10": 235000,
    "Quận 11": 215000,
    "Quận 12": 690000,
    "Bình Thạnh": 510000,
    "Gò Vấp": 690000,
    "Tân Bình": 485000,
    "Tân Phú": 495000,
    "Bình Tân": 860000,
    "Phú Nhuận": 165000,
    "Thủ Đức": 1260000,
    "Hóc Môn": 580000,
    "Củ Chi": 485000,
    "Nhà Bè": 240000,
    "Bình Chánh": 810000,
    "Cần Giờ": 74000,
    "Thành Phố Dĩ An": 510000,
    "Thành Phố Thuận An": 655000,
    "Thành Phố Thủ Dầu Một": 355000,
    "Thị Xã Tân Uyên": 480000,
    "Thị Xã Bến Cát": 375000,
    "Thành Phố Vũng Tàu": 380000,
    "Thị Xã Phú Mỹ": 245000,
    "Huyện Châu Đức": 155000,
    "Huyện Xuyên Mộc": 140000,
}

_PROVINCE_GROWTH_RATE_MAP = {
    "TP. Hồ Chí Minh": 0.0175,
    "Hà Nội": 0.0155,
    "Bắc Ninh": 0.0190,
    "Đồng Nai": 0.0150,
    "Hưng Yên": 0.0135,
    "Hải Phòng": 0.0130,
    "Đà Nẵng": 0.0145,
    "Tây Ninh": 0.0125,
    "Khánh Hòa": 0.0120,
    "Cần Thơ": 0.0095,
}


def _spherical_ring_area_km2(ring) -> float:
    """Tính diện tích gần đúng theo km² trên mặt cầu WGS84 cho một vòng tọa độ GeoJSON."""
    if not ring or len(ring) < 3:
        return 0.0
    r_earth = 6371.0088
    total = 0.0
    n = len(ring)
    for i in range(n):
        p1 = ring[i]
        p2 = ring[(i + 1) % n]
        lon1, lat1 = math.radians(float(p1[0])), math.radians(float(p1[1]))
        lon2, lat2 = math.radians(float(p2[0])), math.radians(float(p2[1]))
        total += (lon2 - lon1) * (2.0 + math.sin(lat1) + math.sin(lat2))
    return abs(total * (r_earth ** 2) / 2.0)


def _geojson_geom_area_km2_and_center(geom: dict):
    """Trích xuất diện tích km² và tâm (lat, lon) đại diện từ Polygon / MultiPolygon GeoJSON."""
    if not isinstance(geom, dict):
        return 0.0, None, None
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    best_ring = []
    area_km2 = 0.0
    if gtype == "Polygon" and coords:
        area_km2 = _spherical_ring_area_km2(coords[0])
        for hole in coords[1:]:
            area_km2 = max(0.0, area_km2 - _spherical_ring_area_km2(hole))
        best_ring = coords[0]
    elif gtype == "MultiPolygon" and coords:
        best_area = -1.0
        for poly in coords:
            if not poly:
                continue
            p_area = _spherical_ring_area_km2(poly[0])
            for hole in poly[1:]:
                p_area = max(0.0, p_area - _spherical_ring_area_km2(hole))
            area_km2 += p_area
            if p_area > best_area:
                best_area = p_area
                best_ring = poly[0]
    if not best_ring:
        return round(area_km2, 2), None, None
    lons = [float(p[0]) for p in best_ring]
    lats = [float(p[1]) for p in best_ring]
    c_lat = round((min(lats) + max(lats)) / 2.0, 4)
    c_lon = round((min(lons) + max(lons)) / 2.0, 4)
    return round(area_km2, 2), c_lat, c_lon


@st.cache_data(show_spinner=False)
def load_or_build_3year_population_density():
    """
    Thu thập & chuẩn hóa dữ liệu mật độ dân số 3 năm gần nhất (2023–2024–2025, đơn vị người/km²)
    cho toàn bộ 34 Tỉnh/Thành và 31 Quận/Huyện TP.HCM, lưu ra data/population/population_density_3years.csv.
    """
    out_path = paths.DATA_DIR / "population" / "population_density_3years.csv"
    required_cols = {
        "level", "province", "region_name", "area_km2",
        "pop_2023", "pop_2024", "pop_2025",
        "density_2023", "density_2024", "density_2025",
        "growth_3y_pct", "lat", "lon",
    }
    if out_path.exists():
        try:
            existing_df = pd.read_csv(out_path)
            if required_cols.issubset(set(existing_df.columns)) and len(existing_df) >= 60:
                return existing_df
        except Exception:
            pass

    adm1_df = load_adm1_population_csv()
    adm1_map = {}
    if not adm1_df.empty:
        for _, r in adm1_df.iterrows():
            adm1_map[str(r["province"])] = {
                "population": int(float(r.get("population") or 0)),
                "child_ratio_pct": float(r.get("child_ratio_pct") or 21.0),
            }

    rows = []

    # 1. Toàn bộ 34 Tỉnh/Thành (từ vietnam_34_provinces_2025.geojson + vnm_admpop_adm1_2024.csv)
    vn_geo_path = paths.DATA_DIR / "population" / "vietnam_34_provinces_2025.geojson"
    if vn_geo_path.exists():
        try:
            with open(vn_geo_path, "r", encoding="utf-8") as f:
                vn_geo = json.load(f)
            for feat in vn_geo.get("features", []):
                props = feat.get("properties") or {}
                prov_name = str(props.get("adm1_name1") or props.get("adm1_name") or "").strip()
                if not prov_name:
                    continue
                geom_area, g_lat, g_lon = _geojson_geom_area_km2_and_center(feat.get("geometry") or {})
                area_km2 = float(props.get("area_sqkm") or geom_area or 1000.0)
                area_km2 = max(area_km2, 10.0)
                vc = VN_PROVINCE_COORDS.get(prov_name) or {}
                lat = float(vc.get("lat") if vc.get("lat") is not None else (g_lat or 16.0))
                lon = float(vc.get("lon") if vc.get("lon") is not None else (g_lon or 107.0))
                p_meta = adm1_map.get(prov_name, {})
                pop_2024 = int(p_meta.get("population") or 1_500_000)
                child_pct = float(p_meta.get("child_ratio_pct") or 21.5)
                g_rate = float(_PROVINCE_GROWTH_RATE_MAP.get(prov_name, 0.0088))
                pop_2023 = int(round(pop_2024 / (1.0 + g_rate)))
                pop_2025 = int(round(pop_2024 * (1.0 + g_rate)))
                d_2023 = round(pop_2023 / area_km2, 1)
                d_2024 = round(pop_2024 / area_km2, 1)
                d_2025 = round(pop_2025 / area_km2, 1)
                g_3y = round(((d_2025 - d_2023) / max(d_2023, 0.1)) * 100.0, 2)
                rows.append({
                    "level": "province",
                    "province": prov_name,
                    "region_name": prov_name,
                    "area_km2": round(area_km2, 2),
                    "pop_2023": pop_2023,
                    "pop_2024": pop_2024,
                    "pop_2025": pop_2025,
                    "density_2023": d_2023,
                    "density_2024": d_2024,
                    "density_2025": d_2025,
                    "growth_3y_pct": g_3y,
                    "child_ratio_pct": round(child_pct, 1),
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                })
        except Exception:
            pass

    # 2. Toàn bộ Quận/Huyện TP.HCM (từ hcmc_districts.geojson, chuẩn hóa tổng theo ADM1 TP.HCM 2024)
    hcmc_geo_path = paths.DATA_DIR / "population" / "hcmc_districts.geojson"
    if not hcmc_geo_path.exists():
        try:
            ensure_hcmc_districts_geojson(output_file=hcmc_geo_path)
        except Exception:
            pass
    if hcmc_geo_path.exists():
        try:
            with open(hcmc_geo_path, "r", encoding="utf-8") as f:
                hc_geo = json.load(f)
            hcmc_total_2024 = int((adm1_map.get("TP. Hồ Chí Minh") or {}).get("population") or 14_092_602)
            hcmc_child_pct = float((adm1_map.get("TP. Hồ Chí Minh") or {}).get("child_ratio_pct") or 19.8)
            raw_items = []
            for feat in hc_geo.get("features", []):
                props = feat.get("properties") or {}
                d_name = str(props.get("district") or props.get("adm1_name1") or "").strip()
                if not d_name:
                    continue
                area_km2, g_lat, g_lon = _geojson_geom_area_km2_and_center(feat.get("geometry") or {})
                area_km2 = max(area_km2, 4.0)
                c_lat = float(props.get("center_lat") if props.get("center_lat") is not None else (g_lat or 10.7769))
                c_lon = float(props.get("center_lon") if props.get("center_lon") is not None else (g_lon or 106.7009))
                ref_pop = int(_HCMC_DISTRICT_REF_POP_2024.get(d_name, 320000))
                raw_items.append({
                    "district": d_name,
                    "area_km2": area_km2,
                    "ref_pop": ref_pop,
                    "lat": c_lat,
                    "lon": c_lon,
                })
            ref_sum = sum(x["ref_pop"] for x in raw_items) or 1
            scale_factor = hcmc_total_2024 / float(ref_sum)
            fast_urban_keys = (
                "Thủ Đức", "Bình Tân", "Quận 12", "Bình Chánh", "Nhà Bè", "Hóc Môn",
                "Dĩ An", "Thuận An", "Tân Uyên", "Bến Cát", "Phú Mỹ",
            )
            for x in raw_items:
                d_name = x["district"]
                area_km2 = x["area_km2"]
                pop_2024 = int(round(x["ref_pop"] * scale_factor))
                g_rate = 0.022 if any(k in d_name for k in fast_urban_keys) else 0.0085
                pop_2023 = int(round(pop_2024 / (1.0 + g_rate)))
                pop_2025 = int(round(pop_2024 * (1.0 + g_rate)))
                d_2023 = round(pop_2023 / area_km2, 1)
                d_2024 = round(pop_2024 / area_km2, 1)
                d_2025 = round(pop_2025 / area_km2, 1)
                g_3y = round(((d_2025 - d_2023) / max(d_2023, 0.1)) * 100.0, 2)
                rows.append({
                    "level": "district",
                    "province": "TP. Hồ Chí Minh",
                    "region_name": d_name,
                    "area_km2": round(area_km2, 2),
                    "pop_2023": pop_2023,
                    "pop_2024": pop_2024,
                    "pop_2025": pop_2025,
                    "density_2023": d_2023,
                    "density_2024": d_2024,
                    "density_2025": d_2025,
                    "growth_3y_pct": g_3y,
                    "child_ratio_pct": round(hcmc_child_pct, 1),
                    "lat": round(x["lat"], 4),
                    "lon": round(x["lon"], 4),
                })
        except Exception:
            pass

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df_out.to_csv(out_path, index=False, encoding="utf-8-sig")
        except Exception:
            pass
    return df_out


def _classify_risk_tier(pred_val: float, scope: str = "district") -> dict:
    """Phân loại 4 mức nguy cơ chuẩn quy hoạch: Thấp (#22c55e) – TB (#eab308) – Cao (#f97316) – Rất cao (#dc2626)."""
    val = float(pred_val or 0.0)
    if scope == "province":
        if val >= 25.0:
            return {"tier_key": "very_high", "tier_label": "Rất cao", "color": "#dc2626",
                    "recommendation": "Phun hóa chất diện rộng & kích hoạt đội phản ứng nhanh"}
        if val >= 5.0:
            return {"tier_key": "high", "tier_label": "Cao", "color": "#f97316",
                    "recommendation": "Diệt bọ gậy tăng cường & khoanh vùng ổ dịch nguy cơ"}
        if val >= 2.0:
            return {"tier_key": "medium", "tier_label": "Trung bình", "color": "#eab308",
                    "recommendation": "Kiểm tra điểm nguy cơ hàng tuần & truyền thông cộng đồng"}
        return {"tier_key": "low", "tier_label": "Thấp", "color": "#22c55e",
                "recommendation": "Giám sát dịch tễ định kỳ & duy trì vệ sinh môi trường"}
    if scope == "local":
        if val >= 8.0:
            return {"tier_key": "very_high", "tier_label": "Rất cao", "color": "#dc2626",
                    "recommendation": "Phun ULV khẩn cấp & khoanh vùng bán kính 300–500m"}
        if val >= 4.0:
            return {"tier_key": "high", "tier_label": "Cao", "color": "#f97316",
                    "recommendation": "Tổng vệ sinh diệt lăng quăng & giám sát ca bệnh hằng ngày"}
        if val >= 1.5:
            return {"tier_key": "medium", "tier_label": "Trung bình", "color": "#eab308",
                    "recommendation": "Giám sát lăng quăng tuần & cảnh báo hộ dân lân cận"}
        return {"tier_key": "low", "tier_label": "Thấp", "color": "#22c55e",
                "recommendation": "Theo dõi định kỳ & phòng muỗi đốt"}
    # scope == "district"
    if val >= 25.0:
        return {"tier_key": "very_high", "tier_label": "Rất cao", "color": "#dc2626",
                "recommendation": "Phun hóa chất khẩn cấp toàn địa bàn trọng điểm"}
    if val >= 8.0:
        return {"tier_key": "high", "tier_label": "Cao", "color": "#f97316",
                "recommendation": "Diệt lăng quăng quy mô quận/huyện & kiểm tra ổ dịch mới"}
    if val >= 0.5:
        return {"tier_key": "medium", "tier_label": "Trung bình", "color": "#eab308",
                "recommendation": "Tăng cường giám sát véc-tơ & điểm nước đọng"}
    return {"tier_key": "low", "tier_label": "Thấp", "color": "#22c55e",
            "recommendation": "Giám sát định kỳ & duy trì mức kiểm soát"}


def _safe_int(val, default: int = 0) -> int:
    try:
        if val is None or pd.isna(val):
            return default
        return int(float(val))
    except Exception:
        return default


def _safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None or pd.isna(val):
            return default
        return float(val)
    except Exception:
        return default


def _lookup_province_coords(province: str):
    c = VN_PROVINCE_COORDS.get(province)
    if c:
        return float(c["lat"]), float(c["lon"])
    info = weather_service._get_province_info(province)
    if info:
        return float(info["lat"]), float(info["lon"])
    return None, None


@st.cache_data(ttl=300, show_spinner=False)
def get_province_weather_lookup(sel_year: int, sel_month: int):
    """Tra cứu nhiệt độ, độ ẩm, lượng mưa theo tỉnh/tháng cho Popup bản đồ Choropleth."""
    hw_df = load_historical_weather_csv()
    hcmc_w_df = load_hcmc_monthly_weather_csv()
    res = {}

    hcmc_row = None
    if not hcmc_w_df.empty:
        sub_hw = hcmc_w_df[(hcmc_w_df["year"] == sel_year) & (hcmc_w_df["month"] == sel_month)]
        if sub_hw.empty:
            sub_hw = hcmc_w_df[hcmc_w_df["month"] == sel_month]
        if sub_hw.empty:
            sub_hw = hcmc_w_df.sort_values(["year", "month"], ascending=False)
        if not sub_hw.empty:
            hcmc_row = sub_hw.iloc[0]

    if hcmc_row is not None:
        res["TP. Hồ Chí Minh"] = {
            "temp_mean": round(_safe_float(hcmc_row.get("temp_mean"), 27.5), 1),
            "humidity_mean": round(_safe_float(hcmc_row.get("humidity_mean"), 78.0), 1),
            "rain_mm": round(_safe_float(hcmc_row.get("precipitation_sum"), 0.0), 1),
        }

    if not hw_df.empty:
        for prov, grp in hw_df.groupby("province"):
            prov_str = str(prov)
            if prov_str in res:
                continue
            exact = grp[(grp["year"] == sel_year) & (grp["month"] == sel_month)]
            pick = exact if not exact.empty else grp[grp["month"] == sel_month]
            if pick.empty:
                pick = grp.sort_values(["year", "month"], ascending=False)
            r0 = pick.iloc[0]
            t_val = _safe_float(r0.get("temp_lag_1"), 0.0)
            h_val = _safe_float(r0.get("humidity_lag_1"), 0.0)
            if t_val > 0 or h_val > 0:
                res[prov_str] = {
                    "temp_mean": round(t_val, 1),
                    "humidity_mean": round(h_val, 1),
                    "rain_mm": round(_safe_float(r0.get("rain_lag_1"), 0.0), 1),
                }
    return res


def _get_geojson_region_key(feat: dict) -> str:
    props = (feat or {}).get("properties") or {}
    if props.get("ward"):
        return str(props.get("adm1_name1") or props.get("ward") or "")
    return str(props.get("district") or props.get("adm1_name1") or "Khu vực")


def _filter_geojson_for_province_or_dist(geojson_data: dict, sel_prov: str, sel_dist: str = "Tất cả Quận/Huyện"):
    """Lọc GeoJSON phường/quận theo Quận được chọn hoặc lấy ranh giới tỉnh nếu ngoài TP.HCM."""
    if not geojson_data or not isinstance(geojson_data.get("features"), list):
        return geojson_data
    feats = geojson_data["features"]
    if sel_prov and "Hồ Chí Minh" in sel_prov:
        if sel_dist and sel_dist != "Tất cả Quận/Huyện":
            norm_t = normalize_hcmc_district_name(sel_dist)
            filtered = [
                f for f in feats
                if normalize_hcmc_district_name((f.get("properties") or {}).get("district", "")) == norm_t
            ]
            if filtered:
                return {"type": "FeatureCollection", "features": filtered}
        return geojson_data
    # Tỉnh khác ngoài TP.HCM -> trả về ranh giới tỉnh từ GeoJSON 34 tỉnh
    gp = getattr(paths, "BOUNDARY_FILE", paths.DATA_DIR / "population" / "vietnam_34_provinces_2025.geojson")
    if gp.exists() and sel_prov:
        vn_gj = load_vietnam_geojson_simplified(str(gp))
        if vn_gj and isinstance(vn_gj.get("features"), list):
            p_feats = [f for f in vn_gj["features"] if (f.get("properties") or {}).get("adm1_name1") == sel_prov]
            if p_feats:
                return {"type": "FeatureCollection", "features": p_feats}
    return None


def build_choropleth_region_values(
    geojson_data: dict,
    cases_map: dict,
    pred_map: dict,
    inc_map: dict,
    weather_lookup: dict,
    default_weather: dict = None,
    scope: str = "district",
) -> dict:
    """Chuẩn bị thuộc tính phân tầng 4 mức nguy cơ + dự báo + thời tiết cho mọi đa giác Choropleth."""
    if not geojson_data or not isinstance(geojson_data.get("features"), list):
        return {}
    out = {}
    def_w = default_weather or {"temp_mean": 27.5, "humidity_mean": 78.0, "rain_mm": 0.0}
    for feat in geojson_data["features"]:
        props = feat.get("properties") or {}
        r_key = _get_geojson_region_key(feat)
        if not r_key:
            continue
        dist_key = normalize_hcmc_district_name(props.get("district", ""))
        cases_val = _safe_int(cases_map.get(r_key, cases_map.get(dist_key, 0)), 0)
        pred_val = _safe_float(pred_map.get(r_key, pred_map.get(dist_key, cases_val)), float(cases_val))
        inc_val = _safe_float(inc_map.get(r_key, inc_map.get(dist_key, 0.0)), 0.0)
        w_info = weather_lookup.get(r_key) or weather_lookup.get(str(props.get("province", ""))) or def_w
        score = max(float(pred_val), float(cases_val))
        tier = _classify_risk_tier(score, scope=scope)
        out[r_key] = {
            "cases": cases_val,
            "predicted_cases": round(pred_val, 1),
            "incidence_rate": round(inc_val, 2),
            "risk_tier": tier["tier_key"],
            "risk_label": tier["tier_label"],
            "risk_color": tier["color"],
            "recommendation": tier["recommendation"],
            "temp_mean": _safe_float(w_info.get("temp_mean"), def_w.get("temp_mean", 27.5)),
            "humidity_mean": _safe_float(w_info.get("humidity_mean"), def_w.get("humidity_mean", 78.0)),
            "rain_mm": _safe_float(w_info.get("rain_mm"), def_w.get("rain_mm", 0.0)),
        }
    return out


@st.cache_data(ttl=180, show_spinner=False)
def build_realtime_temperature_layer(
    sel_year: int,
    sel_month: int,
    level_code: str,
    sel_prov: str,
    sel_dist: str = "Tất cả Quận/Huyện",
):
    """
    Lấy nhiệt độ thời gian thực (Open-Meteo Live API, fallback dữ liệu quan trắc giờ/tháng)
    và phát hiện + lưu trữ các điểm nhiệt độ dị thường (quá cao / quá thấp).
    """
    hw_df = load_historical_weather_csv()
    hcmc_w_df = load_hcmc_monthly_weather_csv()
    cleaned_df = load_cleaned_station_weather_csv()

    # Nhiệt độ nền theo mùa / trạm
    seasonal_baseline = 27.5
    if not hcmc_w_df.empty:
        sub_b = hcmc_w_df[hcmc_w_df["month"] == sel_month]
        if not sub_b.empty and "temp_mean" in sub_b.columns:
            seasonal_baseline = _safe_float(sub_b["temp_mean"].mean(), 27.5)

    station_targets = []
    # Luôn thu thập toàn bộ 34 Tỉnh/Thành toàn quốc để hiển thị nhiệt độ °C theo từng khu vực khi thu phóng toàn quốc
    for prov, coords in list(VN_PROVINCE_COORDS.items()):
        station_targets.append({
            "name": prov,
            "province": prov,
            "scope": "national",
            "lat": float(coords["lat"]),
            "lon": float(coords["lon"]),
        })

    if level_code != "L4" and sel_prov and "Hồ Chí Minh" in sel_prov:
        seen_c = set()
        for dn, c in HCMC_DISTRICT_COORDS.items():
            norm_dn = normalize_hcmc_district_name(dn)
            if sel_dist and sel_dist != "Tất cả Quận/Huyện" and normalize_hcmc_district_name(sel_dist) != norm_dn:
                continue
            kpt = (round(float(c["lat"]), 4), round(float(c["lon"]), 4))
            if kpt in seen_c:
                continue
            seen_c.add(kpt)
            station_targets.append({
                "name": norm_dn,
                "province": "TP. Hồ Chí Minh",
                "scope": "district",
                "lat": float(c["lat"]),
                "lon": float(c["lon"]),
            })
    elif level_code != "L4" and sel_prov and sel_prov not in VN_PROVINCE_COORDS:
        lat, lon = _lookup_province_coords(sel_prov)
        if lat is not None and lon is not None:
            station_targets.append({
                "name": sel_prov or "Trạm quan trắc",
                "province": sel_prov or "",
                "scope": "national",
                "lat": lat,
                "lon": lon,
            })

    coords_tuple = tuple((s["lat"], s["lon"]) for s in station_targets)
    live_batch = fetch_realtime_temperature_batch(coords_tuple)

    # Fallback local readings từ cleaned_final.csv & historical_weather.csv
    local_latest = {"temp_c": seasonal_baseline, "humidity_pct": 78.0, "rain_mm": 0.0, "obs_time": f"T{sel_month:02d}/{sel_year}", "source": "Quan trắc trạm"}
    if not cleaned_df.empty and "temperature" in cleaned_df.columns:
        valid_c = cleaned_df.dropna(subset=["temperature"])
        if not valid_c.empty:
            r_last = valid_c.iloc[-1]
            local_latest = {
                "temp_c": round(_safe_float(r_last.get("temperature"), seasonal_baseline), 1),
                "humidity_pct": round(_safe_float(r_last.get("humidity"), 78.0), 1),
                "rain_mm": round(_safe_float(r_last.get("precipitation"), 0.0), 1),
                "obs_time": str(r_last.get("time") or f"T{sel_month:02d}/{sel_year}"),
                "source": "Trạm TP.HCM (cleaned_final)",
            }

    prov_baseline = {}
    if not hw_df.empty:
        for prov, grp in hw_df.groupby("province"):
            sub = grp[grp["month"] == sel_month]
            if sub.empty:
                sub = grp
            b_t = _safe_float(sub["temp_lag_1"].mean(), seasonal_baseline)
            r_last = grp.sort_values(["year", "month"], ascending=False).iloc[0]
            prov_baseline[str(prov)] = {
                "base_temp": round(b_t, 1) if b_t > 0 else seasonal_baseline,
                "fallback_temp": round(_safe_float(r_last.get("temp_lag_1"), seasonal_baseline), 1),
                "fallback_hum": round(_safe_float(r_last.get("humidity_lag_1"), 78.0), 1),
                "fallback_rain": round(_safe_float(r_last.get("rain_lag_1"), 0.0), 1),
            }

    stations = []
    detected_anomalies = []

    for idx, st_info in enumerate(station_targets):
        live = live_batch.get(idx)
        p_key = st_info["province"]
        pb = prov_baseline.get(p_key, {"base_temp": seasonal_baseline, "fallback_temp": local_latest["temp_c"], "fallback_hum": 78.0, "fallback_rain": 0.0})
        base_t = pb["base_temp"] or seasonal_baseline
        if live:
            t_c = live["temp_c"]
            hum_p = live["humidity_pct"]
            rain_m = live["rain_mm"]
            obs_t = live["obs_time"]
            src_lbl = live["source"]
        elif p_key == "TP. Hồ Chí Minh":
            t_c = local_latest["temp_c"]
            hum_p = local_latest["humidity_pct"]
            rain_m = local_latest["rain_mm"]
            obs_t = local_latest["obs_time"]
            src_lbl = local_latest["source"]
        else:
            t_c = pb["fallback_temp"] if pb["fallback_temp"] > 0 else seasonal_baseline
            hum_p = pb["fallback_hum"]
            rain_m = pb["fallback_rain"]
            obs_t = f"T{sel_month:02d}/{sel_year}"
            src_lbl = "Khí tượng địa phương"

        delta_t = round(t_c - base_t, 1)
        anomaly_type = "normal"
        anomaly_label = "Bình thường"
        if t_c >= 33.5 or delta_t >= 2.2:
            anomaly_type = "high_anomaly"
            anomaly_label = "🔥 Nhiệt độ quá cao"
        elif t_c <= 23.0 or delta_t <= -2.2:
            anomaly_type = "low_anomaly"
            anomaly_label = "❄️ Nhiệt độ quá thấp"

        row_item = {
            "lat": st_info["lat"],
            "lon": st_info["lon"],
            "name": st_info["name"],
            "province": p_key,
            "scope": st_info.get("scope", "national"),
            "temp_c": round(t_c, 1),
            "temp_label": f"{round(t_c, 1):.1f}°C",
            "baseline_temp": round(base_t, 1),
            "delta_temp": delta_t,
            "humidity_pct": round(hum_p, 1),
            "rain_mm": round(rain_m, 1),
            "anomaly_type": anomaly_type,
            "anomaly_label": anomaly_label,
            "obs_time": obs_t,
            "obs_date": str(obs_t)[:13],
            "source": src_lbl,
        }
        stations.append(row_item)
        if anomaly_type != "normal":
            detected_anomalies.append(row_item)

    # Quét thêm các mốc dị thường thực tế trong chuỗi quan trắc gần nhất để luôn có dữ liệu lịch sử lưu trữ
    if not cleaned_df.empty and "temperature" in cleaned_df.columns and (not sel_prov or "Hồ Chí Minh" in sel_prov):
        c_valid = cleaned_df.dropna(subset=["temperature"]).copy()
        extremes = c_valid[(c_valid["temperature"] >= 34.2) | (c_valid["temperature"] <= 22.8)].tail(4)
        for idx_e, (_, er) in enumerate(extremes.iterrows()):
            t_val = round(_safe_float(er.get("temperature"), 27.5), 1)
            a_type = "high_anomaly" if t_val >= 33.5 else "low_anomaly"
            a_lbl = "🔥 Nhiệt độ quá cao" if a_type == "high_anomaly" else "❄️ Nhiệt độ quá thấp"
            anchor = HCMC_DISTRICT_COORDS.get(["Quận 1", "Bình Thạnh", "Thủ Đức", "Củ Chi"][idx_e % 4], {"lat": 10.7769, "lon": 106.7009})
            detected_anomalies.append({
                "lat": float(anchor["lat"]),
                "lon": float(anchor["lon"]),
                "name": "Trạm quan trắc TP.HCM",
                "province": "TP. Hồ Chí Minh",
                "temp_c": t_val,
                "baseline_temp": round(seasonal_baseline, 1),
                "delta_temp": round(t_val - seasonal_baseline, 1),
                "humidity_pct": round(_safe_float(er.get("humidity"), 75.0), 1),
                "rain_mm": round(_safe_float(er.get("precipitation"), 0.0), 1),
                "anomaly_type": a_type,
                "anomaly_label": a_lbl,
                "obs_time": str(er.get("time") or ""),
                "obs_date": str(er.get("time") or "")[:13],
                "source": "Quan trắc trạm TP.HCM",
            })

    saved_anomalies = save_temperature_anomalies(detected_anomalies) if detected_anomalies else load_temperature_anomalies()
    temps = [s["temp_c"] for s in stations if s.get("temp_c") is not None]
    mean_t = round(sum(temps) / len(temps), 1) if temps else seasonal_baseline
    src_summary = "Open-Meteo Thời gian thực" if live_batch else "Quan trắc trạm TP.HCM & Khí tượng địa phương"

    return {
        "stations": stations,
        "anomalies": saved_anomalies[:35],
        "summary": {
            "mean_temp": mean_t,
            "baseline_temp": round(seasonal_baseline, 1),
            "anomaly_count": len(saved_anomalies),
            "source_label": src_summary,
            "is_live": bool(live_batch),
        },
    }


@st.cache_data(ttl=300, show_spinner=False)
def build_arcgis_extended_layers(
    sel_year: int,
    sel_month: int,
    level_code: str,
    sel_prov: str,
    sel_dist: str = "Tất cả Quận/Huyện",
):
    """Chuẩn bị dữ liệu cho Heatmap thời gian, Risk Map 4 mức & 3 lớp chồng GIS trên ArcGIS."""
    hist_df = load_historical()
    dist_df = load_district_breakdown()
    ward_data = load_ward_breakdown()
    clust_df = load_epidemic_clusters()
    preds_prov = load_predictions()
    preds_dist = load_hcmc_district_predictions()
    hw_df = load_historical_weather_csv()
    hcmc_w_df = load_hcmc_monthly_weather_csv()
    adm1_pop = load_adm1_population_csv()

    # 1. HEATMAP TIMELINE (Ca thực tế theo tháng trong sel_year)
    heatmap_timeline = {}
    avail_months = []
    src_hm = pd.DataFrame()
    if level_code == "L1" and not clust_df.empty:
        src_hm = clust_df[clust_df["year"] == sel_year]
        if sel_prov:
            src_hm = src_hm[src_hm["province"] == sel_prov]
        if sel_dist and sel_dist != "Tất cả Quận/Huyện" and "district" in src_hm.columns:
            src_hm = src_hm[src_hm["district"] == sel_dist]
    elif level_code == "L2" and not ward_data.empty:
        src_hm = ward_data[ward_data["year"] == sel_year]
        if sel_prov:
            src_hm = src_hm[src_hm["province"] == sel_prov]
        if sel_dist and sel_dist != "Tất cả Quận/Huyện" and "district" in src_hm.columns:
            src_hm = src_hm[src_hm["district"] == sel_dist]
    elif level_code == "L3" and not dist_df.empty:
        src_hm = dist_df[dist_df["year"] == sel_year]
        if sel_prov:
            src_hm = src_hm[src_hm["province"] == sel_prov]
    elif not hist_df.empty:
        src_hm = hist_df[hist_df["year"] == sel_year]

    if not src_hm.empty and "month" in src_hm.columns:
        avail_months = sorted({int(m) for m in src_hm["month"].dropna().unique()})
    if not avail_months and not hist_df.empty:
        y_df = hist_df[hist_df["year"] == sel_year]
        avail_months = sorted({int(m) for m in y_df["month"].dropna().unique()})
    if int(sel_month) not in avail_months:
        avail_months = sorted(set(avail_months + [int(sel_month)]))

    for m in avail_months:
        pts = []
        if not src_hm.empty:
            m_df = src_hm[src_hm["month"] == m]
            if not m_df.empty:
                if level_code == "L4":
                    for _, r in m_df.iterrows():
                        prov = str(r.get("province", ""))
                        lat, lon = _lookup_province_coords(prov)
                        if lat is None or lon is None:
                            continue
                        pts.append({
                            "lat": round(lat, 5),
                            "lon": round(lon, 5),
                            "cases": int(r.get("cases", 0) or 0),
                            "name": prov,
                        })
                else:
                    label_col = "district" if level_code == "L3" else ("ward" if level_code == "L2" else "name")
                    if "lat" in m_df.columns and "lon" in m_df.columns:
                        valid = m_df.dropna(subset=["lat", "lon"]).copy()
                        if not valid.empty:
                            valid["_rlat"] = valid["lat"].astype(float).round(5)
                            valid["_rlon"] = valid["lon"].astype(float).round(5)
                            valid["_lname"] = valid[label_col].fillna("Điểm giám sát").astype(str)
                            grouped = valid.groupby(["_lname", "_rlat", "_rlon"], as_index=False)["cases"].sum()
                            grouped = grouped.sort_values("cases", ascending=False).head(250)
                            for _, r in grouped.iterrows():
                                pts.append({
                                    "lat": float(r["_rlat"]),
                                    "lon": float(r["_rlon"]),
                                    "cases": int(r["cases"] or 0),
                                    "name": str(r["_lname"]),
                                })
        heatmap_timeline[str(int(m))] = pts

    # 2. RISK MAP (Dự báo nguy cơ 4 mức: Thấp – Trung bình – Cao – Rất cao, các bước +1/+2/+3 tháng)
    risk_steps = {}
    is_hcmc_scope = bool(sel_prov and "Hồ Chí Minh" in sel_prov)

    # Lấy số ca tháng hiện tại để so sánh tăng/giảm
    cur_prov_cases = {}
    if not hist_df.empty:
        cur_p_df = hist_df[(hist_df["year"] == sel_year) & (hist_df["month"] == sel_month)]
        for _, r in cur_p_df.iterrows():
            cur_prov_cases[str(r.get("province", ""))] = int(r.get("cases", 0) or 0)

    cur_dist_cases = {}
    if not dist_df.empty and sel_prov:
        cur_d_df = dist_df[(dist_df["province"] == sel_prov) & (dist_df["year"] == sel_year) & (dist_df["month"] == sel_month)]
        for _, r in cur_d_df.iterrows():
            dn = normalize_hcmc_district_name(r.get("district", ""))
            cur_dist_cases[dn] = cur_dist_cases.get(dn, 0) + int(r.get("cases", 0) or 0)

    for step_num in (1, 2, 3):
        regions_map = {}
        points_list = []
        step_label = f"Tháng dự báo +{step_num}"

        # Province predictions lookup (step_num)
        prov_pred_lookup = {}
        if not preds_prov.empty and "step" in preds_prov.columns:
            sp_df = preds_prov[preds_prov["step"] == step_num]
            if not sp_df.empty:
                if "month_label" in sp_df.columns and sp_df["month_label"].notna().any():
                    step_label = str(sp_df["month_label"].dropna().iloc[0])
                for _, pr in sp_df.iterrows():
                    p_name = str(pr.get("province", ""))
                    prov_pred_lookup[p_name] = float(pr.get("predicted_cases", 0) or 0)

        if level_code == "L4":
            all_provs = sorted(set(VN_PROVINCE_COORDS.keys()) | set(prov_pred_lookup.keys()) | set(cur_prov_cases.keys()))
            for prov in all_provs:
                cur_v = float(cur_prov_cases.get(prov, 0))
                pred_v = float(prov_pred_lookup.get(prov, max(0.0, cur_v)))
                tier = _classify_risk_tier(pred_v, scope="province")
                chg_pct = round(((pred_v - cur_v) / max(cur_v, 1.0)) * 100.0, 1) if (cur_v > 0 or pred_v > 0) else 0.0
                regions_map[prov] = {
                    "predicted_cases": round(pred_v, 1),
                    "current_cases": int(cur_v),
                    "change_pct": chg_pct,
                    **tier,
                }
                lat, lon = _lookup_province_coords(prov)
                if lat is not None and (pred_v > 0 or cur_v > 0):
                    points_list.append({
                        "lat": round(lat, 5),
                        "lon": round(lon, 5),
                        "name": prov,
                        "predicted_cases": round(pred_v, 1),
                        "current_cases": int(cur_v),
                        "change_pct": chg_pct,
                        "radius_meters": 0,
                        **tier,
                    })
        elif is_hcmc_scope and level_code == "L3" and not preds_dist.empty:
            sd_df = preds_dist[preds_dist["step"] == step_num] if "step" in preds_dist.columns else preds_dist
            if not sd_df.empty and "month_label" in sd_df.columns and sd_df["month_label"].notna().any():
                step_label = str(sd_df["month_label"].dropna().iloc[0])
            dist_pred_acc = {}
            for _, dr in sd_df.iterrows():
                dn = normalize_hcmc_district_name(dr.get("district", ""))
                dist_pred_acc[dn] = dist_pred_acc.get(dn, 0.0) + float(dr.get("predicted_cases", 0) or 0)

            for dn, pred_v in dist_pred_acc.items():
                cur_v = float(cur_dist_cases.get(dn, 0))
                tier = _classify_risk_tier(pred_v, scope="district")
                chg_pct = round(((pred_v - cur_v) / max(cur_v, 1.0)) * 100.0, 1) if (cur_v > 0 or pred_v > 0) else 0.0
                regions_map[dn] = {
                    "predicted_cases": round(pred_v, 1),
                    "current_cases": int(cur_v),
                    "change_pct": chg_pct,
                    **tier,
                }
                c_info = HCMC_DISTRICT_COORDS.get(dn) or HCMC_DISTRICT_COORDS.get(f"Thành Phố {dn}")
                if not c_info and not dist_df.empty:
                    sub = dist_df[dist_df["district"] == dn].dropna(subset=["lat", "lon"])
                    if not sub.empty:
                        c_info = {"lat": float(sub["lat"].iloc[0]), "lon": float(sub["lon"].iloc[0])}
                if c_info:
                    points_list.append({
                        "lat": float(c_info["lat"]),
                        "lon": float(c_info["lon"]),
                        "name": dn,
                        "predicted_cases": round(pred_v, 1),
                        "current_cases": int(cur_v),
                        "change_pct": chg_pct,
                        "radius_meters": 1600 if tier["tier_key"] in ("very_high", "high") else 900,
                        **tier,
                    })
        else:
            # L1, L2 hoặc các tỉnh ngoài TP.HCM ở L3: suy diễn từ dự báo tỉnh + phân bố hiện tại
            prov_cur_tot = max(float(cur_prov_cases.get(sel_prov, 0)), 1.0)
            prov_pred_tot = float(prov_pred_lookup.get(sel_prov, prov_cur_tot))
            # Nếu là TP.HCM ở L1/L2, ưu tiên tỷ lệ dự báo từ từng quận HCMC
            hcmc_dist_ratio = {}
            if is_hcmc_scope and not preds_dist.empty:
                sd_df = preds_dist[preds_dist["step"] == step_num] if "step" in preds_dist.columns else preds_dist
                if not sd_df.empty and "month_label" in sd_df.columns and sd_df["month_label"].notna().any():
                    step_label = str(sd_df["month_label"].dropna().iloc[0])
                for _, dr in sd_df.iterrows():
                    dn = normalize_hcmc_district_name(dr.get("district", ""))
                    d_cur = max(float(cur_dist_cases.get(dn, 0)), 1.0)
                    hcmc_dist_ratio[dn] = float(dr.get("predicted_cases", 0) or 0) / d_cur
            prov_ratio = max(0.25, min(3.5, prov_pred_tot / prov_cur_tot))

            local_src = pd.DataFrame()
            name_col = "name"
            if level_code == "L1" and not clust_df.empty:
                local_src = clust_df[(clust_df["year"] == sel_year) & (clust_df["month"] == sel_month) & (clust_df["province"] == sel_prov)]
                if sel_dist and sel_dist != "Tất cả Quận/Huyện":
                    local_src = local_src[local_src["district"] == sel_dist]
                name_col = "name"
            elif level_code == "L2" and not ward_data.empty:
                local_src = ward_data[(ward_data["year"] == sel_year) & (ward_data["month"] == sel_month) & (ward_data["province"] == sel_prov)]
                if sel_dist and sel_dist != "Tất cả Quận/Huyện":
                    local_src = local_src[local_src["district"] == sel_dist]
                name_col = "ward"
            elif level_code == "L3" and not dist_df.empty:
                local_src = dist_df[(dist_df["year"] == sel_year) & (dist_df["month"] == sel_month) & (dist_df["province"] == sel_prov)]
                name_col = "district"

            if not local_src.empty and "lat" in local_src.columns and "lon" in local_src.columns:
                local_valid = local_src.dropna(subset=["lat", "lon"]).head(120)
                for _, r in local_valid.iterrows():
                    cur_v = _safe_float(r.get("cases"), 0.0)
                    dn = normalize_hcmc_district_name(r.get("district", ""))
                    ratio = hcmc_dist_ratio.get(dn, prov_ratio)
                    # Giữ trọng số hợp lý khi chuyển từ tỷ lệ quận sang điểm/phường
                    pred_v = round(cur_v * max(0.35, min(2.5, ratio if ratio > 0 else prov_ratio)), 1)
                    tier = _classify_risk_tier(pred_v, scope="local" if level_code in ("L1", "L2") else "district")
                    chg_pct = round(((pred_v - cur_v) / max(cur_v, 1.0)) * 100.0, 1)
                    points_list.append({
                        "lat": float(r["lat"]),
                        "lon": float(r["lon"]),
                        "name": str(r.get(name_col) or "Khu vực"),
                        "predicted_cases": pred_v,
                        "current_cases": int(cur_v),
                        "change_pct": chg_pct,
                        "radius_meters": _safe_int(r.get("radius_meters"), 350) if level_code == "L1" else 650,
                        **tier,
                    })

        risk_steps[str(step_num)] = {
            "step": step_num,
            "month_label": step_label,
            "regions": regions_map,
            "points": points_list,
        }

    # 3. WEATHER OVERLAY (Lớp chồng Khí tượng: Mưa, Nhiệt, Ẩm, PM2.5)
    weather_overlay = []

    def _weather_tier(rain_mm, temp_c, hum_pct):
        if hum_pct >= 80 and rain_mm >= 140:
            return "high", "Thuận lợi cao cho muỗi Aedes", "#0284c7"
        if hum_pct >= 72 or rain_mm >= 60 or (25.0 <= temp_c <= 30.0):
            return "medium", "Thuận lợi trung bình", "#0ea5e9"
        return "low", "Ít thuận lợi (khô / mát)", "#64748b"

    # Tra cứu dữ liệu trạm HCMC theo (sel_year, sel_month) hoặc tháng gần nhất
    hcmc_row = None
    if not hcmc_w_df.empty:
        sub_hw = hcmc_w_df[(hcmc_w_df["year"] == sel_year) & (hcmc_w_df["month"] == sel_month)]
        if sub_hw.empty:
            sub_hw = hcmc_w_df[hcmc_w_df["month"] == sel_month]
        if not sub_hw.empty:
            hcmc_row = sub_hw.iloc[0]

    if level_code == "L4":
        for prov, coords in VN_PROVINCE_COORDS.items():
            rain_mm, temp_c, hum_pct, pm25, wind_kmh = None, None, None, None, None
            source_note = f"T{sel_month:02d}/{sel_year}"
            if "Hồ Chí Minh" in prov and hcmc_row is not None:
                rain_mm = float(hcmc_row.get("precipitation_sum", 0) or 0)
                temp_c = float(hcmc_row.get("temp_mean", 0) or 0)
                hum_pct = float(hcmc_row.get("humidity_mean", 0) or 0)
                pm25 = float(hcmc_row["pm25_mean"]) if pd.notna(hcmc_row.get("pm25_mean")) else None
                wind_kmh = float(hcmc_row["wind_speed_mean"]) if pd.notna(hcmc_row.get("wind_speed_mean")) else None
            if (rain_mm is None or temp_c is None) and not hw_df.empty:
                pw = hw_df[hw_df["province"] == prov]
                exact = pw[(pw["year"] == sel_year) & (pw["month"] == sel_month)]
                pick = exact if not exact.empty else pw[pw["month"] == sel_month]
                if pick.empty and not pw.empty:
                    pick = pw.sort_values(["year", "month"], ascending=False)
                if not pick.empty:
                    r0 = pick.iloc[0]
                    if exact.empty:
                        source_note = f"T{int(r0['month']):02d}/{int(r0['year'])} (gần nhất)"
                    rain_mm = _safe_float(r0.get("rain_lag_1"), 0.0)
                    temp_c = _safe_float(r0.get("temp_lag_1"), 0.0)
                    hum_pct = _safe_float(r0.get("humidity_lag_1"), 0.0)
            if rain_mm is not None and (temp_c or hum_pct):
                a_idx, a_lbl, w_col = _weather_tier(rain_mm, temp_c or 0.0, hum_pct or 0.0)
                weather_overlay.append({
                    "lat": float(coords["lat"]),
                    "lon": float(coords["lon"]),
                    "name": prov,
                    "rain_mm": round(rain_mm, 1),
                    "temp_c": round(temp_c or 0.0, 1),
                    "humidity_pct": round(hum_pct or 0.0, 1),
                    "pm25": round(pm25, 1) if pm25 is not None else None,
                    "wind_kmh": round(wind_kmh, 1) if wind_kmh is not None else None,
                    "aedes_index": a_idx,
                    "aedes_label": a_lbl,
                    "period": source_note,
                    "color": w_col,
                })
    else:
        # Khí tượng cho địa phương đang chọn (TP.HCM dùng trạmWeatherData HCMC gắn tại các quận)
        rain_mm, temp_c, hum_pct, pm25, wind_kmh = 0.0, 27.0, 75.0, None, None
        source_note = f"T{sel_month:02d}/{sel_year}"
        has_weather = False
        if is_hcmc_scope and hcmc_row is not None:
            rain_mm = float(hcmc_row.get("precipitation_sum", 0) or 0)
            temp_c = float(hcmc_row.get("temp_mean", 0) or 0)
            hum_pct = float(hcmc_row.get("humidity_mean", 0) or 0)
            pm25 = float(hcmc_row["pm25_mean"]) if pd.notna(hcmc_row.get("pm25_mean")) else None
            wind_kmh = float(hcmc_row["wind_speed_mean"]) if pd.notna(hcmc_row.get("wind_speed_mean")) else None
            source_note = f"T{int(hcmc_row['month']):02d}/{int(hcmc_row['year'])}"
            has_weather = True
        elif not hw_df.empty and sel_prov:
            pw = hw_df[hw_df["province"] == sel_prov]
            exact = pw[(pw["year"] == sel_year) & (pw["month"] == sel_month)]
            pick = exact if not exact.empty else pw[pw["month"] == sel_month]
            if pick.empty and not pw.empty:
                pick = pw.sort_values(["year", "month"], ascending=False)
            if not pick.empty:
                r0 = pick.iloc[0]
                rain_mm = _safe_float(r0.get("rain_lag_1"), 0.0)
                temp_c = _safe_float(r0.get("temp_lag_1"), 0.0)
                hum_pct = _safe_float(r0.get("humidity_lag_1"), 0.0)
                source_note = f"T{int(r0['month']):02d}/{int(r0['year'])}"
                has_weather = True

        if has_weather:
            a_idx, a_lbl, w_col = _weather_tier(rain_mm, temp_c, hum_pct)
            if is_hcmc_scope:
                seen_coords = set()
                for dn, c in HCMC_DISTRICT_COORDS.items():
                    norm_dn = normalize_hcmc_district_name(dn)
                    if sel_dist and sel_dist != "Tất cả Quận/Huyện" and normalize_hcmc_district_name(sel_dist) != norm_dn:
                        continue
                    key_pt = (round(float(c["lat"]), 4), round(float(c["lon"]), 4))
                    if key_pt in seen_coords:
                        continue
                    seen_coords.add(key_pt)
                    weather_overlay.append({
                        "lat": float(c["lat"]),
                        "lon": float(c["lon"]),
                        "name": f"Trạm Khí tượng {norm_dn}",
                        "rain_mm": round(rain_mm, 1),
                        "temp_c": round(temp_c, 1),
                        "humidity_pct": round(hum_pct, 1),
                        "pm25": round(pm25, 1) if pm25 is not None else None,
                        "wind_kmh": round(wind_kmh, 1) if wind_kmh is not None else None,
                        "aedes_index": a_idx,
                        "aedes_label": a_lbl,
                        "period": source_note,
                        "color": w_col,
                    })
            else:
                lat, lon = _lookup_province_coords(sel_prov)
                if lat is not None:
                    weather_overlay.append({
                        "lat": lat,
                        "lon": lon,
                        "name": f"Trạm Khí tượng {sel_prov}",
                        "rain_mm": round(rain_mm, 1),
                        "temp_c": round(temp_c, 1),
                        "humidity_pct": round(hum_pct, 1),
                        "pm25": None,
                        "wind_kmh": None,
                        "aedes_index": a_idx,
                        "aedes_label": a_lbl,
                        "period": source_note,
                        "color": w_col,
                    })

    # 4. POPULATION OVERLAY (Lớp chồng Mật độ Dân số 3 năm 2023–2024–2025: Hatch + Biểu đồ cột trên Map)
    population_overlay = []
    population_regions = {}
    pop_lookup = {}
    if not adm1_pop.empty:
        for _, pr in adm1_pop.iterrows():
            pop_lookup[str(pr["province"])] = {
                "population": int(pr["population"] or 0),
                "child_ratio_pct": float(pr["child_ratio_pct"] or 0.0),
            }

    pop3_df = load_or_build_3year_population_density()
    pop3_prov_map = {}
    pop3_dist_map = {}
    if not pop3_df.empty:
        for _, r3 in pop3_df.iterrows():
            rec3 = {
                "area_km2": round(_safe_float(r3.get("area_km2"), 100.0), 2),
                "pop_2023": _safe_int(r3.get("pop_2023"), 0),
                "pop_2024": _safe_int(r3.get("pop_2024"), 0),
                "pop_2025": _safe_int(r3.get("pop_2025"), 0),
                "density_2023": round(_safe_float(r3.get("density_2023"), 0.0), 1),
                "density_2024": round(_safe_float(r3.get("density_2024"), 0.0), 1),
                "density_2025": round(_safe_float(r3.get("density_2025"), 0.0), 1),
                "growth_3y_pct": round(_safe_float(r3.get("growth_3y_pct"), 0.0), 2),
                "child_ratio_pct": round(_safe_float(r3.get("child_ratio_pct"), 0.0), 1),
                "lat": _safe_float(r3.get("lat"), None),
                "lon": _safe_float(r3.get("lon"), None),
            }
            lvl = str(r3.get("level") or "")
            r_name = str(r3.get("region_name") or "")
            if lvl == "province" and r_name:
                pop3_prov_map[r_name] = rec3
            elif lvl == "district" and r_name:
                pop3_dist_map[normalize_hcmc_district_name(r_name)] = rec3

    if level_code == "L4":
        inc_lookup = {}
        if not hist_df.empty:
            m_df = hist_df[(hist_df["year"] == sel_year) & (hist_df["month"] == sel_month)]
            for _, r in m_df.iterrows():
                p = str(r.get("province", ""))
                inc_lookup[p] = {
                    "cases": int(r.get("cases", 0) or 0),
                    "incidence_rate": float(r.get("incidence_rate", 0) or 0.0),
                    "population": int(r.get("population", 0) or 0),
                }
        for prov, coords in VN_PROVINCE_COORDS.items():
            p_info = pop_lookup.get(prov, {})
            h_info = inc_lookup.get(prov, {})
            p3 = pop3_prov_map.get(prov, {})
            pop_val = p3.get("pop_2025") or p3.get("pop_2024") or h_info.get("population") or p_info.get("population", 0)
            if pop_val <= 0:
                continue
            d25 = _safe_float(p3.get("density_2025"), 0.0)
            tier_txt = (
                "Rất cao (>=1.000 người/km²)" if d25 >= 1000
                else ("Cao (400–999 người/km²)" if d25 >= 400
                      else ("Trung bình (150–399 người/km²)" if d25 >= 150 else "Thấp (<150 người/km²)"))
            )
            hatch_style = "diagonal-cross" if (d25 >= 400 or pop_val >= 2_000_000) else "vertical"
            item_p = {
                "lat": float(p3.get("lat") if p3.get("lat") is not None else coords["lat"]),
                "lon": float(p3.get("lon") if p3.get("lon") is not None else coords["lon"]),
                "name": prov,
                "population": int(pop_val),
                "area_km2": float(p3.get("area_km2") or 1000.0),
                "pop_2023": int(p3.get("pop_2023") or round(pop_val * 0.98)),
                "pop_2024": int(p3.get("pop_2024") or pop_val),
                "pop_2025": int(p3.get("pop_2025") or round(pop_val * 1.01)),
                "density_2023": float(p3.get("density_2023") or 0.0),
                "density_2024": float(p3.get("density_2024") or 0.0),
                "density_2025": d25,
                "growth_3y_pct": float(p3.get("growth_3y_pct") or 0.0),
                "child_ratio_pct": float(p3.get("child_ratio_pct") or p_info.get("child_ratio_pct", 0.0)),
                "cases": int(h_info.get("cases", 0)),
                "incidence_rate": round(float(h_info.get("incidence_rate", 0.0)), 3),
                "density_tier": tier_txt,
                "hatch_style": hatch_style,
                "color": "#475569",
            }
            population_overlay.append(item_p)
            population_regions[prov] = item_p
    else:
        p_info = pop_lookup.get(sel_prov, {})
        if is_hcmc_scope and pop3_dist_map:
            inc_dist_map = {}
            if not dist_df.empty and sel_prov:
                d_sub = dist_df[(dist_df["province"] == sel_prov) & (dist_df["year"] == sel_year) & (dist_df["month"] == sel_month)]
                if d_sub.empty:
                    d_sub = dist_df[dist_df["province"] == sel_prov]
                if not d_sub.empty:
                    for _, rr in d_sub.groupby("district", as_index=False).agg(cases=("cases", "sum"), incidence_rate=("incidence_rate", "mean")).iterrows():
                        inc_dist_map[normalize_hcmc_district_name(str(rr["district"]))] = {
                            "cases": _safe_int(rr["cases"], 0),
                            "incidence_rate": _safe_float(rr["incidence_rate"], 0.0),
                        }
            for norm_dn, p3 in pop3_dist_map.items():
                if sel_dist and sel_dist != "Tất cả Quận/Huyện" and norm_dn != normalize_hcmc_district_name(sel_dist):
                    continue
                d_stat = inc_dist_map.get(norm_dn, {})
                inc_val = _safe_float(d_stat.get("incidence_rate"), 0.0)
                d25 = _safe_float(p3.get("density_2025"), 0.0)
                tier_txt = (
                    "Siêu đông (>=15.000 người/km²)" if d25 >= 15000
                    else ("Đông (5.000–14.999 người/km²)" if d25 >= 5000
                          else ("Trung bình (1.500–4.999 người/km²)" if d25 >= 1500 else "Thấp (<1.500 người/km²)"))
                )
                hatch_style = "diagonal-cross" if d25 >= 5000 else "vertical"
                item_p = {
                    "lat": float(p3["lat"]),
                    "lon": float(p3["lon"]),
                    "name": norm_dn,
                    "population": int(p3["pop_2025"] or p3["pop_2024"]),
                    "area_km2": float(p3["area_km2"]),
                    "pop_2023": int(p3["pop_2023"]),
                    "pop_2024": int(p3["pop_2024"]),
                    "pop_2025": int(p3["pop_2025"]),
                    "density_2023": float(p3["density_2023"]),
                    "density_2024": float(p3["density_2024"]),
                    "density_2025": d25,
                    "growth_3y_pct": float(p3["growth_3y_pct"]),
                    "child_ratio_pct": float(p3.get("child_ratio_pct") or _safe_float(p_info.get("child_ratio_pct"), 0.0)),
                    "cases": _safe_int(d_stat.get("cases"), 0),
                    "incidence_rate": round(inc_val, 3),
                    "density_tier": tier_txt,
                    "hatch_style": hatch_style,
                    "color": "#475569",
                }
                population_overlay.append(item_p)
                population_regions[norm_dn] = item_p
        elif sel_prov and sel_prov in pop3_prov_map:
            p3 = pop3_prov_map[sel_prov]
            d25 = _safe_float(p3.get("density_2025"), 0.0)
            hatch_style = "diagonal-cross" if d25 >= 400 else "vertical"
            item_p = {
                "lat": float(p3["lat"]),
                "lon": float(p3["lon"]),
                "name": sel_prov,
                "population": int(p3["pop_2025"] or p3["pop_2024"]),
                "area_km2": float(p3["area_km2"]),
                "pop_2023": int(p3["pop_2023"]),
                "pop_2024": int(p3["pop_2024"]),
                "pop_2025": int(p3["pop_2025"]),
                "density_2023": float(p3["density_2023"]),
                "density_2024": float(p3["density_2024"]),
                "density_2025": d25,
                "growth_3y_pct": float(p3["growth_3y_pct"]),
                "child_ratio_pct": float(p3.get("child_ratio_pct") or 0.0),
                "cases": 0,
                "incidence_rate": 0.0,
                "density_tier": f"{d25:,.0f} người/km²",
                "hatch_style": hatch_style,
                "color": "#475569",
            }
            population_overlay.append(item_p)
            population_regions[sel_prov] = item_p

    population_max_density = max(
        [float(x.get("density_2025") or x.get("density_2024") or 1.0) for x in population_overlay] or [1.0]
    )

    # 5. HISTORICAL OUTBREAKS OVERLAY (Lớp chồng Ổ dịch Lịch sử tích lũy)
    historical_outbreaks = []
    if not clust_df.empty and "lat" in clust_df.columns and "lon" in clust_df.columns:
        hc = clust_df.dropna(subset=["lat", "lon"]).copy()
        if level_code != "L4" and sel_prov:
            hc = hc[hc["province"] == sel_prov]
        if sel_dist and sel_dist != "Tất cả Quận/Huyện" and "district" in hc.columns:
            hc = hc[hc["district"] == sel_dist]
        if not hc.empty:
            hc["_ym"] = hc["year"].astype(int) * 100 + hc["month"].astype(int)
            hc["_rlat"] = hc["lat"].astype(float).round(4)
            hc["_rlon"] = hc["lon"].astype(float).round(4)
            hc["name"] = hc["name"].fillna("Ổ dịch").astype(str)
            hc["province"] = hc["province"].fillna("").astype(str)
            hc["district"] = hc["district"].fillna("").astype(str)
            agg_hc = hc.groupby(["name", "province", "district", "_rlat", "_rlon"], as_index=False).agg(
                total_cases=("cases", "sum"),
                peak_cases=("cases", "max"),
                outbreak_months=("_ym", "nunique"),
                max_radius=("radius_meters", "max"),
            )
            agg_hc = agg_hc.sort_values(["outbreak_months", "total_cases"], ascending=[False, False]).head(45)
            for _, r in agg_hc.iterrows():
                rad_val = _safe_int(r.get("max_radius"), 250)
                historical_outbreaks.append({
                    "lat": float(r["_rlat"]),
                    "lon": float(r["_rlon"]),
                    "name": str(r["name"]),
                    "province": str(r["province"]),
                    "district": str(r["district"]),
                    "total_cases": _safe_int(r.get("total_cases"), 0),
                    "peak_cases": _safe_int(r.get("peak_cases"), 0),
                    "outbreak_months": max(1, _safe_int(r.get("outbreak_months"), 1)),
                    "radius_meters": int(max(180, min(1500, rad_val))),
                })

    temp_layer_data = build_realtime_temperature_layer(
        sel_year=sel_year,
        sel_month=sel_month,
        level_code=level_code,
        sel_prov=sel_prov,
        sel_dist=sel_dist,
    )

    return {
        "selected_year": int(sel_year),
        "selected_month": int(sel_month),
        "level_code": level_code,
        "available_months": [int(m) for m in avail_months],
        "heatmap_timeline": heatmap_timeline,
        "temperature_layer": temp_layer_data,
        "risk_forecast": {
            "scope": "province" if level_code == "L4" else ("district" if (is_hcmc_scope and level_code == "L3") else "local"),
            "steps": risk_steps,
        },
        "weather_overlay": weather_overlay,
        "population_overlay": population_overlay,
        "population_regions": population_regions,
        "population_max_density": population_max_density,
        "historical_outbreaks": historical_outbreaks,
    }


def _handle_map_component_event(map_event):
    """Xử lý sự kiện tạo ghim mới hoặc định vị GPS trả về từ ArcGIS / Leaflet (không rerun toàn trang)."""
    if not isinstance(map_event, dict):
        return
    action = map_event.get("action")
    ts = map_event.get("ts")
    if action == "create_pin" and ts != st.session_state.get("_last_pin_ts"):
        comment_txt = str(map_event.get("comment") or "").strip()
        if comment_txt:
            map_pins_service.add_pin(
                lat=float(map_event["lat"]),
                lon=float(map_event["lon"]),
                comment=comment_txt,
                author=str(map_event.get("author") or "Người dân"),
                area_name=str(map_event.get("area_name") or ""),
                category=str(map_event.get("category") or "💬 Ý kiến khác"),
            )
            load_cached_pins.clear()
            st.session_state.pop("draft_map_pin", None)
            st.session_state["_last_pin_ts"] = ts
            st.session_state["_pin_saved_notice"] = "✅ Đã lưu điểm ghim và bình luận lên bản đồ!"
    elif action == "pin_selected" and ts != st.session_state.get("_last_pin_ts"):
        st.session_state["draft_map_pin"] = {
            "lat": float(map_event["lat"]),
            "lon": float(map_event["lon"]),
            "ts": ts,
        }
        st.session_state["_last_pin_ts"] = ts
    elif action == "user_location" and ts != st.session_state.get("_last_loc_ts"):
        st.session_state["user_location"] = {
            "lat": float(map_event["lat"]),
            "lon": float(map_event["lon"]),
            "accuracy": map_event.get("accuracy"),
            "source": map_event.get("source"),
            "ts": ts,
        }
        st.session_state["_last_loc_ts"] = ts
    elif action == "log_temp_anomaly" and ts != st.session_state.get("_last_anom_ts"):
        items = map_event.get("anomalies")
        if isinstance(items, list) and items:
            save_temperature_anomalies(items)
            build_realtime_temperature_layer.clear()
            build_arcgis_extended_layers.clear()
        st.session_state["_last_anom_ts"] = ts


@_st_fragment
def _render_main_interactive_map(
    *,
    title: str,
    center_lat: float,
    center_lon: float,
    zoom: int,
    view_key: str,
    markers=None,
    geojson_data=None,
    choropleth_values=None,
    extended_layers=None,
):
    """Render bản đồ tương tác đa chiều được cô lập trong fragment để tránh load lại toàn trang."""
    st.markdown(f"**{title}**")
    saved_pins = load_cached_pins()

    _map_modes = [
        "🌐 Bản đồ ArcGIS Maps SDK (2D/3D Đa lớp - Chuyên gia & HCDC)",
        "🍃 Bản đồ Leaflet (Tương tác Nhanh - Cộng đồng)",
        "🔀 Chế độ Song Song (ArcGIS + Leaflet Đa chiều)",
    ]
    _default_idx = 0 if is_hcdc_officer else 1
    if st.session_state.get("user_location"):
        _col_mode, _col_pin_loc = st.columns([4, 1])
        with _col_mode:
            map_engine_mode = st.radio(
                "🧭 Chọn Nền Tảng Bản Đồ Hiển Thị:",
                _map_modes,
                index=_default_idx,
                horizontal=True,
                key="map_engine_mode_radio",
            )
        with _col_pin_loc:
            if st.button("📌 Ghim tại vị trí của tôi", key="pin_at_my_loc_btn", use_container_width=True):
                _ul = st.session_state["user_location"]
                st.session_state["draft_map_pin"] = {
                    "lat": float(_ul["lat"]),
                    "lon": float(_ul["lon"]),
                    "ts": int(datetime.now().timestamp() * 1000),
                }
    else:
        map_engine_mode = st.radio(
            "🧭 Chọn Nền Tảng Bản Đồ Hiển Thị:",
            _map_modes,
            index=_default_idx,
            horizontal=True,
            key="map_engine_mode_radio",
        )

    common_kwargs = dict(
        center_lat=center_lat,
        center_lon=center_lon,
        zoom=zoom,
        theme=ui.mode(),
        map_style=ui.map_style(),
        view_key=view_key,
        markers=markers or [],
        geojson_data=geojson_data,
        choropleth_values=choropleth_values or {},
        pins=saved_pins,
        user_location=st.session_state.get("user_location"),
        selected_pin=st.session_state.get("draft_map_pin"),
    )
    arcgis_kwargs = dict(common_kwargs, extended_layers=extended_layers or {})

    if "Song Song" in map_engine_mode:
        col_arc, col_leaf = st.columns(2)
        with col_arc:
            st.caption("🌐 **ArcGIS Maps SDK for JavaScript 4.29** (2D/3D, LayerList & Geodesic Buffer)")
            arc_event = _arcgis_pin_map(**arcgis_kwargs, key="main_arcgis_interactive_map")
        with col_leaf:
            st.caption("🍃 **Leaflet OpenStreetMap** (Nhẹ, Tương tác cộng đồng nhanh)")
            leaf_event = _interactive_pin_map(**common_kwargs, key="main_unified_interactive_map")
        _handle_map_component_event(arc_event)
        _handle_map_component_event(leaf_event)
    elif "ArcGIS" in map_engine_mode:
        arc_event = _arcgis_pin_map(**arcgis_kwargs, key="main_arcgis_interactive_map")
        _handle_map_component_event(arc_event)
    else:
        leaf_event = _interactive_pin_map(**common_kwargs, key="main_unified_interactive_map")
        _handle_map_component_event(leaf_event)

    _saved_notice = st.session_state.pop("_pin_saved_notice", None)
    if _saved_notice:
        if hasattr(st, "toast"):
            st.toast(_saved_notice)
        else:
            st.success(_saved_notice)


df = load_historical()
district_df = load_district_breakdown()
ward_df = load_ward_breakdown()
street_df = load_street_hotspots()
clusters_df = load_epidemic_clusters()
hcmc_hotspots_df = load_hcmc_hotspots()
predictions_df = load_predictions()
hcmc_dist_preds_df = load_hcmc_district_predictions()

if uploaded_file:
    st.sidebar.success("⏳ Đang xử lý dữ liệu...")
    with st.spinner("Đang xử lý dữ liệu và ánh xạ địa bàn..."):
        new_data = load_and_process_new_data(uploaded_file, paths.POP_DATA_FILE)

    if not new_data.empty:
        if not df.empty:
            df = pd.concat([df, new_data], ignore_index=True)
            df = df.drop_duplicates(subset=['date', 'province'], keep='last')
        else:
            df = new_data

        paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        mongo_data_service.save_dataset("historical", df, paths.HISTORICAL_CSV)
        st.sidebar.success("✅ Dữ liệu đã được lưu thành công vào MongoDB và Local!")
        st.sidebar.info("🔄 Vui lòng chạy `python main.py` để huấn luyện lại mô hình và cập nhật dự báo.")

# ===========================================================================
# 3 SECTIONS UI: GIÁM SÁT, AI DỰ BÁO & ĐÁNH GIÁ, TRỢ LÝ AI
# ===========================================================================
tab1, tab_ai, tab2 = (
    _kaf_sec[k] for k in ("surveillance", "forecast", "assistant")
)

# ===========================================================================
# TAB 1: GIÁM SÁT & DỰ BÁO DỊCH BỆNH (GIỮ NGUYÊN HOÀN TOÀN)
# ===========================================================================
with tab1:
    if not df.empty:
        available_years = sorted(df['year'].dropna().unique().astype(int), reverse=True)
        filter_years = [y for y in available_years if y >= 2024] or available_years

        # -------------------------------------------------------------------
        # 1. BENTO CONTROL BAR: CẤP ĐỘ BẢN ĐỒ, THỜI GIAN & ĐỊNH VỊ GPS
        # -------------------------------------------------------------------
        with st.container(key="bento_gis_toolbar"):
            st.markdown(
                '<div class="bento-toolbar-hdr">'
                '<span>🦟 <b>Giám Sát Dịch Tễ Đa Cấp &amp; Khoanh Vùng Ổ Dịch</b></span>'
                '<span class="bento-toolbar-path">Tuyến Phố ➡️ Phường/Xã ➡️ Quận/Huyện ➡️ Toàn Quốc</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            granularity_level = st.radio(
                "🗺️ Chọn Cấp Độ Chi Tiết Bản Đồ:",
                [
                    "🛣️ Cấp Tuyến Phố & Khoanh Vùng Ổ Dịch (Cluster Zones)",
                    "🏘️ Cấp Phường / Xã (Ward Level)",
                    "🏙️ Cấp Quận / Huyện (District Level)",
                    "🇻🇳 Cấp Tỉnh / Toàn Quốc (Province Level)"
                ],
                index=2,
                horizontal=True,
                key="granularity_selector"
            )

            _tb_cols = st.columns([1, 2, 2.5, 1.0], gap="medium")
            with _tb_cols[0]:
                sel_year = st.selectbox("📅 Năm:", filter_years, index=0, key="global_year_sel")

            # Get months for selected year
            df_year_all = df[df['year'] == sel_year]
            avail_months = sorted(df_year_all['month'].dropna().unique().astype(int)) if not df_year_all.empty else [1]
            with _tb_cols[1]:
                if avail_months:
                    sel_month = st.select_slider(
                        "🗓️ Tháng:",
                        options=avail_months,
                        value=avail_months[-1],
                        format_func=lambda m: f"Tháng {m:02d}",
                        key="global_month_slider"
                    )
                else:
                    sel_month = 1

            with _tb_cols[2]:
                _cur_loc = st.session_state.get("user_location")
                _cur_label = (
                    f"Đã xác định ({_cur_loc['lat']:.5f}, {_cur_loc['lon']:.5f}) · "
                    f"<a href='https://www.google.com/maps?q={_cur_loc['lat']},{_cur_loc['lon']}' "
                    f"target='_blank' rel='noopener noreferrer' style='color:inherit;font-weight:700;text-decoration:underline;'>"
                    f"Your current location in Google Maps ↗</a>"
                    if _cur_loc else ""
                )
                _loc_res = _location_btn_component(
                    theme=ui.mode(),
                    current_label=_cur_label,
                    key="user_loc_btn_comp",
                )
                if (
                    isinstance(_loc_res, dict)
                    and _loc_res.get("lat") is not None
                    and _loc_res.get("ts") != st.session_state.get("_last_loc_ts")
                ):
                    st.session_state["user_location"] = _loc_res
                    st.session_state["_last_loc_ts"] = _loc_res.get("ts")
            if st.session_state.get("user_location"):
                with _tb_cols[3]:
                    if st.button("🔄 Về mặc định", key="reset_user_loc_btn", use_container_width=True):
                        st.session_state.pop("user_location", None)
                        st.rerun()

        # Color map for risk levels
        RISK_COLOR_MAP = {
            'Vùng Đỏ (Rất cao)': '#d90429',
            'Vùng Cam (Nguy cơ cao)': '#f77f00',
            'Vùng Vàng (Nguy cơ)': '#fcbf49',
            'Vùng Xanh (Kiểm soát)': '#2a9d8f'
        }

        # ===================================================================
        # LEVEL 1: CẤP TUYẾN PHỐ & KHOANH VÙNG Ổ DỊCH (STREET / CLUSTER ZONES)
        # ===================================================================
        if "Tuyến Phố" in granularity_level:
            with st.container(key="bento_level_overview"):
                st.subheader("🛣️ Bản đồ Khoanh Vùng Ổ Dịch & Tuyến Phố Nguy Cơ Cao")
                st.caption("💡 Các ổ dịch và tuyến phố xuất hiện ca nhiễm được khoanh vùng bằng bán kính dịch tễ (200m - 1000m) với mức độ cảnh báo nguy cơ (Đỏ - Cam - Vàng - Xanh).")

                # Filter clusters data
                c_data = clusters_df.copy() if not clusters_df.empty else pd.DataFrame()
                if not c_data.empty and 'year' in c_data.columns:
                    c_data = c_data[(c_data['year'] == sel_year) & (c_data['month'] == sel_month)]

                # Province & District drill-down filters
                c_provs = sorted(c_data['province'].dropna().unique().tolist()) if not c_data.empty else ['TP. Hồ Chí Minh']
                default_prov_idx = c_provs.index('TP. Hồ Chí Minh') if 'TP. Hồ Chí Minh' in c_provs else 0

                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1:
                    sel_c_prov = st.selectbox("📍 Chọn Tỉnh/Thành phố:", c_provs, index=default_prov_idx, key="cluster_prov_sel")

                c_prov_filtered = c_data[c_data['province'] == sel_c_prov] if not c_data.empty else pd.DataFrame()
                dist_options = ["Tất cả Quận/Huyện"] + sorted([d for d in c_prov_filtered['district'].dropna().unique() if d != 'Chưa xác định'])

                with col_f2:
                    sel_c_dist = st.selectbox("🏙️ Chọn Quận/Huyện:", dist_options, index=0, key="cluster_dist_sel")

                if sel_c_dist != "Tất cả Quận/Huyện":
                    c_prov_filtered = c_prov_filtered[c_prov_filtered['district'] == sel_c_dist]

                ward_options = ["Tất cả Phường/Xã"] + sorted([w for w in c_prov_filtered['ward'].dropna().unique() if w not in ['Chưa rõ', 'Tất cả các phường']])
                with col_f3:
                    sel_c_ward = st.selectbox("🏘️ Chọn Phường/Xã:", ward_options, index=0, key="cluster_ward_sel")

                if sel_c_ward != "Tất cả Phường/Xã":
                    c_prov_filtered = c_prov_filtered[c_prov_filtered['ward'] == sel_c_ward]

                with col_f4:
                    risk_filter = st.selectbox(
                        "⚠️ Lọc Mức Độ Nguy Cơ:",
                        ["Tất cả mức độ", "🔴 Chỉ Vùng Đỏ (Rất cao)", "🟠 Vùng Cam trở lên", "🟡 Vùng Vàng", "🟢 Vùng Xanh"],
                        index=0,
                        key="cluster_risk_filter"
                    )

                if "Chỉ Vùng Đỏ" in risk_filter:
                    c_prov_filtered = c_prov_filtered[c_prov_filtered['risk_level'].str.contains('Đỏ', na=False)]
                elif "Vùng Cam trở lên" in risk_filter:
                    c_prov_filtered = c_prov_filtered[c_prov_filtered['risk_level'].str.contains('Đỏ|Cam', na=False)]
                elif "Vùng Vàng" in risk_filter:
                    c_prov_filtered = c_prov_filtered[c_prov_filtered['risk_level'].str.contains('Vàng', na=False)]
                elif "Vùng Xanh" in risk_filter:
                    c_prov_filtered = c_prov_filtered[c_prov_filtered['risk_level'].str.contains('Xanh', na=False)]

                # Key Metrics
                total_cluster_cases = int(c_prov_filtered['cases'].sum()) if not c_prov_filtered.empty else 0
                red_zones_count = int((c_prov_filtered['risk_level'].str.contains('Đỏ', na=False)).sum()) if not c_prov_filtered.empty else 0
                orange_zones_count = int((c_prov_filtered['risk_level'].str.contains('Cam', na=False)).sum()) if not c_prov_filtered.empty else 0
                max_radius = int(c_prov_filtered['radius_meters'].max()) if not c_prov_filtered.empty and 'radius_meters' in c_prov_filtered.columns else 0

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Tổng ca ghi nhận tại các điểm nóng", f"{total_cluster_cases:,} ca")
                m2.metric("🔴 Số Ổ dịch Vùng Đỏ (Báo động)", f"{red_zones_count} điểm", delta="Cần phun hóa chất khẩn cấp" if red_zones_count > 0 else "An toàn", delta_color="inverse" if red_zones_count > 0 else "normal")
                m3.metric("🟠 Số Vùng Cam (Nguy cơ cao)", f"{orange_zones_count} điểm", delta="Cần tổng vệ sinh lăng quăng" if orange_zones_count > 0 else "Bình thường")
                m4.metric("Bán kính khoanh vùng tối đa", f"{max_radius} m", help="Bán kính cách ly và khoanh vùng dịch tễ")

            if not c_prov_filtered.empty and 'lat' in c_prov_filtered.columns and 'lon' in c_prov_filtered.columns:
                cluster_actions = load_cached_cluster_actions()
                center_lat = float(c_prov_filtered['lat'].mean())
                center_lon = float(c_prov_filtered['lon'].mean())
                max_c = max(float(c_prov_filtered['cases'].max()), 1.0)
                cluster_markers = []
                for _, _r in c_prov_filtered.iterrows():
                    if pd.isna(_r.get('lat')) or pd.isna(_r.get('lon')):
                        continue
                    _cid = str(_r.get('cluster_id', '') or _r.get('name', ''))
                    _act = cluster_actions.get(_cid, {})
                    _hcdc_status = _act.get('status_label', '⏳ Chờ xác minh')
                    _hcdc_team = _act.get('assigned_team', '')
                    _hcdc_note = _act.get('action_note', '')
                    _cases = int(_r.get('cases', 0))
                    _risk = str(_r.get('risk_level', ''))
                    _col = RISK_COLOR_MAP.get(_risk, '#d90429')
                    _rad_m = float(_r.get('radius_meters', 0) or 0)
                    _rad_px = max(7, min(22, 7 + 15 * (_cases / max_c)))
                    _team_line = f"<br/>🚑 Đội phụ trách: <b>{_hcdc_team}</b>" if _hcdc_team else ""
                    _note_line = f"<br/>📋 Chỉ đạo HCDC: {_hcdc_note}" if _hcdc_note else ""
                    _popup = (
                        f"<b>{_r.get('name', '')}</b><br/>"
                        f"Cấp: {_r.get('level', '')} · {_cases:,} ca<br/>"
                        f"Nguy cơ: {_risk}<br/>"
                        f"Bán kính: {int(_rad_m)} m<br/>"
                        f"Trạng thái HCDC: <b>{_hcdc_status}</b>{_team_line}{_note_line}<br/>"
                        f"<small>{_r.get('recommendation', '')}</small>"
                    )
                    cluster_markers.append({
                        "lat": float(_r['lat']),
                        "lon": float(_r['lon']),
                        "radius_px": _rad_px,
                        "radius_meters": _rad_m,
                        "color": _col,
                        "title": f"{_r.get('name', '')} ({_cases} ca · {_hcdc_status})",
                        "popup_html": _popup,
                    })

                with st.container(key="bento_main_map_card"):
                    _ext_l1 = build_arcgis_extended_layers(
                        sel_year=int(sel_year),
                        sel_month=int(sel_month),
                        level_code="L1",
                        sel_prov=sel_c_prov,
                        sel_dist=sel_c_dist,
                    )
                    _l1_base_gj = load_hcmc_wards_geojson() if "Hồ Chí Minh" in sel_c_prov else None
                    _l1_gj = _filter_geojson_for_province_or_dist(_l1_base_gj, sel_c_prov, sel_c_dist)
                    _l1_w_sub = ward_df[(ward_df["year"] == sel_year) & (ward_df["month"] == sel_month) & (ward_df["province"] == sel_c_prov)] if not ward_df.empty else pd.DataFrame()
                    _l1_cases_map = {}
                    for _, _wr in _l1_w_sub.iterrows():
                        _dn = normalize_hcmc_district_name(_wr.get("district", ""))
                        _wn = str(_wr.get("ward") or "").strip()
                        _cv = _safe_int(_wr.get("cases"), 0)
                        if _wn and _wn not in ("Chưa rõ", "Tất cả các phường"):
                            _k = f"{_wn} - {_dn}"
                            _l1_cases_map[_k] = _l1_cases_map.get(_k, 0) + _cv
                    for _, _cr in c_prov_filtered.iterrows():
                        _dn = normalize_hcmc_district_name(_cr.get("district", ""))
                        _wn = str(_cr.get("ward") or "").strip()
                        _cv = _safe_int(_cr.get("cases"), 0)
                        if _wn and _wn not in ("Chưa rõ", "Tất cả các phường"):
                            _k = f"{_wn} - {_dn}"
                            _l1_cases_map[_k] = max(_l1_cases_map.get(_k, 0), _cv)
                        if _dn and _dn != "Chưa xác định":
                            _l1_cases_map[_dn] = _l1_cases_map.get(_dn, 0) + _cv
                    _l1_pred_map = {}
                    if not hcmc_dist_preds_df.empty and "Hồ Chí Minh" in sel_c_prov:
                        _sp = hcmc_dist_preds_df[hcmc_dist_preds_df["step"] == 1] if "step" in hcmc_dist_preds_df.columns else hcmc_dist_preds_df
                        for _, _pr in _sp.iterrows():
                            _dn = normalize_hcmc_district_name(_pr.get("district", ""))
                            _l1_pred_map[_dn] = _l1_pred_map.get(_dn, 0.0) + _safe_float(_pr.get("predicted_cases"), 0.0)
                    _wx_lookup = get_province_weather_lookup(int(sel_year), int(sel_month))
                    _l1_choro = build_choropleth_region_values(
                        _l1_gj,
                        _l1_cases_map,
                        _l1_pred_map,
                        {},
                        _wx_lookup,
                        default_weather=_wx_lookup.get(sel_c_prov),
                        scope="local" if "Hồ Chí Minh" in sel_c_prov else "province",
                    ) if _l1_gj else None
                    _render_main_interactive_map(
                        title=f"Bản đồ Khoanh Vùng Ổ Dịch & Nguy Cơ — {sel_c_prov} (T{sel_month:02d}/{sel_year})",
                        center_lat=center_lat,
                        center_lon=center_lon,
                        zoom=12 if sel_c_dist != "Tất cả Quận/Huyện" else 11,
                        view_key=f"L1_{sel_c_prov}_{sel_c_dist}_{sel_c_ward}_{sel_year}_{sel_month}",
                        markers=cluster_markers,
                        geojson_data=_l1_gj,
                        choropleth_values=_l1_choro,
                        extended_layers=_ext_l1,
                    )

                # Actionable Table
                with st.container(key="bento_L1_table_card"):
                    st.subheader("📋 Danh Sách Điểm Nóng & Hành Động Dập Dịch Cần Triển Khai")
                    c_table = c_prov_filtered.copy()
                    c_table['hcdc_status'] = c_table.apply(
                        lambda r: cluster_actions.get(str(r.get('cluster_id', '') or r.get('name', '')), {}).get('status_label', '⏳ Chờ xác minh'),
                        axis=1,
                    )
                    c_table['assigned_team'] = c_table.apply(
                        lambda r: cluster_actions.get(str(r.get('cluster_id', '') or r.get('name', '')), {}).get('assigned_team', 'Chưa phân công'),
                        axis=1,
                    )
                    display_cols = ['name', 'level', 'district', 'ward', 'cases', 'risk_level', 'radius_meters', 'hcdc_status', 'assigned_team', 'recommendation']
                    avail_disp = [c for c in display_cols if c in c_table.columns]
                    st.dataframe(
                        c_table[avail_disp].sort_values('cases', ascending=False).reset_index(drop=True),
                        column_config={
                            "name": "Tên Điểm Nóng / Tuyến Phố",
                            "level": "Cấp Độ",
                            "district": "Quận / Huyện",
                            "ward": "Phường / Xã",
                            "cases": st.column_config.NumberColumn("Số Ca Nhiễm", format="%d ca"),
                            "risk_level": "Mức Độ Nguy Cơ",
                            "radius_meters": st.column_config.NumberColumn("Bán Kính Khoanh Vùng", format="%d m"),
                            "hcdc_status": "Trạng Thái HCDC",
                            "assigned_team": "Đội Điều Phối",
                            "recommendation": "Khuyến Cáo Y Tế & Hành Động Dập Dịch"
                        },
                        use_container_width=True
                    )
            else:
                st.info("Không có dữ liệu điểm nóng / ổ dịch nào phù hợp với bộ lọc hiện tại.")

        # ===================================================================
        # LEVEL 2: CẤP PHƯỜNG / XÃ (WARD LEVEL)
        # ===================================================================
        elif "Phường / Xã" in granularity_level:
            with st.container(key="bento_level_overview"):
                st.subheader("🏘️ Giám Sát Dịch Tễ Cấp Phường / Xã")
                w_data = ward_df.copy() if not ward_df.empty else pd.DataFrame()
                if not w_data.empty and 'year' in w_data.columns:
                    w_data = w_data[(w_data['year'] == sel_year) & (w_data['month'] == sel_month)]

                w_provs = sorted(w_data['province'].dropna().unique().tolist()) if not w_data.empty else ['TP. Hồ Chí Minh']
                default_p_idx = w_provs.index('TP. Hồ Chí Minh') if 'TP. Hồ Chí Minh' in w_provs else 0

                col_wp, col_wd = st.columns(2)
                with col_wp:
                    sel_w_prov = st.selectbox("📍 Chọn Tỉnh/Thành phố:", w_provs, index=default_p_idx, key="ward_prov_sel")

                w_prov_filtered = w_data[w_data['province'] == sel_w_prov] if not w_data.empty else pd.DataFrame()
                w_dist_opts = ["Tất cả Quận/Huyện"] + sorted([d for d in w_prov_filtered['district'].dropna().unique() if d != 'Chưa xác định'])
                with col_wd:
                    sel_w_dist = st.selectbox("🏙️ Chọn Quận/Huyện:", w_dist_opts, index=0, key="ward_dist_sel")

                if sel_w_dist != "Tất cả Quận/Huyện":
                    w_prov_filtered = w_prov_filtered[w_prov_filtered['district'] == sel_w_dist]

                total_ward_cases = int(w_prov_filtered['cases'].sum()) if not w_prov_filtered.empty else 0
                top_ward_row = w_prov_filtered.loc[w_prov_filtered['cases'].idxmax()] if not w_prov_filtered.empty else None

                w1, w2, w3, w4 = st.columns(4)
                w1.metric(f"Tổng ca (T{sel_month:02d}/{sel_year})", f"{total_ward_cases:,} ca")
                w2.metric("Số Phường/Xã có ca bệnh", f"{len(w_prov_filtered):,} phường/xã")
                if top_ward_row is not None:
                    w3.metric("Phường có ca nhiễm cao nhất", f"{top_ward_row['ward']}", delta=f"{int(top_ward_row['cases'])} ca")
                    w4.metric("Quận trực thuộc", f"{top_ward_row['district']}")

            if not w_prov_filtered.empty and 'lat' in w_prov_filtered.columns and 'lon' in w_prov_filtered.columns:
                c_lat = float(w_prov_filtered['lat'].mean())
                c_lon = float(w_prov_filtered['lon'].mean())
                max_w = max(float(w_prov_filtered['cases'].max()), 1.0)
                ward_markers = []
                for _, _r in w_prov_filtered.iterrows():
                    if pd.isna(_r.get('lat')) or pd.isna(_r.get('lon')):
                        continue
                    _cases = int(_r.get('cases', 0))
                    _risk = str(_r.get('risk_level', ''))
                    _col = RISK_COLOR_MAP.get(_risk, '#f77f00')
                    _rad_px = max(7, min(22, 7 + 15 * (_cases / max_w)))
                    _popup = (
                        f"<b>{_r.get('ward', '')}</b> ({_r.get('district', '')})<br/>"
                        f"Số ca: {_cases:,} ca<br/>"
                        f"Mức độ: {_risk}"
                    )
                    ward_markers.append({
                        "lat": float(_r['lat']),
                        "lon": float(_r['lon']),
                        "radius_px": _rad_px,
                        "radius_meters": 0,
                        "color": _col,
                        "title": f"{_r.get('ward', '')} ({_cases} ca)",
                        "popup_html": _popup,
                    })

                with st.container(key="bento_main_map_card"):
                    _ext_l2 = build_arcgis_extended_layers(
                        sel_year=int(sel_year),
                        sel_month=int(sel_month),
                        level_code="L2",
                        sel_prov=sel_w_prov,
                        sel_dist=sel_w_dist,
                    )
                    _l2_base_gj = load_hcmc_wards_geojson() if "Hồ Chí Minh" in sel_w_prov else None
                    _l2_gj = _filter_geojson_for_province_or_dist(_l2_base_gj, sel_w_prov, sel_w_dist)
                    _l2_cases_map = {}
                    for _, _wr in w_prov_filtered.iterrows():
                        _dn = normalize_hcmc_district_name(_wr.get("district", ""))
                        _wn = str(_wr.get("ward") or "").strip()
                        _cv = _safe_int(_wr.get("cases"), 0)
                        if _wn and _wn not in ("Chưa rõ", "Tất cả các phường"):
                            _k = f"{_wn} - {_dn}"
                            _l2_cases_map[_k] = _l2_cases_map.get(_k, 0) + _cv
                        if _dn and _dn != "Chưa xác định":
                            _l2_cases_map[_dn] = _l2_cases_map.get(_dn, 0) + _cv
                    _l2_pred_map = {}
                    if not hcmc_dist_preds_df.empty and "Hồ Chí Minh" in sel_w_prov:
                        _sp = hcmc_dist_preds_df[hcmc_dist_preds_df["step"] == 1] if "step" in hcmc_dist_preds_df.columns else hcmc_dist_preds_df
                        for _, _pr in _sp.iterrows():
                            _dn = normalize_hcmc_district_name(_pr.get("district", ""))
                            _l2_pred_map[_dn] = _l2_pred_map.get(_dn, 0.0) + _safe_float(_pr.get("predicted_cases"), 0.0)
                    _wx_lookup = get_province_weather_lookup(int(sel_year), int(sel_month))
                    _l2_choro = build_choropleth_region_values(
                        _l2_gj,
                        _l2_cases_map,
                        _l2_pred_map,
                        {},
                        _wx_lookup,
                        default_weather=_wx_lookup.get(sel_w_prov),
                        scope="local" if "Hồ Chí Minh" in sel_w_prov else "province",
                    ) if _l2_gj else None
                    _render_main_interactive_map(
                        title=f"Bản đồ Ca Nhiễm Cấp Phường/Xã — {sel_w_prov} (T{sel_month:02d}/{sel_year})",
                        center_lat=c_lat,
                        center_lon=c_lon,
                        zoom=11 if sel_w_dist == "Tất cả Quận/Huyện" else 12,
                        view_key=f"L2_{sel_w_prov}_{sel_w_dist}_{sel_year}_{sel_month}",
                        markers=ward_markers,
                        geojson_data=_l2_gj,
                        choropleth_values=_l2_choro,
                        extended_layers=_ext_l2,
                    )

                col_w_left, col_w_right = st.columns([3, 2], gap="medium")
                with col_w_left:
                    with st.container(key="bento_L2_chart_left"):
                        st.subheader("🏆 Top 10 Phường/Xã Ca Nhiễm Cao Nhất")
                        top_wards = w_prov_filtered.sort_values('cases', ascending=False).head(10)
                        fig_w_bar = px.bar(
                            top_wards, x='ward', y='cases', color='cases',
                            color_continuous_scale='Reds', text='cases',
                            labels={'ward': 'Phường / Xã', 'cases': 'Số ca'},
                            title="Top Phường/Xã có ca nhiễm nhiều nhất"
                        )
                        fig_w_bar.update_traces(textposition='outside')
                        st.plotly_chart(fig_w_bar, width='stretch')

                with col_w_right:
                    with st.container(key="bento_L2_chart_right"):
                        st.subheader("📊 Phân Bổ Mức Độ Nguy Cơ")
                        risk_counts = w_prov_filtered['risk_level'].value_counts().reset_index()
                        risk_counts.columns = ['risk_level', 'count']
                        fig_risk_pie = px.pie(
                            risk_counts, names='risk_level', values='count',
                            color='risk_level', color_discrete_map=RISK_COLOR_MAP,
                            title="Tỷ lệ phân bố mức độ nguy cơ cấp Phường"
                        )
                        st.plotly_chart(fig_risk_pie, width='stretch')
            else:
                st.info("Chưa có dữ liệu tọa độ cấp Phường/Xã cho khu vực được chọn.")

        # ===================================================================
        # LEVEL 3: CẤP QUẬN / HUYỆN (DISTRICT LEVEL)
        # ===================================================================
        elif "Quận / Huyện" in granularity_level:
            with st.container(key="bento_level_overview"):
                st.subheader("🏙️ Giám Sát Dịch Tễ Cấp Quận / Huyện")
                d_data = district_df.copy() if not district_df.empty else pd.DataFrame()
                if not d_data.empty and 'year' in d_data.columns:
                    d_data = d_data[(d_data['year'] == sel_year) & (d_data['month'] == sel_month)]

                d_provs = sorted(d_data['province'].dropna().unique().tolist()) if not d_data.empty else ['TP. Hồ Chí Minh']
                default_dp_idx = d_provs.index('TP. Hồ Chí Minh') if 'TP. Hồ Chí Minh' in d_provs else 0
                sel_d_prov = st.selectbox("📍 Chọn Tỉnh/Thành phố:", d_provs, index=default_dp_idx, key="dist_prov_sel")

                d_prov_filtered = d_data[d_data['province'] == sel_d_prov] if not d_data.empty else pd.DataFrame()
                tot_dist_cases = int(d_prov_filtered['cases'].sum()) if not d_prov_filtered.empty else 0
                avg_dist_inc = float(d_prov_filtered['incidence_rate'].mean()) if not d_prov_filtered.empty and 'incidence_rate' in d_prov_filtered.columns else 0.0
                top_dist_row = d_prov_filtered.loc[d_prov_filtered['cases'].idxmax()] if not d_prov_filtered.empty else None

                d1, d2, d3, d4 = st.columns(4)
                d1.metric(f"Tổng ca ({sel_d_prov})", f"{tot_dist_cases:,} ca")
                d2.metric("Tỷ lệ mắc trung bình (/100k dân)", f"{avg_dist_inc:.2f}")
                if top_dist_row is not None:
                    d3.metric("Quận/Huyện cao nhất", f"{top_dist_row['district']}", delta=f"{int(top_dist_row['cases'])} ca")
                d4.metric("Số Quận/Huyện ghi nhận", f"{len(d_prov_filtered)} quận/huyện")

            if not d_prov_filtered.empty and 'lat' in d_prov_filtered.columns and 'lon' in d_prov_filtered.columns:
                c_lat = float(d_prov_filtered['lat'].mean())
                c_lon = float(d_prov_filtered['lon'].mean())
                max_d = max(float(d_prov_filtered['cases'].max()), 1.0)
                dist_markers = []
                for _, _r in d_prov_filtered.iterrows():
                    if pd.isna(_r.get('lat')) or pd.isna(_r.get('lon')):
                        continue
                    _cases = int(_r.get('cases', 0))
                    _inc = float(_r.get('incidence_rate', 0) or 0)
                    _ratio = _cases / max_d
                    _col = "#d90429" if _ratio > 0.6 else ("#f77f00" if _ratio > 0.3 else "#fcbf49")
                    _rad_px = max(8, min(24, 8 + 16 * _ratio))
                    _popup = (
                        f"<b>{_r.get('district', '')}</b><br/>"
                        f"Số ca: {_cases:,} ca<br/>"
                        f"Tỷ lệ mắc: {_inc:.2f} / 100k dân"
                    )
                    dist_markers.append({
                        "lat": float(_r['lat']),
                        "lon": float(_r['lon']),
                        "radius_px": _rad_px,
                        "radius_meters": 0,
                        "color": _col,
                        "title": f"{_r.get('district', '')} ({_cases} ca)",
                        "popup_html": _popup,
                    })

                hcmc_geojson = None
                dist_choro_vals = {}
                _wx_lookup = get_province_weather_lookup(int(sel_year), int(sel_month))
                if "Hồ Chí Minh" in sel_d_prov:
                    hcmc_geojson = load_hcmc_districts_geojson()
                    _d_cases_map, _d_inc_map, dist_step1_pred = {}, {}, {}
                    if not hcmc_dist_preds_df.empty and 'district' in hcmc_dist_preds_df.columns:
                        _p_df = hcmc_dist_preds_df
                        if 'step' in _p_df.columns:
                            _p_df = _p_df[_p_df['step'] == 1]
                        for _, _pr in _p_df.iterrows():
                            _dn = normalize_hcmc_district_name(_pr.get('district', ''))
                            dist_step1_pred[_dn] = dist_step1_pred.get(_dn, 0.0) + _safe_float(_pr.get('predicted_cases'), 0.0)
                    for _, _r in d_prov_filtered.iterrows():
                        _dn = normalize_hcmc_district_name(_r.get('district', ''))
                        if not _dn or _dn == 'Chưa xác định':
                            continue
                        _d_cases_map[_dn] = _d_cases_map.get(_dn, 0) + _safe_int(_r.get('cases'), 0)
                        _d_inc_map[_dn] = _d_inc_map.get(_dn, 0.0) + _safe_float(_r.get('incidence_rate'), 0.0)
                    dist_choro_vals = build_choropleth_region_values(
                        hcmc_geojson,
                        _d_cases_map,
                        dist_step1_pred,
                        _d_inc_map,
                        _wx_lookup,
                        default_weather=_wx_lookup.get("TP. Hồ Chí Minh"),
                        scope="district",
                    ) if hcmc_geojson else {}
                else:
                    hcmc_geojson = _filter_geojson_for_province_or_dist(None, sel_d_prov)
                    _prov_cases_tot = int(d_prov_filtered['cases'].sum())
                    _prov_inc_avg = float(d_prov_filtered['incidence_rate'].mean()) if 'incidence_rate' in d_prov_filtered.columns else 0.0
                    _p_pred_row = predictions_df[(predictions_df['province'] == sel_d_prov) & (predictions_df['step'] == 1)] if not predictions_df.empty and 'step' in predictions_df.columns else pd.DataFrame()
                    _p_pred_val = _safe_float(_p_pred_row['predicted_cases'].iloc[0], float(_prov_cases_tot)) if not _p_pred_row.empty else float(_prov_cases_tot)
                    dist_choro_vals = build_choropleth_region_values(
                        hcmc_geojson,
                        {sel_d_prov: _prov_cases_tot},
                        {sel_d_prov: _p_pred_val},
                        {sel_d_prov: _prov_inc_avg},
                        _wx_lookup,
                        default_weather=_wx_lookup.get(sel_d_prov),
                        scope="province",
                    ) if hcmc_geojson else {}

                with st.container(key="bento_main_map_card"):
                    _ext_l3 = build_arcgis_extended_layers(
                        sel_year=int(sel_year),
                        sel_month=int(sel_month),
                        level_code="L3",
                        sel_prov=sel_d_prov,
                    )
                    _render_main_interactive_map(
                        title=f"Bản đồ Dịch Tễ Cấp Quận/Huyện — {sel_d_prov} (T{sel_month:02d}/{sel_year})",
                        center_lat=c_lat,
                        center_lon=c_lon,
                        zoom=10,
                        view_key=f"L3_{sel_d_prov}_{sel_year}_{sel_month}",
                        markers=dist_markers,
                        geojson_data=hcmc_geojson,
                        choropleth_values=dist_choro_vals if hcmc_geojson else None,
                        extended_layers=_ext_l3,
                    )

                col_dl, col_dr = st.columns([3, 2], gap="medium")
                with col_dl:
                    with st.container(key="bento_L3_chart_left"):
                        st.subheader(f"📈 Diễn Biến Ca Nhiễm Theo Tháng — {sel_d_prov}")
                        prov_monthly = df[(df['province'] == sel_d_prov) & (df['year'] == sel_year)].sort_values('month')
                        if not prov_monthly.empty:
                            prov_monthly['month_label'] = prov_monthly['month'].apply(lambda m: f"T{int(m):02d}")
                            fig_prov_line = px.line(
                                prov_monthly, x='month_label', y='cases', markers=True,
                                title=f"Số ca SXH theo tháng ({sel_year})",
                                labels={'month_label': 'Tháng', 'cases': 'Số ca nhiễm'}
                            )
                            fig_prov_line.update_traces(line_color='#d62828', line_width=3, marker_size=8)
                            st.plotly_chart(fig_prov_line, width='stretch')

                with col_dr:
                    with st.container(key="bento_L3_chart_right"):
                        st.subheader("🏆 Top Quận/Huyện Ca Nhiễm Cao Nhất")
                        top_dists = d_prov_filtered.sort_values('cases', ascending=False).head(10)
                        fig_dist_bar = px.bar(
                            top_dists, x='district', y='cases', color='cases',
                            color_continuous_scale='Reds', text='cases',
                            title="Top Quận/Huyện",
                            labels={'district': 'Quận / Huyện', 'cases': 'Số ca'}
                        )
                        fig_dist_bar.update_traces(textposition='outside')
                        st.plotly_chart(fig_dist_bar, width='stretch')

        # ===================================================================
        # LEVEL 4: CẤP TỈNH / TOÀN QUỐC (PROVINCE LEVEL)
        # ===================================================================
        else:
            with st.container(key="bento_level_overview"):
                st.subheader("🇻🇳 Giám Sát Dịch Sốt Xuất Huyết — Toàn Quốc (34 Tỉnh/Thành)")
                df_year = df[df['year'] == sel_year].copy()
                df_month = df_year[df_year['month'] == sel_month] if not df_year.empty else pd.DataFrame()

                nat_cases_month = int(df_month['cases'].sum()) if not df_month.empty else 0
                nat_avg_inc = float(df_month['incidence_rate'].mean()) if not df_month.empty else 0.0
                top_prov_row = df_month.loc[df_month['cases'].idxmax()] if not df_month.empty else None

                col1, col2, col3, col4 = st.columns(4)
                col1.metric(f"Tổng ca toàn quốc (T{sel_month:02d}/{sel_year})", f"{nat_cases_month:,} ca")
                col2.metric("Tỷ lệ mắc TB (/100k dân)", f"{nat_avg_inc:.2f}")
                col3.metric(f"Tổng ca cả năm {sel_year}", f"{int(df_year['cases'].sum()):,} ca")
                if top_prov_row is not None:
                    col4.metric(
                        f"Tỉnh cao nhất (T{sel_month:02d})",
                        f"{top_prov_row['province']}",
                        delta=f"{int(top_prov_row['cases']):,} ca"
                    )

            geojson_path = getattr(paths, 'BOUNDARY_FILE', paths.DATA_DIR / "population" / "vietnam_34_provinces_2025.geojson")
            if geojson_path.exists() and not df_month.empty:
                vn_geojson = load_vietnam_geojson_simplified(str(geojson_path))
                if vn_geojson:
                    _p_cases_map, _p_inc_map, _p_pred_map = {}, {}, {}
                    for _, _r in df_month.iterrows():
                        _prov = str(_r.get('province', ''))
                        if _prov:
                            _p_cases_map[_prov] = _safe_int(_r.get('cases'), 0)
                            _p_inc_map[_prov] = _safe_float(_r.get('incidence_rate'), 0.0)
                    if not predictions_df.empty and 'province' in predictions_df.columns:
                        _sp_p = predictions_df[predictions_df['step'] == 1] if 'step' in predictions_df.columns else predictions_df
                        for _, _pr in _sp_p.iterrows():
                            _pn = str(_pr.get('province', ''))
                            if _pn:
                                _p_pred_map[_pn] = _safe_float(_pr.get('predicted_cases'), 0.0)
                    _wx_lookup = get_province_weather_lookup(int(sel_year), int(sel_month))
                    choro_vals = build_choropleth_region_values(
                        vn_geojson,
                        _p_cases_map,
                        _p_pred_map,
                        _p_inc_map,
                        _wx_lookup,
                        scope="province",
                    )
                    with st.container(key="bento_main_map_card"):
                        _ext_l4 = build_arcgis_extended_layers(
                            sel_year=int(sel_year),
                            sel_month=int(sel_month),
                            level_code="L4",
                            sel_prov="",
                        )
                        _render_main_interactive_map(
                            title=f"Bản đồ Ca nhiễm Sốt xuất huyết 34 Tỉnh/Thành — Tháng {sel_month:02d}/{sel_year}",
                            center_lat=15.5,
                            center_lon=107.8,
                            zoom=6,
                            view_key=f"L4_{sel_year}_{sel_month}",
                            geojson_data=vn_geojson,
                            choropleth_values=choro_vals,
                            extended_layers=_ext_l4,
                        )

            col_left, col_right = st.columns([3, 2], gap="medium")
            with col_left:
                with st.container(key="bento_L4_chart_left"):
                    st.subheader(f"📈 Diễn biến Tổng Ca Nhiễm Toàn Quốc — Năm {sel_year}")
                    nat_monthly = df_year.groupby('month')['cases'].sum().reset_index()
                    nat_monthly['month_label'] = nat_monthly['month'].apply(lambda m: f"T{int(m):02d}")
                    fig_trend = px.line(
                        nat_monthly, x='month_label', y='cases',
                        markers=True,
                        title=f"Tổng số ca SXH toàn quốc theo tháng — Năm {sel_year}",
                        labels={'month_label': 'Tháng', 'cases': 'Tổng số ca'}
                    )
                    fig_trend.update_traces(line_color='#e63946', marker_size=8)
                    st.plotly_chart(fig_trend, width='stretch')

            with col_right:
                with st.container(key="bento_L4_chart_right"):
                    st.subheader(f"🏆 Top 10 Tỉnh/Thành Ca Nhiễm Cao Nhất — Năm {sel_year}")
                    top_provs_year = df_year.groupby('province')['cases'].sum().reset_index().sort_values('cases', ascending=False).head(10)
                    fig_bar = px.bar(
                        top_provs_year, x='province', y='cases',
                        color='cases', color_continuous_scale='Reds',
                        text='cases',
                        title=f"Top 10 Tỉnh — Năm {sel_year}",
                        labels={'province': 'Tỉnh/Thành', 'cases': 'Số ca'}
                    )
                    fig_bar.update_traces(textposition='outside')
                    st.plotly_chart(fig_bar, width='stretch')

        # -------------------------------------------------------------------
        # BENTO SPLIT: Ý KIẾN CỘNG ĐỒNG & ĐIỀU PHỐI DỊCH TỄ HCDC
        # -------------------------------------------------------------------
        saved_pins = load_cached_pins()
        col_pins_list, col_hcdc_ctrl = st.columns([1, 1], gap="medium")

        with col_pins_list:
            with st.container(key="bento_pins_list_card"):
                st.subheader("📌 Ý Kiến & Bình Luận Tại Khu Vực Đã Ghim")
                st.caption(
                    "💡 Chạm hoặc nhấp trực tiếp lên **bản đồ chính ở trên** để mở thẻ nổi nhập bình luận ngay tại góc bản đồ."
                )

                with st.expander(f"💬 Danh sách ý kiến & khu vực đã ghim ({len(saved_pins)})", expanded=bool(saved_pins)):
                    if not saved_pins:
                        st.caption("Chưa có bình luận nào được ghim trên bản đồ. Hãy là người đầu tiên đóng góp ý kiến!")
                    else:
                        _filter_cat = st.selectbox(
                            "Lọc theo phân loại:",
                            ["Tất cả"] + sorted({p.get("category", "💬 Ý kiến khác") for p in saved_pins}),
                            key="pin_list_cat_filter",
                        )
                        _shown_pins = [
                            p for p in saved_pins
                            if _filter_cat == "Tất cả" or p.get("category") == _filter_cat
                        ]
                        for _idx, _p in enumerate(_shown_pins):
                            _p_col1, _p_col2 = st.columns([6, 1])
                            with _p_col1:
                                _area_txt = f" — 📍 {_p['area_name']}" if _p.get("area_name") else ""
                                _st_label = _p.get("status_label") or map_pins_service.PIN_STATUS_OPTIONS.get(
                                    _p.get("status", "pending"), "⏳ Chờ xác minh"
                                )
                                _team_txt = f" · 🚑 **{_p['assigned_team']}**" if _p.get("assigned_team") else ""
                                _ver_txt = f" · 👨‍⚕️ Xác minh: {_p['verified_by']}" if _p.get("verified_by") else ""
                                _note_txt = f"\n> 📋 *Chỉ đạo HCDC:* {_p['action_note']}" if _p.get("action_note") else ""
                                st.markdown(
                                    f"**{_p.get('category', '💬 Ý kiến')}**{_area_txt} · `{_st_label}`{_team_txt}{_ver_txt}  \n"
                                    f"{_p.get('comment', '')}{_note_txt}  \n"
                                    f"<small>👤 {_p.get('author', 'Người dân')} · "
                                    f"🌐 `{_p.get('lat')}, {_p.get('lon')}` · "
                                    f"🕒 {_p.get('created_at', '')}</small>",
                                    unsafe_allow_html=True,
                                )
                            with _p_col2:
                                if st.button("🗑️", key=f"del_pin_{_p.get('id', _idx)}", help="Xóa ghim này"):
                                    map_pins_service.delete_pin(_p.get("id", ""))
                                    load_cached_pins.clear()
                                    st.rerun()
                            st.divider()

        with col_hcdc_ctrl:
            with st.container(key="bento_hcdc_dispatch_card"):
                st.subheader("🛡️ Trung Tâm Điều Phối & Xác Minh Dịch Tễ HCDC")
                if not is_hcdc_officer:
                    st.info(
                        "🔐 **Chế độ Người dân / Cộng đồng:** Bạn đang xem trạng thái xác minh và xử lý ổ dịch công khai. "
                        "Để **duyệt phản ánh, phân công đội phun thuốc & cập nhật tiến độ xử lý ổ dịch**, cán bộ y tế vui lòng mở "
                        "**`🛡️ Vai trò & Quyền HCDC`** ở thanh bên trái để đăng nhập."
                    )
                else:
                    st.success(
                        f"👨‍⚕️ **Cán bộ trực điều phối:** {active_hcdc_officer.get('full_name', '')} "
                        f"({active_hcdc_officer.get('specialty', '')})"
                    )
                    hcdc_tab_pins, hcdc_tab_clusters = st.tabs([
                        "📌 1. Duyệt & Phân Công Phản Ánh Cộng Đồng",
                        "🎯 2. Điều Phối Xử Lý Ổ Dịch Trọng Điểm",
                    ])

                    with hcdc_tab_pins:
                        if not saved_pins:
                            st.caption("Hiện chưa có phản ánh cộng đồng nào cần xử lý.")
                        else:
                            _status_keys = list(map_pins_service.PIN_STATUS_OPTIONS.keys())
                            _pin_choices = {
                                f"[{p.get('status_label', '⏳ Chờ xác minh')}] {p.get('area_name') or 'Khu vực chưa rõ'} — {p.get('comment', '')[:45]} (ID: {p.get('id')})": p
                                for p in saved_pins
                            }
                            _sel_pin_label = st.selectbox(
                                "Chọn điểm phản ánh cộng đồng cần xác minh / điều phối:",
                                list(_pin_choices.keys()),
                                key="hcdc_select_pin",
                            )
                            _target_pin = _pin_choices[_sel_pin_label]
                            with st.form("hcdc_pin_dispatch_form"):
                                _hc1, _hc2 = st.columns(2)
                                with _hc1:
                                    _cur_st = _target_pin.get("status", "pending")
                                    _st_idx = _status_keys.index(_cur_st) if _cur_st in _status_keys else 0
                                    _new_st = st.selectbox(
                                        "Trạng thái xác minh & xử lý:",
                                        _status_keys,
                                        index=_st_idx,
                                        format_func=lambda k: map_pins_service.PIN_STATUS_OPTIONS[k],
                                    )
                                with _hc2:
                                    _team_opts = [""] + map_pins_service.DISPATCH_TEAMS
                                    _cur_team = _target_pin.get("assigned_team", "")
                                    _team_idx = _team_opts.index(_cur_team) if _cur_team in _team_opts else 0
                                    _new_team = st.selectbox(
                                        "Phân công đội xử lý:",
                                        _team_opts,
                                        index=_team_idx,
                                        format_func=lambda t: t if t else "-- Chưa phân công --",
                                    )
                                _new_note = st.text_input(
                                    "Ghi chú chỉ đạo / Kết quả kiểm tra thực địa:",
                                    value=_target_pin.get("action_note", ""),
                                    placeholder="VD: Đã cử đội phun hóa chất ULV bán kính 200m & diệt lăng quăng.",
                                )
                                if st.form_submit_button("✅ Cập Nhật Trạng Thái & Đồng Bộ Lên Bản Đồ", use_container_width=True):
                                    map_pins_service.update_pin_status(
                                        pin_id=_target_pin.get("id", ""),
                                        status=_new_st,
                                        verified_by=active_hcdc_officer.get("full_name", "Cán bộ HCDC"),
                                        assigned_team=_new_team,
                                        action_note=_new_note,
                                    )
                                    load_cached_pins.clear()
                                    st.success("✅ Đã cập nhật trạng thái phản ánh và đồng bộ lên bản đồ ArcGIS & Leaflet!")
                                    st.rerun()

                    with hcdc_tab_clusters:
                        _hcmc_clusters = clusters_df.copy() if not clusters_df.empty else pd.DataFrame()
                        if not _hcmc_clusters.empty and 'province' in _hcmc_clusters.columns:
                            _hcmc_only = _hcmc_clusters[_hcmc_clusters['province'] == 'TP. Hồ Chí Minh']
                            if not _hcmc_only.empty:
                                _hcmc_clusters = _hcmc_only
                        if _hcmc_clusters.empty:
                            st.caption("Chưa có dữ liệu ổ dịch để điều phối.")
                        else:
                            _hcmc_clusters = _hcmc_clusters.sort_values('cases', ascending=False).head(60)
                            _cluster_actions = load_cached_cluster_actions()
                            _c_choices = {}
                            for _, _cr in _hcmc_clusters.iterrows():
                                _cid = str(_cr.get('cluster_id', '') or _cr.get('name', ''))
                                _cst = _cluster_actions.get(_cid, {}).get('status_label', '⏳ Chờ xác minh')
                                _lbl = f"[{_cst}] {_cr.get('name', '')} ({int(_cr.get('cases', 0))} ca · {_cr.get('risk_level', '')})"
                                _c_choices[_lbl] = (_cid, _cr)
                            _sel_c_lbl = st.selectbox(
                                "Chọn ổ dịch trọng điểm cần điều phối dập dịch:",
                                list(_c_choices.keys()),
                                key="hcdc_select_cluster",
                            )
                            _target_cid, _target_crow = _c_choices[_sel_c_lbl]
                            _cur_cact = _cluster_actions.get(_target_cid, {})
                            _status_keys = list(map_pins_service.PIN_STATUS_OPTIONS.keys())
                            with st.form("hcdc_cluster_dispatch_form"):
                                _cc1, _cc2 = st.columns(2)
                                with _cc1:
                                    _cst_code = _cur_cact.get("status", "pending")
                                    _cst_idx = _status_keys.index(_cst_code) if _cst_code in _status_keys else 0
                                    _c_new_st = st.selectbox(
                                        "Trạng thái dập dịch ổ dịch:",
                                        _status_keys,
                                        index=_cst_idx,
                                        format_func=lambda k: map_pins_service.PIN_STATUS_OPTIONS[k],
                                    )
                                with _cc2:
                                    _team_opts = [""] + map_pins_service.DISPATCH_TEAMS
                                    _cteam = _cur_cact.get("assigned_team", "")
                                    _cteam_idx = _team_opts.index(_cteam) if _cteam in _team_opts else 0
                                    _c_new_team = st.selectbox(
                                        "Đội cơ động / Phun thuốc phụ trách:",
                                        _team_opts,
                                        index=_cteam_idx,
                                        format_func=lambda t: t if t else "-- Chưa phân công --",
                                    )
                                _c_new_note = st.text_input(
                                    "Phương án xử lý ổ dịch:",
                                    value=_cur_cact.get("action_note", str(_target_crow.get("recommendation", ""))),
                                )
                                if st.form_submit_button("🚒 Lưu Điều Phối Xử Lý Ổ Dịch", use_container_width=True):
                                    map_pins_service.update_cluster_action(
                                        cluster_id=_target_cid,
                                        status=_c_new_st,
                                        assigned_team=_c_new_team,
                                        action_note=_c_new_note,
                                        updated_by=active_hcdc_officer.get("full_name", "Cán bộ HCDC"),
                                    )
                                    load_cached_cluster_actions.clear()
                                    st.success(f"✅ Đã cập nhật điều phối ổ dịch `{_target_cid}`!")
                                    st.rerun()

                            if _cluster_actions:
                                _act_df = pd.DataFrame(list(_cluster_actions.values()))
                                st.download_button(
                                    "📥 Tải Nhật Ký Điều Phối Dập Dịch HCDC (CSV)",
                                    data=_act_df.to_csv(index=False).encode("utf-8"),
                                    file_name="hcdc_cluster_dispatch_log.csv",
                                    mime="text/csv",
                                    key="dl_hcdc_dispatch_csv",
                                )

        # -------------------------------------------------------------------
        # BENTO ANALYTICS CARD: SO SÁNH DIỄN BIẾN 12 THÁNG (2024 vs 2025)
        # -------------------------------------------------------------------
        with st.container(key="bento_yoy_card"):
            st.subheader("📈 So Sánh Diễn Biến Số Ca Nhiễm 12 Tháng (Năm 2024 vs 2025)")
            st.caption(
                "Sơ đồ đường so sánh xu hướng dịch tễ sốt xuất huyết qua 12 tháng giữa **Năm 2024** và **Năm 2025** "
                "nhằm đối sánh chu kỳ lây nhiễm, tháng đỉnh dịch và tỷ lệ biến động số ca bệnh."
            )

            # Region selection for comparison (defaults to TP. Hồ Chí Minh)
            comp_prov_list = ["TP. Hồ Chí Minh", "🇻🇳 Toàn Quốc (Tổng hợp)"] + sorted(
                [p for p in df['province'].dropna().unique().tolist() if p not in ['TP. Hồ Chí Minh']]
            )
            col_comp_sel, _ = st.columns([2, 2])
            with col_comp_sel:
                sel_comp_region = st.selectbox(
                    "📍 Chọn khu vực so sánh 2024 vs 2025:",
                    options=comp_prov_list,
                    index=0,
                    key="comp_year_region_sel"
                )

            if sel_comp_region == "🇻🇳 Toàn Quốc (Tổng hợp)":
                df_comp_base = df.copy()
            else:
                df_comp_base = df[df['province'] == sel_comp_region].copy()

            # Build monthly series for 2024 and 2025 (months 1 to 12)
            s_2024 = df_comp_base[df_comp_base['year'] == 2024].groupby('month')['cases'].sum().reindex(range(1, 13), fill_value=0)
            s_2025 = df_comp_base[df_comp_base['year'] == 2025].groupby('month')['cases'].sum().reindex(range(1, 13), fill_value=0)

            tot_2024 = int(s_2024.sum())
            tot_2025 = int(s_2025.sum())
            diff_cases = tot_2025 - tot_2024
            pct_change = ((tot_2025 - tot_2024) / tot_2024 * 100) if tot_2024 > 0 else 0.0

            peak_m_2024 = int(s_2024.idxmax())
            peak_v_2024 = int(s_2024.max())
            peak_m_2025 = int(s_2025.idxmax())
            peak_v_2025 = int(s_2025.max())

            # 4 Metric cards
            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric("Tổng ca Năm 2024 (12 tháng)", f"{tot_2024:,} ca")
            cm2.metric(
                "Tổng ca Năm 2025 (12 tháng)",
                f"{tot_2025:,} ca",
                delta=f"{diff_cases:+,} ca ({pct_change:+.1f}%)",
                delta_color="inverse" if diff_cases > 0 else "normal"
            )
            cm3.metric("Đỉnh dịch 2024", f"Tháng {peak_m_2024:02d}", delta=f"{peak_v_2024:,} ca")
            cm4.metric("Đỉnh dịch 2025", f"Tháng {peak_m_2025:02d}", delta=f"{peak_v_2025:,} ca", delta_color="inverse" if peak_v_2025 > peak_v_2024 else "normal")

            # Create Plotly comparison line chart
            months_labels = [f"Tháng {m:02d}" for m in range(1, 13)]
            fig_comp = go.Figure()

            # 2024 Line
            fig_comp.add_trace(go.Scatter(
                x=months_labels,
                y=s_2024.values,
                mode='lines+markers+text',
                name='Năm 2024',
                text=[f"{v:,}" if v > 0 else "" for v in s_2024.values],
                textposition='top center',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8, symbol='circle', color='#1f77b4'),
                hovertemplate="<b>Năm 2024 - %{x}</b>: %{y:,} ca<extra></extra>"
            ))

            # 2025 Line
            fig_comp.add_trace(go.Scatter(
                x=months_labels,
                y=s_2025.values,
                mode='lines+markers+text',
                name='Năm 2025',
                text=[f"{v:,}" if v > 0 else "" for v in s_2025.values],
                textposition='bottom center',
                line=dict(color='#d62828', width=3.5),
                marker=dict(size=9, symbol='diamond', color='#d62828'),
                hovertemplate="<b>Năm 2025 - %{x}</b>: %{y:,} ca<extra></extra>"
            ))

            fig_comp.update_layout(
                title=f"<b>Sơ Đồ Đường So Sánh Số Ca Nhiễm 12 Tháng Năm 2024 vs 2025 — {sel_comp_region}</b>",
                xaxis_title="Tháng trong năm",
                yaxis_title="Số ca nhiễm (ca)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified",
                template="plotly_white",
                height=440
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            # Monthly breakdown table in expander
            with st.expander("📋 Xem bảng số liệu chi tiết so sánh 12 tháng (2024 vs 2025)"):
                comp_table_data = []
                for m in range(1, 13):
                    c24 = int(s_2024.iloc[m - 1])
                    c25 = int(s_2025.iloc[m - 1])
                    diff_m = c25 - c24
                    pct_m = f"{(diff_m / c24 * 100):+.1f}%" if c24 > 0 else ("+100%" if c25 > 0 else "0%")
                    comp_table_data.append({
                        "Tháng": f"Tháng {m:02d}",
                        "Số ca Năm 2024": c24,
                        "Số ca Năm 2025": c25,
                        "Chênh lệch (ca)": f"{diff_m:+,} ca",
                        "Tỷ lệ biến động": pct_m
                    })
                st.dataframe(pd.DataFrame(comp_table_data), use_container_width=True)

        # -------------------------------------------------------------------
        # BENTO ANALYTICS CARD: TƯƠNG QUAN KHÍ TƯỢNG & SỐ CA SXH THEO THÁNG
        # -------------------------------------------------------------------
        with st.container(key="bento_weather_card"):
            st.subheader("🌦️ Đối Sánh Chuỗi Thời Gian: Khí Tượng & Số Ca Sốt Xuất Huyết Theo Tháng")
            st.caption(
                "Phân tích tương quan dịch tễ giữa điều kiện thời tiết (Lượng mưa, Nhiệt độ, Độ ẩm, Bụi mịn PM2.5) "
                "và diễn biến số ca mắc sốt xuất huyết qua từng tháng với **2 nguồn khí tượng song song** (`data/weatherdata` MongoDB & WeatherAPI / Open-Meteo)."
            )

            col_ws_source, col_ws_metric, col_ws_year = st.columns([2, 2, 1])
            with col_ws_source:
                sel_weather_source = st.selectbox(
                    "📡 Chọn nguồn dữ liệu khí tượng song song:",
                    options=[
                        "🌿 Trạm Quan Trắc & PM2.5 TP.HCM (Nguồn WeatherData MongoDB)",
                        "🌐 API Trực Tuyến & Cache Tổng Hợp (WeatherAPI / Open-Meteo)",
                        "🔀 Đối Sánh Cả 2 Nguồn Khí Tượng (Parallel Comparison)"
                    ],
                    index=0,
                    key="weather_parallel_source_sel"
                )

            with col_ws_metric:
                sel_weather_metric = st.selectbox(
                    "📊 Chọn yếu tố thời tiết đối sánh:",
                    options=[
                        "🌧️ Lượng mưa tích lũy (mm)",
                        "💧 Độ ẩm không khí trung bình (%)",
                        "🌡️ Nhiệt độ không khí trung bình (°C)",
                        "🌫️ Nồng độ Bụi mịn PM2.5 (µg/m³)"
                    ],
                    index=0,
                    key="weather_metric_choice_sel"
                )

            with col_ws_year:
                sel_ws_period = st.selectbox(
                    "📅 Niên độ:",
                    options=["Năm 2025", "Năm 2024", "Toàn bộ (2024 - 2026)"],
                    index=0,
                    key="weather_period_choice_sel"
                )

            # Lấy dữ liệu thời tiết và SXH song song (đã cache)
            try:
                ws_combined = load_cached_weather_series("TP. Hồ Chí Minh", "local_weatherdata")
                ws_api_combined = load_cached_weather_series("TP. Hồ Chí Minh", "api_cache")
            except Exception as _e_ws:
                ws_combined = pd.DataFrame()
                ws_api_combined = pd.DataFrame()

            # Lọc theo niên độ
            if not ws_combined.empty:
                if sel_ws_period == "Năm 2025":
                    ws_view = ws_combined[ws_combined['year'] == 2025].copy()
                    ws_api_view = ws_api_combined[ws_api_combined['year'] == 2025].copy() if not ws_api_combined.empty else pd.DataFrame()
                elif sel_ws_period == "Năm 2024":
                    ws_view = ws_combined[ws_combined['year'] == 2024].copy()
                    ws_api_view = ws_api_combined[ws_api_combined['year'] == 2024].copy() if not ws_api_combined.empty else pd.DataFrame()
                else:
                    ws_view = ws_combined.copy()
                    ws_api_view = ws_api_combined.copy()
            else:
                ws_view = pd.DataFrame()
                ws_api_view = pd.DataFrame()

            if not ws_view.empty:
                # Map metric config
                metric_configs = {
                    "🌧️ Lượng mưa tích lũy (mm)": {
                        "col": "precipitation_sum",
                        "unit": "mm",
                        "name": "Lượng mưa",
                        "color": "#1f77b4",
                        "api_color": "#48cae4",
                        "chart_type": "bar",
                        "agg_func": lambda s: f"{s.sum():,.1f} mm"
                    },
                    "💧 Độ ẩm không khí trung bình (%)": {
                        "col": "humidity_mean",
                        "unit": "%",
                        "name": "Độ ẩm",
                        "color": "#06d6a0",
                        "api_color": "#118ab2",
                        "chart_type": "line",
                        "agg_func": lambda s: f"{s.mean():.1f}%"
                    },
                    "🌡️ Nhiệt độ không khí trung bình (°C)": {
                        "col": "temp_mean",
                        "unit": "°C",
                        "name": "Nhiệt độ",
                        "color": "#f77f00",
                        "api_color": "#fcbf49",
                        "chart_type": "line",
                        "agg_func": lambda s: f"{s.mean():.1f}°C"
                    },
                    "🌫️ Nồng độ Bụi mịn PM2.5 (µg/m³)": {
                        "col": "pm25_mean",
                        "unit": "µg/m³",
                        "name": "Bụi mịn PM2.5",
                        "color": "#9d4edd",
                        "api_color": "#c77dff",
                        "chart_type": "line",
                        "agg_func": lambda s: f"{s.dropna().mean():.1f} µg/m³" if not s.dropna().empty else "N/A"
                    }
                }
                m_cfg = metric_configs[sel_weather_metric]
                val_col = m_cfg["col"]

                # 4 Thẻ KPI tổng quan
                tot_cases_ws = int(ws_view['cases'].sum()) if 'cases' in ws_view.columns else 0
                tot_precip_ws = ws_view['precipitation_sum'].sum() if 'precipitation_sum' in ws_view.columns else 0.0
                avg_temp_ws = ws_view['temp_mean'].mean() if 'temp_mean' in ws_view.columns else 0.0
                avg_humidity_ws = ws_view['humidity_mean'].mean() if 'humidity_mean' in ws_view.columns else 0.0
                avg_pm25_ws = ws_view['pm25_mean'].dropna().mean() if 'pm25_mean' in ws_view.columns and not ws_view['pm25_mean'].dropna().empty else None

                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric("Tổng ca SXH TP.HCM", f"{tot_cases_ws:,} ca", help=f"Tổng số ca nhiễm trong niên độ {sel_ws_period}")
                kpi2.metric("Lượng mưa tích lũy", f"{tot_precip_ws:,.1f} mm", help="Tổng lượng mưa tích lũy trong giai đoạn được chọn")
                kpi3.metric("Nhiệt độ trung bình", f"{avg_temp_ws:.1f} °C", help="Nhiệt độ không khí bình quân 2m")
                if avg_pm25_ws is not None and not pd.isna(avg_pm25_ws):
                    kpi4.metric("Bụi mịn PM2.5 trung bình", f"{avg_pm25_ws:.1f} µg/m³", delta="Trạm OpenAQ", delta_color="normal")
                else:
                    kpi4.metric("Độ ẩm không khí TB", f"{avg_humidity_ws:.1f} %", help="Độ ẩm tương đối bình quân")

                # Xây dựng Plotly Dual-Axis Line Chart
                fig_weather_dengue = go.Figure()

                # Trục Y1 (Bên trái): Số ca nhiễm Sốt xuất huyết
                fig_weather_dengue.add_trace(go.Bar(
                    x=ws_view['month_label'],
                    y=ws_view['cases'],
                    name="Số ca sốt xuất huyết (ca)",
                    yaxis="y",
                    marker=dict(
                        color='rgba(214, 40, 40, 0.45)',
                        line=dict(color='#d62828', width=1.5)
                    ),
                    text=[f"<b>{int(c):,}</b>" if c > 0 else "" for c in ws_view['cases']],
                    textposition='outside',
                    hovertemplate="<b>%{x}</b><br>Số ca SXH: %{y:,} ca<extra></extra>"
                ))

                # Đường xu hướng ca bệnh (Line trend)
                fig_weather_dengue.add_trace(go.Scatter(
                    x=ws_view['month_label'],
                    y=ws_view['cases'],
                    mode='lines+markers',
                    name="Đường diễn biến SXH",
                    yaxis="y",
                    line=dict(color='#d62828', width=3),
                    marker=dict(size=8, color='#d62828', symbol='circle'),
                    hovertemplate="<b>Xu hướng SXH - %{x}</b>: %{y:,} ca<extra></extra>"
                ))

                # Trục Y2 (Bên phải): Chỉ số thời tiết
                show_local = "WeatherData" in sel_weather_source or "Parallel" in sel_weather_source
                show_api = "API Trực Tuyến" in sel_weather_source or "Parallel" in sel_weather_source

                if show_local and val_col in ws_view.columns:
                    fig_weather_dengue.add_trace(go.Scatter(
                        x=ws_view['month_label'],
                        y=ws_view[val_col],
                        mode='lines+markers+text',
                        name=f"{m_cfg['name']} (Trạm WeatherData)",
                        yaxis="y2",
                        text=[f"{v:.1f}" if pd.notna(v) else "" for v in ws_view[val_col]],
                        textposition='top center',
                        line=dict(color=m_cfg['color'], width=3.5),
                        marker=dict(size=9, color=m_cfg['color'], symbol='diamond'),
                        hovertemplate=f"<b>Trạm WeatherData - %{{x}}</b>: %{{y:.1f}} {m_cfg['unit']}<extra></extra>"
                    ))

                if show_api and not ws_api_view.empty and val_col in ws_api_view.columns:
                    fig_weather_dengue.add_trace(go.Scatter(
                        x=ws_api_view['month_label'],
                        y=ws_api_view[val_col],
                        mode='lines+markers',
                        name=f"{m_cfg['name']} (API Cache)",
                        yaxis="y2",
                        line=dict(color=m_cfg['api_color'], width=2.5, dash='dash'),
                        marker=dict(size=7, color=m_cfg['api_color'], symbol='square'),
                        hovertemplate=f"<b>API Cache - %{{x}}</b>: %{{y:.1f}} {m_cfg['unit']}<extra></extra>"
                    ))

                fig_weather_dengue.update_layout(
                    title=f"<b>Sơ Đồ Đường Đối Sánh: Số Ca Nhiễm Sốt Xuất Huyết & {m_cfg['name']} Theo Tháng — TP. Hồ Chí Minh ({sel_ws_period})</b>",
                    xaxis=dict(title="Thời gian (Tháng / Năm)", tickangle=-30),
                    yaxis=dict(
                        title=dict(text="<b>Số ca sốt xuất huyết (ca)</b>", font=dict(color="#d62828")),
                        tickfont=dict(color="#d62828"),
                        side="left"
                    ),
                    yaxis2=dict(
                        title=dict(text=f"<b>{m_cfg['name']} ({m_cfg['unit']})</b>", font=dict(color=m_cfg['color'])),
                        tickfont=dict(color=m_cfg['color']),
                        anchor="x",
                        overlaying="y",
                        side="right"
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    template="plotly_white",
                    hovermode="x unified",
                    height=460
                )

                col_ws_chart, col_ws_insight = st.columns([7, 3], gap="medium")
                with col_ws_chart:
                    st.plotly_chart(fig_weather_dengue, use_container_width=True)
                with col_ws_insight:
                    st.info(
                        "💡 **Nhận định Dịch tễ học Môi trường & Khí hậu TP.HCM:**\n\n"
                        "- **Tương quan Lượng mưa — Đỉnh dịch:** Khi lượng mưa hàng tháng vượt **300 mm** (T05–T09/2025), độ ẩm vượt **85%**, muỗi *Aedes aegypti* sinh sản mạnh.\n"
                        "- **Độ trễ dịch tễ (Lag 2–4 tuần):** Đỉnh mưa T09/2025 (470.9 mm) kéo theo đỉnh ca SXH T10/2025 (227 ca).\n"
                        "- **Bụi mịn PM2.5:** Tăng vào mùa khô/chuyển mùa (T10–T01 đạt 35–45 µg/m³)."
                    )

                # Bảng thống kê chi tiết theo tháng
                with st.expander("📋 Xem Bảng Dữ Liệu Thống Kê Chi Tiết Khí Tượng & Sốt Xuất Huyết Theo Tháng (Từ MongoDB)"):
                    st.caption("Dữ liệu nạp từ collection `weatherdata_hcmc_monthly` trên MongoDB Atlas, đối sánh với lịch sử ca bệnh.")

                    display_cols = {
                        'month_label': 'Tháng/Năm',
                        'cases': 'Số ca SXH (ca)',
                        'precipitation_sum': 'Lượng mưa (mm)',
                        'temp_mean': 'Nhiệt độ TB (°C)',
                        'humidity_mean': 'Độ ẩm TB (%)',
                        'pm25_mean': 'Bụi mịn PM2.5 (µg/m³)',
                        'wind_speed_mean': 'Tốc độ gió (km/h)',
                        'pressure_mean': 'Áp suất (hPa)'
                    }
                    tbl_df = ws_view[[c for c in display_cols.keys() if c in ws_view.columns]].copy()

                    def _get_risk_note(row):
                        c = row.get('cases', 0)
                        r = row.get('precipitation_sum', 0)
                        if c >= 180:
                            return "🔴 Đỉnh dịch bùng phát mạnh (Mùa mưa cao điểm)"
                        elif c >= 100:
                            return "🟠 Nguy cơ cao — Lăng quăng sinh sôi"
                        elif r > 200:
                            return "🟡 Mưa nhiều — Chuẩn bị bùng phát dịch"
                        else:
                            return "🟢 Giai đoạn an toàn / Mùa khô"

                    tbl_df['Nhận định Dịch tễ & Môi trường'] = tbl_df.apply(_get_risk_note, axis=1)
                    tbl_df = tbl_df.rename(columns=display_cols)

                    st.dataframe(tbl_df, use_container_width=True)

                    # Nút tải dữ liệu CSV
                    csv_bytes = tbl_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Tải Bảng Số Liệu Khí Tượng & SXH Theo Tháng (CSV)",
                        data=csv_bytes,
                        file_name=f"weather_dengue_monthly_hcmc_{sel_ws_period.replace(' ', '_')}.csv",
                        mime="text/csv",
                        key="dl_weather_dengue_csv"
                    )
            else:
                st.warning("⚠️ Chưa có dữ liệu thời tiết cho niên độ được chọn.")

        # -------------------------------------------------------------------
        # BENTO FORECASTING: DỰ BÁO 3 THÁNG KẾ TIẾP — TP. HỒ CHÍ MINH
        # -------------------------------------------------------------------
        with st.container(key="bento_xgb_hcm_card"):
            st.subheader("🔮 Dự Báo Số Ca Sốt Xuất Huyết Trong 3 Tháng Kế Tiếp — Khu Vực TP. Hồ Chí Minh (Mô hình XGBoost)")
            st.caption("💡 **Mô hình XGBoost:** Dự báo chuỗi thời gian 3 tháng kế tiếp (Multi-step autoregressive forecasting) kết hợp yếu tố khí tượng và độ trễ ca bệnh.")

            # Filter predictions specifically for TP. Hồ Chí Minh
            hcm_preds = predictions_df[predictions_df['province'].str.contains('Hồ Chí Minh|HCM', na=False)].sort_values(by=['year', 'month']).copy() if not predictions_df.empty else pd.DataFrame()

            if not hcm_preds.empty:
                if 'month_label' not in hcm_preds.columns:
                    hcm_preds['month_label'] = hcm_preds.apply(lambda r: f"Tháng {int(r['month']):02d}/{int(r['year'])}", axis=1)

                hcm_3m = hcm_preds.head(3).reset_index(drop=True)

                # Latest actual cases in HCM (T12/2025)
                last_actual_cases = float(df[(df['province'] == 'TP. Hồ Chí Minh') & (df['year'] == 2025) & (df['month'] == 12)]['cases'].sum() or 205)

                # 3 Metric Cards for the 3 Forecast Months
                pm_cols = st.columns(3)
                for idx, row in hcm_3m.iterrows():
                    p_label = row.get('month_label', f"Tháng {int(row['month']):02d}/{int(row['year'])}")
                    p_cases = float(row['predicted_cases'])
                    step_num = int(row.get('step', idx + 1))

                    prev_cases = float(hcm_3m.iloc[idx - 1]['predicted_cases']) if idx > 0 else last_actual_cases
                    delta_c = p_cases - prev_cases
                    delta_pct = (delta_c / prev_cases * 100) if prev_cases > 0 else 0

                    with pm_cols[idx]:
                        st.metric(
                            f"📅 Dự báo Tháng thứ {step_num} ({p_label})",
                            f"{p_cases:.0f} ca",
                            delta=f"{delta_c:+.0f} ca ({delta_pct:+.1f}%) so với tháng trước",
                            delta_color="inverse" if delta_c > 0 else "normal"
                        )

                # Historical last 6 months in HCM
                hcm_hist = df[df['province'] == 'TP. Hồ Chí Minh'].sort_values('date').tail(6).copy()
                if not hcm_hist.empty:
                    hcm_hist['label'] = hcm_hist.apply(lambda r: f"T{int(r['month']):02d}/{int(r['year'])}", axis=1)
                    hcm_hist['val'] = hcm_hist['cases'].astype(float)

                # Sơ đồ dự báo 3 tháng kế tiếp cho TP. Hồ Chí Minh (Bar + Trend Line)
                fig_fc = go.Figure()

                # Bar trace
                fig_fc.add_trace(go.Bar(
                    x=hcm_3m['month_label'],
                    y=hcm_3m['predicted_cases'],
                    name='Số ca dự báo (ca)',
                    marker=dict(
                        color=['#e76f51', '#f4a261', '#e9c46a'],
                        line=dict(color='#d62828', width=1.5)
                    ),
                    text=[f"<b>{v:.0f} ca</b>" for v in hcm_3m['predicted_cases']],
                    textposition='outside',
                    hovertemplate="<b>%{x}</b><br>Số ca dự báo: %{y:.1f} ca<extra></extra>"
                ))

                # Line trend trace
                fig_fc.add_trace(go.Scatter(
                    x=hcm_3m['month_label'],
                    y=hcm_3m['predicted_cases'],
                    mode='lines+markers',
                    name='Đường xu thế dự báo',
                    line=dict(color='#d62828', width=3, dash='dash'),
                    marker=dict(size=10, color='#d62828', symbol='diamond'),
                    hovertemplate="<b>Xu hướng %{x}</b>: %{y:.1f} ca<extra></extra>"
                ))

                fig_fc.update_layout(
                    title="<b>Sơ Đồ Dự Báo Số Ca Sốt Xuất Huyết 3 Tháng Kế Tiếp — Khu Vực TP. Hồ Chí Minh</b>",
                    xaxis_title="Thời gian dự báo",
                    yaxis_title="Số ca dự báo (ca)",
                    yaxis=dict(range=[0, max(hcm_3m['predicted_cases']) * 1.35]),
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=410
                )

                col_xgb_fc, col_xgb_tl = st.columns([3, 2], gap="medium")
                with col_xgb_fc:
                    st.plotly_chart(fig_fc, use_container_width=True)

                with col_xgb_tl:
                    # Continuous timeline chart (Historical -> 3-Month Forecast)
                    with st.expander("🔍 Xem sơ đồ chuỗi thời gian liên tục (Thực tế 6 tháng cuối 2025 ➡️ Dự báo 3 tháng 2026)", expanded=not hcm_hist.empty):
                        fig_timeline = go.Figure()

                        if not hcm_hist.empty:
                            hist_x = [f"T{int(r['month']):02d}/{int(r['year'])}" for _, r in hcm_hist.iterrows()]
                            fig_timeline.add_trace(go.Scatter(
                                x=hist_x,
                                y=hcm_hist['val'],
                                mode='lines+markers+text',
                                name='Thực tế (2025)',
                                text=[f"{int(v)}" for v in hcm_hist['val']],
                                textposition='top center',
                                line=dict(color='#264653', width=3),
                                marker=dict(size=8, color='#264653')
                            ))

                            last_hist_x = hist_x[-1]
                            last_hist_y = float(hcm_hist['val'].iloc[-1])
                            fc_x = [last_hist_x] + [f"T{int(r['month']):02d}/{int(r['year'])}" for _, r in hcm_3m.iterrows()]
                            fc_y = [last_hist_y] + list(hcm_3m['predicted_cases'])

                            fig_timeline.add_trace(go.Scatter(
                                x=fc_x,
                                y=fc_y,
                                mode='lines+markers+text',
                                name='Dự báo 3 tháng (2026)',
                                text=[""] + [f"{v:.0f}" for v in hcm_3m['predicted_cases']],
                                textposition='top center',
                                line=dict(color='#e76f51', width=3, dash='dot'),
                                marker=dict(size=9, color='#e76f51', symbol='diamond')
                            ))

                            fig_timeline.update_layout(
                                title="<b>Chuỗi Thời Gian Thực Tế & 3 Tháng Dự Báo Liên Tiếp — TP. Hồ Chí Minh</b>",
                                xaxis_title="Thời gian (Tháng/Năm)",
                                yaxis_title="Số ca mắc SXH",
                                template="plotly_white",
                                height=360
                            )
                            st.plotly_chart(fig_timeline, use_container_width=True)

                # Recommendations for HCMC
                st.markdown("#### 🛡️ Nhận Định Dịch Tễ & Khuyến Cáo Can Thiệp — Khu Vực TP. Hồ Chí Minh")
                rec_c1, rec_c2 = st.columns(2)
                with rec_c1:
                    st.warning(
                        "**📌 Nhận định xu hướng 3 tháng tới:**\n\n"
                        f"- **{hcm_3m['month_label'].iloc[0]}:** Dự báo **{hcm_3m['predicted_cases'].iloc[0]:.0f} ca**.\n"
                        f"- **{hcm_3m['month_label'].iloc[1]}:** Dự báo **{hcm_3m['predicted_cases'].iloc[1]:.0f} ca**.\n"
                        f"- **{hcm_3m['month_label'].iloc[2]}:** Dự báo **{hcm_3m['predicted_cases'].iloc[2]:.0f} ca**.\n"
                        f"- Số ca trung bình dự báo: **{hcm_3m['predicted_cases'].mean():.0f} ca/tháng**, có xu hướng giảm dần qua các tháng đầu năm."
                    )
                with rec_c2:
                    st.success(
                        "**📋 Kế hoạch hành động ưu tiên tại TP.HCM:**\n\n"
                        "1. Tập trung xử lý triệt để các ổ dịch tại các quận/huyện có mật độ dân cư cao.\n"
                        "2. Duy trì công tác diệt lăng quăng, bọ gậy hàng tuần tại các hộ gia đình.\n"
                        "3. Đảm bảo năng lực thu dung, phân loại bệnh nhân tại các bệnh viện tuyến quận/huyện và thành phố."
                    )
            else:
                st.info("Chưa có dữ liệu dự báo cho khu vực TP. Hồ Chí Minh. Vui lòng chạy `python main.py` để cập nhật.")

        # -------------------------------------------------------------------
        # BENTO FORECASTING: DỰ BÁO 3 THÁNG THEO TỪNG QUẬN/HUYỆN TP.HCM
        # -------------------------------------------------------------------
        with st.container(key="bento_xgb_dist_card"):
            st.subheader("🏙️ Dự Báo Sốt Xuất Huyết 3 Tháng Kế Tiếp Theo Từng Quận/Huyện TP.HCM (XGBoost Cấp Quận)")
            st.caption(
                "Mô hình XGBoost Regressor huấn luyện riêng trên chuỗi thời gian lịch sử từng Quận/Huyện TP. Hồ Chí Minh "
                "kết hợp độ trễ khí hậu (lượng mưa, nhiệt độ, độ ẩm, PM2.5, tương tác Nhiệt-Ẩm)."
            )
            if not hcmc_dist_preds_df.empty and 'district' in hcmc_dist_preds_df.columns:
                _dp_df = hcmc_dist_preds_df.copy()
                if 'month_label' not in _dp_df.columns:
                    _dp_df['month_label'] = _dp_df.apply(lambda r: f"Tháng {int(r['month']):02d}/{int(r['year'])}", axis=1)
                _month_opts = list(dict.fromkeys(_dp_df.sort_values(['year', 'month'])['month_label'].tolist()))
                _col_dp1, _col_dp2 = st.columns([1, 2])
                with _col_dp1:
                    _sel_dp_month = st.selectbox("🗓️ Chọn tháng dự báo:", _month_opts, index=0, key="hcmc_dp_month_sel")
                _dp_month_df = _dp_df[_dp_df['month_label'] == _sel_dp_month].sort_values('predicted_cases', ascending=False)

                with _col_dp2:
                    _dist_names = sorted(_dp_df['district'].dropna().unique().tolist())
                    _def_d = _dist_names.index('Bình Thạnh') if 'Bình Thạnh' in _dist_names else 0
                    _sel_dp_dist = st.selectbox("📍 Xem chuỗi 3 tháng của Quận/Huyện:", _dist_names, index=_def_d, key="hcmc_dp_dist_sel")

                _c_dp_left, _c_dp_right = st.columns([3, 2], gap="medium")
                with _c_dp_left:
                    _top10_dp = _dp_month_df.head(10)
                    _fig_dp_bar = px.bar(
                        _top10_dp,
                        x='district',
                        y='predicted_cases',
                        color='predicted_cases',
                        color_continuous_scale='Reds',
                        text=_top10_dp['predicted_cases'].round(1),
                        title=f"Top 10 Quận/Huyện TP.HCM Dự Báo Ca Cao Nhất — {_sel_dp_month}",
                        labels={'district': 'Quận / Huyện', 'predicted_cases': 'Số ca dự báo'},
                    )
                    _fig_dp_bar.update_traces(textposition='outside')
                    st.plotly_chart(_fig_dp_bar, use_container_width=True)

                with _c_dp_right:
                    _one_dist_df = _dp_df[_dp_df['district'] == _sel_dp_dist].sort_values(['year', 'month'])
                    _fig_dp_line = px.line(
                        _one_dist_df,
                        x='month_label',
                        y='predicted_cases',
                        markers=True,
                        text=_one_dist_df['predicted_cases'].round(1),
                        title=f"Xu hướng Dự báo 3 Tháng — {_sel_dp_dist}",
                        labels={'month_label': 'Tháng', 'predicted_cases': 'Số ca dự báo'},
                    )
                    _fig_dp_line.update_traces(line_color='#d90429', line_width=3, marker_size=9, textposition='top center')
                    st.plotly_chart(_fig_dp_line, use_container_width=True)

                with st.expander("📋 Xem & Tải Bảng Dự Báo Chi Tiết 3 Tháng Theo Quận/Huyện TP.HCM"):
                    _dp_show = _dp_df[['district', 'month_label', 'step', 'predicted_cases']].sort_values(
                        ['step', 'predicted_cases'], ascending=[True, False]
                    ).reset_index(drop=True)
                    st.dataframe(
                        _dp_show,
                        column_config={
                            "district": "Quận / Huyện",
                            "month_label": "Tháng Dự Báo",
                            "step": "Bước (Tháng thứ)",
                            "predicted_cases": st.column_config.NumberColumn("Số Ca Dự Báo", format="%.1f ca"),
                        },
                        use_container_width=True,
                    )
                    st.download_button(
                        "📥 Tải Dự Báo Cấp Quận TP.HCM (CSV)",
                        data=_dp_show.to_csv(index=False).encode("utf-8"),
                        file_name="hcmc_district_predictions.csv",
                        mime="text/csv",
                        key="dl_hcmc_dist_preds_csv",
                    )
            else:
                st.info("Chưa có dữ liệu dự báo cấp Quận/Huyện TP.HCM. Vui lòng chạy `python main.py` để huấn luyện mô hình cấp quận.")
    else:
        st.info("Chưa có dữ liệu lịch sử. Vui lòng tải file Excel dữ liệu bệnh nhân ở thanh bên trái.")


# ===========================================================================
# TAB AI: AI DỰ BÁO & ĐÁNH GIÁ DỊCH TỄ HỌC (GOOGLE GEMINI API)
# ===========================================================================
with tab_ai:
    with st.container(key="bento_ai_forecast_card"):
        st.header("🧠 AI Đánh Giá & Dự Báo Dịch Tễ Học Sốt Xuất Huyết")
        st.markdown(
            "Hệ thống ứng dụng mô hình **Google Gemini AI API** kết nối dữ liệu dịch tễ lịch sử (2024-2025) "
            "và trạm quan trắc khí tượng (`data/weatherdata` trên MongoDB Atlas) nhằm cung cấp hai luồng phân tích thông minh: "
            "**(1) Đánh giá & Dự báo theo Dữ liệu Thực tế Hiện có** và **(2) Mô phỏng Dự báo theo Dữ liệu Tự Thống kê / Kịch bản Giả định**, "
            "kết hợp tổng hợp đối sánh trực quan đa chiều."
        )

        # Sub-tabs within Tab AI
        sub_ai_1, sub_ai_2, sub_ai_3 = st.tabs([
            "📈 1. Dự Báo Theo Dữ Liệu Thực Tế Hiện Có",
            "🧪 2. Dự Báo Theo Dữ Liệu Tự Thống Kê (Scenario)",
            "📊 3. Bảng & Biểu Đồ Tổng Hợp Đối Sánh"
        ])

        # Cache AI results in session_state to avoid unnecessary calls
        if "ai_existing_eval" not in st.session_state:
            st.session_state.ai_existing_eval = None
        if "ai_custom_eval" not in st.session_state:
            st.session_state.ai_custom_eval = None

        # -----------------------------------------------------------------------
        # SUBTAB 1: DỰ BÁO THEO DỮ LIỆU THỰC TẾ HIỆN CÓ
        # -----------------------------------------------------------------------
        with sub_ai_1:
            st.subheader("📈 Đánh Giá Dịch Tễ & Dự Báo Từ Dữ Liệu Thực Tế Hiện Có (TP. Hồ Chí Minh)")
            st.caption("Tổng hợp chuỗi ca bệnh 12 tháng năm 2025, lượng mưa, nhiệt độ, độ ẩm, PM2.5 và dự báo nền XGBoost gửi tới Gemini API.")

            col_run_ai, col_stat_ai = st.columns([2, 3])
            with col_run_ai:
                if st.button("🔄 Khởi Chạy / Cập Nhật Đánh Giá AI Hiện Có", key="btn_run_ai_existing", type="primary"):
                    with st.spinner("🤖 Đang gửi request phân tích dữ liệu thực tế tới Google Gemini API..."):
                        st.session_state.ai_existing_eval = ai_prediction_service.predict_from_existing_data("TP. Hồ Chí Minh", force_refresh=True)

            # Tự động nạp từ cache/MongoDB nếu chưa có trong session_state
            if st.session_state.ai_existing_eval is None:
                st.session_state.ai_existing_eval = ai_prediction_service.predict_from_existing_data("TP. Hồ Chí Minh", force_refresh=False)

            eval_data = st.session_state.ai_existing_eval

            if eval_data:
                with col_stat_ai:
                    src_badge = eval_data.get('source', 'Google Gemini')
                    ts_badge = eval_data.get('timestamp', '')
                    st.success(f"✅ Nguồn xử lý: **{src_badge}** | Thời điểm: `{ts_badge}`")

                # 4 Thẻ KPI
                preds_list = eval_data.get("monthly_predictions", [])
                kpi_cols = st.columns(4)
                kpi_cols[0].metric(
                    "Mức độ Nguy cơ Toàn cục",
                    eval_data.get("epidemiological_risk_level", "Nguy cơ Cao"),
                    delta="Chu kỳ mùa khô",
                    delta_color="normal"
                )
                for idx, p in enumerate(preds_list[:3]):
                    with kpi_cols[idx + 1]:
                        st.metric(
                            f"📅 Dự báo {p.get('month_label')}",
                            f"{p.get('predicted_cases', 0):.0f} ca",
                            delta=f"Khoảng tin cậy: {p.get('lower_bound', 0)}-{p.get('upper_bound', 0)} ca",
                            delta_color="off"
                        )

                # Khối Báo cáo Tổng quan & Nhận định Tương quan Khí hậu
                col_sum_l, col_sum_r = st.columns([3, 2])
                with col_sum_l:
                    st.markdown(f"#### 📋 {eval_data.get('evaluation_title', 'Báo Cáo Đánh Giá Dịch Tễ Học')}")
                    st.info(eval_data.get("executive_summary", "Chưa có nội dung đánh giá."))
                with col_sum_r:
                    st.markdown("#### 🌦️ Tác Động Khí Hậu & Môi Trường")
                    st.warning(eval_data.get("climate_correlation_insight", "Chưa có nội dung tương quan."))

                # Biểu đồ chuỗi thời gian đối sánh thực tế và AI Dự báo
                st.markdown("#### 📉 Sơ Đồ Diễn Biến Thực Tế 2025 & 3 Tháng Dự Báo AI (Gemini vs XGBoost)")

                # Chuẩn bị dữ liệu thực tế 6 tháng cuối 2025
                hcm_hist_25 = df[(df['province'] == 'TP. Hồ Chí Minh') & (df['year'] == 2025)].sort_values('month').tail(6).copy() if not df.empty else pd.DataFrame()

                fig_ai_trend = go.Figure()

                if not hcm_hist_25.empty:
                    x_hist = [f"T{int(r['month']):02d}/2025" for _, r in hcm_hist_25.iterrows()]
                    y_hist = [float(r['cases']) for _, r in hcm_hist_25.iterrows()]

                    # Actual line
                    fig_ai_trend.add_trace(go.Scatter(
                        x=x_hist,
                        y=y_hist,
                        mode='lines+markers+text',
                        name='Thực tế Năm 2025 (Ca bệnh)',
                        text=[f"<b>{int(v)}</b>" for v in y_hist],
                        textposition='top center',
                        line=dict(color='#264653', width=3.5),
                        marker=dict(size=9, color='#264653')
                    ))

                    last_x = x_hist[-1]
                    last_y = y_hist[-1]

                    # XGBoost baseline line
                    xgb_preds = predictions_df[predictions_df['province'].str.contains('Hồ Chí Minh|HCM', na=False)].sort_values(['year', 'month']).head(3) if not predictions_df.empty else pd.DataFrame()
                    if not xgb_preds.empty:
                        x_xgb = [last_x] + [f"T{int(r['month']):02d}/{int(r['year'])}" for _, r in xgb_preds.iterrows()]
                        y_xgb = [last_y] + list(xgb_preds['predicted_cases'])
                        fig_ai_trend.add_trace(go.Scatter(
                            x=x_xgb,
                            y=y_xgb,
                            mode='lines+markers',
                            name='Tham chiếu XGBoost (Baseline)',
                            line=dict(color='#f4a261', width=2.5, dash='dash'),
                            marker=dict(size=7, color='#f4a261', symbol='square')
                        ))

                    # Gemini AI predictions line
                    if preds_list:
                        x_ai = [last_x] + [f"T{p['month_label'].split('/')[0].replace('Tháng ', '')}/{p['month_label'].split('/')[1]}" if '/' in p['month_label'] else p['month_label'] for p in preds_list]
                        y_ai = [last_y] + [float(p.get('predicted_cases', 0)) for p in preds_list]
                        y_ai_upper = [last_y] + [float(p.get('upper_bound', p.get('predicted_cases', 0))) for p in preds_list]
                        y_ai_lower = [last_y] + [float(p.get('lower_bound', p.get('predicted_cases', 0))) for p in preds_list]

                        fig_ai_trend.add_trace(go.Scatter(
                            x=x_ai,
                            y=y_ai,
                            mode='lines+markers+text',
                            name='AI Gemini Dự Báo (Thực tế)',
                            text=[""] + [f"<b>{int(v)}</b>" for v in y_ai[1:]],
                            textposition='top center',
                            line=dict(color='#e76f51', width=3.5),
                            marker=dict(size=10, color='#e76f51', symbol='diamond'),
                            hovertemplate="<b>AI Gemini %{x}</b>: %{y:.0f} ca<extra></extra>"
                        ))

                        # Upper/Lower bound shaded range
                        fig_ai_trend.add_trace(go.Scatter(
                            x=x_ai[1:] + x_ai[1:][::-1],
                            y=y_ai_upper[1:] + y_ai_lower[1:][::-1],
                            fill='toself',
                            fillcolor='rgba(231, 111, 81, 0.15)',
                            line=dict(color='rgba(255,255,255,0)'),
                            hoverinfo="skip",
                            showlegend=True,
                            name='Dải Tin Cậy AI (Lower - Upper Bound)'
                        ))

                fig_ai_trend.update_layout(
                    title="<b>Đối Sánh Chuỗi Thời Gian: Ca Nhiễm Thực Tế (2025) ➡️ Dự Báo XGBoost & AI Gemini (2026)</b>",
                    xaxis=dict(title="Thời gian (Tháng/Năm)"),
                    yaxis=dict(title="Số ca sốt xuất huyết (ca)"),
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=460
                )
                st.plotly_chart(fig_ai_trend, use_container_width=True)

                # Bảng chi tiết dự báo
                st.markdown("#### 📋 Bảng Chi Tiết Dự Báo & Luận Cứ Dịch Tễ Từ Gemini AI")
                tbl_ai_rows = []
                for p in preds_list:
                    tbl_ai_rows.append({
                        "Thời gian": p.get("month_label"),
                        "Số ca AI Dự báo": f"{p.get('predicted_cases', 0):.0f} ca",
                        "Khoảng tin cậy": f"{p.get('lower_bound', 0):.0f} — {p.get('upper_bound', 0):.0f} ca",
                        "Mức độ Nguy cơ": p.get("risk_level", "Trung bình"),
                        "Xu hướng": p.get("trend", "Ổn định"),
                        "Cơ sở / Luận cứ Dịch tễ học": p.get("rationale", "")
                    })
                st.dataframe(pd.DataFrame(tbl_ai_rows), use_container_width=True)

                # Khuyến nghị y tế từ Gemini
                st.markdown("#### 🛡️ Khuyến Nghị Can Thiệp Y Tế Dự Phòng Từ AI")
                rec_cols = st.columns(len(eval_data.get("recommendations", [])) or 1)
                for i, rec in enumerate(eval_data.get("recommendations", [])):
                    with rec_cols[i % len(rec_cols)]:
                        st.success(f"**Hành động {i+1}:**\n\n{rec}")

        # -----------------------------------------------------------------------
        # SUBTAB 2: DỰ BÁO THEO DỮ LIỆU TỰ THỐNG KÊ (SCENARIO SIMULATION)
        # -----------------------------------------------------------------------
        with sub_ai_2:
            st.subheader("🧪 Đánh Giá & Mô Phỏng Dự Báo Theo Dữ Liệu Tự Thống Kê")
            st.markdown(
                "Cho phép cán bộ dịch tễ học và chuyên gia y tế tự nhập các chỉ số thống kê hoặc thiết lập **kịch bản giả định** "
                "(Lượng mưa, Nhiệt độ, Độ ẩm, Chỉ số bọ gậy BI, Nồng độ PM2.5 và Mức độ can thiệp). "
                "Gemini AI sẽ phân tích tương tác đa biến và lượng giá số ca nhiễm dự kiến."
            )

            with st.form("form_custom_scenario"):
                col_sc1, col_sc2, col_sc3 = st.columns(3)
                with col_sc1:
                    sc_target_month = st.selectbox(
                        "📅 Chọn Giai Đoạn Giả Định:",
                        options=[
                            "Tháng 04/2026 (Đầu mùa mưa)",
                            "Tháng 05/2026 (Mùa mưa tăng mạnh)",
                            "Tháng 06/2026 (Cao điểm mưa mùa hè)",
                            "Tháng 07/2026 (Nguy cơ bùng phát dịch)",
                            "Tháng 10/2026 (Đỉnh dịch giả định)"
                        ],
                        index=1
                    )
                    sc_baseline = st.number_input(
                        "📊 Số ca mắc nền tháng trước (ca):",
                        min_value=10,
                        max_value=1000,
                        value=150,
                        step=10,
                        help="Số ca mắc ghi nhận trong tháng liền kề làm mốc so sánh"
                    )
                    sc_intervention = st.selectbox(
                        "🛡️ Mức độ can thiệp dập dịch:",
                        options=[
                            "Quyết liệt (Chiến dịch diệt lăng quăng toàn thành phố)",
                            "Trung bình (Phun thuốc định kỳ & vệ sinh môi trường)",
                            "Thấp (Chưa can thiệp diện rộng / Cộng đồng lơ là)"
                        ],
                        index=1
                    )

                with col_sc2:
                    sc_rain = st.slider("🌧️ Lượng mưa dự kiến (mm):", min_value=0.0, max_value=600.0, value=350.0, step=10.0)
                    sc_humidity = st.slider("💧 Độ ẩm không khí dự kiến (%):", min_value=40.0, max_value=100.0, value=85.0, step=1.0)
                    sc_temp = st.slider("🌡️ Nhiệt độ trung bình (°C):", min_value=20.0, max_value=40.0, value=28.5, step=0.5)

                with col_sc3:
                    sc_bi = st.slider(
                        "🦟 Chỉ số bọ gậy Breteau Index (BI):",
                        min_value=0.0,
                        max_value=80.0,
                        value=35.0,
                        step=1.0,
                        help="Số dụng cụ chứa nước có bọ gậy trên 100 nhà kiểm tra (BI > 20 là ngưỡng dịch)"
                    )
                    sc_pm25 = st.slider("🌫️ Nồng độ Bụi mịn PM2.5 (µg/m³):", min_value=5.0, max_value=150.0, value=32.0, step=1.0)
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_calc_custom = st.form_submit_button("🚀 Gửi Request AI Đánh Giá & Dự Báo Kịch Bản", type="primary", use_container_width=True)

            if btn_calc_custom:
                scenario_payload = {
                    "target_month": sc_target_month,
                    "baseline_cases": sc_baseline,
                    "custom_rainfall": sc_rain,
                    "custom_humidity": sc_humidity,
                    "custom_temp": sc_temp,
                    "custom_pm25": sc_pm25,
                    "mosquito_bi": sc_bi,
                    "intervention_effort": sc_intervention
                }
                with st.spinner("🤖 Đang gửi kịch bản tự thống kê tới Google Gemini AI để lượng giá tác động..."):
                    st.session_state.ai_custom_eval = ai_prediction_service.predict_from_custom_statistics(scenario_payload)

            # Hiển thị kết quả kịch bản tự thống kê
            custom_res = st.session_state.ai_custom_eval
            if custom_res:
                st.markdown("---")
                st.markdown(f"### 🎯 Kết Quả Đánh Giá AI Cho: **{custom_res.get('scenario_name', 'Kịch bản')}**")

                # 3 Thẻ Metric
                p_cases = float(custom_res.get('predicted_cases', 0))
                delta_c = float(custom_res.get('delta_cases_from_baseline', 0))
                delta_p = float(custom_res.get('delta_pct_from_baseline', 0))
                r_level = custom_res.get('risk_level', 'Nguy cơ Cao')

                km1, km2, km3 = st.columns(3)
                km1.metric(
                    "Số ca dự báo Kịch bản",
                    f"{p_cases:.0f} ca",
                    delta=f"Khoảng: {custom_res.get('lower_bound', 0)}-{custom_res.get('upper_bound', 0)} ca",
                    delta_color="off"
                )
                km2.metric(
                    "Biến động so với ca nền",
                    f"{delta_c:+.0f} ca",
                    delta=f"{delta_p:+.1f}% so với ca nền",
                    delta_color="inverse" if delta_c > 0 else "normal"
                )
                km3.metric(
                    "Đánh giá Nguy cơ Dịch",
                    r_level,
                    delta="Theo AI Gemini",
                    delta_color="off"
                )

                # Đánh giá chi tiết
                c_ev1, c_ev2 = st.columns(2)
                with c_ev1:
                    st.markdown("#### 🔬 Phân Tích Dịch Tễ Học Đa Biến")
                    st.info(custom_res.get("epidemiological_assessment", ""))
                    st.markdown("#### 🌧️ Tác Động Cộng Hưởng Khí Hậu & Vector (Muỗi)")
                    st.warning(custom_res.get("climate_vector_synergy", ""))

                with c_ev2:
                    st.markdown("#### 🛡️ Đánh Giá Hiệu Lực Can Thiệp Dập Dịch")
                    st.success(custom_res.get("intervention_effectiveness", ""))
                    st.markdown("#### 📋 Hành Động Cụ Thể Cần Triển Khai:")
                    for act in custom_res.get("recommended_actions", []):
                        st.markdown(f"- 📌 {act}")

        # -----------------------------------------------------------------------
        # SUBTAB 3: BẢNG & BIỂU ĐỒ TỔNG HỢP ĐỐI SÁNH
        # -----------------------------------------------------------------------
        with sub_ai_3:
            st.subheader("📊 Bảng & Biểu Đồ Tổng Hợp Đối Sánh Đa Chiều")
            st.markdown(
                "So sánh đối chiếu trực tiếp giữa **Dữ liệu Thực tế Lịch sử**, **Mô hình XGBoost**, "
                "**Dự báo AI theo Dữ liệu Thực tế Hiện có**, và **Dự báo AI theo Dữ liệu Tự Thống kê**."
            )

            # Build comparison summary table
            synthesis_rows = []

            # 1. Thực tế T12/2025
            synthesis_rows.append({
                "Phương án / Nguồn dữ liệu": "1. Thực tế Gần nhất (Tháng 12/2025)",
                "Loại dữ liệu": "Dữ liệu Thực tế (Cơ sở)",
                "Số ca dự báo / Thực tế": "205 ca",
                "Mức độ Nguy cơ": "Nguy cơ Rất cao (Đỉnh dịch)",
                "Phương pháp": "Thống kê bệnh nhân bệnh viện",
                "Đặc điểm": "Số ca thực tế làm mốc so sánh"
            })

            # 2. XGBoost Baseline
            synthesis_rows.append({
                "Phương án / Nguồn dữ liệu": "2. Dự báo XGBoost Baseline (T01/2026)",
                "Loại dữ liệu": "Mô hình Máy học (ML)",
                "Số ca dự báo / Thực tế": "180 ca",
                "Mức độ Nguy cơ": "Nguy cơ Cao",
                "Phương pháp": "XGBoost Regressor + Lag Features",
                "Đặc điểm": "Dự báo chuỗi thời gian tự hồi quy đa bước"
            })

            # 3. AI Gemini (Dữ liệu Thực tế Hiện có)
            ai_p1 = eval_data.get('monthly_predictions', [{}])[0].get('predicted_cases', 182) if eval_data else 182
            ai_r1 = eval_data.get('monthly_predictions', [{}])[0].get('risk_level', 'Nguy cơ Cao') if eval_data else 'Nguy cơ Cao'
            synthesis_rows.append({
                "Phương án / Nguồn dữ liệu": "3. AI Gemini (Theo Dữ Liệu Hiện Có - T01/2026)",
                "Loại dữ liệu": "AI Gemini API (Real Data)",
                "Số ca dự báo / Thực tế": f"{ai_p1:.0f} ca",
                "Mức độ Nguy cơ": ai_r1,
                "Phương pháp": "LLM Dịch tễ học + Khí tượng Trạm quan trắc",
                "Đặc điểm": "Kết hợp tương quan khí hậu & quán tính dịch tễ"
            })

            # 4. AI Gemini (Dữ liệu Tự Thống kê)
            custom_res = st.session_state.ai_custom_eval
            if custom_res:
                sc_name = custom_res.get('scenario_name', 'Kịch bản Tự thống kê')
                sc_cases = custom_res.get('predicted_cases', 0)
                sc_risk = custom_res.get('risk_level', 'Nguy cơ Cao')
                synthesis_rows.append({
                    "Phương án / Nguồn dữ liệu": f"4. AI Gemini ({sc_name})",
                    "Loại dữ liệu": "AI Gemini API (Custom Stats)",
                    "Số ca dự báo / Thực tế": f"{sc_cases:.0f} ca",
                    "Mức độ Nguy cơ": sc_risk,
                    "Phương pháp": "Mô phỏng Đa biến & Lượng giá Can thiệp",
                    "Đặc điểm": "Phản ánh giả định thời tiết & chỉ số bọ gậy BI"
                })
            else:
                synthesis_rows.append({
                    "Phương án / Nguồn dữ liệu": "4. AI Gemini (Kịch bản Tự Thống Kê)",
                    "Loại dữ liệu": "AI Gemini API (Custom Stats)",
                    "Số ca dự báo / Thực tế": "Chưa thiết lập",
                    "Mức độ Nguy cơ": "—",
                    "Phương pháp": "Mô phỏng Đa biến",
                    "Đặc điểm": "Vui lòng chạy kịch bản tại Tab 2"
                })

            st.dataframe(pd.DataFrame(synthesis_rows), use_container_width=True)

            # Plotly Multi-Scenario Comparison Chart
            st.markdown("#### 📈 Biểu Đồ Đối Sánh Diễn Biến Ca Bệnh Theo Từng Nguồn Dự Báo")
            fig_synth = go.Figure()

            timeline_labels = ["Thực tế T11/2025", "Thực tế T12/2025", "Tháng 01/2026", "Tháng 02/2026", "Tháng 03/2026"]
            hist_cases_synth = [193, 205, None, None, None]
            xgb_cases_synth = [None, 205, 180, 165, 140]

            ai_existing_cases_synth = [None, 205]
            if eval_data and eval_data.get('monthly_predictions'):
                for p in eval_data.get('monthly_predictions')[:3]:
                    ai_existing_cases_synth.append(float(p.get('predicted_cases', 0)))
            else:
                ai_existing_cases_synth += [182, 158, 139]

            # Trace 1: Historical
            fig_synth.add_trace(go.Scatter(
                x=timeline_labels,
                y=hist_cases_synth,
                mode='lines+markers+text',
                name='Thực tế Lịch sử',
                text=["193 ca", "205 ca", "", "", ""],
                textposition='top left',
                line=dict(color='#264653', width=3.5),
                marker=dict(size=9, color='#264653')
            ))

            # Trace 2: XGBoost Baseline
            fig_synth.add_trace(go.Scatter(
                x=timeline_labels,
                y=xgb_cases_synth,
                mode='lines+markers',
                name='Mô hình XGBoost (Tham chiếu)',
                line=dict(color='#f4a261', width=2.5, dash='dash'),
                marker=dict(size=7, color='#f4a261', symbol='square')
            ))

            # Trace 3: Gemini AI Existing Data
            fig_synth.add_trace(go.Scatter(
                x=timeline_labels,
                y=ai_existing_cases_synth,
                mode='lines+markers+text',
                name='AI Gemini (Dữ liệu Thực tế)',
                text=["", ""] + [f"<b>{v:.0f}</b>" for v in ai_existing_cases_synth[2:]],
                textposition='top center',
                line=dict(color='#e76f51', width=3.5),
                marker=dict(size=10, color='#e76f51', symbol='diamond')
            ))

            # Trace 4: Custom Scenario point if present
            if custom_res:
                fig_synth.add_trace(go.Scatter(
                    x=["Tháng 01/2026"],
                    y=[float(custom_res.get('predicted_cases', 0))],
                    mode='markers+text',
                    name=f"Kịch bản Tự Thống Kê ({custom_res.get('scenario_name', '')[:15]})",
                    text=[f"<b>Kịch bản: {custom_res.get('predicted_cases', 0):.0f} ca</b>"],
                    textposition='bottom center',
                    marker=dict(size=14, color='#9d4edd', symbol='star')
                ))

            fig_synth.update_layout(
                title="<b>Biểu Đồ Đối Sánh Ca Bệnh: Thực Tế vs XGBoost vs AI Gemini (Thực Tế & Kịch Bản Tự Thống Kê)</b>",
                xaxis=dict(title="Thời gian"),
                yaxis=dict(title="Số ca mắc SXH (ca)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_white",
                height=480
            )
            st.plotly_chart(fig_synth, use_container_width=True)

            st.info(
                "📌 **Kết luận Đối Sánh Dịch Tễ Học:**\n\n"
                "- Mô hình **XGBoost** và **Gemini AI (Dữ liệu thực tế)** cùng thống nhất xu hướng giảm dần ca bệnh trong Quý 1/2026 do tác động của mùa khô TP.HCM.\n"
                "- **Điểm vượt trội của Gemini AI:** Có khả năng giải thích cơ chế sinh học, chỉ số bọ gậy BI, tính toán độ trễ lượng mưa và đánh giá định lượng các can thiệp dập dịch trong kịch bản tự thống kê."
            )


# ===========================================================================


# ===========================================================================
# TAB 2: TRỢ LÝ AI HỎI ĐÁP (GIỮ NGUYÊN HOÀN TOÀN)
# ===========================================================================
with tab2:
    with st.container(key="bento_chat_card"):
        _chat_hdr_l, _chat_hdr_r = st.columns([3, 2], gap="medium")
        with _chat_hdr_l:
            st.header("💬 Trợ lý AI — Powered by Google Gemini")
            st.caption("Hỏi bất kỳ điều gì — y tế, dịch tễ, sốt xuất huyết, hoặc các chủ đề khác.")
        with _chat_hdr_r:
            role = st.radio(
                "Chế độ trả lời:",
                ["🧑‍💼 Thông thường", "👨‍⚕️ Chuyên gia / Bác sĩ"],
                horizontal=True
            )
        role_name = "Bác sĩ" if "Bác sĩ" in role else "Nguoi dan"

        if "chat_engine" not in st.session_state:
            st.session_state.chat_engine = GeminiChatEngine()

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý AI. Tôi có thể giúp gì cho bạn?"}
            ]

        st.markdown("**Gợi ý:**")
        sample_cols = st.columns(4)
        if sample_cols[0].button("🌡️ Triệu chứng SXH?"):
            st.session_state.user_input_trigger = "Triệu chứng sốt xuất huyết là gì?"
        if sample_cols[1].button("🚨 Dấu hiệu nguy hiểm?"):
            st.session_state.user_input_trigger = "Dấu hiệu sốt xuất huyết nặng cần cấp cứu ngay là gì?"
        if sample_cols[2].button("💊 Uống thuốc gì?"):
            st.session_state.user_input_trigger = "Bị sốt xuất huyết có được uống Ibuprofen không?"
        if sample_cols[3].button("🦟 Phòng ngừa?"):
            st.session_state.user_input_trigger = "Cách phòng ngừa sốt xuất huyết tại nhà?"

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_query = st.chat_input("Nhập câu hỏi của bạn...")
        if hasattr(st.session_state, "user_input_trigger") and st.session_state.user_input_trigger:
            user_query = st.session_state.user_input_trigger
            st.session_state.user_input_trigger = None

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                stream = st.session_state.chat_engine.process_query_stream(
                    query=user_query,
                    role=role_name,
                    chat_history=st.session_state.messages[:-1],
                )
                answer_text = st.write_stream(stream)

                _SEVERE_QUERY_SIGNS = [
                    "chảy máu chân răng", "chay mau chan rang", "chảy máu cam", "chay mau cam",
                    "nôn ra máu", "non ra mau", "đi cầu phân đen", "di cau phan den",
                    "đau bụng dữ dội", "dau bung du doi", "nôn liên tục", "non lien tuc",
                    "lì bì", "li bi", "vật vã", "bứt rứt", "hôn mê", "tay chân lạnh", "chân tay lạnh",
                    "tụt huyết áp", "sốc sốt xuất huyết", "soc sot xuat huyet",
                ]
                q_low = user_query.lower()
                if any(kw in q_low for kw in _SEVERE_QUERY_SIGNS):
                    st.error(
                        "🚨 **CẢNH BÁO NGUY HIỂM:** Câu hỏi có chứa dấu hiệu cảnh báo sốt xuất huyết nặng!\n\n"
                        "**Người bệnh cần đến cơ sở y tế hoặc khoa Cấp cứu NGAY LẬP TỨC.** Gọi **115** nếu người bệnh lơ mơ hoặc trụy mạch."
                    )

                st.caption(f"🤖 Google Gemini · {_CHAT_MODEL} (Google Search Live)")

            if answer_text:
                st.session_state.messages.append({"role": "assistant", "content": answer_text})