"""
doctor_auth.py - Doctor Authentication & Account Management (SHA-256)
======================================================================
Quản lý xác thực và phân quyền cho Bác sĩ:
1. 4 tài khoản Bác sĩ được cấu hình sẵn với mật khẩu mã hóa SHA-256.
2. Lưu trữ và đồng bộ vào MongoDB collection `doctors`.
3. Quản lý Session Token an toàn cho các chức năng độc quyền của Bác sĩ.
"""

import hashlib
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel

logger = logging.getLogger("booking.doctor_auth")


def hash_password_sha256(password: str) -> str:
    """Mã hóa mật khẩu bằng thuật toán SHA-256 (SHA2)."""
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()


class DoctorProfile(BaseModel):
    doctor_id: str
    username: str
    password_hash: str
    full_name: str
    title: str
    specialty: str
    room: str
    phone: str
    email: str
    avatar_url: str
    created_at: str


# =============================================================================
# 4 TÀI KHOẢN BÁC SĨ MẶC ĐỊNH (Mật khẩu mặc định: Bacsi@123)
# =============================================================================
DEFAULT_PASSWORD_PLAIN = "Bacsi@123"
DEFAULT_PASSWORD_HASH = hash_password_sha256(DEFAULT_PASSWORD_PLAIN)

PREDEFINED_DOCTORS: List[Dict[str, Any]] = [
    {
        "doctor_id": "doc_01",
        "username": "bs_nguyenvana",
        "password_hash": DEFAULT_PASSWORD_HASH,
        "full_name": "BS. CKI Nguyễn Văn A",
        "title": "Bác sĩ Chuyên khoa I",
        "specialty": "Bệnh Truyền Nhiễm & Sốt Xuất Huyết Dengue",
        "room": "Phòng 302, Tầng 3",
        "phone": "0903112233",
        "email": "dr.nguyenvana@clinic.vn",
        "avatar_url": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-01-01T00:00:00"
    },
    {
        "doctor_id": "doc_02",
        "username": "bs_tranthib",
        "password_hash": DEFAULT_PASSWORD_HASH,
        "full_name": "BS. CKII Trần Thị B",
        "title": "Bác sĩ Chuyên khoa II",
        "specialty": "Truyền Nhiễm & Dịch Tễ Học Lâm Sàng",
        "room": "Phòng 304, Tầng 3",
        "phone": "0903223344",
        "email": "dr.tranthib@clinic.vn",
        "avatar_url": "https://images.unsplash.com/photo-1594824813589-3221e537c352?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-01-01T00:00:00"
    },
    {
        "doctor_id": "doc_03",
        "username": "bs_lehoangc",
        "password_hash": DEFAULT_PASSWORD_HASH,
        "full_name": "ThS. BS Lê Hoàng C",
        "title": "Thạc sĩ - Bác sĩ Điều trị",
        "specialty": "Hồi Sức Cấp Cứu Nhi & Sốt Xuất Huyết Nặng",
        "room": "Phòng 306, Tầng 3",
        "phone": "0903334455",
        "email": "dr.lehoangc@clinic.vn",
        "avatar_url": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-01-01T00:00:00"
    },
    {
        "doctor_id": "doc_04",
        "username": "bs_phamminhd",
        "password_hash": DEFAULT_PASSWORD_HASH,
        "full_name": "BS. CKI Phạm Minh D",
        "title": "Bác sĩ Chuyên khoa I",
        "specialty": "Nội Tổng Quát & Chẩn Đoán Sớm Sốt Xuất Huyết",
        "room": "Phòng 308, Tầng 3",
        "phone": "0903445566",
        "email": "dr.phamminhd@clinic.vn",
        "avatar_url": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-01-01T00:00:00"
    }
]


