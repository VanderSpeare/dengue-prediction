"""
app.py - Main Application Entry Point | Dengue AI System & Medical Appointment Portal
======================================================================================
Tích hợp toàn diện:
1. 🤖 Trợ lý AI Dengue (Gemini SSE streaming + live Google Search).
2. 📅 Hệ thống Đặt Lịch Khám Bệnh Trực Tuyến & Thời gian biểu Bác sĩ.
3. 🔒 Đăng nhập Bác sĩ với mật khẩu mã hóa SHA-256 (4 tài khoản có sẵn).
4. 🩺 Cổng Bác Sĩ (Doctor Portal): Quản lý bệnh nhân, gọi khám, ghi bệnh án & khóa ca.
5. 🍃 Lưu trữ MongoDB Atlas (bookings, schedules, counters, doctors).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional, List, Dict, Any

from fastapi import FastAPI, Query, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path & Environment Setup
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
_BOOKING_DIR = _ROOT / "booking_demo"
_CHATBOT_DIR = _ROOT / "chatbot_demo"

sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(_ROOT))

from src.booking import (
    mongo_manager,
    doctor_auth_service,
    DoctorProfile,
    booking_service,
    BookingTicket,
    TimeSlotInfo,
    SlotStatus,
    BookingStatus,
    ExaminationStatus
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("dengue.main_app")

# ---------------------------------------------------------------------------
# Gemini Config & Client Setup
# ---------------------------------------------------------------------------
try:
    from config import settings
    GEMINI_API_KEY = settings.GEMINI_API_KEY
    GEMINI_MODEL = settings.GEMINI_MODEL
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

_genai_client = None
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        from google import genai as _genai_sdk
        _genai_client = _genai_sdk.Client(api_key=GEMINI_API_KEY)
        logger.info(f"Gemini client sẵn sàng: {GEMINI_MODEL}")
    except Exception as exc:
        logger.warning(f"Lỗi khởi tạo Gemini ({exc}) - Chuyển sang Offline Fallback.")
else:
    logger.info("Chưa cấu hình GEMINI_API_KEY - Kích hoạt chế độ Offline Keyword Fallback.")

_OFFLINE_KNOWLEDGE = {
    "trieu chung": (
        "**Triệu chứng Sốt xuất huyết Dengue:**\n\n"
        "- **Ngày 1-3:** Sốt cao đột ngột 39-40°C, nhức đầu dữ dội, đau hốc mắt, đau mỏi cơ khớp.\n"
        "- **Ngày 4-5 (Giai đoạn nguy hiểm):** Hạ sốt nhưng có thể xuất huyết dưới da, chảy máu chân răng/cam.\n"
        "- **Dấu hiệu cảnh báo nặng:** Đau bụng nhiều, nôn ói liên tục, mệt lả, li bì, tay chân lạnh ẩm.\n\n"
        "*Nếu có dấu hiệu cảnh báo nặng, hãy đến bệnh viện NGAY LẬP TỨC.*"
    ),
    "phong ngua": (
        "**Phòng ngừa Sốt xuất huyết:**\n\n"
        "1. Diệt lăng quăng/bọ gậy, đậy kín các dụng cụ chứa nước sinh hoạt.\n"
        "2. Mặc quần áo dài tay, ngủ mùng (màn) cả ban ngày.\n"
        "3. Dùng kem xua muỗi hoặc xịt muỗi định kỳ.\n"
        "4. Dọn dẹp phế thải quanh nhà (vỏ dừa, lốp xe đọng nước)."
    ),
    "dieu tri": (
        "**Chăm sóc Sốt xuất huyết tại nhà:**\n\n"
        "- Nghỉ ngơi tuyệt đối, uống nhiều nước (Oresol, nước dừa, nước ép trái cây).\n"
        "- **Chỉ dùng Paracetamol** để hạ sốt (10-15mg/kg/lần, cách 4-6 giờ).\n"
        "- **TUYỆT ĐỐI KHÔNG dùng** Aspirin, Ibuprofen, Diclofenac vì gây tăng nguy cơ xuất huyết tiêu hóa.\n"
        "- Theo dõi sát và tái khám mỗi ngày theo hẹn của Bác sĩ."
    ),
}

def _offline_answer(message: str) -> str:
    m = message.lower()
    for kw, ans in _OFFLINE_KNOWLEDGE.items():
        if kw in m:
            return ans
    return (
        "**Chế độ Offline:** Tôi có thể hỗ trợ bạn các thông tin về: "
        "**triệu chứng**, **phòng ngừa**, **điều trị** sốt xuất huyết hoặc bạn có thể chuyển qua tab **Đặt Lịch Khám** để hẹn gặp Bác sĩ trực tiếp."
    )

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Hệ Thống Y Tế Dự Đoán & Đặt Lịch Khám Sốt Xuất Huyết",
    description="Hệ thống tổng hợp: AI Chatbot, Đặt lịch khám bệnh, Quản lý thời gian biểu Bác sĩ và Lưu trữ MongoDB.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    message: str
    history: list[list] | None = None
    thinking_level: Optional[str] = "low"
    max_tokens: int = 2048


class BookingRequest(BaseModel):
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = ""
    appointment_date: str
    start_time: str
    symptoms: Optional[str] = ""
    assigned_doctor: Optional[str] = None


class CancelRequest(BaseModel):
    booking_code: str
    cancellation_reason: Optional[str] = ""
    simulated_now_iso: Optional[str] = None


class DoctorLoginRequest(BaseModel):
    username: str
    password: str


class ExamStatusUpdateRequest(BaseModel):
    booking_code: str
    examination_status: str


class ClinicalNoteRequest(BaseModel):
    booking_code: str
    diagnosis: str
    tests_recommended: Optional[str] = ""
    prescription: Optional[str] = ""


class SlotBlockRequest(BaseModel):
    date_str: str
    start_time: str
    block: bool
    reason: Optional[str] = ""


def get_current_doctor(
    authorization: Optional[str] = Header(None),
    x_doctor_token: Optional[str] = Header(None)
) -> DoctorProfile:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif x_doctor_token:
        token = x_doctor_token

    if not token:
        raise HTTPException(status_code=401, detail="Vui lòng đăng nhập tài khoản Bác sĩ.")

    doctor = doctor_auth_service.get_doctor_from_token(token)
    if not doctor:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập Bác sĩ đã hết hạn hoặc không hợp lệ.")
    return doctor


# ---------------------------------------------------------------------------
# 1. AI CHATBOT ROUTES
# ---------------------------------------------------------------------------
async def _stream_gemini(req: PredictRequest) -> AsyncGenerator[str, None]:
    history = req.history or []
    if _genai_client is None:
        ans = _offline_answer(req.message)
        yield f"data: {json.dumps({'text': ans, 'done': True})}\n\n"
        return

    import datetime
    from google.genai import types as _gt

    contents_history = []
    for turn in history:
        if len(turn) >= 2:
            u_text, a_text = turn[0], turn[1]
            if u_text:
                contents_history.append(_gt.Content(role="user", parts=[_gt.Part.from_text(text=u_text)]))
            if a_text:
                contents_history.append(_gt.Content(role="model", parts=[_gt.Part.from_text(text=a_text)]))

    now_str = datetime.datetime.now().strftime("%d/%m/%Y")
    system_prompt = (
        f"Thời điểm hiện tại: Ngày {now_str}.\n"
        "Bạn là Trợ lý AI Y tế chuyên gia về Sốt Xuất Huyết Dengue.\n"
        "Tư vấn chính xác, chu đáo, khuyến cáo bệnh nhân khám Bác sĩ khi có dấu hiệu cảnh báo.\n"
        "Trả lời bằng Tiếng Việt rõ ràng, dễ hiểu."
    )

    t_level = req.thinking_level if req.thinking_level in ["minimal", "low", "medium", "high"] else "low"
    cfg = _gt.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[_gt.Tool(google_search=_gt.GoogleSearch())],
        thinking_config=_gt.ThinkingConfig(thinking_level=t_level),
        max_output_tokens=req.max_tokens,
    )

    try:
        chat = _genai_client.chats.create(model=GEMINI_MODEL, config=cfg, history=contents_history)
        response = chat.send_message_stream(req.message)
        full_text = ""
        for chunk in response:
            delta = getattr(chunk, "text", "")
            if delta:
                full_text += delta
                yield f"data: {json.dumps({'text': full_text, 'done': False})}\n\n"

        final = full_text or "Không nhận được phản hồi từ Gemini. Vui lòng thử lại."
        yield f"data: {json.dumps({'text': final, 'done': True})}\n\n"
    except Exception as exc:
        logger.error(f"Gemini error: {exc}")
        yield f"data: {json.dumps({'text': f'**Lỗi AI:** {exc}', 'done': True})}\n\n"


@app.post("/predict")
async def predict(req: PredictRequest):
    return StreamingResponse(
        _stream_gemini(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "gemini_model": GEMINI_MODEL,
        "gemini_ready": _genai_client is not None,
        "mongodb_connected": mongo_manager.is_connected
    }


# ---------------------------------------------------------------------------
# 2. BOOKING & TIMETABLE PUBLIC ROUTES
# ---------------------------------------------------------------------------
@app.get("/api/clinic-info")
def get_clinic_info():
    return {
        "doctor_name": booking_service.doctor_name,
        "doctor_specialty": booking_service.doctor_specialty,
        "clinic_location": booking_service.location,
        "working_hours": "08:00 - 17:00 (Nghỉ trưa 11:30 - 13:30)",
        "slot_duration": "30 phút / lượt khám"
    }


@app.get("/api/db-status")
def get_db_status():
    return mongo_manager.get_status()


@app.post("/api/db-reconnect")
def reconnect_db():
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env", override=True)
    mongo_manager.uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
    mongo_manager.db_name = os.getenv("MONGODB_DB_NAME", "dengue_clinic_db")
    connected = mongo_manager.connect()
    if connected:
        booking_service.sync_to_mongodb()
    return {"success": connected, "status": mongo_manager.get_status()}


@app.post("/api/db-sync")
def sync_db():
    synced_count, total_slots = booking_service.sync_to_mongodb()
    return {
        "success": True,
        "synced_bookings": synced_count,
        "total_schedule_slots_on_mongo": total_slots,
        "db_status": mongo_manager.get_status()
    }


@app.get("/api/schedule")
def get_schedule(date_str: Optional[str] = Query(None, alias="date")):
    from datetime import datetime
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
        "slots": [s.dict() if hasattr(s, 'dict') else s.model_dump() for s in slots]
    }


@app.post("/api/book")
def book_appointment(req: BookingRequest):
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
    from datetime import datetime
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
    ticket = booking_service.get_booking(booking_code)
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy mã đặt lịch này.")
    return ticket.dict() if hasattr(ticket, 'dict') else ticket.model_dump()


@app.get("/api/doctor/public-list")
def get_public_doctors():
    return {
        "total": 4,
        "doctors": doctor_auth_service.list_public_doctors()
    }


# ---------------------------------------------------------------------------
# 3. DOCTOR AUTH & PROTECTED DOCTOR PORTAL
# ---------------------------------------------------------------------------
@app.post("/api/doctor/login")
def doctor_login(req: DoctorLoginRequest):
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
        "message": f"Chào mừng {doc_profile.title} {doc_profile.full_name}!",
        "token": token,
        "doctor": doc_profile.dict() if hasattr(doc_profile, 'dict') else doc_profile.model_dump()
    }


@app.get("/api/doctor/me")
def get_doctor_me(current_doctor: DoctorProfile = Depends(get_current_doctor)):
    return {
        "authenticated": True,
        "doctor": current_doctor.dict() if hasattr(current_doctor, 'dict') else current_doctor.model_dump()
    }


@app.post("/api/doctor/logout")
def doctor_logout(
    authorization: Optional[str] = Header(None),
    x_doctor_token: Optional[str] = Header(None)
):
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
    from datetime import datetime
    target_date = date_str or datetime.now().strftime("%Y-%m-%d")
    all_bookings = booking_service.list_all_bookings(date_filter=target_date)
    slots = booking_service.get_schedule(target_date)

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
        "schedule_slots": [s.dict() if hasattr(s, 'dict') else s.model_dump() for s in slots]
    }


@app.post("/api/doctor/appointment/status")
def update_examination_status(
    req: ExamStatusUpdateRequest,
    current_doctor: DoctorProfile = Depends(get_current_doctor)
):
    from datetime import datetime
    ok, updated_doc, msg = mongo_manager.update_doctor_examination_status(
        booking_code=req.booking_code,
        exam_status=req.examination_status,
        doctor_name=current_doctor.full_name
    )

    ticket = booking_service.get_booking(req.booking_code)
    if ticket:
        ticket.examination_status = ExaminationStatus(req.examination_status)
        ticket.last_updated_by = current_doctor.full_name
        ticket.last_updated_at = datetime.now().isoformat()

    if not ok:
        return JSONResponse(status_code=400, content={"success": False, "message": msg})

    return {"success": True, "message": msg, "booking_code": req.booking_code}


@app.post("/api/doctor/appointment/clinical-note")
def save_clinical_note(
    req: ClinicalNoteRequest,
    current_doctor: DoctorProfile = Depends(get_current_doctor)
):
    from datetime import datetime
    if not req.diagnosis.strip():
        return JSONResponse(status_code=400, content={"success": False, "message": "Vui lòng nhập chẩn đoán lâm sàng."})

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

    return {"success": True, "message": msg, "booking_code": req.booking_code}


@app.post("/api/doctor/slot/toggle-block")
def toggle_slot_block(
    req: SlotBlockRequest,
    current_doctor: DoctorProfile = Depends(get_current_doctor)
):
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


# ---------------------------------------------------------------------------
# 4. ROOT HTML VIEW
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    booking_html = _BOOKING_DIR / "index.html"
    if booking_html.exists():
        return FileResponse(booking_html)
    return HTMLResponse("<h1>Dengue System & Medical Portal Ready</h1>")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Dengue Unified System -> http://127.0.0.1:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
