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
# 5 TABS UI: GIÁM SÁT, TRỢ LÝ AI, ĐẶT LỊCH, TRA CỨU, CỔNG BÁC SĨ
# ===========================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Giám sát & Dự báo Dịch bệnh",
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