class DoctorAuthService:
    """Service xử lý Đăng nhập, Xác thực Token & Phân quyền Bác sĩ."""

    def __init__(self):
        # In-memory session tokens: { token_str: { "doctor": DoctorProfile, "created_at": datetime } }
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        # In-memory doctors dict: { username: DoctorProfile }
        self._doctors_cache: Dict[str, DoctorProfile] = {
            doc["username"]: DoctorProfile(**doc) for doc in PREDEFINED_DOCTORS
        }

    def seed_doctors_to_mongo(self, mongo_db):
        """Đồng bộ 4 tài khoản Bác sĩ vào MongoDB collection `doctors`."""
        if mongo_db is None:
            return

        try:
            for doc in PREDEFINED_DOCTORS:
                mongo_db.doctors.update_one(
                    {"username": doc["username"]},
                    {"$setOnInsert": doc},
                    upsert=True
                )
            logger.info("Đã đồng bộ 4 tài khoản Bác sĩ (mã hóa SHA-256) vào MongoDB collection 'doctors'.")
        except Exception as e:
            logger.error(f"Lỗi khi đồng bộ tài khoản bác sĩ lên MongoDB: {e}")

    def authenticate_doctor(self, username: str, password_plain: str, mongo_db=None) -> Optional[Tuple[str, DoctorProfile]]:
        """
        Xác thực đăng nhập Bác sĩ:
        - Mã hóa mật khẩu nhập vào bằng SHA-256.
        - So khớp với mật khẩu hash trong MongoDB hoặc RAM.
        - Nếu đúng -> Cấp session token.
        """
        clean_user = username.strip().lower()
        pass_hash = hash_password_sha256(password_plain)

        doctor_data = None

        # 1. Tìm trên MongoDB nếu có
        if mongo_db is not None:
            try:
                db_doc = mongo_db.doctors.find_one({"username": clean_user})
                if db_doc:
                    doctor_data = db_doc
            except Exception as e:
                logger.warning(f"Lỗi truy vấn MongoDB doctors: {e}")

        # 2. Fallback tìm trong bộ nhớ
        if not doctor_data and clean_user in self._doctors_cache:
            doctor_data = self._doctors_cache[clean_user].dict()

        if not doctor_data:
            return None

        # 3. So khớp mã băm SHA-256
        if doctor_data.get("password_hash") != pass_hash:
            return None

        # 4. Sinh Session Token
        session_token = f"doc_sec_{uuid.uuid4().hex}"
        doc_profile = DoctorProfile(
            doctor_id=doctor_data["doctor_id"],
            username=doctor_data["username"],
            password_hash="[PROTECTED_SHA256]",
            full_name=doctor_data["full_name"],
            title=doctor_data["title"],
            specialty=doctor_data["specialty"],
            room=doctor_data["room"],
            phone=doctor_data["phone"],
            email=doctor_data["email"],
            avatar_url=doctor_data.get("avatar_url", ""),
            created_at=doctor_data.get("created_at", "")
        )

        self._active_sessions[session_token] = {
            "doctor": doc_profile,
            "logged_in_at": datetime.now().isoformat()
        }

        return session_token, doc_profile

    def get_doctor_from_token(self, token: str) -> Optional[DoctorProfile]:
        """Lấy thông tin Bác sĩ từ Session Token."""
        if not token:
            return None
        session = self._active_sessions.get(token.strip())
        if session:
            return session["doctor"]
        return None

    def logout_doctor(self, token: str) -> bool:
        """Đăng xuất và hủy Session Token."""
        if token in self._active_sessions:
            del self._active_sessions[token]
            return True
        return False

    def list_public_doctors(self) -> List[Dict[str, Any]]:
        """Lấy danh sách thông tin công khai của 4 bác sĩ (để hiển thị gợi ý đăng nhập)."""
        return [
            {
                "doctor_id": doc["doctor_id"],
                "username": doc["username"],
                "full_name": doc["full_name"],
                "title": doc["title"],
                "specialty": doc["specialty"],
                "room": doc["room"],
                "avatar_url": doc["avatar_url"],
                "default_password": DEFAULT_PASSWORD_PLAIN
            }
            for doc in PREDEFINED_DOCTORS
        ]


# Singleton auth service
doctor_auth_service = DoctorAuthService()
