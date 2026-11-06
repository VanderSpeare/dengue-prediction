import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import sys
import re
from datetime import datetime, date, timedelta
from pathlib import Path

# Fix sys.path for standalone or root launch
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_ROOT))

import paths
from data_processor import load_and_process_new_data
from chatbot.gemini_chat_engine import GeminiChatEngine, GEMINI_MODEL as _CHAT_MODEL

# Import MongoDB Data Layer for Dengue Datasets
try:
    from mongo_data_service import mongo_data_service
except ImportError:
    from src.mongo_data_service import mongo_data_service

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

# Import Core Booking & Doctor Portal Module
try:
    from booking import (
        mongo_manager,
        doctor_auth_service,
        DoctorProfile,
        hash_password_sha256,
        PREDEFINED_DOCTORS,
        booking_service,
        BookingTicket,
        TimeSlotInfo,
        SlotStatus,
        BookingStatus,
        ExaminationStatus,
        STANDARD_TIME_SLOTS
    )
except ImportError:
    from src.booking import (
        mongo_manager,
        doctor_auth_service,
        DoctorProfile,
        hash_password_sha256,
        PREDEFINED_DOCTORS,
        booking_service,
        BookingTicket,
        TimeSlotInfo,
        SlotStatus,
        BookingStatus,
        ExaminationStatus,
        STANDARD_TIME_SLOTS
    )


# ---------------------------------------------------------------------------
# Plotly Version Compatibility Helpers
# ---------------------------------------------------------------------------
def _scatter_map_compat(df, lat, lon, size, color, hover_name,
                        hover_data, color_continuous_scale,
                        size_max, zoom, center, title, **kwargs):
    """Render a scatter bubble map compatible with both Plotly old & new versions."""
    common = dict(
        lat=lat, lon=lon, size=size, color=color,
        hover_name=hover_name, hover_data=hover_data,
        color_continuous_scale=color_continuous_scale,
        size_max=size_max, zoom=zoom, center=center, title=title,
    )
    try:
        if hasattr(px, 'scatter_map'):
            return px.scatter_map(df, map_style="open-street-map", **common, **kwargs)
        elif hasattr(px, 'scatter_mapbox'):
            return px.scatter_mapbox(df, mapbox_style="open-street-map", **common, **kwargs)
        else:
            raise AttributeError("Plotly không hỗ trợ scatter map API.")
    except Exception as exc:
        raise RuntimeError(f"Không thể dựng scatter map: {exc}") from exc


def _choropleth_map_compat(df, geojson, locations, featureidkey,
                           color, hover_name, hover_data,
                           color_continuous_scale, center, zoom,
                           opacity, title, **kwargs):
    """Render a choropleth map compatible with both Plotly old & new versions."""
    common = dict(
        geojson=geojson, locations=locations, featureidkey=featureidkey,
        color=color, hover_name=hover_name, hover_data=hover_data,
        color_continuous_scale=color_continuous_scale,
        center=center, zoom=zoom, opacity=opacity, title=title,
    )
    try:
        if hasattr(px, 'choropleth_map'):
            return px.choropleth_map(df, map_style="open-street-map", **common, **kwargs)
        elif hasattr(px, 'choropleth_mapbox'):
            return px.choropleth_mapbox(df, mapbox_style="open-street-map", **common, **kwargs)
        else:
            raise AttributeError("Plotly không hỗ trợ choropleth map API.")
    except Exception as exc:
        raise RuntimeError(f"Không thể dựng choropleth map: {exc}") from exc


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Hệ thống Giám sát Dịch Sốt xuất huyết & Đặt Lịch Khám Bác Sĩ",
    layout="wide",
    page_icon="🦟"
)

st.title("🦟 Hệ thống Giám sát Dịch Sốt xuất huyết & Cổng Y Tế Trực Tuyến")
st.markdown("Giám sát dịch tễ, dự báo vùng nguy cơ, tư vấn AI và hệ thống đặt lịch khám bệnh trực tiếp với Bác sĩ chuyên khoa.")

# ---------------------------------------------------------------------------
# Sidebar Management
# ---------------------------------------------------------------------------
st.sidebar.header("📍 Cấp Độ Giám Sát Dịch Tễ")
st.sidebar.caption("🗺️ Hỗ trợ 4 cấp độ: **Phố > Phường > Quận > Toàn Quốc** kèm khoanh vùng bán kính ổ dịch trực quan.")

st.sidebar.header("🍃 Cơ Sở Dữ Liệu")
if mongo_manager.is_connected:
    st.sidebar.success(f"🟢 MongoDB: Đã kết nối (`{mongo_manager.db_name}`)")
    stat = mongo_manager.get_status()
    st.sidebar.caption(f"📊 Đã lưu: {stat.get('total_bookings_stored', 0)} vé khám • {stat.get('total_doctors', 0)} bác sĩ")
    if st.sidebar.button("🔄 Đồng bộ dữ liệu lên MongoDB"):
        s_cnt, t_slots = booking_service.sync_to_mongodb()
        st.sidebar.info(f"Đã đồng bộ {s_cnt} lịch hẹn và {t_slots} khung giờ lên MongoDB!")
