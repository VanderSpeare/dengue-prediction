import os
import math
import geopandas as gpd
import pandas as pd
import logging
from shapely.geometry import Point, MultiPoint, box
from shapely.ops import voronoi_diagram

try:
    from . import paths
    from .data_processor import HCMC_DISTRICT_COORDS
except ImportError:
    import paths
    from data_processor import HCMC_DISTRICT_COORDS

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_map_data(agg_data, boundary_file=None, output_file=None):
    if boundary_file is None:
        boundary_file = paths.BOUNDARY_FILE
    if output_file is None:
        output_file = paths.MAP_OUTPUT_FILE

    logger.info(f"Loading boundary GeoJSON from {boundary_file}...")

    try:
        gdf = gpd.read_file(boundary_file)
        if gdf.crs is not None and str(gdf.crs).lower() != "epsg:4326":
            logger.info(f"Converting boundary CRS from {gdf.crs} to EPSG:4326 (WGS84)...")
            gdf = gdf.to_crs(epsg=4326)
        gdf['geometry'] = gdf['geometry'].make_valid()
    except Exception as e:
        logger.error(f"Error loading boundaries: {e}")
        return None

    if 'date' in agg_data.columns:
        latest_date = agg_data['date'].max()
        map_df = agg_data[agg_data['date'] == latest_date].copy()
    else:
        map_df = agg_data.copy()

    logger.info(f"Merging map data for {len(map_df)} provinces...")

    if 'adm1_name1' not in gdf.columns:
        logger.error(
            f"Expected join key 'adm1_name1' not found in boundary file. "
            f"Available columns: {list(gdf.columns)}"
        )
        return None

    merged = gdf.merge(map_df, left_on='adm1_name1', right_on='province', how='left')

    unmatched = merged[merged['province'].isna()]['adm1_name1'].unique()
    if len(unmatched) > 0:
        logger.warning(f"No case data found for these boundary provinces: {list(unmatched)}")

    if 'cases' in merged.columns:
        merged['cases'] = merged['cases'].fillna(0)
    if 'incidence_rate' in merged.columns:
        merged['incidence_rate'] = merged['incidence_rate'].fillna(0)
    if 'predicted_cases' in merged.columns:
        merged['predicted_cases'] = merged['predicted_cases'].fillna(0)

    if 'incidence_rate' in merged.columns:
        merged['risk_level'] = pd.cut(
            merged['incidence_rate'],
            bins=[-1, 5, 20, 50, float('inf')],
            labels=['Low', 'Medium', 'High', 'Very High']
        ).astype(str)

    os.makedirs(os.path.dirname(str(output_file)), exist_ok=True)
    merged.to_file(output_file, driver='GeoJSON')
    logger.info(f"✅ GeoJSON ready for ArcGIS Map Viewer at: {output_file}")

    return merged


def create_cluster_geojson(clusters_df: pd.DataFrame, output_file=None):
    """
    Tạo GeoJSON khoanh vùng cụm dịch (Epidemic Buffer Zones / Outbreak Polygons).
    Mỗi ổ dịch được khoanh vùng bằng vòng tròn bán kính dịch tễ (200m - 2000m)
    kèm thông tin mức độ nguy cơ, số ca và khuyến cáo dập dịch.
    """
    if clusters_df is None or clusters_df.empty:
        return None

    if output_file is None:
        output_file = getattr(paths, 'EPIDEMIC_CLUSTERS_GEOJSON', paths.OUTPUTS_DIR / "epidemic_clusters.geojson")

    logger.info(f"Generating Epidemic Clusters GeoJSON for {len(clusters_df)} zones...")

    geometries = []
    for _, row in clusters_df.iterrows():
        lat = float(row.get('lat', 10.7769))
        lon = float(row.get('lon', 106.7009))
        radius_m = float(row.get('radius_meters', 300))

        # Approximate degrees per meter at latitude lat
        deg_lat = radius_m / 111320.0
        deg_lon = radius_m / (111320.0 * max(0.1, math.cos(math.radians(lat))))
        buffer_deg = (deg_lat + deg_lon) / 2.0

        point = Point(lon, lat)
        circle_poly = point.buffer(buffer_deg)
        geometries.append(circle_poly)

    gdf = gpd.GeoDataFrame(clusters_df.copy(), geometry=geometries, crs="EPSG:4326")

    # Format date for JSON export
    if 'date' in gdf.columns:
        gdf['date'] = gdf['date'].astype(str)

    os.makedirs(os.path.dirname(str(output_file)), exist_ok=True)
    gdf.to_file(output_file, driver='GeoJSON')
    logger.info(f"✅ Epidemic Clusters GeoJSON saved to: {output_file}")
    return gdf


