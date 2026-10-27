"""
test_booking.py - Kiểm thử toàn bộ nghiệp vụ đặt lịch khám bệnh
===============================================================
Bao gồm:
1. Đặt lịch thành công: sinh mã duy nhất, STT, trả về thời gian, địa điểm.
2. Chống trùng lịch: 2 người đặt cùng lúc 1 slot -> Chỉ 1 người thành công, người kia bị báo lỗi.
3. Hủy lịch < 1 ngày (< 24h): Khung giờ bị khóa để trống, người mới KHÔNG THỂ đặt vào.
4. Hủy lịch từ 1 - 2 ngày (>= 24h): Khung giờ được mở lại, người mới ĐẶT THÀNH CÔNG.
5. Kiểm tra lỗi cơ bản: Đặt ngày quá khứ, SĐT sai định dạng, họ tên trống.
"""

import unittest
from datetime import datetime, timedelta
import threading
from database import mongo_manager
from booking_service import AppointmentBookingService, SlotStatus, BookingStatus, STANDARD_TIME_SLOTS


def clean_db_for_date(date_str: str):
    """Xóa dữ liệu test trên MongoDB cho một ngày cụ thể."""
    if mongo_manager.is_connected and mongo_manager.db is not None:
        mongo_manager.db.schedules.delete_many({"date_str": date_str})
        mongo_manager.db.bookings.delete_many({"appointment_date": date_str})
        mongo_manager.db.counters.delete_one({"_id": f"queue_{date_str}"})
        mongo_manager.init_day_slots_if_needed(date_str, STANDARD_TIME_SLOTS)


