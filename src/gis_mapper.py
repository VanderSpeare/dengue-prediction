import os
import math
import geopandas as gpd
import pandas as pd
import logging
from shapely.geometry import Point

try:
    from . import paths
except ImportError:
    import paths

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