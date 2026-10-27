"""
src/booking - Core Booking, Timetable & Doctor Portal Package
=============================================================
"""

from .database import mongo_manager
from .doctor_auth import doctor_auth_service, DoctorProfile, hash_password_sha256, PREDEFINED_DOCTORS
from .booking_service import (
    booking_service,
    BookingTicket,
    TimeSlotInfo,
    SlotStatus,
    BookingStatus,
    ExaminationStatus,
    STANDARD_TIME_SLOTS
)

__all__ = [
    "mongo_manager",
    "doctor_auth_service",
    "DoctorProfile",
    "hash_password_sha256",
    "PREDEFINED_DOCTORS",
    "booking_service",
    "BookingTicket",
    "TimeSlotInfo",
    "SlotStatus",
    "BookingStatus",
    "ExaminationStatus",
    "STANDARD_TIME_SLOTS"
]