else:
    st.sidebar.warning("🟡 Lưu trữ: Bộ nhớ tạm (In-Memory)")
    if st.sidebar.button("🔌 Kết nối lại MongoDB Atlas"):
        if mongo_manager.connect():
            st.sidebar.success("Kết nối MongoDB thành công!")
            st.rerun()
        else:
            st.sidebar.error("Chưa kết nối được. Vui lòng mở IP Access List (0.0.0.0/0) trên MongoDB Atlas Network Access.")

# Hiển thị thông tin Bác sĩ nếu đã đăng nhập
if "logged_in_doctor" in st.session_state and st.session_state.logged_in_doctor:
    doc = st.session_state.logged_in_doctor
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👨‍⚕️ **Bác sĩ đang trực:**\n\n**{doc.title} {doc.full_name}**\n\n*{doc.specialty}* ({doc.room})")
    if st.sidebar.button("🚪 Đăng xuất Bác sĩ"):
        st.session_state.logged_in_doctor = None
        st.session_state.doctor_token = None
        st.rerun()

st.sidebar.header("📁 Quản lý Dữ liệu Dịch tễ")
uploaded_file = st.sidebar.file_uploader("Tải lên dữ liệu bệnh nhân mới (Excel)", type=['xlsx'])


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


@st.cache_data(show_spinner=False)
def load_vietnam_geojson(geojson_str_path: str):
    """Cache the 48MB GeoJSON in RAM to prevent blocking disk I/O on every rerun."""
    p = Path(geojson_str_path)
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


df = load_historical()
district_df = load_district_breakdown()
ward_df = load_ward_breakdown()
street_df = load_street_hotspots()
clusters_df = load_epidemic_clusters()
hcmc_hotspots_df = load_hcmc_hotspots()
predictions_df = load_predictions()

if uploaded_file:
    st.sidebar.success("File uploaded! Processing...")
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
        st.sidebar.success("Dữ liệu đã được lưu thành công vào MongoDB và Local!")
        st.sidebar.info("Vui lòng chạy `python main.py` để huấn luyện lại mô hình và cập nhật dự báo.")

# ===========================================================================
# 6 TABS UI: GIÁM SÁT, AI DỰ BÁO & ĐÁNH GIÁ, TRỢ LÝ AI, ĐẶT LỊCH, TRA CỨU, CỔNG BÁC SĨ
# ===========================================================================
tab1, tab_ai, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Giám sát & Dự báo Dịch bệnh",
    "🧠 AI Dự Báo & Đánh Giá Dịch Tễ (Gemini)",
    "💬 Trợ lý AI Hỏi đáp",
    "📅 Đặt Lịch Khám Bệnh",
    "🔍 Tra Cứu & Hủy Lịch Hẹn",
    "🩺 Cổng Bác Sĩ (Doctor Portal)"
])

