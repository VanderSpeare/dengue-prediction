"""
app.py - FastAPI Web Server & API for Appointment Booking Demo (Doctor Auth & Portal)
=====================================================================================
Cung cấp API RESTful & Giao diện Web:
- Public Routes:
  - GET  /                           -> Giao diện chính (Đặt lịch, Tra cứu, Bảng theo dõi & Portal Bác sĩ)
  - GET  /api/clinic-info            -> Thông tin phòng khám
  - GET  /api/db-status              -> Trạng thái MongoDB
  - POST /api/db-reconnect           -> Kết nối lại MongoDB
  - POST /api/db-sync                -> Đồng bộ dữ liệu lên MongoDB
  - GET  /api/schedule               -> Thời gian biểu theo ngày
  - POST /api/book                   -> Bệnh nhân đặt lịch khám
  - POST /api/cancel                 -> Hủy lịch khám (< 1 ngày vs 1-2 ngày)
  - GET  /api/ticket/{code}          -> Tra cứu phiếu khám
  - GET  /api/doctor/public-list     -> Danh sách 4 tài khoản Bác sĩ (hỗ trợ login test)

- Doctor Protected Routes (Yêu cầu Token xác thực SHA-256):
  - POST /api/doctor/login           -> Đăng nhập Bác sĩ (Xác thực mật khẩu SHA-256)
  - GET  /api/doctor/me              -> Thông tin Bác sĩ đang đăng nhập
  - POST /api/doctor/logout          -> Đăng xuất Bác sĩ
  - GET  /api/doctor/appointments    -> Danh sách bệnh nhân & hồ sơ khám theo ngày
  - POST /api/doctor/appointment/status        -> Cập nhật trạng thái khám (IN_PROGRESS, COMPLETED, NO_SHOW)
  - POST /api/doctor/appointment/clinical-note -> Ghi chú bệnh án lâm sàng, chẩn đoán, đơn thuốc
  - POST /api/doctor/slot/toggle-block         -> Bác sĩ chủ động khóa / mở lại ca khám
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from database import mongo_manager
from doctor_auth import doctor_auth_service, DoctorProfile
from booking_service import (
    booking_service,
    BookingTicket,
    TimeSlotInfo,
    SlotStatus,
    BookingStatus,
    ExaminationStatus
)

app = FastAPI(
    title="Hệ Thống Đặt Lịch Khám & Portal Bác Sĩ - Demo",
    description="Demo đặt lịch khám, thời gian biểu, MongoDB, đăng nhập 4 bác sĩ với mật khẩu SHA-256 và trang Bác sĩ độc quyền.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Schemas ---
class BookingRequest(BaseModel):
    patient_name: str = Field(..., description="Họ và tên người khám")
    patient_phone: str = Field(..., description="Số điện thoại liên hệ")
    patient_email: Optional[str] = Field("", description="Email (tùy chọn)")
    appointment_date: str = Field(..., description="Ngày khám YYYY-MM-DD")
    start_time: str = Field(..., description="Giờ bắt đầu ca khám HH:MM")
    symptoms: Optional[str] = Field("", description="Triệu chứng hoặc lý do khám")
    assigned_doctor: Optional[str] = Field(None, description="Bác sĩ chỉ định")


class CancelRequest(BaseModel):
    booking_code: str = Field(..., description="Mã đặt lịch cần hủy")
    cancellation_reason: Optional[str] = Field("", description="Lý do hủy")
    simulated_now_iso: Optional[str] = Field(None, description="Thời điểm giả lập")


class DoctorLoginRequest(BaseModel):
    username: str = Field(..., description="Tên đăng nhập Bác sĩ")
    password: str = Field(..., description="Mật khẩu (sẽ được băm SHA-256)")


class ExamStatusUpdateRequest(BaseModel):
    booking_code: str = Field(..., description="Mã đặt lịch")
    examination_status: str = Field(..., description="WAITING | IN_PROGRESS | COMPLETED | NO_SHOW")


class ClinicalNoteRequest(BaseModel):
    booking_code: str = Field(..., description="Mã đặt lịch")
    diagnosis: str = Field(..., description="Chẩn đoán ban đầu / kết luận")
    tests_recommended: Optional[str] = Field("", description="Đề xuất xét nghiệm (NS1Ag, Dengue IgM/IgG...)")
    prescription: Optional[str] = Field("", description="Đơn thuốc / Hướng dẫn điều trị")


class SlotBlockRequest(BaseModel):
    date_str: str = Field(..., description="Ngày khám YYYY-MM-DD")
    start_time: str = Field(..., description="Giờ bắt đầu ca khám HH:MM")
    block: bool = Field(..., description="True: Khóa ca, False: Mở lại ca")
    reason: Optional[str] = Field("", description="Lý do khóa ca")


# --- Helper Dependency for Doctor Authentication ---
def get_current_doctor(
    authorization: Optional[str] = Header(None),
    x_doctor_token: Optional[str] = Header(None)
) -> DoctorProfile:
    """Xác thực token Bác sĩ từ header Authorization hoặc X-Doctor-Token."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif x_doctor_token:
        token = x_doctor_token

    if not token:
        raise HTTPException(status_code=401, detail="Vui lòng đăng nhập tài khoản Bác sĩ để thực hiện chức năng này.")

    doctor = doctor_auth_service.get_doctor_from_token(token)
    if not doctor:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập Bác sĩ đã hết hạn hoặc không hợp lệ.")

    return doctor


