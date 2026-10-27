"""
app.py - Dengue AI Chatbot | FastAPI + SSE streaming + Gemini API
=================================================================
No Gradio, no numpy, no heavy deps.
- POST /predict  -> text/event-stream (Server-Sent Events)
- GET  /         -> index.html
- GET  /health   -> API status
- API key from .env via config.py (or system env)
- Offline keyword-fallback when API key missing
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_HERE         = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))                    # chatbot_demo/
sys.path.insert(0, str(_PROJECT_ROOT / "src"))    # src/

from utils_chatbot import organize_messages

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config / API key (loaded from .env via src/config.py)
# ---------------------------------------------------------------------------
try:
    from config import settings
    GEMINI_API_KEY = settings.GEMINI_API_KEY
    GEMINI_MODEL   = settings.GEMINI_MODEL
    logger.info(f"Config loaded - model: {GEMINI_MODEL}")
except Exception as e:
    logger.warning(f"config.py unavailable ({e}) - falling back to os.getenv")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# ---------------------------------------------------------------------------
# Gemini client setup (google.genai SDK)
# ---------------------------------------------------------------------------
_genai_client = None

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        from google import genai as _genai_sdk
        _genai_client = _genai_sdk.Client(api_key=GEMINI_API_KEY)
        logger.info(f"Gemini client ready: {GEMINI_MODEL}")
    except ImportError:
        logger.warning("google-genai not installed - offline fallback active")
    except Exception as exc:
        logger.warning(f"Gemini init failed: {exc} - offline fallback active")
else:
    logger.warning("GEMINI_API_KEY not configured - offline fallback active")

# ---------------------------------------------------------------------------
# Offline keyword fallback
# ---------------------------------------------------------------------------
_OFFLINE = {
    "trieu chung": (
        "**Trieu chung Sot xuat huyet:**\n\n"
        "- **Ngay 1-3:** Sot cao dot ngot 39-40 do C, dau dau, dau co the, met moi\n"
        "- **Ngay 4-5:** Ha sot, phat ban do, co the xuat huyet nhe (cam mau, chan rang)\n"
        "- **Dau hieu nang:** Dau bung, non nhieu, xuat huyet, li bi, tay chan lanh\n\n"
        "*Neu co dau hieu nang, hay den co so y te NGAY LAP TUC.*"
    ),
    "phong ngua": (
        "**Phong ngua Sot xuat huyet:**\n\n"
        "1. Diet lang muoi Aedes - day kin dung cu chua nuoc\n"
        "2. Mac quan ao dai, dung man khi ngu\n"
        "3. Phat quang bui ram quanh nha\n"
        "4. Dung kem chong muoi\n"
        "5. Bao cao ca nha hang xom khi phat hien o dich"
    ),
    "dieu tri": (
        "**Cham soc Sot xuat huyet tai nha:**\n\n"
        "- Nghi ngoi, uong nhieu nuoc (oresol, nuoc dua, nuoc ep)\n"
        "- **Chi dung Paracetamol** de ha sot\n"
        "- **KHONG dung** Ibuprofen / Aspirin / Diclofenac\n"
        "- Theo doi sat trieu chung, tai kham hang ngay\n\n"
        "**Can cap cuu ngay:** dau bung, non nhieu, chay mau, li bi, tay chan lanh"
    ),
}


def _offline_answer(message: str) -> str:
    m = message.lower()
    for kw, ans in _OFFLINE.items():
        if kw in m:
            return ans
    return (
        "**Che do Offline** - Chua co Gemini API key.\n\n"
        "De kich hoat AI day du:\n"
        "1. Lay key tai https://aistudio.google.com/app/apikey\n"
        "2. Them `GEMINI_API_KEY=...` vao file `.env` o thu muc goc\n"
        "3. Khoi dong lai: `python chatbot_demo/app.py`\n\n"
        "Hien tai ban co the hoi ve: **trieu chung**, **phong ngua**, **dieu tri**"
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Dengue AI Chatbot", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    message: str
    history: list[list] | None = None
    thinking_level: Optional[str] = "low"
    max_tokens: int = 2048


async def _stream_gemini(req: PredictRequest) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted events with live Google Search."""
    history = req.history or []

    # --- Offline path ---
    if _genai_client is None:
        answer  = _offline_answer(req.message)
        payload = json.dumps({"text": answer, "done": True})
        yield f"data: {payload}\n\n"
        return

    import datetime
    from google.genai import types as _gt

    now_str = datetime.datetime.now().strftime("%d/%m/%Y")
    current_year = datetime.datetime.now().year

    # Build history
    contents_history = []
    for turn in history:
        if len(turn) >= 2:
            u_text, a_text = turn[0], turn[1]
            if u_text:
                contents_history.append(_gt.Content(role="user", parts=[_gt.Part.from_text(text=u_text)]))
            if a_text:
                contents_history.append(_gt.Content(role="model", parts=[_gt.Part.from_text(text=a_text)]))

    system_prompt = (
        f"Thời điểm hiện tại: Ngày {now_str} (Năm {current_year}).\n"
        "Bạn là Trợ lý AI thông minh, hỗ trợ giải đáp mọi thắc mắc của người dùng.\n"
        "Bạn có thể tra cứu thông tin thực tế mới nhất qua Google Search.\n"
        "Luôn trả lời bằng Tiếng Việt thân thiện, rõ ràng, mạch lạc."
    )

    t_level = req.thinking_level if req.thinking_level in ["minimal", "low", "medium", "high"] else "low"
    cfg = _gt.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[_gt.Tool(google_search=_gt.GoogleSearch())],
        thinking_config=_gt.ThinkingConfig(thinking_level=t_level),
        max_output_tokens=req.max_tokens,
    )

    try:
        chat = _genai_client.chats.create(
            model=GEMINI_MODEL,
            config=cfg,
            history=contents_history,
        )
        response = chat.send_message_stream(req.message)

        full_text = ""
        for chunk in response:
            try:
                delta = chunk.text
            except Exception:
                continue
            if delta:
                full_text += delta
                payload = json.dumps({"text": full_text, "done": False})
                yield f"data: {payload}\n\n"

        final   = full_text or "Khong nhan duoc phan hoi tu Gemini. Vui long thu lai."
        payload = json.dumps({"text": final, "done": True})
        yield f"data: {payload}\n\n"

    except Exception as exc:
        logger.error(f"Gemini error: {exc}")
        err = f"**Loi API:** {exc}\n\nVui long kiem tra GEMINI_API_KEY."
        payload = json.dumps({"text": err, "done": True})
        yield f"data: {payload}\n\n"


@app.post("/predict")
async def predict(req: PredictRequest):
    logger.info(f"[predict] msg={req.message[:60]!r} hist_len={len(req.history or [])}")
    return StreamingResponse(
        _stream_gemini(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/", response_class=HTMLResponse)
async def homepage():
    return (_HERE / "index.html").read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {
        "status":    "ok",
        "model":     GEMINI_MODEL,
        "api_ready": _genai_client is not None,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    logger.info(f"Dengue AI Chatbot -> http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