# ===========================================================================
# TAB 1: GIÁM SÁT & DỰ BÁO DỊCH BỆNH (GIỮ NGUYÊN HOÀN TOÀN)
# ===========================================================================
with tab1:
    if not df.empty:
        available_years = sorted(df['year'].dropna().unique().astype(int), reverse=True)
        filter_years = [y for y in available_years if y >= 2024] or available_years

        st.subheader("🦟 Giám Sát Dịch Tễ Đa Cấp & Khoanh Vùng Khu Vực Nhiễm Bệnh")
        st.markdown(
            "Cấu trúc xử lý dữ liệu và tích hợp bản đồ phân cấp: "
            "**Tuyến Phố (Street / Cluster Zones)** ➡️ **Phường / Xã (Ward)** ➡️ **Quận / Huyện (District)** ➡️ **Tỉnh / Toàn Quốc (Province)**"
        )

        # -------------------------------------------------------------------
        # 1. BỘ LỌC ĐỘ CHI TIẾT (GRANULARITY SELECTOR) & THỜI GIAN
        # -------------------------------------------------------------------
        col_gran, col_yr, col_mth = st.columns([3, 1, 2])
        with col_gran:
            granularity_level = st.radio(
                "🗺️ Chọn Cấp Độ Chi Tiết Bản Đồ:",
                [
                    "🛣️ Cấp Tuyến Phố & Khoanh Vùng Ổ Dịch (Cluster Zones)",
                    "🏘️ Cấp Phường / Xã (Ward Level)",
                    "🏙️ Cấp Quận / Huyện (District Level)",
                    "🇻🇳 Cấp Tỉnh / Toàn Quốc (Province Level)"
                ],
                horizontal=False,
                key="granularity_selector"
            )

        with col_yr:
            sel_year = st.selectbox("📅 Năm:", filter_years, index=0, key="global_year_sel")

        # Get months for selected year
        df_year_all = df[df['year'] == sel_year]
        avail_months = sorted(df_year_all['month'].dropna().unique().astype(int)) if not df_year_all.empty else [1]
        with col_mth:
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

        st.markdown("---")

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
            st.subheader("🛣️ Bản đồ Khoanh Vùng Ổ Dịch & Tuyến Phố Nguy Cơ Cao")
            st.info("💡 **Cơ chế Khoanh Vùng:** Các ổ dịch và tuyến phố xuất hiện ca nhiễm được khoanh vùng bằng bán kính dịch tễ (200m - 1000m) với mức độ cảnh báo nguy cơ (Đỏ - Cam - Vàng - Xanh) và khuyến cáo hành động dập dịch khẩn cấp.")

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
                center_lat = float(c_prov_filtered['lat'].mean())
                center_lon = float(c_prov_filtered['lon'].mean())

                # Render Map with Outbreak Zones
                fig_clusters = _scatter_map_compat(
                    c_prov_filtered,
                    lat='lat', lon='lon',
                    size='cases',
                    color='risk_level',
                    hover_name='name',
                    hover_data={
                        'cases': True,
                        'level': True,
                        'radius_meters': True,
                        'recommendation': True,
                        'lat': False,
                        'lon': False,
                        'risk_level': False
                    },
                    color_continuous_scale=None,
                    color_discrete_map=RISK_COLOR_MAP,
                    size_max=32,
                    zoom=11 if sel_c_dist != "Tất cả Quận/Huyện" else 10,
                    center={"lat": center_lat, "lon": center_lon},
                    title=f"Bản đồ Khoanh Vùng Ổ Dịch & Nguy Cơ — {sel_c_prov} (T{sel_month:02d}/{sel_year})"
                )
                st.plotly_chart(fig_clusters, width='stretch')

                # Actionable Table
                st.subheader("📋 Danh Sách Điểm Nóng & Hành Động Dập Dịch Cần Triển Khai")
                display_cols = ['name', 'level', 'district', 'ward', 'cases', 'risk_level', 'radius_meters', 'recommendation']
                avail_disp = [c for c in display_cols if c in c_prov_filtered.columns]
                st.dataframe(
                    c_prov_filtered[avail_disp].sort_values('cases', ascending=False).reset_index(drop=True),
                    column_config={
                        "name": "Tên Điểm Nóng / Tuyến Phố",
                        "level": "Cấp Độ",
                        "district": "Quận / Huyện",
                        "ward": "Phường / Xã",
                        "cases": st.column_config.NumberColumn("Số Ca Nhiễm", format="%d ca"),
                        "risk_level": "Mức Độ Nguy Cơ",
                        "radius_meters": st.column_config.NumberColumn("Bán Kính Khoanh Vùng", format="%d m"),
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

                fig_ward_map = _scatter_map_compat(
                    w_prov_filtered,
                    lat='lat', lon='lon',
                    size='cases',
                    color='risk_level',
                    hover_name='ward',
                    hover_data={'cases': True, 'district': True, 'risk_level': True, 'lat': False, 'lon': False},
                    color_continuous_scale=None,
                    color_discrete_map=RISK_COLOR_MAP,
                    size_max=28,
                    zoom=11,
                    center={"lat": c_lat, "lon": c_lon},
                    title=f"Bản đồ Ca Nhiễm Cấp Phường/Xã — {sel_w_prov} (T{sel_month:02d}/{sel_year})"
                )
                st.plotly_chart(fig_ward_map, width='stretch')

                col_w_left, col_w_right = st.columns([3, 2])
                with col_w_left:
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

                fig_dist_map = _scatter_map_compat(
                    d_prov_filtered,
                    lat='lat', lon='lon',
                    size='cases',
                    color='incidence_rate' if 'incidence_rate' in d_prov_filtered.columns else 'cases',
                    hover_name='district',
                    hover_data={'cases': True, 'incidence_rate': ':.2f', 'lat': False, 'lon': False},
                    color_continuous_scale='YlOrRd',
                    size_max=30,
                    zoom=10,
                    center={"lat": c_lat, "lon": c_lon},
                    title=f"Bản đồ Dịch Tễ Cấp Quận/Huyện — {sel_d_prov} (T{sel_month:02d}/{sel_year})"
                )
                st.plotly_chart(fig_dist_map, width='stretch')

                col_dl, col_dr = st.columns([3, 2])
                with col_dl:
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
                vn_geojson = load_vietnam_geojson(str(geojson_path))
                if vn_geojson:
                    fig_map = _choropleth_map_compat(
                        df_month,
                        geojson=vn_geojson,
                        locations='province',
                        featureidkey="properties.adm1_name1",
                        color='cases',
                        hover_name='province',
                        hover_data={'cases': True, 'incidence_rate': ':.2f'},
                        color_continuous_scale="Reds",
                        center={"lat": 14.0583, "lon": 108.2772},
                        zoom=4.5,
                        opacity=0.75,
                        title=f"Bản đồ Ca nhiễm Sốt xuất huyết 34 Tỉnh/Thành — Tháng {sel_month:02d}/{sel_year}"
                    )
                    st.plotly_chart(fig_map, width='stretch')

            col_left, col_right = st.columns([3, 2])
            with col_left:
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
        # SO SÁNH DIỄN BIẾN SỐ CA NHIỄM 12 THÁNG (NĂM 2024 vs 2025)
        # -------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📈 So Sánh Diễn Biến Số Ca Nhiễm 12 Tháng (Năm 2024 vs 2025)")
        st.markdown(
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
            height=460
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
        # TƯƠNG QUAN KHÍ TƯỢNG (WEATHERDATA & API) & SỐ CA SỐT XUẤT HUYẾT THEO THÁNG
        # -------------------------------------------------------------------
        st.markdown("---")
        st.subheader("🌦️ Đối Sánh Chuỗi Thời Gian: Khí Tượng & Số Ca Sốt Xuất Huyết Theo Tháng")
        st.markdown(
            "Phân tích tương quan dịch tễ giữa điều kiện thời tiết (Lượng mưa, Nhiệt độ, Độ ẩm, Bụi mịn PM2.5) "
            "và diễn biến số ca mắc sốt xuất huyết qua từng tháng. Hệ thống tích hợp **2 nguồn khí tượng song song**: "
            "Dữ liệu Trạm quan trắc địa phương TP.HCM (`data/weatherdata` lưu trữ trên MongoDB Atlas) "
            "kết hợp cùng nguồn API Trực tuyến (`weather_service` — WeatherAPI & Open-Meteo Archive)."
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

        # Lấy dữ liệu thời tiết và SXH song song
        try:
            ws_combined = weather_service.get_weather_dengue_combined_series(
                dengue_df=df,
                province="TP. Hồ Chí Minh",
                weather_source="local_weatherdata"
            )
            ws_api_combined = weather_service.get_weather_dengue_combined_series(
                dengue_df=df,
                province="TP. Hồ Chí Minh",
                weather_source="api_cache"
            )
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
                height=500
            )

            st.plotly_chart(fig_weather_dengue, use_container_width=True)

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

            # Khối Nhận Định Dịch Tễ Môi Trường (Environmental Insights)
            st.info(
                "💡 **Nhận định Dịch tễ học Môi trường & Khí hậu TP.HCM:**\n\n"
                "- **Mối tương quan Lượng mưa — Đỉnh dịch:** Khi lượng mưa tích lũy hàng tháng vượt ngưỡng **300 mm** (từ Tháng 05 đến Tháng 09/2025), độ ẩm không khí tăng mạnh lên trên **85%**. Đây là môi trường lý tưởng để muỗi *Aedes aegypti* đẻ trứng và bùng phát bọ gậy.\n"
                "- **Độ trễ dịch tễ (Epidemiological Lag):** Đỉnh lượng mưa diễn ra vào Tháng 09/2025 (470.9 mm), kéo theo đỉnh điểm số ca sốt xuất huyết bùng phát sau đó vào Tháng 10/2025 (227 ca) — phản ánh đúng chu kỳ phát triển của véc-tơ truyền bệnh từ lăng quăng thành muỗi trưởng thành (độ trễ khoảng 2-4 tuần).\n"
                "- **Chỉ số Bụi mịn PM2.5:** Nồng độ PM2.5 từ trạm OpenAQ có xu hướng tăng vào các tháng chuyển mùa và mùa khô (Tháng 10 - Tháng 01 đạt 35 - 45 µg/m³), khi thời tiết ít mưa và độ ẩm giảm."
            )
        else:
            st.warning("⚠️ Chưa có dữ liệu thời tiết cho niên độ được chọn.")

        # -------------------------------------------------------------------
        # DỰ BÁO SỐ CA 3 THÁNG KẾ TIẾP — KHU VỰC TP. HỒ CHÍ MINH
        # -------------------------------------------------------------------
        st.markdown("---")
        st.subheader("🔮 Dự Báo Số Ca Sốt Xuất Huyết Trong 3 Tháng Kế Tiếp — Khu Vực TP. Hồ Chí Minh (Mô hình XGBoost)")
        st.info("💡 **Mô hình Trí Tuệ Nhân Tạo (XGBoost):** Dự báo chuỗi thời gian 3 tháng kế tiếp (Multi-step autoregressive forecasting) kết hợp yếu tố khí tượng (nhiệt độ, lượng mưa, độ ẩm) và độ trễ ca bệnh.")

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
                height=430
            )
            st.plotly_chart(fig_fc, use_container_width=True)

            # Continuous timeline chart (Historical -> 3-Month Forecast)
            with st.expander("🔍 Xem sơ đồ chuỗi thời gian liên tục (Thực tế 6 tháng cuối 2025 ➡️ Dự báo 3 tháng 2026)"):
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
                        height=420
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

        # Download buttons in sidebar
        if paths.MAP_OUTPUT_FILE.exists():
            with open(paths.MAP_OUTPUT_FILE, 'rb') as f:
                st.sidebar.download_button("🗺️ Tải Bản Đồ Tỉnh GeoJSON", f, "dengue_map.geojson")
        clusters_geojson_path = getattr(paths, 'EPIDEMIC_CLUSTERS_GEOJSON', paths.OUTPUTS_DIR / "epidemic_clusters.geojson")
        if clusters_geojson_path.exists():
            with open(clusters_geojson_path, 'rb') as f:
                st.sidebar.download_button("🎯 Tải Bản Đồ Khoanh Vùng Ổ Dịch GeoJSON", f, "epidemic_clusters.geojson")
    else:
        st.info("Chưa có dữ liệu lịch sử. Vui lòng tải file Excel dữ liệu bệnh nhân ở thanh bên trái.")


# ===========================================================================
# TAB AI: AI DỰ BÁO & ĐÁNH GIÁ DỊCH TỄ HỌC (GOOGLE GEMINI API)
# ===========================================================================
with tab_ai:
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
    st.header("💬 Trợ lý AI — Powered by Google Gemini")
    st.markdown("Hỏi bất kỳ điều gì — y tế, dịch tễ, sốt xuất huyết, hoặc các chủ đề khác.")

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


# ===========================================================================
# TAB 3: ĐẶT LỊCH KHÁM BỆNH TRỰC TUYẾN
# ===========================================================================
with tab3:
    st.header("📅 Đặt Lịch Khám Bệnh Trực Tuyến")
    st.info("🏥 **Địa điểm khám:** Phòng Khám Đa Khoa Quốc Tế — Phòng 302, Tầng 3, 123 Nguyễn Trãi, Quận 1, TP. Hồ Chí Minh")

    col_book_left, col_book_right = st.columns([1, 1], gap="large")

    with col_book_left:
        st.subheader("1. Chọn Thời Gian & Khung Giờ Khám")
        booking_date = st.date_input(
            "Chọn ngày khám:",
            value=datetime.today().date(),
            min_value=datetime.today().date(),
            key="book_date_input"
        )
        date_str = booking_date.strftime("%Y-%m-%d")

        # Lấy lịch từ service
        slots_list = booking_service.get_schedule(date_str)

        st.markdown("**Trạng thái các ca khám trong ngày:**")
        # Render grid nhỏ hiển thị trạng thái
        slot_cols = st.columns(4)
        for i, s in enumerate(slots_list):
            with slot_cols[i % 4]:
                if s.status == SlotStatus.AVAILABLE:
                    st.success(f"🟢 **{s.start_time}**\n\nTrống")
                elif s.status == SlotStatus.BOOKED:
                    st.error(f"🔴 **{s.start_time}**\n\nĐã đặt")
                elif s.status == SlotStatus.CANCELLED_LOCKED:
                    st.warning(f"🟡 **{s.start_time}**\n\nHủy <24h")
                elif s.status == SlotStatus.BLOCKED_BY_DOCTOR:
                    st.info(f"🟣 **{s.start_time}**\n\nBS bận")

        # Danh sách các ca còn trống
        available_starts = [s.start_time for s in slots_list if s.status == SlotStatus.AVAILABLE]

        if available_starts:
            selected_start_time = st.selectbox(
                "👉 Chọn khung giờ bạn muốn khám:",
                options=available_starts,
                format_func=lambda t: f"Ca khám {t} - {next((s[1] for s in STANDARD_TIME_SLOTS if s[0] == t), '')}",
                key="book_slot_select"
            )
        else:
            st.error("⚠️ Ngày được chọn đã kín lịch hoặc tạm khóa. Vui lòng chọn ngày khác.")
            selected_start_time = None

    with col_book_right:
        st.subheader("2. Thông Tin Người Khám")
        with st.form("form_booking"):
            patient_name = st.text_input("Họ và Tên bệnh nhân (*):", placeholder="Ví dụ: Nguyễn Văn An")
            patient_phone = st.text_input("Số điện thoại liên hệ (*):", placeholder="Ví dụ: 0912345678")
            patient_email = st.text_input("Email nhận phiếu (tùy chọn):", placeholder="nguyenvanan@gmail.com")

            assigned_doctor = st.selectbox(
                "Bác sĩ chuyên khoa phụ trách:",
                [
                    "BS. CKI Nguyễn Văn A (Bệnh Truyền Nhiễm & SXH)",
                    "BS. CKII Trần Thị B (Dịch Tễ Học Lâm Sàng)",
                    "ThS. BS Lê Hoàng C (Cấp Cứu Nhi & SXH Nặng)",
                    "BS. CKI Phạm Minh D (Nội Tổng Quát & Nhiễm)"
                ]
            )

            symptoms = st.text_area("Lý do khám / Triệu chứng ban đầu:", placeholder="Ví dụ: Sốt cao liên tục 2 ngày, nhức đầu, mệt mỏi...")

            submit_book = st.form_submit_button("🚀 Xác Nhận Đặt Lịch Khám", use_container_width=True, type="primary")

            if submit_book:
                if not selected_start_time:
                    st.error("Vui lòng chọn một khung giờ còn trống trước khi xác nhận!")
                else:
                    success, ticket, msg = booking_service.book_appointment(
                        patient_name=patient_name,
                        patient_phone=patient_phone,
                        appointment_date=date_str,
                        start_time=selected_start_time,
                        patient_email=patient_email,
                        symptoms=symptoms,
                        assigned_doctor=assigned_doctor
                    )

                    if success and ticket:
                        st.session_state.last_booked_ticket = ticket
                        st.success("🎉 " + msg)
                        st.balloons()
                    else:
                        st.error("❌ " + msg)

    # Hiển thị Phiếu Đặt Lịch Khám vừa tạo thành công
    if "last_booked_ticket" in st.session_state and st.session_state.last_booked_ticket:
        tk = st.session_state.last_booked_ticket
        st.markdown("---")
        st.subheader("🎟️ Phiếu Hẹn Khám Bệnh Trực Tuyến")
        
        ticket_box = st.container(border=True)
        with ticket_box:
            t_col1, t_col2 = st.columns([2, 1])
            with t_col1:
                st.markdown(f"### 👨‍⚕️ {tk.doctor_name}")
                st.markdown(f"*{tk.doctor_specialty}*")
                st.markdown(f"📍 **Địa điểm khám:** {tk.clinic_location}")
                st.markdown(f"⏰ **Thời gian khám:** `{tk.appointment_time}` Ngày `{tk.appointment_date}`")
            with t_col2:
                st.metric("SỐ THỨ TỰ (STT)", f"#{tk.queue_number:02d}")
                st.code(tk.booking_code, language="text")

            st.markdown("---")
            p_col1, p_col2 = st.columns(2)
            p_col1.markdown(f"👤 **Bệnh nhân:** {tk.patient_name}")
            p_col2.markdown(f"📞 **SĐT:** {tk.patient_phone}")
            if tk.symptoms:
                st.markdown(f"📝 **Triệu chứng ban đầu:** *{tk.symptoms}*")


# ===========================================================================
# TAB 4: TRA CỨU & HỦY LỊCH HẸN
# ===========================================================================
with tab4:
    st.header("🔍 Tra Cứu & Quản Lý Lịch Hẹn")
    st.markdown("Nhập mã đặt lịch (dạng `DK-YYYYMMDD-XXXX`) để tra cứu thông tin hoặc hủy lịch hẹn.")

    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_code = st.text_input("Nhập mã đặt lịch:", placeholder="Ví dụ: DK-20261005-A1B2", key="lookup_input").strip().upper()
    with col_search2:
        st.write("")
        st.write("")
        btn_search = st.button("🔎 Tra Cứu", use_container_width=True)

    if search_code or btn_search:
        found_ticket = booking_service.get_booking(search_code)
        if found_ticket:
            st.success("Đã tìm thấy thông tin lịch hẹn!")
            box = st.container(border=True)
            with box:
                b_c1, b_c2 = st.columns([2, 1])
                with b_c1:
                    st.markdown(f"### Mã: `{found_ticket.booking_code}` — STT: `#{found_ticket.queue_number:02d}`")
                    st.markdown(f"👤 **Bệnh nhân:** {found_ticket.patient_name} — 📞 **SĐT:** {found_ticket.patient_phone}")
                    st.markdown(f"⏰ **Thời gian:** `{found_ticket.appointment_time}` ngày `{found_ticket.appointment_date}`")
                    st.markdown(f"📍 **Địa điểm:** {found_ticket.clinic_location}")
                    st.markdown(f"👨‍⚕️ **Bác sĩ:** {found_ticket.doctor_name}")

                with b_c2:
                    if found_ticket.status == BookingStatus.CANCELLED:
                        st.error("❌ TRẠNG THÁI: ĐÃ HỦY")
                    else:
                        st.success("✅ TRẠNG THÁI: ĐÃ XÁC NHẬN")
                    
                    exam_st = found_ticket.examination_status
                    if exam_st == ExaminationStatus.IN_PROGRESS:
                        st.info("🔄 Tiến độ: Đang khám")
                    elif exam_st == ExaminationStatus.COMPLETED:
                        st.success("🏆 Tiến độ: Đã hoàn thành")
                    elif exam_st == ExaminationStatus.NO_SHOW:
                        st.warning("⚠️ Tiến độ: Vắng mặt")
                    else:
                        st.markdown("⏳ Tiến độ: Đang chờ khám")

                if found_ticket.clinical_record:
                    st.markdown("---")
                    st.markdown("🩺 **Hồ Sơ Bệnh Án & Chẩn Đoán Của Bác Sĩ:**")
                    rec = found_ticket.clinical_record
                    st.info(f"**Chẩn đoán:** {rec.get('diagnosis')}\n\n**Chỉ định xét nghiệm:** {rec.get('tests_recommended') or 'Không'}\n\n**Đơn thuốc / Lời dặn:** {rec.get('prescription') or 'Không'}")

                if found_ticket.status != BookingStatus.CANCELLED:
                    st.markdown("---")
                    cancel_reason = st.text_input("Lý do hủy lịch (nếu có):", placeholder="Bận việc đột xuất...", key="cancel_reason_input")
                    if st.button("🚫 Xác Nhận Hủy Lịch Khám Này", type="secondary"):
                        c_ok, c_tk, c_msg = booking_service.cancel_appointment(
                            booking_code=found_ticket.booking_code,
                            cancellation_reason=cancel_reason
                        )
                        if c_ok:
                            st.warning(c_msg)
                            st.rerun()
                        else:
                            st.error(c_msg)
        else:
            if search_code:
                st.error(f"Không tìm thấy lịch hẹn với mã `{search_code}`.")


# ===========================================================================
# TAB 5: CỔNG BÁC SĨ (DOCTOR PORTAL - MẬT KHẨU SHA-256)
# ===========================================================================
with tab5:
    st.header("🩺 Cổng Dành Riêng Cho Bác Sĩ")

    # Kiểm tra trạng thái đăng nhập
    if "logged_in_doctor" not in st.session_state or not st.session_state.logged_in_doctor:
        st.warning("🔒 **Khu vực bảo mật:** Vui lòng đăng nhập bằng 1 trong 4 tài khoản Bác sĩ bên dưới (mật khẩu mã hóa SHA-256).")

        col_login_form, col_quick_docs = st.columns([1, 1], gap="large")

        with col_login_form:
            st.subheader("Đăng Nhập Tài Khoản Bác Sĩ")
            with st.form("form_doctor_login"):
                doc_username = st.text_input("Tên đăng nhập (Username):", placeholder="Ví dụ: bs_nguyenvana", key="doc_user_in")
                doc_password = st.text_input("Mật khẩu:", type="password", placeholder="Nhập mật khẩu...", key="doc_pass_in")
                btn_login = st.form_submit_button("🔑 Đăng Nhập", use_container_width=True, type="primary")

                if btn_login:
                    auth_res = doctor_auth_service.authenticate_doctor(
                        username=doc_username,
                        password_plain=doc_password,
                        mongo_db=mongo_manager.db if mongo_manager.is_connected else None
                    )
                    if auth_res:
                        token, doc_profile = auth_res
                        st.session_state.logged_in_doctor = doc_profile
                        st.session_state.doctor_token = token
                        st.success(f"Chào mừng {doc_profile.title} {doc_profile.full_name} đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Tên đăng nhập hoặc mật khẩu không chính xác!")

        with col_quick_docs:
            st.subheader("📋 4 Tài Khoản Bác Sĩ Mẫu")
            st.caption("Mật khẩu mặc định: `Bacsi@123` (Đã mã hóa SHA-256)")
            for d in PREDEFINED_DOCTORS:
                with st.container(border=True):
                    dc1, dc2 = st.columns([3, 1])
                    with dc1:
                        st.markdown(f"**{d['full_name']}** (`{d['username']}`)")
                        st.caption(f"{d['specialty']} — {d['room']}")
                    with dc2:
                        if st.button("Chọn", key=f"quick_{d['username']}"):
                            auth_res = doctor_auth_service.authenticate_doctor(
                                username=d['username'],
                                password_plain="Bacsi@123",
                                mongo_db=mongo_manager.db if mongo_manager.is_connected else None
                            )
                            if auth_res:
                                token, doc_profile = auth_res
                                st.session_state.logged_in_doctor = doc_profile
                                st.session_state.doctor_token = token
                                st.rerun()

    else:
        # DOCTOR WORKSPACE (ĐÃ ĐĂNG NHẬP)
        current_doc = st.session_state.logged_in_doctor
        
        # Banner Bác sĩ
        st.success(f"👨‍⚕️ **Bác sĩ đang trực:** {current_doc.title} **{current_doc.full_name}** | Chuyên khoa: *{current_doc.specialty}* | {current_doc.room}")

        doc_filter_date = st.date_input(
            "📅 Chọn ngày làm việc:",
            value=datetime.today().date(),
            key="doc_portal_date_filter"
        )
        doc_date_str = doc_filter_date.strftime("%Y-%m-%d")

        # Lấy danh sách bệnh nhân
        all_appts = booking_service.list_all_bookings(date_filter=doc_date_str)
        doc_slots = booking_service.get_schedule(doc_date_str)

        # Thống kê nhanh 4 chỉ số
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        total_ap = len(all_appts)
        waiting_ap = sum(1 for b in all_appts if b.examination_status == ExaminationStatus.WAITING and b.status == BookingStatus.CONFIRMED)
        in_prog_ap = sum(1 for b in all_appts if b.examination_status == ExaminationStatus.IN_PROGRESS and b.status == BookingStatus.CONFIRMED)
        done_ap = sum(1 for b in all_appts if b.examination_status == ExaminationStatus.COMPLETED)

        m_c1.metric("Tổng Lịch Hẹn", f"{total_ap} ca")
        m_c2.metric("Chờ Khám", f"{waiting_ap} ca")
        m_c3.metric("Đang Khám", f"{in_prog_ap} ca")
        m_c4.metric("Đã Hoàn Thành", f"{done_ap} ca")

        st.markdown("---")
        st.subheader(f"📋 Danh Sách Bệnh Nhân Khám Ngày {doc_date_str}")

        if not all_appts:
            st.info("Chưa có lịch hẹn nào của bệnh nhân trong ngày này.")
        else:
            for b in all_appts:
                is_cancelled = (b.status == BookingStatus.CANCELLED)
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 2])
                    with c1:
                        st.markdown(f"**STT #{b.queue_number:02d}** | Mã: `{b.booking_code}`")
                        st.markdown(f"👤 **Bệnh nhân:** `{b.patient_name}` — 📞 `{b.patient_phone}`")
                        st.caption(f"Giờ hẹn: {b.appointment_time}")
                    with c2:
                        st.markdown(f"📝 **Triệu chứng:** *{b.symptoms or 'Không ghi chú'}*")
                        if is_cancelled:
                            st.error("Đã hủy")
                        elif b.examination_status == ExaminationStatus.IN_PROGRESS:
                            st.info("🔄 Đang khám")
                        elif b.examination_status == ExaminationStatus.COMPLETED:
                            st.success("✅ Đã hoàn thành")
                        elif b.examination_status == ExaminationStatus.NO_SHOW:
                            st.warning("⚠️ Vắng mặt")
                        else:
                            st.markdown("⏳ Đang chờ khám")
                    with c3:
                        if not is_cancelled:
                            act_col1, act_col2 = st.columns(2)
                            with act_col1:
                                if st.button("📞 Gọi Khám", key=f"start_{b.booking_code}"):
                                    mongo_manager.update_doctor_examination_status(b.booking_code, "IN_PROGRESS", current_doc.full_name)
                                    b.examination_status = ExaminationStatus.IN_PROGRESS
                                    st.rerun()
                            with act_col2:
                                if st.button("⚠️ Vắng Mặt", key=f"noshow_{b.booking_code}"):
                                    mongo_manager.update_doctor_examination_status(b.booking_code, "NO_SHOW", current_doc.full_name)
                                    b.examination_status = ExaminationStatus.NO_SHOW
                                    st.rerun()

                    # Form ghi bệnh án
                    if not is_cancelled:
                        with st.expander(f"🩺 Ghi Hồ Sơ Bệnh Án & Toa Thuốc cho {b.patient_name} (#{b.queue_number:02d})"):
                            diag = st.text_input("Chẩn đoán lâm sàng (*):", value=b.clinical_record.get('diagnosis', '') if b.clinical_record else "", key=f"diag_{b.booking_code}")
                            tests = st.text_input("Chỉ định xét nghiệm (NS1Ag, CTM...):", value=b.clinical_record.get('tests_recommended', '') if b.clinical_record else "", key=f"tests_{b.booking_code}")
                            presc = st.text_area("Đơn thuốc & Lời dặn điều trị:", value=b.clinical_record.get('prescription', '') if b.clinical_record else "", key=f"presc_{b.booking_code}")

                            if st.button("💾 Lưu Bệnh Án & Hoàn Thành Ca", key=f"save_rec_{b.booking_code}", type="primary"):
                                if not diag.strip():
                                    st.error("Vui lòng nhập chẩn đoán lâm sàng!")
                                else:
                                    mongo_manager.save_doctor_clinical_record(b.booking_code, diag, tests, presc, current_doc.full_name)
                                    b.examination_status = ExaminationStatus.COMPLETED
                                    b.clinical_record = {
                                        "diagnosis": diag,
                                        "tests_recommended": tests,
                                        "prescription": presc,
                                        "doctor_name": current_doc.full_name
                                    }
                                    st.success("Đã lưu bệnh án và đánh dấu hoàn thành ca khám!")
                                    st.rerun()

        # Quản lý khóa / mở ca khám của Bác sĩ
        st.markdown("---")
        st.subheader("🚫 Quản Lý Khóa / Mở Ca Khám Đột Xuất (Bác Sĩ Bận)")
        st.caption("Khóa ca khám khi Bác sĩ bận hội chẩn hoặc trực cấp cứu đột xuất.")

        b_cols = st.columns(4)
        for idx, s in enumerate(doc_slots):
            with b_cols[idx % 4]:
                if s.status == SlotStatus.BLOCKED_BY_DOCTOR:
                    st.info(f"🟣 **{s.start_time}** (Đã khóa)")
                    if st.button("Mở lại ca", key=f"unblock_{s.start_time}"):
                        mongo_manager.toggle_slot_block_by_doctor(doc_date_str, s.start_time, False, "", current_doc.full_name)
                        st.rerun()
                elif s.status == SlotStatus.AVAILABLE:
                    st.success(f"🟢 **{s.start_time}** (Còn trống)")
                    if st.button("Khóa ca", key=f"block_{s.start_time}"):
                        mongo_manager.toggle_slot_block_by_doctor(doc_date_str, s.start_time, True, "Bác sĩ bận hội chẩn", current_doc.full_name)
                        st.rerun()
                elif s.status == SlotStatus.BOOKED:
                    st.error(f"🔴 **{s.start_time}** (Đã đặt)")
                elif s.status == SlotStatus.CANCELLED_LOCKED:
                    st.warning(f"🟡 **{s.start_time}** (Trống <24h)")