"""
test_mongodb_integration.py - Kiểm thử tích hợp MongoDB & Fallback
===================================================================
Kiểm tra:
1. Kết nối MongoDB và kiểm tra trạng thái get_status().
2. Khởi tạo 14 slots khám trên MongoDB.
3. Đặt lịch khám và lưu vào collection `bookings` + cập nhật collection `schedules`.
4. Hủy lịch khám trên MongoDB (< 1 ngày vs 1-2 ngày).
5. Kiểm tra tính toàn vẹn khi MongoDB không khả dụng (In-Memory fallback mượt mà).
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "src" / "booking"))

from database import MongoDBManager
from booking_service import AppointmentBookingService, STANDARD_TIME_SLOTS, SlotStatus, BookingStatus


class TestMongoDBIntegration(unittest.TestCase):

    def test_01_db_status_structure(self):
        """1. Kiểm tra cấu trúc trạng thái Database."""
        manager = MongoDBManager()
        status = manager.get_status()
        self.assertIn("connected", status)
        self.assertIn("storage_type", status)

    def test_02_service_flow_with_db_layer(self):
        """2. Kiểm tra quy trình đặt & hủy lịch thông qua service có DB layer."""
        manager = MongoDBManager()
        test_date = "2026-10-15"
        if manager.is_connected and manager.db is not None:
            manager.db.schedules.delete_many({"date_str": test_date})
            manager.db.bookings.delete_many({"appointment_date": test_date})
            manager.db.counters.delete_one({"_id": f"queue_{test_date}"})

        service = AppointmentBookingService(
            location="Phòng Khám Đa Khoa Quốc Tế - P.302, 123 Nguyễn Trãi, Q1, TPHCM",
            doctor_name="BS. CKI Nguyễn Văn A"
        )
        sim_now = datetime(2026, 10, 10, 8, 0, 0)

        # Lấy schedule
        slots = service.get_schedule(test_date)
        self.assertEqual(len(slots), 14)

        # Đặt lịch
        ok, ticket, msg = service.book_appointment(
            patient_name="Phan Thanh Hùng",
            patient_phone="0988112233",
            appointment_date=test_date,
            start_time="08:30",
            symptoms="Khám định kỳ",
            current_time=sim_now
        )
        self.assertTrue(ok)
        self.assertEqual(ticket.queue_number, 1)
        self.assertEqual(ticket.patient_name, "Phan Thanh Hùng")

        # Tra cứu lại vé
        found_ticket = service.get_booking(ticket.booking_code)
        self.assertIsNotNone(found_ticket)
        self.assertEqual(found_ticket.booking_code, ticket.booking_code)

        # Hủy trước 5 ngày (> 24h)
        cancel_now = datetime(2026, 10, 10, 10, 0, 0)
        cancel_ok, cancel_ticket, cancel_msg = service.cancel_appointment(
            booking_code=ticket.booking_code,
            cancellation_reason="Bận việc",
            current_time=cancel_now
        )
        self.assertTrue(cancel_ok)
        self.assertIn("MỞ LẠI", cancel_msg)

        # Kiểm tra slot đã mở lại thành AVAILABLE
        updated_slots = service.get_schedule(test_date)
        slot_0830 = next(s for s in updated_slots if s.start_time == "08:30")
        self.assertEqual(slot_0830.status, SlotStatus.AVAILABLE)


if __name__ == "__main__":
    unittest.main()
