"""
src/booking/booking_service.py - Core Booking & Timetable Business Logic
========================================================================
"""

from datetime import datetime, date, time, timedelta
from enum import Enum
import threading
import uuid
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

try:
    from .database import mongo_manager
except ImportError:
    from database import mongo_manager

logger = logging.getLogger("booking.service")


class SlotStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    CANCELLED_LOCKED = "CANCELLED_LOCKED"
    BLOCKED_BY_DOCTOR = "BLOCKED_BY_DOCTOR"
    CANCELLED_REOPENED = "AVAILABLE"


class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class ExaminationStatus(str, Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


CLINIC_LOCATION = "Phòng Khám Đa Khoa Quốc Tế - Phòng 302, Tầng 3, Số 123 Đường Nguyễn Trãi, Quận 1, TP. Hồ Chí Minh"
DOCTOR_NAME = "BS. CKI Nguyễn Văn A"
DOCTOR_SPECIALTY = "Bệnh Truyền Nhiễm & Sốt Xuất Huyết"

STANDARD_TIME_SLOTS = [
    ("08:00", "08:30"),
    ("08:30", "09:00"),
    ("09:00", "09:30"),
    ("09:30", "10:00"),
    ("10:00", "10:30"),
    ("10:30", "11:00"),
    ("11:00", "11:30"),
    ("13:30", "14:00"),
    ("14:00", "14:30"),
    ("14:30", "15:00"),
    ("15:00", "15:30"),
    ("15:30", "16:00"),
    ("16:00", "16:30"),
    ("16:30", "17:00"),
]


class TimeSlotInfo(BaseModel):
    slot_id: str
    date_str: str
    start_time: str
    end_time: str
    status: SlotStatus
    booking_code: Optional[str] = None
    patient_name: Optional[str] = None
    queue_number: Optional[int] = None
    status_note: Optional[str] = None


class ClinicalRecord(BaseModel):
    diagnosis: str
    tests_recommended: Optional[str] = ""
    prescription: Optional[str] = ""
    doctor_name: str
    recorded_at: str


class BookingTicket(BaseModel):
    booking_code: str
    queue_number: int
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = ""
    appointment_date: str
    appointment_time: str
    clinic_location: str
    doctor_name: str
    doctor_specialty: str
    symptoms: Optional[str] = ""
    status: BookingStatus = BookingStatus.CONFIRMED
    examination_status: ExaminationStatus = ExaminationStatus.WAITING
    clinical_record: Optional[Dict[str, Any]] = None
    created_at: str
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None
    slot_lock_note: Optional[str] = None
    last_updated_by: Optional[str] = None
    last_updated_at: Optional[str] = None


class AppointmentBookingService:
    """Service quản lý Đặt lịch & Thời gian biểu có kết nối MongoDB và Fallback In-Memory."""

    def __init__(self, location: str = CLINIC_LOCATION, doctor_name: str = DOCTOR_NAME):
        self.location = location
        self.doctor_name = doctor_name
        self.doctor_specialty = DOCTOR_SPECIALTY
        self._lock = threading.RLock()
        
        self._schedules: Dict[str, Dict[str, TimeSlotInfo]] = {}
        self._bookings: Dict[str, BookingTicket] = {}
        self._daily_queue_counter: Dict[str, int] = {}

        if mongo_manager.is_connected:
            today_str = datetime.now().strftime("%Y-%m-%d")
            mongo_manager.init_day_slots_if_needed(today_str, STANDARD_TIME_SLOTS)

    def _get_or_init_day_slots(self, date_str: str) -> Dict[str, TimeSlotInfo]:
        with self._lock:
            if date_str not in self._schedules:
                slots = {}
                for start_t, end_t in STANDARD_TIME_SLOTS:
                    slot_id = f"{date_str}_{start_t}"
                    slots[start_t] = TimeSlotInfo(
                        slot_id=slot_id,
                        date_str=date_str,
                        start_time=start_t,
                        end_time=end_t,
                        status=SlotStatus.AVAILABLE,
                        status_note="Khung giờ còn trống"
                    )
                self._schedules[date_str] = slots
                if date_str not in self._daily_queue_counter:
                    self._daily_queue_counter[date_str] = 0
            return self._schedules[date_str]

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        clean_phone = re.sub(r"[\s\-\.]", "", phone)
        return bool(re.match(r"^(0|\+84)[3|5|7|8|9][0-9]{8}$", clean_phone))

    @staticmethod
    def _parse_datetime(date_str: str, time_str: str) -> datetime:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    def get_schedule(self, date_str: str) -> List[TimeSlotInfo]:
        if mongo_manager.is_connected:
            mongo_slots = mongo_manager.get_schedule(date_str, STANDARD_TIME_SLOTS)
            if mongo_slots:
                result = []
                for s in mongo_slots:
                    result.append(TimeSlotInfo(
                        slot_id=s.get("slot_id", f"{date_str}_{s['start_time']}"),
                        date_str=date_str,
                        start_time=s["start_time"],
                        end_time=s["end_time"],
                        status=SlotStatus(s.get("status", "AVAILABLE")),
                        booking_code=s.get("booking_code"),
                        patient_name=s.get("patient_name"),
                        queue_number=s.get("queue_number"),
                        status_note=s.get("status_note")
                    ))
                return result

        with self._lock:
            slots_dict = self._get_or_init_day_slots(date_str)
            return list(slots_dict.values())

    def book_appointment(
        self,
        patient_name: str,
        patient_phone: str,
        appointment_date: str,
        start_time: str,
        patient_email: str = "",
        symptoms: str = "",
        current_time: Optional[datetime] = None,
        assigned_doctor: Optional[str] = None
    ) -> Tuple[bool, Optional[BookingTicket], str]:
        now = current_time or datetime.now()

        clean_name = patient_name.strip()
        if not clean_name:
            return False, None, "Vui lòng nhập họ và tên người khám."

        clean_phone = patient_phone.strip()
        if not self._validate_phone(clean_phone):
            return False, None, "Số điện thoại không hợp lệ (yêu cầu 10 chữ số, định dạng VN vd: 0912345678)."

        try:
            target_dt = self._parse_datetime(appointment_date, start_time)
        except ValueError:
            return False, None, "Định dạng ngày hoặc giờ khám không hợp lệ."

        if target_dt < now:
            return False, None, f"Không thể đặt lịch trong quá khứ. Thời điểm khám ({appointment_date} {start_time}) đã qua."

        valid_starts = [s[0] for s in STANDARD_TIME_SLOTS]
        if start_time not in valid_starts:
            return False, None, f"Khung giờ '{start_time}' không nằm trong ca làm việc của phòng khám."

        slot_id = f"{appointment_date}_{start_time}"

        date_part = appointment_date.replace("-", "")
        while True:
            random_suffix = uuid.uuid4().hex[:4].upper()
            booking_code = f"DK-{date_part}-{random_suffix}"
            if not mongo_manager.is_connected or mongo_manager.get_booking(booking_code) is None:
                if booking_code not in self._bookings:
                    break

        end_time = next(s[1] for s in STANDARD_TIME_SLOTS if s[0] == start_time)
        time_range_str = f"{start_time} - {end_time}"

        if mongo_manager.is_connected:
            queue_number = mongo_manager.get_next_queue_number(appointment_date)
        else:
            with self._lock:
                self._get_or_init_day_slots(appointment_date)
                self._daily_queue_counter[appointment_date] += 1
                queue_number = self._daily_queue_counter[appointment_date]

        ticket = BookingTicket(
            booking_code=booking_code,
            queue_number=queue_number,
            patient_name=clean_name,
            patient_phone=clean_phone,
            patient_email=patient_email.strip() if patient_email else "",
            appointment_date=appointment_date,
            appointment_time=time_range_str,
            clinic_location=self.location,
            doctor_name=assigned_doctor or self.doctor_name,
            doctor_specialty=self.doctor_specialty,
            symptoms=symptoms.strip() if symptoms else "",
            status=BookingStatus.CONFIRMED,
            examination_status=ExaminationStatus.WAITING,
            created_at=now.isoformat()
        )

        if mongo_manager.is_connected:
            mongo_manager.init_day_slots_if_needed(appointment_date, STANDARD_TIME_SLOTS)
            ticket_dict = ticket.dict() if hasattr(ticket, 'dict') else ticket.model_dump()
            ok, mongo_msg = mongo_manager.atomic_book_slot(slot_id, ticket_dict)
            if not ok:
                return False, None, mongo_msg

            self._bookings[booking_code] = ticket
            return True, ticket, "Đặt lịch khám thành công và đã lưu lên MongoDB!"

        with self._lock:
            day_slots = self._get_or_init_day_slots(appointment_date)
            slot = day_slots.get(start_time)

            if not slot:
                return False, None, "Khung giờ không tồn tại."

            if slot.status == SlotStatus.BOOKED:
                return False, None, f"Khung giờ {start_time} ngày {appointment_date} đã có người đặt trước. Vui lòng chọn khung giờ khác."

            if slot.status == SlotStatus.CANCELLED_LOCKED:
                return False, None, f"Khung giờ {start_time} ngày {appointment_date} tạm thời bị khóa (do bệnh nhân trước hủy sát giờ khám < 24h)."

            if slot.status == SlotStatus.BLOCKED_BY_DOCTOR:
                return False, None, f"Khung giờ {start_time} ngày {appointment_date} tạm thời bị Bác sĩ khóa."

            slot.status = SlotStatus.BOOKED
            slot.booking_code = booking_code
            slot.patient_name = clean_name
            slot.queue_number = queue_number
            slot.status_note = f"Đã đặt bởi {clean_name} (Mã: {booking_code}, STT: #{queue_number})"

            self._bookings[booking_code] = ticket

            return True, ticket, "Đặt lịch khám thành công!"

    def cancel_appointment(
        self,
        booking_code: str,
        cancellation_reason: str = "",
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, Optional[BookingTicket], str]:
        now = current_time or datetime.now()
        clean_code = booking_code.strip().upper()

        if mongo_manager.is_connected:
            existing_doc = mongo_manager.get_booking(clean_code)
            if not existing_doc:
                if clean_code in self._bookings:
                    existing_doc = self._bookings[clean_code].dict() if hasattr(self._bookings[clean_code], 'dict') else self._bookings[clean_code].model_dump()
                    mongo_manager.atomic_book_slot(
                        f"{existing_doc['appointment_date']}_{existing_doc['appointment_time'].split('-')[0].strip()}",
                        existing_doc
                    )
                else:
                    return False, None, f"Không tìm thấy thông tin lịch khám với mã '{clean_code}'."

            if existing_doc.get("status") == "CANCELLED":
                return False, BookingTicket(**existing_doc), "Lịch khám này đã được hủy trước đó."

            start_t = existing_doc["appointment_time"].split("-")[0].strip()
            appointment_dt = self._parse_datetime(existing_doc["appointment_date"], start_t)
            time_diff = appointment_dt - now
            hours_diff = time_diff.total_seconds() / 3600.0

            ok, updated_dict, msg = mongo_manager.cancel_booking(
                booking_code=clean_code,
                hours_diff=hours_diff,
                reason=cancellation_reason.strip() if cancellation_reason else "Bệnh nhân yêu cầu hủy",
                now_iso=now.isoformat()
            )
            if ok and updated_dict:
                ticket_obj = BookingTicket(**updated_dict)
                self._bookings[clean_code] = ticket_obj
                return True, ticket_obj, msg
            return False, None, msg

        with self._lock:
            ticket = self._bookings.get(clean_code)
            if not ticket:
                return False, None, f"Không tìm thấy thông tin lịch khám với mã '{clean_code}'."

            if ticket.status == BookingStatus.CANCELLED:
                return False, ticket, "Lịch khám này đã được hủy trước đó."

            start_t = ticket.appointment_time.split("-")[0].strip()
            appointment_dt = self._parse_datetime(ticket.appointment_date, start_t)

            time_diff = appointment_dt - now
            hours_diff = time_diff.total_seconds() / 3600.0

            ticket.status = BookingStatus.CANCELLED
            ticket.cancelled_at = now.isoformat()
            ticket.cancellation_reason = cancellation_reason.strip() if cancellation_reason else "Bệnh nhân yêu cầu hủy"

            day_slots = self._get_or_init_day_slots(ticket.appointment_date)
            slot = day_slots.get(start_t)

            if hours_diff < 24.0:
                if slot:
                    slot.status = SlotStatus.CANCELLED_LOCKED
                    slot.booking_code = None
                    slot.patient_name = None
                    slot.status_note = "Đã hủy sát giờ (< 24h) - Khóa slot để trống theo quy định"
                
                ticket.slot_lock_note = "Lịch hủy cách giờ khám dưới 1 ngày (< 24h): Khung giờ này được giữ TRỐNG, không nhận bệnh nhân mới."
                msg = f"Đã hủy lịch thành công. Do thời gian hủy cách giờ khám dưới 24h ({hours_diff:.1f}h), khung giờ này sẽ được ĐỂ TRỐNG."
            else:
                if slot:
                    slot.status = SlotStatus.AVAILABLE
                    slot.booking_code = None
                    slot.patient_name = None
                    slot.status_note = "Khung giờ vừa được mở lại (Bệnh nhân trước hủy trước > 24h)"
                
                ticket.slot_lock_note = "Lịch hủy trước hơn 1 ngày (>= 24h): Khung giờ đã được MỞ LẠI để đón nhận bệnh nhân mới."
                msg = f"Đã hủy lịch thành công. Do hủy trước giờ khám trên 24h ({hours_diff:.1f}h), khung giờ đã được MỞ LẠI để đón nhận người đặt mới."

            return True, ticket, msg

    def get_booking(self, booking_code: str) -> Optional[BookingTicket]:
        clean_code = booking_code.strip().upper()
        if mongo_manager.is_connected:
            doc = mongo_manager.get_booking(clean_code)
            if doc:
                return BookingTicket(**doc)

        with self._lock:
            return self._bookings.get(clean_code)

    def list_all_bookings(self, date_filter: Optional[str] = None) -> List[BookingTicket]:
        if mongo_manager.is_connected:
            docs = mongo_manager.list_all_bookings(date_filter=date_filter)
            if docs:
                return [BookingTicket(**d) for d in docs]

        with self._lock:
            all_list = list(self._bookings.values())
            if date_filter:
                all_list = [b for b in all_list if b.appointment_date == date_filter]
            return sorted(
                all_list,
                key=lambda x: (x.appointment_date, x.appointment_time, x.queue_number)
            )

    def sync_to_mongodb(self) -> Tuple[int, int]:
        if not mongo_manager.is_connected:
            return 0, 0

        synced_bookings = 0
        today_str = datetime.now().strftime("%Y-%m-%d")
        mongo_manager.init_day_slots_if_needed(today_str, STANDARD_TIME_SLOTS)

        with self._lock:
            for b_code, ticket in self._bookings.items():
                slot_id = f"{ticket.appointment_date}_{ticket.appointment_time.split('-')[0].strip()}"
                mongo_manager.init_day_slots_if_needed(ticket.appointment_date, STANDARD_TIME_SLOTS)
                t_dict = ticket.dict() if hasattr(ticket, 'dict') else ticket.model_dump()
                if ticket.status == BookingStatus.CONFIRMED:
                    mongo_manager.atomic_book_slot(slot_id, t_dict)
                    synced_bookings += 1
                elif ticket.status == BookingStatus.CANCELLED:
                    mongo_manager.cancel_booking(
                        ticket.booking_code,
                        0,
                        ticket.cancellation_reason or "Đồng bộ hủy",
                        ticket.cancelled_at or datetime.now().isoformat()
                    )
                    synced_bookings += 1

        total_slots = mongo_manager.db.schedules.count_documents({}) if mongo_manager.db is not None else 0
        return synced_bookings, total_slots


booking_service = AppointmentBookingService()