_HCMC_EXTRA_MERGED_COORDS = {
    'Thành Phố Dĩ An': {'lat': 10.9068, 'lon': 106.7694},
    'Thành Phố Thuận An': {'lat': 10.9037, 'lon': 106.7016},
    'Thành Phố Thủ Dầu Một': {'lat': 10.9804, 'lon': 106.6519},
    'Thị Xã Tân Uyên': {'lat': 11.0695, 'lon': 106.7916},
    'Thị Xã Bến Cát': {'lat': 11.1587, 'lon': 106.5973},
    'Thành Phố Vũng Tàu': {'lat': 10.3460, 'lon': 107.0843},
    'Thị Xã Phú Mỹ': {'lat': 10.5925, 'lon': 107.0522},
    'Huyện Châu Đức': {'lat': 10.6540, 'lon': 107.2512},
    'Huyện Xuyên Mộc': {'lat': 10.5563, 'lon': 107.4561},
}


def normalize_hcmc_district_name(name: str) -> str:
    """Chuẩn hóa tên Quận/Huyện TP.HCM để khớp nhất quán giữa dữ liệu và GeoJSON."""
    s = str(name or "").strip()
    if s == "Thành Phố Thủ Đức":
        return "Thủ Đức"
    return s


def ensure_hcmc_districts_geojson(output_file=None, province_boundary_file=None):
    """
    Sinh file GeoJSON ranh giới hành chính các Quận/Huyện TP. Hồ Chí Minh
    bằng thuật toán phân hoạch Voronoi cắt theo ranh giới tỉnh TP.HCM (EPSG:4326)
    để hiển thị bản đồ Choropleth chi tiết trên ArcGIS Maps SDK và Leaflet.
    """
    if output_file is None:
        output_file = getattr(paths, 'HCMC_BOUNDARY_FILE', paths.DATA_DIR / "population" / "hcmc_districts.geojson")
    if province_boundary_file is None:
        province_boundary_file = getattr(paths, 'BOUNDARY_FILE', paths.DATA_DIR / "population" / "vietnam_34_provinces_2025.geojson")

    # Tải đa giác ranh giới TP. Hồ Chí Minh từ boundary cấp tỉnh (nếu có)
    clip_poly = None
    if province_boundary_file:
        try:
            prov_gdf = gpd.read_file(province_boundary_file)
            if prov_gdf.crs is not None and str(prov_gdf.crs).lower() != "epsg:4326":
                prov_gdf = prov_gdf.to_crs(epsg=4326)
            hcm_rows = prov_gdf[prov_gdf['adm1_name1'].astype(str).str.contains('Hồ Chí Minh', case=False, na=False)]
            if not hcm_rows.empty:
                geom_union = (
                    hcm_rows.geometry.union_all()
                    if hasattr(hcm_rows.geometry, 'union_all')
                    else hcm_rows.geometry.unary_union
                )
                clip_poly = geom_union.simplify(0.002, preserve_topology=True)
                clip_poly = clip_poly.buffer(0)
        except Exception as exc:
            logger.warning(f"Không đọc được ranh giới TP.HCM từ {province_boundary_file}: {exc}")

    if clip_poly is None or clip_poly.is_empty:
        # Bounding polygon chuẩn cho TP.HCM
        clip_poly = box(106.35, 10.35, 107.02, 11.17)

    # Xây dựng danh sách điểm trung tâm duy nhất cho từng Quận/Huyện
    minx, miny, maxx, maxy = clip_poly.bounds
    coords_dict = {}
    for name, c in HCMC_DISTRICT_COORDS.items():
        norm_name = normalize_hcmc_district_name(name)
        if norm_name not in coords_dict:
            coords_dict[norm_name] = c

    # Nếu ranh giới TP.HCM mở rộng sang khu vực sáp nhập, bổ sung tọa độ các địa bàn liên quan
    if maxy > 11.08 or maxx > 107.05:
        for name, c in _HCMC_EXTRA_MERGED_COORDS.items():
            if name not in coords_dict:
                coords_dict[name] = c

    names = list(coords_dict.keys())
    points = [Point(float(coords_dict[n]['lon']), float(coords_dict[n]['lat'])) for n in names]
    mp = MultiPoint(points)

    vor_geom = voronoi_diagram(mp, envelope=clip_poly.envelope.buffer(0.5))
    vor_polys = [g for g in getattr(vor_geom, 'geoms', []) if not g.is_empty]

    records = []
    for name, pt in zip(names, points):
        matched_poly = None
        for vp in vor_polys:
            if vp.contains(pt) or vp.distance(pt) < 1e-6:
                matched_poly = vp
                break
        if matched_poly is None and vor_polys:
            matched_poly = min(vor_polys, key=lambda g: g.distance(pt))

        if matched_poly is not None:
            clipped = matched_poly.intersection(clip_poly).buffer(0)
            if not clipped.is_empty:
                records.append({
                    'district': name,
                    'adm1_name1': name,
                    'province': 'TP. Hồ Chí Minh',
                    'center_lat': round(pt.y, 6),
                    'center_lon': round(pt.x, 6),
                    'geometry': clipped,
                })

    try:
        gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    except Exception:
        gdf = gpd.GeoDataFrame(records)
    os.makedirs(os.path.dirname(str(output_file)), exist_ok=True)
    gdf.to_file(output_file, driver='GeoJSON')
    logger.info(f"✅ HCMC Districts GeoJSON saved ({len(gdf)} districts) at: {output_file}")
    return gdf


