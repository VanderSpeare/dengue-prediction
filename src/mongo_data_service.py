"""
mongo_data_service.py - MongoDB Persistence & Data Layer for Dengue Datasets
=============================================================================
Cung cấp cơ chế:
1. Backup toàn bộ dữ liệu từ thư mục data/processed lên MongoDB.
2. Sử dụng MongoDB làm Nguồn Dữ Liệu Chính (Primary Source).
3. Fallback / Callback về Local CSV khi mất kết nối MongoDB để đảm bảo hệ thống không bị gián đoạn.
4. Tự động đồng bộ hai chiều (MongoDB <-> Local Cache).
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient, ReplaceOne, UpdateOne

try:
    from . import paths
except ImportError:
    import paths

logger = logging.getLogger("mongo_data_service")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Load environment
_ROOT = paths.PROJECT_ROOT
load_dotenv(_ROOT / ".env", override=True)


COLLECTION_MAPPING = {
    "historical": "historical_cases",
    "district_breakdown": "district_breakdown",
    "ward_breakdown": "ward_breakdown",
    "street_hotspots": "street_hotspots",
    "epidemic_clusters": "epidemic_clusters",
    "hcmc_hotspots": "hcmc_hotspots",
    "historical_weather": "historical_weather",
    "latest_predictions": "latest_predictions",
    "weather_cache": "weather_cache",
    "vector_store": "vector_store"
}

FILE_PATH_MAPPING = {
    "historical": paths.HISTORICAL_CSV,
    "district_breakdown": paths.DISTRICT_CSV,
    "ward_breakdown": getattr(paths, 'WARD_CSV', paths.PROCESSED_DIR / "ward_breakdown.csv"),
    "street_hotspots": getattr(paths, 'STREET_HOTSPOTS_CSV', paths.PROCESSED_DIR / "street_hotspots.csv"),
    "epidemic_clusters": getattr(paths, 'EPIDEMIC_CLUSTERS_CSV', paths.PROCESSED_DIR / "epidemic_clusters.csv"),
    "hcmc_hotspots": paths.HCMC_HOTSPOTS_CSV,
    "historical_weather": paths.PROCESSED_DIR / "historical_weather.csv",
    "latest_predictions": paths.PREDICTIONS_CSV,
    "weather_cache": paths.PROCESSED_DIR / "weather_cache.csv",
    "vector_store": paths.VECTOR_STORE_FILE
}


class MongoDataService:
    """Quản lý đọc / ghi / backup dữ liệu dịch tễ với MongoDB là nguồn chính."""

    def __init__(self):
        self.uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME", "dengue_clinic_db")
        self.client: Optional[MongoClient] = None
        self.db = None
        self._is_connected = False
        self._connection_error = None
        self.connect()

    def connect(self) -> bool:
        """Kết nối tới MongoDB an toàn với nhiều phương thức TLS fallback."""
        load_dotenv(_ROOT / ".env", override=True)
        self.uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME", "dengue_clinic_db")

        if not self.uri or self.uri == "your_mongodb_uri_here":
            self._is_connected = False
            self._connection_error = "Chưa cấu hình MONGODB_URI trong .env"
            return False

        # Thử các phương thức kết nối an toàn
        attempts = []
        try:
            import certifi
            attempts.append({"tlsCAFile": certifi.where(), "serverSelectionTimeoutMS": 3000, "connectTimeoutMS": 3000})
        except Exception:
            pass

        attempts.append({"tlsAllowInvalidCertificates": True, "serverSelectionTimeoutMS": 3000, "connectTimeoutMS": 3000})
        attempts.append({"serverSelectionTimeoutMS": 3000, "connectTimeoutMS": 3000})

        for opts in attempts:
            try:
                client = MongoClient(self.uri, **opts)
                client.admin.command("ping")
                self.client = client
                self.db = self.client.get_database(self.db_name)
                self._is_connected = True
                self._connection_error = None
                logger.info(f"MongoDataService kết nối thành công Database: '{self.db_name}'")
                return True
            except Exception as e:
                self._connection_error = str(e)
                try:
                    if client:
                        client.close()
                except Exception:
                    pass

        self._is_connected = False
        logger.warning(
            f"MongoDataService không thể kết nối tới MongoDB: {self._connection_error}. "
            "Kích hoạt cơ chế Local Fallback."
        )
        return False

    @property
    def is_connected(self) -> bool:
        if not self._is_connected or self.db is None:
            return False
        return True

    def backup_dataframe_to_mongo(self, dataset_key: str, df: pd.DataFrame) -> bool:
        """Lưu toàn bộ DataFrame vào MongoDB collection tương ứng."""
        if not self.is_connected or df.empty:
            return False

        coll_name = COLLECTION_MAPPING.get(dataset_key, dataset_key)
        try:
            coll = self.db[coll_name]
            records = df.to_dict(orient="records")

            # Xử lý datetime chuyển sang string ISO format để MongoDB lưu chuẩn
            for r in records:
                for k, v in list(r.items()):
                    if pd.isna(v):
                        r[k] = None
                    elif isinstance(v, (pd.Timestamp, datetime)):
                        r[k] = v.isoformat()

            coll.delete_many({})  # Thay thế dữ liệu mới nhất
            if records:
                coll.insert_many(records)

            # Cập nhật metadata
            self.db["backup_metadata"].replace_one(
                {"dataset": dataset_key},
                {
                    "dataset": dataset_key,
                    "collection": coll_name,
                    "row_count": len(records),
                    "last_backup": datetime.now().isoformat(),
                    "status": "SUCCESS"
                },
                upsert=True
            )
            logger.info(f"Đã backup thành công {len(records)} dòng từ '{dataset_key}' lên MongoDB collection '{coll_name}'.")
            return True
        except Exception as e:
            logger.error(f"Lỗi backup '{dataset_key}' lên MongoDB: {e}")
            return False

    def backup_json_to_mongo(self, dataset_key: str, json_file_path: Path) -> bool:
        """Backup file JSON (ví dụ vector_store) lên MongoDB."""
        if not self.is_connected or not json_file_path.exists():
            return False

        coll_name = COLLECTION_MAPPING.get(dataset_key, dataset_key)
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            coll = self.db[coll_name]
            coll.delete_many({})
            if isinstance(content, list):
                if content:
                    coll.insert_many(content)
            elif isinstance(content, dict):
                coll.insert_one(content)

            self.db["backup_metadata"].replace_one(
                {"dataset": dataset_key},
                {
                    "dataset": dataset_key,
                    "collection": coll_name,
                    "last_backup": datetime.now().isoformat(),
                    "status": "SUCCESS"
                },
                upsert=True
            )
            logger.info(f"Đã backup file JSON '{dataset_key}' lên MongoDB collection '{coll_name}'.")
            return True
        except Exception as e:
            logger.error(f"Lỗi backup JSON '{dataset_key}': {e}")
            return False

    def backup_all_processed_files(self) -> Dict[str, Any]:
        """Đọc toàn bộ file trong data/processed và đẩy lên MongoDB."""
        logger.info("=== Bắt đầu Backup toàn bộ data/processed lên MongoDB ===")
        results = {}
        for key, path in FILE_PATH_MAPPING.items():
            if not path.exists():
                results[key] = "FILE_NOT_FOUND"
                continue

            if path.suffix == ".csv":
                try:
                    df = pd.read_csv(path)
                    ok = self.backup_dataframe_to_mongo(key, df)
                    results[key] = "BACKED_UP" if ok else "FALLBACK_LOCAL"
                except Exception as e:
                    results[key] = f"ERROR: {e}"
            elif path.suffix == ".json":
                ok = self.backup_json_to_mongo(key, path)
                results[key] = "BACKED_UP" if ok else "FALLBACK_LOCAL"

        logger.info(f"Kết quả backup MongoDB: {results}")
        return results

    def load_dataset(self, dataset_key: str, local_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Đọc dataset với MONGODB LÀ NGUỒN CHÍNH (SRC CHÍNH).
        Nếu MongoDB có data -> load từ MongoDB.
        Nếu không -> fallback sang file Local CSV.
        """
        coll_name = COLLECTION_MAPPING.get(dataset_key, dataset_key)
        if local_path is None:
            local_path = FILE_PATH_MAPPING.get(dataset_key)

        # 1. Thử load từ MongoDB làm nguồn chính
        if self.is_connected:
            try:
                coll = self.db[coll_name]
                cursor = coll.find({}, {"_id": 0})
                records = list(cursor)
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"[MongoDB Primary] Đã tải {len(df)} dòng từ MongoDB collection '{coll_name}'.")
                    # Tự động đồng bộ / cập nhật local cache
                    if local_path:
                        try:
                            local_path.parent.mkdir(parents=True, exist_ok=True)
                            df.to_csv(local_path, index=False)
                        except Exception:
                            pass
                    return df
            except Exception as e:
                logger.warning(f"Lỗi khi đọc từ MongoDB collection '{coll_name}': {e}. Chuyển sang Fallback Local.")

        # 2. Callback / Fallback đọc từ Local file
        if local_path and local_path.exists():
            try:
                df = pd.read_csv(local_path)
                logger.info(f"[Local Fallback] Đã tải {len(df)} dòng từ local file '{local_path.name}'.")
                return df
            except Exception as e:
                logger.error(f"Lỗi đọc local file '{local_path}': {e}")

        logger.warning(f"Dataset '{dataset_key}' không có dữ liệu trên cả MongoDB và Local.")
        return pd.DataFrame()

    def save_dataset(self, dataset_key: str, df: pd.DataFrame, local_path: Optional[Path] = None) -> None:
        """
        Lưu dataset: Lưu lên MongoDB (Nguồn chính) và đồng thời lưu file Local.
        """
        if local_path is None:
            local_path = FILE_PATH_MAPPING.get(dataset_key)

        # 1. Lưu Local file
        if local_path and not df.empty:
            try:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(local_path, index=False)
                logger.info(f"Đã lưu {len(df)} dòng ra local file '{local_path.name}'.")
            except Exception as e:
                logger.error(f"Lỗi lưu local file '{local_path}': {e}")

        # 2. Lưu lên MongoDB
        if self.is_connected and not df.empty:
            self.backup_dataframe_to_mongo(dataset_key, df)


# Khởi tạo singleton service
mongo_data_service = MongoDataService()