# =============================================================================
# PUBLIC ROUTES
# =============================================================================

@app.get("/api/clinic-info")
def get_clinic_info():
    """Thông tin bác sĩ và địa điểm phòng khám."""
    return {
        "doctor_name": booking_service.doctor_name,
        "doctor_specialty": booking_service.doctor_specialty,
        "clinic_location": booking_service.location,
        "working_hours": "08:00 - 17:00 (Nghỉ trưa 11:30 - 13:30)",
        "slot_duration": "30 phút / lượt khám"
    }


@app.get("/api/db-status")
def get_db_status():
    """Trạng thái kết nối cơ sở dữ liệu MongoDB."""
    return mongo_manager.get_status()


@app.post("/api/db-reconnect")
def reconnect_db():
    """Tải lại .env và thử kết nối lại MongoDB."""
    from dotenv import load_dotenv
    _ROOT = _HERE.parent
    load_dotenv(_ROOT / ".env", override=True)
    load_dotenv(_HERE / ".env", override=True)

    mongo_manager.uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
    mongo_manager.db_name = os.getenv("MONGODB_DB_NAME", "dengue_clinic_db")
    connected = mongo_manager.connect()
    if connected:
        booking_service.sync_to_mongodb()

    return {
        "success": connected,
        "status": mongo_manager.get_status()
    }


@app.post("/api/db-sync")
def sync_db():
    """Đồng bộ toàn bộ lịch hẹn và thời gian biểu lên MongoDB."""
    synced_count, total_slots = booking_service.sync_to_mongodb()
    return {
        "success": True,
        "synced_bookings": synced_count,
        "total_schedule_slots_on_mongo": total_slots,
        "db_status": mongo_manager.get_status()
    }


@app.get("/api/schedule")
def get_schedule(date_str: Optional[str] = Query(None, alias="date")):
    """Lấy danh sách các khung giờ trong ngày và trạng thái."""
    target_date = date_str or datetime.now().strftime("%Y-%m-%d")
    slots = booking_service.get_schedule(target_date)
    return {
        "date": target_date,
        "storage": "MongoDB" if mongo_manager.is_connected else "In-Memory Fallback",
        "total_slots": len(slots),
        "available_slots": sum(1 for s in slots if s.status == SlotStatus.AVAILABLE),
        "booked_slots": sum(1 for s in slots if s.status == SlotStatus.BOOKED),
        "locked_empty_slots": sum(1 for s in slots if s.status == SlotStatus.CANCELLED_LOCKED),
        "blocked_by_doctor_slots": sum(1 for s in slots if s.status == SlotStatus.BLOCKED_BY_DOCTOR),
        "slots": [s.dict() for s in slots]
    }


@app.post("/api/book")
def book_appointment(req: BookingRequest):
    """Đặt lịch khám mới và lưu trữ MongoDB."""
    success, ticket, msg = booking_service.book_appointment(
        patient_name=req.patient_name,
        patient_phone=req.patient_phone,
        appointment_date=req.appointment_date,
        start_time=req.start_time,
        patient_email=req.patient_email or "",
        symptoms=req.symptoms or "",
        assigned_doctor=req.assigned_doctor
    )

    if not success:
        return JSONResponse(status_code=400, content={"success": False, "message": msg})

    t_dict = ticket.dict() if hasattr(ticket, 'dict') else ticket.model_dump()
    return {
        "success": True,
        "message": msg,
        "storage": "MongoDB" if mongo_manager.is_connected else "In-Memory",
        "ticket": t_dict
    }