class TestAppointmentBooking(unittest.TestCase):

    def setUp(self):
        self.service = AppointmentBookingService(
            location="Phòng Khám Đa Khoa Sài Gòn - P.204 Tầng 2, 123 Nguyễn Trãi, Q1",
            doctor_name="BS. CKI Nguyễn Văn A"
        )

    def test_01_successful_booking_returns_all_info(self):
        """1. Đặt lịch khám thành công -> Trả về Mã, STT, Thời gian, Địa điểm."""
        test_date = "2026-11-10"
        clean_db_for_date(test_date)
        current_time = datetime(2026, 10, 1, 8, 0, 0)
        
        success, ticket, msg = self.service.book_appointment(
            patient_name="Trần Thị Mai",
            patient_phone="0912345678",
            appointment_date=test_date,
            start_time="09:00",
            patient_email="mai.tran@example.com",
            symptoms="Sốt cao liên tục 2 ngày, đau mỏi cơ",
            current_time=current_time
        )

        self.assertTrue(success)
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.queue_number, 1)
        self.assertEqual(ticket.appointment_time, "09:00 - 09:30")
        self.assertEqual(ticket.appointment_date, test_date)
        self.assertIn("123 Nguyễn Trãi", ticket.clinic_location)
        self.assertEqual(ticket.patient_name, "Trần Thị Mai")

        # Kiểm tra trạng thái slot trong timetable
        schedule = self.service.get_schedule(test_date)
        slot_0900 = next(s for s in schedule if s.start_time == "09:00")
        self.assertEqual(slot_0900.status, SlotStatus.BOOKED)
        self.assertEqual(slot_0900.booking_code, ticket.booking_code)
        clean_db_for_date(test_date)

    def test_02_prevent_double_booking_same_slot(self):
        """2. Hai người đặt cùng 1 khung giờ -> Người thứ hai bị từ chối."""
        test_date = "2026-11-11"
        clean_db_for_date(test_date)
        current_time = datetime(2026, 10, 1, 8, 0, 0)

        # Người thứ 1 đặt slot 09:00
        ok1, ticket1, _ = self.service.book_appointment(
            patient_name="Nguyễn Văn B",
            patient_phone="0987654321",
            appointment_date=test_date,
            start_time="09:00",
            current_time=current_time
        )
        self.assertTrue(ok1)

        # Người thứ 2 cố tình đặt cùng slot 09:00
        ok2, ticket2, msg2 = self.service.book_appointment(
            patient_name="Lê Văn C",
            patient_phone="0901234567",
            appointment_date=test_date,
            start_time="09:00",
            current_time=current_time
        )
        self.assertFalse(ok2)
        self.assertIsNone(ticket2)
        self.assertIn("người đặt trước", msg2)
        clean_db_for_date(test_date)

    def test_03_concurrent_multithread_booking(self):
        """3. Kiểm tra tính an toàn đồng thời (Concurrency Lock) khi 10 luồng cùng tranh chấp 1 slot."""
        test_date = "2026-11-12"
        clean_db_for_date(test_date)
        current_time = datetime(2026, 10, 1, 8, 0, 0)
        success_count = 0
        failure_count = 0
        lock = threading.Lock()

        def try_book(user_idx):
            nonlocal success_count, failure_count
            ok, ticket, _ = self.service.book_appointment(
                patient_name=f"User {user_idx}",
                patient_phone=f"091100000{user_idx}",
                appointment_date=test_date,
                start_time="10:00",
                current_time=current_time
            )
            with lock:
                if ok:
                    success_count += 1
                else:
                    failure_count += 1

        threads = [threading.Thread(target=try_book, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Đúng 1 luồng thành công, 9 luồng còn lại thất bại
        self.assertEqual(success_count, 1)
        self.assertEqual(failure_count, 9)
        clean_db_for_date(test_date)

    def test_04_cancellation_under_1_day_leaves_slot_locked_empty(self):
        """4. Hủy lịch < 1 ngày (< 24h) -> Để điểm đó TRỐNG, người mới không thể đặt vào."""
        target_date = "2026-11-13"
        clean_db_for_date(target_date)
        booking_time = datetime(2026, 10, 1, 8, 0, 0)
        cancel_time = datetime(2026, 11, 12, 20, 0, 0) # 09:00 ngày 13 cách 13h (< 24h)
        
        ok, ticket, _ = self.service.book_appointment(
            patient_name="Phạm Văn D",
            patient_phone="0933111222",
            appointment_date=target_date,
            start_time="09:00",
            current_time=booking_time
        )
        self.assertTrue(ok)

        # Thực hiện hủy lịch
        cancel_ok, cancel_ticket, msg = self.service.cancel_appointment(
            booking_code=ticket.booking_code,
            cancellation_reason="Bận việc đột xuất",
            current_time=cancel_time
        )
        self.assertTrue(cancel_ok)
        self.assertEqual(cancel_ticket.status, BookingStatus.CANCELLED)
        self.assertIn("ĐỂ TRỐNG", msg)

        # Kiểm tra slot bị đánh dấu CANCELLED_LOCKED
        schedule = self.service.get_schedule(target_date)
        slot_0900 = next(s for s in schedule if s.start_time == "09:00")
        self.assertEqual(slot_0900.status, SlotStatus.CANCELLED_LOCKED)

        # Người mới cố đặt vào slot này -> Bị từ chối
        new_ok, new_ticket, new_msg = self.service.book_appointment(
            patient_name="Người Mới",
            patient_phone="0977888999",
            appointment_date=target_date,
            start_time="09:00",
            current_time=cancel_time
        )
        self.assertFalse(new_ok)
        self.assertIsNone(new_ticket)
        self.assertIn("tạm thời bị khóa", new_msg)
        clean_db_for_date(target_date)

    def test_05_cancellation_1_to_2_days_reopens_slot_for_new_patients(self):
        """5. Hủy lịch từ 1 - 2 ngày (>= 24h) -> Mở lại slot, xếp người đặt mới vào thành công."""
        target_date = "2026-11-14"
        clean_db_for_date(target_date)
        booking_time = datetime(2026, 10, 1, 8, 0, 0)
        cancel_time = datetime(2026, 11, 11, 10, 0, 0) # Cách > 24h

        ok, ticket, _ = self.service.book_appointment(
            patient_name="Võ Thị E",
            patient_phone="0944555666",
            appointment_date=target_date,
            start_time="14:00",
            current_time=booking_time
        )
        self.assertTrue(ok)

        # Bệnh nhân hủy lịch trước 3 ngày
        cancel_ok, cancel_ticket, msg = self.service.cancel_appointment(
            booking_code=ticket.booking_code,
            cancellation_reason="Đổi lịch công tác",
            current_time=cancel_time
        )
        self.assertTrue(cancel_ok)
        self.assertIn("MỞ LẠI", msg)

        # Kiểm tra slot được chuyển sang AVAILABLE
        schedule = self.service.get_schedule(target_date)
        slot_1400 = next(s for s in schedule if s.start_time == "14:00")
        self.assertEqual(slot_1400.status, SlotStatus.AVAILABLE)

        # Người mới đặt vào khung giờ vừa mở -> Thành công!
        new_booking_time = datetime(2026, 11, 11, 11, 0, 0)
        new_ok, new_ticket, new_msg = self.service.book_appointment(
            patient_name="Đặng Văn F (Người mới)",
            patient_phone="0966777888",
            appointment_date=target_date,
            start_time="14:00",
            current_time=new_booking_time
        )
        self.assertTrue(new_ok)
        self.assertIsNotNone(new_ticket)
        self.assertEqual(new_ticket.patient_name, "Đặng Văn F (Người mới)")
        self.assertEqual(new_ticket.queue_number, 2)
        clean_db_for_date(target_date)

    def test_06_validation_rules_and_error_handling(self):
        """6. Kiểm tra các lỗi cơ bản: Tên rỗng, SĐT sai, Ngày quá khứ."""
        test_date = "2026-11-15"
        clean_db_for_date(test_date)
        current_time = datetime(2026, 10, 1, 8, 0, 0)

        # Tên rỗng
        ok, _, msg = self.service.book_appointment(
            patient_name="",
            patient_phone="0912345678",
            appointment_date=test_date,
            start_time="08:00",
            current_time=current_time
        )
        self.assertFalse(ok)
        self.assertIn("họ và tên", msg)

        # SĐT sai định dạng
        ok, _, msg = self.service.book_appointment(
            patient_name="Test User",
            patient_phone="12345",
            appointment_date=test_date,
            start_time="08:00",
            current_time=current_time
        )
        self.assertFalse(ok)
        self.assertIn("Số điện thoại không hợp lệ", msg)

        # Đặt ngày quá khứ
        ok, _, msg = self.service.book_appointment(
            patient_name="Test User",
            patient_phone="0912345678",
            appointment_date="2026-09-20",
            start_time="08:00",
            current_time=current_time
        )
        self.assertFalse(ok)
        self.assertIn("quá khứ", msg)
        clean_db_for_date(test_date)


if __name__ == "__main__":
    unittest.main()
