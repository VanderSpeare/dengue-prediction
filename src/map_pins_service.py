"""
map_pins_service.py - Persistence for User Map Pins & Community Comments
========================================================================
Lưu trữ và truy xuất các điểm ghim trên bản đồ kèm ý kiến / bình luận
của người dân về tình hình dịch sốt xuất huyết tại khu vực.
Ưu tiên lưu trên MongoDB (collection `map_pins`) và luôn đồng bộ fallback
về tệp JSON cục bộ (`data/processed/map_pins.json`) khi mất kết nối.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from . import paths
    from .mongo_data_service import mongo_data_service
except ImportError:
    import paths
    from mongo_data_service import mongo_data_service

logger = logging.getLogger("map_pins_service")

LOCAL_PINS_FILE: Path = getattr(paths, "PROCESSED_DIR", Path("data/processed")) / "map_pins.json"
COLLECTION_NAME = "map_pins"


def _read_local_pins() -> List[Dict[str, Any]]:
    if not LOCAL_PINS_FILE.exists():
        return []
    try:
        data = json.loads(LOCAL_PINS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.warning("Không đọc được %s: %s", LOCAL_PINS_FILE, exc)
        return []


def _write_local_pins(pins: List[Dict[str, Any]]) -> None:
    try:
        LOCAL_PINS_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_PINS_FILE.write_text(
            json.dumps(pins, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Không ghi được %s: %s", LOCAL_PINS_FILE, exc)


def load_pins() -> List[Dict[str, Any]]:
    """Tải danh sách điểm ghim & bình luận (ưu tiên MongoDB, fallback JSON cục bộ)."""
    if mongo_data_service.is_connected and mongo_data_service.db is not None:
        try:
            docs = list(
                mongo_data_service.db[COLLECTION_NAME]
                .find({}, {"_id": 0})
                .sort("created_at", -1)
            )
            if docs:
                _write_local_pins(docs)
                return docs
            # Nếu MongoDB chưa có dữ liệu nhưng local có, đồng bộ lên
            local = _read_local_pins()
            if local:
                mongo_data_service.db[COLLECTION_NAME].insert_many(
                    [dict(item) for item in local]
                )
            return local
        except Exception as exc:
            logger.warning("Lỗi đọc map_pins từ MongoDB, dùng local fallback: %s", exc)

    pins = _read_local_pins()
    pins.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return pins


def add_pin(
    lat: float,
    lon: float,
    comment: str,
    author: str = "Người dân",
    area_name: str = "",
    category: str = "💬 Ý kiến khác",
) -> Dict[str, Any]:
    """Thêm một điểm ghim mới kèm ý kiến/bình luận và lưu bền vững."""
    clean_comment = (comment or "").strip()
    if not clean_comment:
        raise ValueError("Nội dung bình luận không được để trống.")

    pin: Dict[str, Any] = {
        "id": str(uuid.uuid4())[:8],
        "lat": round(float(lat), 6),
        "lon": round(float(lon), 6),
        "area_name": (area_name or "").strip(),
        "author": (author or "Người dân").strip() or "Người dân",
        "category": (category or "💬 Ý kiến khác").strip(),
        "comment": clean_comment,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    pins = _read_local_pins()
    pins.insert(0, pin)
    _write_local_pins(pins)

    if mongo_data_service.is_connected and mongo_data_service.db is not None:
        try:
            mongo_data_service.db[COLLECTION_NAME].insert_one(dict(pin))
        except Exception as exc:
            logger.warning("Không lưu được pin lên MongoDB (đã lưu local): %s", exc)

    return pin


def delete_pin(pin_id: str) -> bool:
    """Xóa một điểm ghim theo id."""
    if not pin_id:
        return False

    pins = _read_local_pins()
    new_pins = [p for p in pins if p.get("id") != pin_id]
    deleted = len(new_pins) < len(pins)
    if deleted:
        _write_local_pins(new_pins)

    if mongo_data_service.is_connected and mongo_data_service.db is not None:
        try:
            res = mongo_data_service.db[COLLECTION_NAME].delete_one({"id": pin_id})
            if res.deleted_count > 0:
                deleted = True
        except Exception as exc:
            logger.warning("Không xóa được pin trên MongoDB: %s", exc)

    return deleted
