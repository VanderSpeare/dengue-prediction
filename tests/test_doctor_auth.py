"""
test_doctor_auth.py - Unit test cho tính năng Đăng nhập Bác sĩ & Trang Bác sĩ độc quyền
========================================================================================
Kiểm tra:
1. Mã hóa SHA-256 cho 4 tài khoản Bác sĩ.
2. Đăng nhập thành công với mật khẩu đúng (SHA-256 match) & Cấp Token.
3. Từ chối đăng nhập với mật khẩu sai.
4. Truy cập các chức năng độc quyền của Bác sĩ (cập nhật trạng thái khám, ghi bệnh án, khóa ca).
5. Chặn truy cập trái phép khi không có token (401 Unauthorized).
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "src" / "booking"))

from fastapi.testclient import TestClient
from app import app
from doctor_auth import hash_password_sha256, PREDEFINED_DOCTORS, doctor_auth_service


class TestDoctorAuthAndPortal(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_sha256_hash_verification(self):
        """1. Kiểm tra mã hóa mật khẩu SHA-256."""
        plain = "Bacsi@123"
        hashed = hash_password_sha256(plain)
        self.assertEqual(len(hashed), 64) # Độ dài chuẩn chuỗi Hex SHA-256 là 64 ký tự
        self.assertEqual(hashed, hash_password_sha256("Bacsi@123"))
        self.assertNotEqual(hashed, hash_password_sha256("WrongPassword"))

    def test_02_login_success_for_all_4_doctors(self):
        """2. Kiểm tra đăng nhập thành công cho cả 4 tài khoản bác sĩ."""
        for doc in PREDEFINED_DOCTORS:
            res = self.client.post("/api/doctor/login", json={
                "username": doc["username"],
                "password": "Bacsi@123"
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertIn("token", data)
            self.assertEqual(data["doctor"]["username"], doc["username"])

    def test_03_login_failure_wrong_password(self):
        """3. Kiểm tra từ chối đăng nhập khi sai mật khẩu."""
        res = self.client.post("/api/doctor/login", json={
            "username": "bs_nguyenvana",
            "password": "WrongPassword123"
        })
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertFalse(data["success"])

    def test_04_protected_route_requires_token(self):
        """4. Kiểm tra route độc quyền chặn truy cập nếu không có token."""
        res = self.client.get("/api/doctor/appointments?date=2026-10-20")
        self.assertEqual(res.status_code, 401)

    def test_05_doctor_portal_workflow(self):
        """5. Toàn bộ luồng Bác sĩ: Đăng nhập -> Xem danh sách -> Cập nhật tiến độ -> Ghi bệnh án -> Khóa ca."""
        # 1. Đăng nhập
        login_res = self.client.post("/api/doctor/login", json={
            "username": "bs_nguyenvana",
            "password": "Bacsi@123"
        })
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Tạo 1 ca khám thử nghiệm
        test_date = "2026-11-25"
        from database import mongo_manager
        from booking_service import STANDARD_TIME_SLOTS
        if mongo_manager.is_connected and mongo_manager.db is not None:
            mongo_manager.db.schedules.delete_many({"date_str": test_date})
            mongo_manager.db.bookings.delete_many({"appointment_date": test_date})
            mongo_manager.db.counters.delete_one({"_id": f"queue_{test_date}"})
            mongo_manager.init_day_slots_if_needed(test_date, STANDARD_TIME_SLOTS)

        book_res = self.client.post("/api/book", json={
            "patient_name": "Lê Văn Test",
            "patient_phone": "0912345678",
            "appointment_date": test_date,
            "start_time": "08:30",
            "symptoms": "Sốt xuất huyết ngày 2"
        })
        self.assertEqual(book_res.status_code, 200)
        booking_code = book_res.json()["ticket"]["booking_code"]

        # 3. Bác sĩ xem danh sách
        appts_res = self.client.get(f"/api/doctor/appointments?date={test_date}", headers=headers)
        self.assertEqual(appts_res.status_code, 200)

        # 4. Bác sĩ chuyển trạng thái sang Đang khám (IN_PROGRESS)
        status_res = self.client.post("/api/doctor/appointment/status", headers=headers, json={
            "booking_code": booking_code,
            "examination_status": "IN_PROGRESS"
        })
        self.assertEqual(status_res.status_code, 200)

        # 5. Bác sĩ ghi bệnh án & đơn thuốc
        clinical_res = self.client.post("/api/doctor/appointment/clinical-note", headers=headers, json={
            "booking_code": booking_code,
            "diagnosis": "Sốt xuất huyết Dengue thể nhẹ",
            "tests_recommended": "Công thức máu, NS1Ag",
            "prescription": "Paracetamol 500mg, bù nước Oresol"
        })
        self.assertEqual(clinical_res.status_code, 200)

        # 6. Bác sĩ khóa ca 16:00 do bận trực
        block_res = self.client.post("/api/doctor/slot/toggle-block", headers=headers, json={
            "date_str": test_date,
            "start_time": "16:00",
            "block": True,
            "reason": "Bận hội chẩn"
        })
        self.assertEqual(block_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