@app.post("/api/cancel")
def cancel_appointment(req: CancelRequest):
    """Hủy lịch khám theo quy tắc < 1 ngày vs 1-2 ngày."""
    sim_now = None
    if req.simulated_now_iso:
        try:
            sim_now = datetime.fromisoformat(req.simulated_now_iso)
        except Exception:
            sim_now = None

    success, ticket, msg = booking_service.cancel_appointment(
        booking_code=req.booking_code,
        cancellation_reason=req.cancellation_reason or "",
        current_time=sim_now
    )

    if not success:
        return JSONResponse(status_code=400, content={"success": False, "message": msg})

    t_dict = ticket.dict() if hasattr(ticket, 'dict') else ticket.model_dump()
    return {
        "success": True,
        "message": msg,
        "storage": "MongoDB" if mongo_manager.is_connected else "In-Memory",
        "ticket": t_dict
    }


@app.get("/api/ticket/{booking_code}")
def get_ticket(booking_code: str):
    """Tra cứu chi tiết phiếu đặt lịch theo mã từ MongoDB."""
    ticket = booking_service.get_booking(booking_code)
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy mã đặt lịch này.")
    return ticket.dict() if hasattr(ticket, 'dict') else ticket.model_dump()


@app.get("/api/doctor/public-list")
def get_public_doctors():
    """Lấy danh sách 4 tài khoản Bác sĩ có sẵn (hỗ trợ kiểm thử đăng nhập nhanh)."""
    return {
        "total": 4,
        "doctors": doctor_auth_service.list_public_doctors()
    }


# =============================================================================
# DOCTOR AUTH & PROTECTED DOCTOR PORTAL ROUTES
# =============================================================================

@app.post("/api/doctor/login")
def doctor_login(req: DoctorLoginRequest):
    """
    Đăng nhập Bác sĩ:
    - Mật khẩu được mã hóa SHA-256.
    - Cấp Session Token cho phiên làm việc.
    """
    auth_result = doctor_auth_service.authenticate_doctor(
        username=req.username,
        password_plain=req.password,
        mongo_db=mongo_manager.db if mongo_manager.is_connected else None
    )

    if not auth_result:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Tên đăng nhập hoặc mật khẩu không chính xác."}
        )

    token, doc_profile = auth_result
    return {
        "success": True,
        "message": f"Chào mừng {doc_profile.title} {doc_profile.full_name} đăng nhập thành công!",
        "token": token,
        "doctor": doc_profile.dict()
    }


@app.get("/api/doctor/me")
def get_doctor_me(current_doctor: DoctorProfile = Depends(get_current_doctor)):
    """Lấy thông tin Bác sĩ hiện tại đang đăng nhập."""
    return {
        "authenticated": True,
        "doctor": current_doctor.dict()
    }


