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

CLUSTER_ACTIONS_FILE: Path = getattr(
    paths,
    "CLUSTER_ACTIONS_FILE",
    getattr(paths, "PROCESSED_DIR", Path("data/processed")) / "cluster_actions.json",
)
CLUSTER_COLLECTION_NAME = "cluster_actions"

PIN_STATUS_OPTIONS: Dict[str, str] = {
    "pending": "⏳ Chờ xác minh",
    "verified": "✅ Đã xác minh ổ dịch",
    "spraying": "🚒 Đang điều phối phun thuốc",
    "resolved": "🛡️ Đã xử lý / An toàn",
}

DISPATCH_TEAMS: List[str] = [
    "Đội cơ động chống dịch HCDC",
    "Đội phun hóa chất Quận/Huyện",
    "Trạm Y tế Phường/Xã",
    "Đội giám sát véc-tơ cộng đồng",
]


def _normalize_pin_record(pin: Dict[str, Any]) -> Dict[str, Any]:
    """Đảm bảo mọi bản ghi pin cũ/mới đều có đủ các trường trạng thái quản lý dịch."""
    item = dict(pin)
    st_code = item.get("status") or "pending"
    if st_code not in PIN_STATUS_OPTIONS:
        st_code = "pending"
    item["status"] = st_code
    item["status_label"] = item.get("status_label") or PIN_STATUS_OPTIONS[st_code]
    item.setdefault("verified_by", "")
    item.setdefault("assigned_team", "")
    item.setdefault("action_note", "")
    item.setdefault("updated_at", item.get("created_at", ""))
    return item


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
                normalized = [_normalize_pin_record(d) for d in docs]
                _write_local_pins(normalized)
                return normalized
            # Nếu MongoDB chưa có dữ liệu nhưng local có, đồng bộ lên
            local = [_normalize_pin_record(d) for d in _read_local_pins()]
            if local:
                mongo_data_service.db[COLLECTION_NAME].insert_many(
                    [dict(item) for item in local]
                )
            return local
        except Exception as exc:
            logger.warning("Lỗi đọc map_pins từ MongoDB, dùng local fallback: %s", exc)

    pins = [_normalize_pin_record(d) for d in _read_local_pins()]
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

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pin: Dict[str, Any] = {
        "id": str(uuid.uuid4())[:8],
        "lat": round(float(lat), 6),
        "lon": round(float(lon), 6),
        "area_name": (area_name or "").strip(),
        "author": (author or "Người dân").strip() or "Người dân",
        "category": (category or "💬 Ý kiến khác").strip(),
        "comment": clean_comment,
        "status": "pending",
        "status_label": PIN_STATUS_OPTIONS["pending"],
        "verified_by": "",
        "assigned_team": "",
        "action_note": "",
        "created_at": now_str,
        "updated_at": now_str,
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


def update_pin_status(
    pin_id: str,
    status: str,
    verified_by: str = "",
    assigned_team: str = "",
    action_note: str = "",
) -> bool:
    """Cập nhật trạng thái xác minh & điều phối xử lý cho một điểm phản ánh cộng đồng."""
    if not pin_id:
        return False
    if status not in PIN_STATUS_OPTIONS:
        raise ValueError(f"Trạng thái không hợp lệ: {status}")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_label = PIN_STATUS_OPTIONS[status]
    updated = False

    pins = [_normalize_pin_record(p) for p in _read_local_pins()]
    for p in pins:
        if p.get("id") == pin_id:
            p["status"] = status
            p["status_label"] = status_label
            p["verified_by"] = (verified_by or p.get("verified_by", "")).strip()
            p["assigned_team"] = (assigned_team or "").strip()
            p["action_note"] = (action_note or "").strip()
            p["updated_at"] = now_str
            updated = True
            break
    if updated:
        _write_local_pins(pins)

    if mongo_data_service.is_connected and mongo_data_service.db is not None:
        try:
            res = mongo_data_service.db[COLLECTION_NAME].update_one(
                {"id": pin_id},
                {
                    "$set": {
                        "status": status,
                        "status_label": status_label,
                        "verified_by": (verified_by or "").strip(),
                        "assigned_team": (assigned_team or "").strip(),
                        "action_note": (action_note or "").strip(),
                        "updated_at": now_str,
                    }
                },
            )
            if res.matched_count > 0:
                updated = True
        except Exception as exc:
            logger.warning("Không cập nhật được trạng thái pin trên MongoDB: %s", exc)

    return updated


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


def _read_local_cluster_actions() -> Dict[str, Dict[str, Any]]:
    if not CLUSTER_ACTIONS_FILE.exists():
        return {}
    try:
        data = json.loads(CLUSTER_ACTIONS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("Không đọc được %s: %s", CLUSTER_ACTIONS_FILE, exc)
        return {}


def _write_local_cluster_actions(actions: Dict[str, Dict[str, Any]]) -> None:
    try:
        CLUSTER_ACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CLUSTER_ACTIONS_FILE.write_text(
            json.dumps(actions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Không ghi được %s: %s", CLUSTER_ACTIONS_FILE, exc)


def load_cluster_actions() -> Dict[str, Dict[str, Any]]:
    """Tải trạng thái điều phối & xử lý các ổ dịch (ưu tiên MongoDB, fallback JSON cục bộ)."""
    if mongo_data_service.is_connected and mongo_data_service.db is not None:
        try:
            docs = list(mongo_data_service.db[CLUSTER_COLLECTION_NAME].find({}, {"_id": 0}))
            if docs:
                actions = {d["cluster_id"]: d for d in docs if d.get("cluster_id")}
                _write_local_cluster_actions(actions)
                return actions
            local = _read_local_cluster_actions()
            if local:
                mongo_data_service.db[CLUSTER_COLLECTION_NAME].insert_many(
                    [dict(v) for v in local.values()]
                )
            return local
        except Exception as exc:
            logger.warning("Lỗi đọc cluster_actions từ MongoDB, dùng local fallback: %s", exc)

    return _read_local_cluster_actions()


def update_cluster_action(
    cluster_id: str,
    status: str,
    assigned_team: str = "",
    action_note: str = "",
    updated_by: str = "",
) -> Dict[str, Any]:
    """Cập nhật trạng thái xử lý & điều phối đội dập dịch cho một ổ dịch (cluster_id)."""
    clean_id = (cluster_id or "").strip()
    if not clean_id:
        raise ValueError("cluster_id không được để trống.")
    if status not in PIN_STATUS_OPTIONS:
        raise ValueError(f"Trạng thái không hợp lệ: {status}")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record: Dict[str, Any] = {
        "cluster_id": clean_id,
        "status": status,
        "status_label": PIN_STATUS_OPTIONS[status],
        "assigned_team": (assigned_team or "").strip(),
        "action_note": (action_note or "").strip(),
        "updated_by": (updated_by or "").strip(),
        "updated_at": now_str,
    }

    actions = _read_local_cluster_actions()
    actions[clean_id] = record
    _write_local_cluster_actions(actions)

    if mongo_data_service.is_connected and mongo_data_service.db is not None:
        try:
            mongo_data_service.db[CLUSTER_COLLECTION_NAME].update_one(
                {"cluster_id": clean_id},
                {"$set": dict(record)},
                upsert=True,
            )
        except Exception as exc:
            logger.warning("Không cập nhật được cluster_action lên MongoDB: %s", exc)

    return record
