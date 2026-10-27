import unittest
import pandas as pd
from pathlib import Path

from src.data_processor import (
    parse_hierarchical_address,
    extract_province,
    extract_district,
    classify_risk_level,
    generate_epidemic_clusters,
    load_and_process_new_data
)
from src import paths


class TestHierarchicalDataProcessor(unittest.TestCase):

    def test_parse_street_level_addresses(self):
        addr1 = "70/14 Lê Văn Thọ , Thành phố Hồ Chí Minh"
        p1 = parse_hierarchical_address(addr1)
        self.assertEqual(p1['province'], 'TP. Hồ Chí Minh')
        self.assertEqual(p1['district'], 'Gò Vấp')
        self.assertEqual(p1['street'], 'Lê Văn Thọ')
        self.assertEqual(p1['geo_level'], 'street')
        self.assertAlmostEqual(p1['lat'], 10.8418, places=3)
        self.assertAlmostEqual(p1['lon'], 106.6575, places=3)

        addr2 = "82/10 Điện Biên Phủ  , Tp Hồ Chí Minh"
        p2 = parse_hierarchical_address(addr2)
        self.assertEqual(p2['province'], 'TP. Hồ Chí Minh')
        self.assertEqual(p2['district'], 'Bình Thạnh')
        self.assertEqual(p2['street'], 'Điện Biên Phủ')

    def test_parse_ward_level_addresses(self):
        addr = "Phường An Phú Đông, Tp Hồ Chí Minh"
        p = parse_hierarchical_address(addr)
        self.assertEqual(p['province'], 'TP. Hồ Chí Minh')
        self.assertEqual(p['district'], 'Quận 12')
        self.assertEqual(p['ward'], 'Phường An Phú Đông')
        self.assertEqual(p['geo_level'], 'ward')

    def test_parse_district_level_addresses(self):
        addr = "Quận Bình Thạnh, Thành phố Hồ Chí Minh"
        p = parse_hierarchical_address(addr)
        self.assertEqual(p['province'], 'TP. Hồ Chí Minh')
        self.assertEqual(p['district'], 'Bình Thạnh')

    def test_risk_classification(self):
        risk_red, col_red, r_red, _ = classify_risk_level(20, level='ward')
        self.assertIn('Đỏ', risk_red)
        self.assertEqual(col_red, '#d90429')
        self.assertGreaterEqual(r_red, 500)

        risk_green, col_green, _, _ = classify_risk_level(1, level='ward')
        self.assertIn('Xanh', risk_green)
        self.assertEqual(col_green, '#2a9d8f')

    def test_cluster_generation(self):
        data = [
            {
                'province': 'TP. Hồ Chí Minh',
                'district': 'Gò Vấp',
                'ward': 'Phường 11',
                'street': 'Lê Văn Thọ',
                'lat': 10.8418,
                'lon': 106.6575,
                'date': pd.to_datetime('2025-05-15')
            },
            {
                'province': 'TP. Hồ Chí Minh',
                'district': 'Gò Vấp',
                'ward': 'Phường 11',
                'street': 'Lê Văn Thọ',
                'lat': 10.8418,
                'lon': 106.6575,
                'date': pd.to_datetime('2025-05-20')
            }
        ]
        df_enriched = pd.DataFrame(data)
        clusters = generate_epidemic_clusters(df_enriched)
        self.assertFalse(clusters.empty)
        self.assertIn('cluster_id', clusters.columns)
        self.assertIn('radius_meters', clusters.columns)
        self.assertIn('risk_level', clusters.columns)


if __name__ == '__main__':
    unittest.main()