def create_hcmc_district_map_data(district_df: pd.DataFrame, boundary_file=None, output_file=None, predictions_df: pd.DataFrame = None):
    """
    Kết hợp số liệu ca bệnh & dự báo cấp Quận/Huyện TP.HCM với GeoJSON ranh giới quận
    để xuất file GeoJSON sẵn sàng cho ArcGIS Maps SDK và Leaflet.
    """
    if boundary_file is None:
        boundary_file = getattr(paths, 'HCMC_BOUNDARY_FILE', paths.DATA_DIR / "population" / "hcmc_districts.geojson")
    if output_file is None:
        output_file = getattr(paths, 'HCMC_MAP_OUTPUT_FILE', paths.OUTPUTS_DIR / "hcmc_districts_risk.geojson")

    if not os.path.exists(boundary_file):
        gdf = ensure_hcmc_districts_geojson(output_file=boundary_file)
    else:
        gdf = gpd.read_file(boundary_file)
        if gdf.crs is not None and str(gdf.crs).lower() != "epsg:4326":
            gdf = gdf.to_crs(epsg=4326)

    if district_df is None or district_df.empty:
        return gdf

    hcm_df = district_df[district_df['province'].astype(str).str.contains('Hồ Chí Minh', case=False, na=False)].copy()
    if hcm_df.empty:
        return gdf

    if 'date' in hcm_df.columns:
        latest_date = hcm_df['date'].max()
        hcm_latest = hcm_df[hcm_df['date'] == latest_date].copy()
    else:
        hcm_latest = hcm_df.copy()

    hcm_latest['district_norm'] = hcm_latest['district'].apply(normalize_hcmc_district_name)
    agg_cols = {'cases': 'sum'}
    if 'incidence_rate' in hcm_latest.columns:
        agg_cols['incidence_rate'] = 'sum'
    dist_summary = hcm_latest.groupby('district_norm', as_index=False).agg(agg_cols)

    if predictions_df is not None and not predictions_df.empty and 'district' in predictions_df.columns:
        pred_copy = predictions_df.copy()
        pred_copy['district_norm'] = pred_copy['district'].apply(normalize_hcmc_district_name)
        if 'step' in pred_copy.columns:
            pred_step1 = pred_copy[pred_copy['step'] == 1]
            if pred_step1.empty:
                pred_step1 = pred_copy
        else:
            pred_step1 = pred_copy
        pred_agg = pred_step1.groupby('district_norm', as_index=False)['predicted_cases'].sum()
        dist_summary = dist_summary.merge(pred_agg, on='district_norm', how='left')

    merged = gdf.merge(dist_summary, left_on='district', right_on='district_norm', how='left')
    if 'district_norm' in merged.columns:
        merged = merged.drop(columns=['district_norm'])

    merged['cases'] = merged['cases'].fillna(0) if 'cases' in merged.columns else 0
    merged['incidence_rate'] = merged['incidence_rate'].fillna(0) if 'incidence_rate' in merged.columns else 0
    if 'predicted_cases' in merged.columns:
        merged['predicted_cases'] = merged['predicted_cases'].fillna(0)

    merged['risk_level'] = pd.cut(
        merged['cases'],
        bins=[-1, 2, 10, 25, float('inf')],
        labels=['Vùng Xanh (Kiểm soát)', 'Vùng Vàng (Nguy cơ)', 'Vùng Cam (Nguy cơ cao)', 'Vùng Đỏ (Rất cao)']
    ).astype(str)

    os.makedirs(os.path.dirname(str(output_file)), exist_ok=True)
    merged.to_file(output_file, driver='GeoJSON')
    logger.info(f"✅ HCMC Districts Risk GeoJSON saved at: {output_file}")
    return merged


