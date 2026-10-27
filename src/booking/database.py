"""
src/booking/database.py - MongoDB Connection & Persistence Layer
================================================================
Quản lý kết nối MongoDB và lưu trữ dữ liệu cho hệ thống Đặt Lịch Khám & Cổng Bác Sĩ:
- Collections:
  1. `bookings`: Lưu thông tin vé khám, trạng thái khám và bệnh án lâm sàng.
  2. `schedules`: Lưu thời gian biểu 14 slot khám trong ngày.
  3. `counters`: Sinh số thứ tự (STT) tự tăng theo ngày một cách nguyên tử.
  4. `doctors`: Lưu 4 tài khoản Bác sĩ với mật khẩu mã hóa SHA-256.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient, ReturnDocument, UpdateOne

logger = logging.getLogger("booking.mongodb")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

load_dotenv(_ROOT / ".env", override=True)
load_dotenv(_HERE / ".env", override=True)


class MongoDBManager:
    """Quản lý kết nối và thao tác MongoDB cho hệ thống Đặt Lịch Khám."""

    def __init__(self):
        self.uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME", "dengue_clinic_db")
        self.client = None
        self.db = None
        self._is_connected = False
        self._connection_error = None
        self._initialized_dates: set = set()
        self._cached_status: Optional[Dict[str, Any]] = None
        self._status_cache_time: Optional[float] = None

        if self.uri and self.uri != "your_mongodb_uri_here":
            self.connect()
        else:
            logger.info("Chưa tìm thấy MONGODB_URI hợp lệ trong .env -> Hệ thống kích hoạt In-Memory Persistence.")

    def connect(self) -> bool:
        """Thực hiện kết nối tới MongoDB với hỗ trợ certifi TLS."""
        try:
            load_dotenv(_ROOT / ".env", override=True)
            load_dotenv(_HERE / ".env", override=True)
            self.uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
            self.db_name = os.getenv("MONGODB_DB_NAME", "dengue_clinic_db")

            if not self.uri or self.uri == "your_mongodb_uri_here":
                self._is_connected = False
                return False

            # Thử kết nối với TLS CA bundle từ certifi
            client = None
            try:
                import certifi
                client = MongoClient(
                    self.uri,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=4000,
                    connectTimeoutMS=4000
                )
                client.admin.command("ping")
            except Exception as e_certifi:
                # Fallback kết nối tiêu chuẩn
                try:
                    if client:
                        client.close()
                    client = MongoClient(
                        self.uri,
                        serverSelectionTimeoutMS=4000,
                        connectTimeoutMS=4000
                    )
                    client.admin.command("ping")
                except Exception as e_std:
                    # Fallback kết nối bỏ qua xác thực SSL nếu cần
                    try:
                        if client:
                            client.close()
                        client = MongoClient(
                            self.uri,
                            tlsAllowInvalidCertificates=True,
                            serverSelectionTimeoutMS=4000,
                            connectTimeoutMS=4000
                        )
                        client.admin.command("ping")
                    except Exception as e_final:
                        if client:
                            client.close()
                        raise e_final

            self.client = client
            self.db = self.client.get_database(self.db_name)
            self._is_connected = True
            self._connection_error = None
            logger.info(f"Kết nối MongoDB thành công! Database: '{self.db_name}'")

            self._setup_indexes()
            self._seed_doctor_accounts()
            return True

        except Exception as e:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            self.client = None
            self.db = None
            self._is_connected = False
            self._connection_error = str(e)
            logger.warning(f"Không thể kết nối tới MongoDB ({e}). Hệ thống chuyển sang In-Memory Fallback.")
            return False

    def _setup_indexes(self):
        """Khởi tạo Unique Index trên MongoDB."""
        try:
            if not self._is_connected or self.db is None:
                return

            self.db.bookings.create_index("booking_code", unique=True)
            self.db.bookings.create_index([("appointment_date", 1), ("queue_number", 1)])
            self.db.bookings.create_index("patient_phone")
            self.db.schedules.create_index([("date_str", 1), ("start_time", 1)], unique=True)
            self.db.doctors.create_index("username", unique=True)

            logger.info("MongoDB Indexes đã được thiết lập thành công.")
        except Exception as e:
            logger.warning(f"Lỗi khi tạo MongoDB Indexes: {e}")

    def _seed_doctor_accounts(self):
        """Khởi tạo 4 tài khoản Bác sĩ mặc định vào MongoDB collection 'doctors'."""
        try:
            from .doctor_auth import doctor_auth_service
            doctor_auth_service.seed_doctors_to_mongo(self.db)
        except Exception as e:
            logger.warning(f"Lỗi seed tài khoản bác sĩ: {e}")

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def get_status(self) -> Dict[str, Any]:
        """Lấy thông tin trạng thái kết nối MongoDB với TTL Cache 30s."""
        if not self._is_connected:
            return {
                "connected": False,
                "storage_type": "In-Memory Fallback",
                "error": self._connection_error,
                "hint": "Cấu hình MONGODB_URI trong file .env để lưu dữ liệu lâu dài vào MongoDB."
            }

        import time
        now = time.time()
        if self._cached_status and self._status_cache_time and (now - self._status_cache_time < 30.0):
            return self._cached_status

        try:
            total_bookings = self.db.bookings.count_documents({})
            total_schedules = self.db.schedules.count_documents({})
            total_doctors = self.db.doctors.count_documents({})
            status_data = {
                "connected": True,
                "storage_type": "MongoDB Atlas / Server",
                "database": self.db_name,
                "total_bookings_stored": total_bookings,
                "total_schedule_slots": total_schedules,
                "total_doctors": total_doctors
            }
            self._cached_status = status_data
            self._status_cache_time = now
            return status_data
        except Exception as e:
            return {
                "connected": False,
                "storage_type": "MongoDB (Error querying stats)",
                "error": str(e)
            }

    def init_day_slots_if_needed(self, date_str: str, standard_slots: List[Tuple[str, str]]):
        """Khởi tạo 14 khung giờ khám trong ngày trên MongoDB nếu chưa có (Cached check)."""
        if not self._is_connected or self.db is None:
            return

        if date_str in self._initialized_dates:
            return

        try:
            operations = []
            for start_t, end_t in standard_slots:
                slot_id = f"{date_str}_{start_t}"
                operations.append(
                    UpdateOne(
                        {"_id": slot_id},
                        {
                            "$setOnInsert": {
                                "slot_id": slot_id,
                                "date_str": date_str,
                                "start_time": start_t,
                                "end_time": end_t,
                                "status": "AVAILABLE",
                                "booking_code": None,
                                "patient_name": None,
                                "queue_number": None,
                                "status_note": "Khung giờ còn trống",
                                "updated_at": datetime.now().isoformat()
                            }
                        },
                        upsert=True
                    )
                )

            if operations:
                res = self.db.schedules.bulk_write(operations, ordered=False)
                if res.upserted_count > 0:
                    logger.info(f"Đã tạo {res.upserted_count} slots mới cho ngày {date_str} trên MongoDB.")
            self._initialized_dates.add(date_str)
        except Exception as e:
            logger.error(f"Lỗi khởi tạo slots cho ngày {date_str} trên MongoDB: {e}")

    def get_schedule(self, date_str: str, standard_slots: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Lấy danh sách các khung giờ trong ngày từ MongoDB."""
        if not self._is_connected or self.db is None:
            return []

        self.init_day_slots_if_needed(date_str, standard_slots)
        try:
            slots_cursor = self.db.schedules.find({"date_str": date_str}).sort("start_time", 1)
            slots = list(slots_cursor)
            for s in slots:
                s.pop("_id", None)
            return slots
        except Exception as e:
            logger.error(f"Lỗi đọc schedule từ MongoDB: {e}")
            return []

    def get_next_queue_number(self, date_str: str) -> int:
        """Tăng và trả về số thứ tự (STT) trong ngày bằng MongoDB find_one_and_update (Atomic)."""
        if not self._is_connected or self.db is None:
            return 1

        try:
            counter_id = f"queue_{date_str}"
            result = self.db.counters.find_one_and_update(
                {"_id": counter_id},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            return result.get("seq", 1) if result else 1
        except Exception as e:
            logger.error(f"Lỗi tăng STT trên MongoDB: {e}")
            return 1

    def atomic_book_slot(
        self,
        slot_id: str,
        booking_ticket_dict: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Khóa và đặt slot trên MongoDB một cách nguyên tử."""
        if not self._is_connected or self.db is None:
            return True, "Success (In-Memory)"

        try:
            updated_slot = self.db.schedules.find_one_and_update(
                {
                    "_id": slot_id,
                    "status": "AVAILABLE"
                },
                {
                    "$set": {
                        "status": "BOOKED",
                        "booking_code": booking_ticket_dict["booking_code"],
                        "patient_name": booking_ticket_dict["patient_name"],
                        "queue_number": booking_ticket_dict["queue_number"],
                        "status_note": f"Đã đặt bởi {booking_ticket_dict['patient_name']} (Mã: {booking_ticket_dict['booking_code']})",
                        "updated_at": datetime.now().isoformat()
                    }
                },
                return_document=ReturnDocument.AFTER
            )

            if not updated_slot:
                current_slot = self.db.schedules.find_one({"_id": slot_id})
                if current_slot:
                    status = current_slot.get("status")
                    if status == "CANCELLED_LOCKED":
                        return False, "Khung giờ này tạm thời bị khóa để trống (do bệnh nhân trước hủy sát giờ < 24h)."
                    elif status == "BLOCKED_BY_DOCTOR":
                        return False, "Khung giờ này tạm thời bị Bác sĩ khóa (bận ca trực cấp cứu hoặc hội chẩn)."
                return False, "Khung giờ này vừa có người đặt trước. Vui lòng chọn khung giờ khác."

            if "examination_status" not in booking_ticket_dict:
                booking_ticket_dict["examination_status"] = "WAITING"
            if "clinical_record" not in booking_ticket_dict:
                booking_ticket_dict["clinical_record"] = None

            self.db.bookings.replace_one(
                {"booking_code": booking_ticket_dict["booking_code"]},
                booking_ticket_dict,
                upsert=True
            )
            logger.info(f"Đã lưu thành công lịch khám {booking_ticket_dict['booking_code']} lên MongoDB!")
            return True, "Thành công"

        except Exception as e:
            logger.error(f"Lỗi khi lưu đặt lịch lên MongoDB: {e}")
            return False, f"Lỗi lưu trữ dữ liệu MongoDB: {e}"

    def cancel_booking(
        self,
        booking_code: str,
        hours_diff: float,
        reason: str,
        now_iso: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Hủy lịch khám trên MongoDB."""
        if not self._is_connected or self.db is None:
            return False, None, "MongoDB chưa kết nối."

        try:
            ticket = self.db.bookings.find_one({"booking_code": booking_code})
            if not ticket:
                return False, None, f"Không tìm thấy lịch khám với mã {booking_code} trên MongoDB."

            if ticket.get("status") == "CANCELLED":
                return False, ticket, "Lịch khám này đã được hủy trước đó."

            start_t = ticket["appointment_time"].split("-")[0].strip()
            slot_id = f"{ticket['appointment_date']}_{start_t}"

            if hours_diff < 24.0:
                new_slot_status = "CANCELLED_LOCKED"
                slot_note = "Đã hủy sát giờ (< 24h) - Khóa slot để trống theo quy định"
                ticket_lock_note = "Lịch hủy cách giờ khám dưới 1 ngày (< 24h): Khung giờ này được giữ TRỐNG, không nhận bệnh nhân mới."
                msg = f"Đã hủy lịch thành công. Do thời gian hủy cách giờ khám dưới 24h ({hours_diff:.1f}h), khung giờ này sẽ được ĐỂ TRỐNG."
            else:
                new_slot_status = "AVAILABLE"
                slot_note = "Khung giờ vừa được mở lại (Bệnh nhân trước hủy trước > 24h)"
                ticket_lock_note = "Lịch hủy trước hơn 1 ngày (>= 24h): Khung giờ đã được MỞ LẠI để đón nhận bệnh nhân mới."
                msg = f"Đã hủy lịch thành công. Do hủy trước giờ khám trên 24h ({hours_diff:.1f}h), khung giờ đã được MỞ LẠI để đón nhận người đặt mới."

            self.db.bookings.update_one(
                {"booking_code": booking_code},
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": now_iso,
                        "cancellation_reason": reason,
                        "slot_lock_note": ticket_lock_note
                    }
                }
            )

            self.db.schedules.update_one(
                {"_id": slot_id},
                {
                    "$set": {
                        "status": new_slot_status,
                        "booking_code": None,
                        "patient_name": None,
                        "status_note": slot_note,
                        "updated_at": now_iso
                    }
                }
            )

            updated_ticket = self.db.bookings.find_one({"booking_code": booking_code})
            if updated_ticket:
                updated_ticket.pop("_id", None)

            return True, updated_ticket, msg

        except Exception as e:
            logger.error(f"Lỗi hủy lịch trên MongoDB: {e}")
            return False, None, f"Lỗi thao tác trên MongoDB: {e}"

    def update_doctor_examination_status(
        self,
        booking_code: str,
        exam_status: str,
        doctor_name: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Cập nhật trạng thái ca khám của Bác sĩ (WAITING, IN_PROGRESS, COMPLETED, NO_SHOW)."""
        clean_code = booking_code.strip().upper()
        if not self._is_connected or self.db is None:
            return True, {"booking_code": clean_code, "examination_status": exam_status}, "Cập nhật thành công (In-Memory)"

        try:
            now_iso = datetime.now().isoformat()
            res = self.db.bookings.find_one_and_update(
                {"booking_code": clean_code},
                {
                    "$set": {
                        "examination_status": exam_status,
                        "last_updated_by": doctor_name,
                        "last_updated_at": now_iso
                    }
                },
                return_document=ReturnDocument.AFTER
            )
            if not res:
                return False, None, "Không tìm thấy mã lịch hẹn này."
            res.pop("_id", None)
            return True, res, f"Đã cập nhật trạng thái ca khám thành: {exam_status}"
        except Exception as e:
            logger.error(f"Lỗi cập nhật trạng thái ca khám: {e}")
            return False, None, str(e)

    def save_doctor_clinical_record(
        self,
        booking_code: str,
        diagnosis: str,
        tests: str,
        prescription: str,
        doctor_name: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Lưu bệnh án lâm sàng & chẩn đoán của Bác sĩ vào lịch hẹn."""
        clean_code = booking_code.strip().upper()
        if not self._is_connected or self.db is None:
            return True, None, "Lưu bệnh án thành công (In-Memory)"

        try:
            record = {
                "diagnosis": diagnosis.strip(),
                "tests_recommended": tests.strip(),
                "prescription": prescription.strip(),
                "doctor_name": doctor_name,
                "recorded_at": datetime.now().isoformat()
            }
            res = self.db.bookings.find_one_and_update(
                {"booking_code": clean_code},
                {
                    "$set": {
                        "clinical_record": record,
                        "examination_status": "COMPLETED",
                        "last_updated_by": doctor_name,
                        "last_updated_at": datetime.now().isoformat()
                    }
                },
                return_document=ReturnDocument.AFTER
            )
            if not res:
                return False, None, "Không tìm thấy mã lịch hẹn này."
            res.pop("_id", None)
            return True, res, "Đã lưu chẩn đoán & bệnh án lâm sàng thành công!"
        except Exception as e:
            logger.error(f"Lỗi lưu bệnh án bác sĩ: {e}")
            return False, None, str(e)

    def toggle_slot_block_by_doctor(
        self,
        date_str: str,
        start_time: str,
        block: bool,
        reason: str,
        doctor_name: str
    ) -> Tuple[bool, str]:
        """Bác sĩ chủ động Khóa (Block) hoặc Mở lại (Unblock) 1 khung giờ khám."""
        if not self._is_connected or self.db is None:
            return True, "Thao tác thành công (In-Memory)"

        slot_id = f"{date_str}_{start_time}"
        try:
            slot = self.db.schedules.find_one({"_id": slot_id})
            if not slot:
                return False, "Không tìm thấy khung giờ này."

            if block:
                if slot.get("status") == "BOOKED":
                    return False, "Khung giờ này đã có bệnh nhân đặt lịch, không thể khóa."
                self.db.schedules.update_one(
                    {"_id": slot_id},
                    {
                        "$set": {
                            "status": "BLOCKED_BY_DOCTOR",
                            "status_note": f"Bác sĩ khóa: {reason or 'Bận hội chẩn / Trực đột xuất'}",
                            "blocked_by": doctor_name,
                            "updated_at": datetime.now().isoformat()
                        }
                    }
                )
                return True, f"Đã khóa khung giờ {start_time} thành công."
            else:
                self.db.schedules.update_one(
                    {"_id": slot_id},
                    {
                        "$set": {
                            "status": "AVAILABLE",
                            "status_note": "Khung giờ còn trống",
                            "updated_at": datetime.now().isoformat()
                        }
                    }
                )
                return True, f"Đã mở lại khung giờ {start_time} để đón nhận bệnh nhân."
        except Exception as e:
            logger.error(f"Lỗi toggle block slot: {e}")
            return False, str(e)

    def get_booking(self, booking_code: str) -> Optional[Dict[str, Any]]:
        """Tra cứu vé khám từ MongoDB."""
        if not self._is_connected or self.db is None:
            return None
        try:
            doc = self.db.bookings.find_one({"booking_code": booking_code.strip().upper()})
            if doc:
                doc.pop("_id", None)
            return doc
        except Exception as e:
            logger.error(f"Lỗi tra cứu booking từ MongoDB: {e}")
            return None

    def list_all_bookings(self, date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách vé khám từ MongoDB."""
        if not self._is_connected or self.db is None:
            return []
        try:
            query = {}
            if date_filter:
                query["appointment_date"] = date_filter
            cursor = self.db.bookings.find(query).sort([("appointment_date", 1), ("appointment_time", 1), ("queue_number", 1)])
            results = list(cursor)
            for r in results:
                r.pop("_id", None)
            return results
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách bookings từ MongoDB: {e}")
            return []


mongo_manager = MongoDBManager()
