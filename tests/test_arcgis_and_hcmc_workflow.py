import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src import paths  # noqa: E402
from src import map_pins_service  # noqa: E402
from src.gis_mapper import (  # noqa: E402
    ensure_hcmc_districts_geojson,
    create_hcmc_district_map_data,
)
from src.model import (  # noqa: E402
    train_district_model,
    predict_future_districts,
)


class TestArcGISAndHCMCWorkflow(unittest.TestCase):

    def test_arcgis_component_exists_and_valid(self):
        comp_path = paths.SRC_DIR / "arcgis_component" / "index.html"
        self.assertTrue(comp_path.exists(), "ArcGIS component index.html must exist")
        html_text = comp_path.read_text(encoding="utf-8")
        self.assertIn("https://js.arcgis.com/4.29/", html_text)
        self.assertIn("esri/views/MapView", html_text)
        self.assertIn("esri/views/SceneView", html_text)
        self.assertIn("esri/widgets/LayerList", html_text)
        self.assertIn("esri/layers/GraphicsLayer", html_text)
        self.assertIn("streamlit:componentReady", html_text)
        self.assertIn("pin_selected", html_text)

    def test_hcmc_districts_geojson_and_risk_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            boundary_out = tmp_path / "hcmc_districts.geojson"
            risk_out = tmp_path / "hcmc_districts_risk.geojson"

            gdf = ensure_hcmc_districts_geojson(output_file=boundary_out, province_boundary_file="")
            self.assertTrue(boundary_out.exists())
            self.assertGreaterEqual(len(gdf), 20)
            self.assertIn("district", gdf.columns)
            gj = json.loads(boundary_out.read_text(encoding="utf-8"))
            self.assertEqual(gj.get("type"), "FeatureCollection")
            self.assertGreaterEqual(len(gj.get("features", [])), 20)

            dist_df = pd.DataFrame([
                {"province": "TP. Hồ Chí Minh", "district": "Bình Thạnh", "date": "2025-12-31", "cases": 57, "incidence_rate": 0.6},
                {"province": "TP. Hồ Chí Minh", "district": "Gò Vấp", "date": "2025-12-31", "cases": 55, "incidence_rate": 0.58},
                {"province": "TP. Hồ Chí Minh", "district": "Thành Phố Thủ Đức", "date": "2025-12-31", "cases": 21, "incidence_rate": 0.22},
            ])
            preds_df = pd.DataFrame([
                {"province": "TP. Hồ Chí Minh", "district": "Bình Thạnh", "step": 1, "predicted_cases": 42.5},
                {"province": "TP. Hồ Chí Minh", "district": "Gò Vấp", "step": 1, "predicted_cases": 39.0},
            ])

            merged = create_hcmc_district_map_data(
                dist_df,
                boundary_file=boundary_out,
                output_file=risk_out,
                predictions_df=preds_df,
            )
            self.assertTrue(risk_out.exists())
            self.assertIn("risk_level", merged.columns)
            self.assertIn("predicted_cases", merged.columns)

            bt_row = merged[merged["district"] == "Bình Thạnh"].iloc[0]
            self.assertEqual(float(bt_row["cases"]), 57.0)
            self.assertAlmostEqual(float(bt_row["predicted_cases"]), 42.5, places=1)
            td_row = merged[merged["district"] == "Thủ Đức"].iloc[0]
            self.assertEqual(float(td_row["cases"]), 21.0)

    def test_hcmc_district_xgboost_train_and_predict(self):
        rows = []
        weather_rows = []
        dates = pd.date_range("2025-01-31", periods=8, freq="ME")
        for idx, dt in enumerate(dates):
            weather_rows.append({
                "province": "TP. Hồ Chí Minh",
                "year": dt.year,
                "month": dt.month,
                "precipitation_sum": 50.0 + idx * 35.0,
                "temp_mean": 27.0 + (idx % 3) * 0.6,
                "humidity_mean": 72.0 + idx * 2.0,
                "pm25_mean": 25.0 + idx,
            })
            for dist, base in [("Quận 1", 8), ("Bình Thạnh", 22), ("Gò Vấp", 18), ("Thủ Đức", 15)]:
                rows.append({
                    "province": "TP. Hồ Chí Minh",
                    "district": dist,
                    "date": dt.strftime("%Y-%m-%d"),
                    "year": dt.year,
                    "month": dt.month,
                    "cases": base + idx * 3,
                })

        dist_df = pd.DataFrame(rows)
        weather_df = pd.DataFrame(weather_rows)

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "district_xgb.pkl"
            bundle = train_district_model(dist_df, weather_df=weather_df, model_path=model_path, test_months=2)
            self.assertIsNotNone(bundle)
            self.assertTrue(model_path.exists())
            self.assertIn("rmse", bundle["metrics"])
            self.assertIn("mae", bundle["metrics"])

            preds = predict_future_districts(bundle, dist_df, weather_df=weather_df, n_months=3)
            self.assertEqual(len(preds), 4 * 3)
            self.assertTrue((preds["predicted_cases"] >= 0).all())
            self.assertEqual(sorted(preds["step"].unique().tolist()), [1, 2, 3])

    def test_pin_and_cluster_dispatch_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pins_file = tmp_path / "map_pins.json"
            actions_file = tmp_path / "cluster_actions.json"

            offline_mongo = types.SimpleNamespace(is_connected=False, db=None)
            with patch.object(map_pins_service, "LOCAL_PINS_FILE", pins_file), \
                 patch.object(map_pins_service, "CLUSTER_ACTIONS_FILE", actions_file), \
                 patch.object(map_pins_service, "mongo_data_service", offline_mongo):

                created = map_pins_service.add_pin(
                    lat=10.8106,
                    lon=106.7091,
                    comment="Có nhiều lăng quăng quanh hẻm trọ",
                    author="Nguyễn Văn Test",
                    area_name="Phường 25, Bình Thạnh",
                    category="💧 Nước đọng / Lăng quăng",
                )
                self.assertEqual(created["status"], "pending")
                self.assertEqual(created["status_label"], map_pins_service.PIN_STATUS_OPTIONS["pending"])

                ok = map_pins_service.update_pin_status(
                    pin_id=created["id"],
                    status="spraying",
                    verified_by="BS. CKI Nguyễn Văn A",
                    assigned_team="Đội cơ động chống dịch HCDC",
                    action_note="Đã điều xe phun ULV bán kính 200m",
                )
                self.assertTrue(ok)

                loaded = map_pins_service.load_pins()
                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0]["status"], "spraying")
                self.assertEqual(loaded[0]["verified_by"], "BS. CKI Nguyễn Văn A")
                self.assertEqual(loaded[0]["assigned_team"], "Đội cơ động chống dịch HCDC")

                c_act = map_pins_service.update_cluster_action(
                    cluster_id="ST_HCM_BinhThanh_Test",
                    status="resolved",
                    assigned_team="Trạm Y tế Phường/Xã",
                    action_note="Đã hoàn tất phun hóa chất đợt 2",
                    updated_by="BS. CKI Nguyễn Văn A",
                )
                self.assertEqual(c_act["status"], "resolved")
                all_actions = map_pins_service.load_cluster_actions()
                self.assertIn("ST_HCM_BinhThanh_Test", all_actions)
                self.assertEqual(all_actions["ST_HCM_BinhThanh_Test"]["status_label"], map_pins_service.PIN_STATUS_OPTIONS["resolved"])

                deleted = map_pins_service.delete_pin(created["id"])
                self.assertTrue(deleted)
                self.assertEqual(len(map_pins_service.load_pins()), 0)


if __name__ == "__main__":
    unittest.main()
