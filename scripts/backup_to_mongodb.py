"""
scripts/backup_to_mongodb.py
============================
Script thực hiện sao lưu toàn bộ dữ liệu từ thư mục `data/processed` lên MongoDB.
Đồng thời kiểm tra và xác thực dữ liệu nguồn chính (Primary Source).

Cách chạy:
    python scripts/backup_to_mongodb.py
"""

import sys
from pathlib import Path

# Add src to sys.path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.stdout.reconfigure(encoding='utf-8')

from mongo_data_service import mongo_data_service
import paths


def main():
    print("=" * 65)
    print(" Dengue Prediction System - MongoDB Backup & Sync Utility ")
    print("=" * 65)
    print(f"Data Processed Dir: {paths.PROCESSED_DIR}")

    if not paths.PROCESSED_DIR.exists():
        print(f"Thư mục {paths.PROCESSED_DIR} không tồn tại!")
        return

    print("\n[1/3] Kiểm tra kết nối MongoDB...")
    if mongo_data_service.is_connected:
        print(f"✅ Kết nối MongoDB thành công! Database: '{mongo_data_service.db_name}'")
    else:
        print(f"⚠️ Không thể kết nối tới MongoDB ({mongo_data_service._connection_error}).")
        print("   Hệ thống sẽ ghi nhận và sẵn sàng kích hoạt Local Fallback.")

    print("\n[2/3] Tiến hành sao lưu dữ liệu data/processed lên MongoDB...")
    results = mongo_data_service.backup_all_processed_files()
    for ds, status in results.items():
        print(f" - Dataset [{ds}]: {status}")

    print("\n[3/3] Thử nghiệm đọc Callback từ MongoDB (Primary Source Test)...")
    for key in ["historical", "district_breakdown", "hcmc_hotspots", "latest_predictions"]:
        df = mongo_data_service.load_dataset(key)
        print(f" -> Tải dataset '{key}': {len(df)} dòng dữ liệu.")

    print("\n" + "=" * 65)
    print(" Hoàn tất quy trình Backup và Kiểm tra Callback MongoDB!")
    print("=" * 65)


if __name__ == "__main__":
    main()
