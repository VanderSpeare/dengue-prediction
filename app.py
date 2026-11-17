"""
app.py - Main Application Entry Point | Dengue AI System
========================================================
1. 🤖 Trợ lý AI Dengue (Gemini SSE streaming + live Google Search).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Path & Environment Setup
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
_CHATBOT_DIR = _ROOT / "chatbot_demo"

sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(_ROOT))

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
        "**triệu chứng**, **phòng ngừa**, **điều trị** sốt xuất huyết."
    )

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Hệ Thống AI Giám Sát & Tư Vấn Sốt Xuất Huyết",
    description="Hệ thống AI Chatbot tư vấn Sốt Xuất Huyết Dengue.",
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
    }


# ---------------------------------------------------------------------------
# 2. STATIC FILES & ROOT HTML VIEW
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    chatbot_html = _CHATBOT_DIR / "index.html"
    if chatbot_html.exists():
        return HTMLResponse(chatbot_html.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dengue AI System Ready</h1>")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Dengue AI System -> http://127.0.0.1:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