@app.post("/api/doctor/logout")
def doctor_logout(
    authorization: Optional[str] = Header(None),
    x_doctor_token: Optional[str] = Header(None)
):
    """Đăng xuất Bác sĩ và hủy token."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif x_doctor_token:
        token = x_doctor_token

    if token:
        doctor_auth_service.logout_doctor(token)

    return {"success": True, "message": "Đã đăng xuất thành công."}


@app.get("/api/doctor/appointments")
def get_doctor_appointments(
    date_str: Optional[str] = Query(None, alias="date"),
    current_doctor: DoctorProfile = Depends(get_current_doctor)
):
    """
    [ĐỘC QUYỀN BÁC SĨ] Lấy danh sách bệnh nhân và hồ sơ khám theo ngày.
    """
    target_date = date_str or datetime.now().strftime("%Y-%m-%d")
    all_bookings = booking_service.list_all_bookings(date_filter=target_date)

    slots = booking_service.get_schedule(target_date)

    # Thống kê nhanh theo trạng thái khám
    stats = {
        "total_appointments": len(all_bookings),
        "waiting_count": sum(1 for b in all_bookings if b.examination_status == ExaminationStatus.WAITING and b.status == BookingStatus.CONFIRMED),
        "in_progress_count": sum(1 for b in all_bookings if b.examination_status == ExaminationStatus.IN_PROGRESS and b.status == BookingStatus.CONFIRMED),
        "completed_count": sum(1 for b in all_bookings if b.examination_status == ExaminationStatus.COMPLETED),
        "cancelled_count": sum(1 for b in all_bookings if b.status == BookingStatus.CANCELLED),
        "no_show_count": sum(1 for b in all_bookings if b.examination_status == ExaminationStatus.NO_SHOW)
    }

    return {
        "date": target_date,
        "doctor_viewing": current_doctor.full_name,
        "stats": stats,
        "appointments": [b.dict() if hasattr(b, 'dict') else b.model_dump() for b in all_bookings],
        "schedule_slots": [s.dict() for s in slots]
    }


@app.post("/api/doctor/appointment/status")
def update_examination_status(
    req: ExamStatusUpdateRequest,
    current_doctor: DoctorProfile = Depends(get_current_doctor)
):
    """
    [ĐỘC QUYỀN BÁC SĨ] Cập nhật tiến độ ca khám:
    - IN_PROGRESS: Bắt đầu gọi khám bệnh nhân.
    - COMPLETED: Đã khám xong.
    - NO_SHOW: Bệnh nhân vắng mặt.
    - WAITING: Đưa về trạng thái chờ.
    """
    valid_statuses = [s.value for s in ExaminationStatus]
    if req.examination_status not in valid_statuses:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Trạng thái '{req.examination_status}' không hợp lệ."}
        )

    # Cập nhật MongoDB / Service
    ok, updated_doc, msg = mongo_manager.update_doctor_examination_status(
        booking_code=req.booking_code,
        exam_status=req.examination_status,
        doctor_name=current_doctor.full_name
    )

    # Đồng bộ bộ nhớ RAM
    ticket = booking_service.get_booking(req.booking_code)
    if ticket:
        ticket.examination_status = ExaminationStatus(req.examination_status)
        ticket.last_updated_by = current_doctor.full_name
        ticket.last_updated_at = datetime.now().isoformat()

    if not ok:
        return JSONResponse(status_code=400, content={"success": False, "message": msg})

    return {
        "success": True,
        "message": msg,
        "booking_code": req.booking_code,
        "new_status": req.examination_status
    }


@app.post("/api/doctor/appointment/clinical-note")
def save_clinical_note(
    req: ClinicalNoteRequest,
    current_doctor: DoctorProfile = Depends(get_current_doctor)
):
    """
    [ĐỘC QUYỀN BÁC SĨ] Nhập chẩn đoán lâm sàng, đề xuất xét nghiệm & toa thuốc.
    """
    if not req.diagnosis.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Vui lòng nhập chẩn đoán lâm sàng."}
        )

    ok, updated_doc, msg = mongo_manager.save_doctor_clinical_record(
        booking_code=req.booking_code,
        diagnosis=req.diagnosis,
        tests=req.tests_recommended or "",
        prescription=req.prescription or "",
        doctor_name=current_doctor.full_name
    )

    ticket = booking_service.get_booking(req.booking_code)
    if ticket:
        ticket.clinical_record = {
            "diagnosis": req.diagnosis.strip(),
            "tests_recommended": (req.tests_recommended or "").strip(),
            "prescription": (req.prescription or "").strip(),
            "doctor_name": current_doctor.full_name,
            "recorded_at": datetime.now().isoformat()
        }
        ticket.examination_status = ExaminationStatus.COMPLETED
        ticket.last_updated_by = current_doctor.full_name
        ticket.last_updated_at = datetime.now().isoformat()

    if not ok:
        return JSONResponse(status_code=400, content={"success": False, "message": msg})

    return {
        "success": True,
        "message": msg,
        "booking_code": req.booking_code,
        "clinical_record": ticket.clinical_record if ticket else None
    }


@app.post("/api/doctor/slot/toggle-block")
def toggle_slot_block(
    req: SlotBlockRequest,
    current_doctor: DoctorProfile = Depends(get_current_doctor)
):
    """
    [ĐỘC QUYỀN BÁC SĨ] Bác sĩ chủ động khóa (Block) ca khám khi bận đột xuất hoặc mở lại (Unblock).
    """
    ok, msg = mongo_manager.toggle_slot_block_by_doctor(
        date_str=req.date_str,
        start_time=req.start_time,
        block=req.block,
        reason=req.reason or "",
        doctor_name=current_doctor.full_name
    )

    if not ok:
        return JSONResponse(status_code=400, content={"success": False, "message": msg})

    return {
        "success": True,
        "message": msg,
        "date_str": req.date_str,
        "start_time": req.start_time,
        "status": "BLOCKED_BY_DOCTOR" if req.block else "AVAILABLE"
    }


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Giao diện Web HTML chính."""
    html_file = _HERE / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("<h1>Booking Demo UI đang được tải...</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