def ensure_hcmc_wards_geojson(output_file=None, district_boundary_file=None, ward_csv_file=None):
    """
    Sinh file GeoJSON ranh giới hành chính các Phường/Xã TP. Hồ Chí Minh
    bằng thuật toán phân hoạch Voronoi bên trong từng đa giác Quận/Huyện
    của `hcmc_districts.geojson` để phủ kín 100% diện tích TP.HCM không có khe hở.
    """
    if output_file is None:
        output_file = getattr(paths, 'HCMC_WARDS_BOUNDARY_FILE', paths.DATA_DIR / "population" / "hcmc_wards.geojson")
    if district_boundary_file is None:
        district_boundary_file = getattr(paths, 'HCMC_BOUNDARY_FILE', paths.DATA_DIR / "population" / "hcmc_districts.geojson")
    if ward_csv_file is None:
        ward_csv_file = getattr(paths, 'WARD_CSV', paths.PROCESSED_DIR / "ward_breakdown.csv")

    if not os.path.exists(district_boundary_file):
        dist_gdf = ensure_hcmc_districts_geojson(output_file=district_boundary_file)
    else:
        dist_gdf = gpd.read_file(district_boundary_file)
        if dist_gdf.crs is not None and str(dist_gdf.crs).lower() != "epsg:4326":
            dist_gdf = dist_gdf.to_crs(epsg=4326)

    wards_by_dist = {}
    if ward_csv_file and os.path.exists(ward_csv_file):
        try:
            wdf = pd.read_csv(ward_csv_file)
            wdf = wdf[wdf['province'].astype(str).str.contains('Hồ Chí Minh', case=False, na=False)].copy()
            wdf['ward_clean'] = wdf['ward'].fillna('').astype(str).str.strip()
            wdf = wdf[~wdf['ward_clean'].isin(['', 'Chưa rõ', 'Tất cả các phường'])]
            wdf = wdf.dropna(subset=['lat', 'lon'])
            if not wdf.empty:
                wdf['dist_norm'] = wdf['district'].apply(normalize_hcmc_district_name)
                agg_w = wdf.groupby(['dist_norm', 'ward_clean'], as_index=False).agg(
                    lat=('lat', 'mean'),
                    lon=('lon', 'mean'),
                )
                for _, wr in agg_w.iterrows():
                    dn = str(wr['dist_norm'])
                    wards_by_dist.setdefault(dn, []).append({
                        'ward': str(wr['ward_clean']),
                        'lat': float(wr['lat']),
                        'lon': float(wr['lon']),
                    })
        except Exception as exc:
            logger.warning(f"Không đọc được ward_breakdown.csv để tách phường: {exc}")

    records = []
    for _, drow in dist_gdf.iterrows():
        dist_name = normalize_hcmc_district_name(drow.get('district') or drow.get('adm1_name1') or '')
        dist_geom = drow.geometry
        if dist_geom is None or dist_geom.is_empty:
            continue
        dist_poly = dist_geom.buffer(0)
        ward_list = wards_by_dist.get(dist_name, [])

        if len(ward_list) >= 2:
            pts = []
            used_coords = set()
            for idx, w in enumerate(ward_list):
                w_lat = float(w['lat'])
                w_lon = float(w['lon'])
                key = (round(w_lat, 5), round(w_lon, 5))
                if key in used_coords:
                    angle = idx * 1.1
                    w_lat += 0.0018 * math.sin(angle)
                    w_lon += 0.0018 * math.cos(angle)
                used_coords.add((round(w_lat, 5), round(w_lon, 5)))
                pts.append(Point(w_lon, w_lat))

            mp = MultiPoint(pts)
            vor_geom = voronoi_diagram(mp, envelope=dist_poly.envelope.buffer(0.25))
            vor_polys = [g for g in getattr(vor_geom, 'geoms', []) if not g.is_empty]

            used_vp = set()
            for w, pt in zip(ward_list, pts):
                matched_idx = None
                for i, vp in enumerate(vor_polys):
                    if i in used_vp:
                        continue
                    if vp.contains(pt) or vp.distance(pt) < 1e-6:
                        matched_idx = i
                        break
                if matched_idx is None:
                    avail = [(i, vp) for i, vp in enumerate(vor_polys) if i not in used_vp]
                    if avail:
                        matched_idx = min(avail, key=lambda pair: pair[1].distance(pt))[0]

                if matched_idx is not None:
                    used_vp.add(matched_idx)
                    clipped = vor_polys[matched_idx].intersection(dist_poly).buffer(0)
                    if not clipped.is_empty:
                        w_name = w['ward']
                        records.append({
                            'ward': w_name,
                            'district': dist_name,
                            'adm1_name1': f"{w_name} - {dist_name}",
                            'province': 'TP. Hồ Chí Minh',
                            'is_ward_split': True,
                            'center_lat': round(pt.y, 6),
                            'center_lon': round(pt.x, 6),
                            'geometry': clipped,
                        })
        else:
            c_pt = dist_poly.representative_point()
            w_name = ward_list[0]['ward'] if len(ward_list) == 1 else dist_name
            records.append({
                'ward': w_name,
                'district': dist_name,
                'adm1_name1': f"{w_name} - {dist_name}" if len(ward_list) == 1 else dist_name,
                'province': 'TP. Hồ Chí Minh',
                'is_ward_split': bool(len(ward_list) == 1),
                'center_lat': round(float(drow.get('center_lat') or c_pt.y), 6),
                'center_lon': round(float(drow.get('center_lon') or c_pt.x), 6),
                'geometry': dist_poly,
            })

    try:
        gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    except Exception:
        gdf = gpd.GeoDataFrame(records)
    os.makedirs(os.path.dirname(str(output_file)), exist_ok=True)
    gdf.to_file(output_file, driver='GeoJSON')
    logger.info(f"✅ HCMC Wards GeoJSON saved ({len(gdf)} polygons) at: {output_file}")
    return gdf