"""
test_mongo_data_service.py - Test MongoDB data persistence and fallback
"""
import unittest
import sys
from pathlib import Path
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from mongo_data_service import mongo_data_service
import paths


class TestMongoDataService(unittest.TestCase):

    def test_01_service_initialization(self):
        """Kiểm tra khởi tạo mongo_data_service."""
        self.assertIsNotNone(mongo_data_service)
        self.assertTrue(hasattr(mongo_data_service, "load_dataset"))
        self.assertTrue(hasattr(mongo_data_service, "save_dataset"))
        self.assertTrue(hasattr(mongo_data_service, "backup_all_processed_files"))

    def test_02_load_dataset_fallback(self):
        """Kiểm tra đọc dữ liệu (qua MongoDB hoặc Callback local)."""
        df = mongo_data_service.load_dataset("historical", paths.HISTORICAL_CSV)
        self.assertFalse(df.empty)
        self.assertIn("province", df.columns)
        self.assertIn("cases", df.columns)

    def test_03_save_and_reload(self):
        """Kiểm tra lưu và tải lại dữ liệu."""
        sample_df = pd.DataFrame([
            {"province": "Hà Nội", "year": 2026, "month": 10, "cases": 99}
        ])
        test_path = paths.PROCESSED_DIR / "test_sample.csv"
        mongo_data_service.save_dataset("test_sample", sample_df, test_path)
        
        reloaded = mongo_data_service.load_dataset("test_sample", test_path)
        self.assertFalse(reloaded.empty)
        self.assertEqual(int(reloaded["cases"].iloc[0]), 99)

        # Cleanup test file
        if test_path.exists():
            test_path.unlink()


if __name__ == "__main__":
    unittest.main()
