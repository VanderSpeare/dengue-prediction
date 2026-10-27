"""
gemini_chat_engine.py
=====================
Direct Gemini API chat engine with Google Search Grounding & Real-Time Date Awareness.
No RAG dependencies, no outdated 2024 knowledge limits.

Features:
- Live Google Search Grounding for up-to-date data & real-time statistics (2026+)
- Dynamic current date/time context injection
- Chat session streaming with AFC (Automatic Function Calling) support
- Streamlit st.write_stream() generator compatibility
- High-precision emergency detection (avoids false alarms on standard terms)
- Offline keyword fallback if API key is missing
"""
from __future__ import annotations

import datetime
import logging
import os
import sys
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config — load API key & model from .env via src/config.py
# ---------------------------------------------------------------------------
_SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SRC_DIR))

try:
    from config import settings as _cfg
    GEMINI_API_KEY = _cfg.GEMINI_API_KEY
    GEMINI_MODEL   = _cfg.GEMINI_MODEL
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# ---------------------------------------------------------------------------
# Gemini client (google.genai SDK)
# ---------------------------------------------------------------------------
_genai_client = None

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        from google import genai
        _genai_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info(f"GeminiChatEngine ready: {GEMINI_MODEL}")
    except ImportError:
        logger.warning("google-genai not installed — offline fallback active")
    except Exception as exc:
        logger.warning(f"Gemini init error: {exc} — offline fallback active")
else:
    logger.warning("GEMINI_API_KEY not set — offline fallback active")


def _get_system_prompt(role: str) -> str:
    """Build dynamic system prompt with current date/time and role tone."""
    now_str = datetime.datetime.now().strftime("%d/%m/%Y")
    current_year = datetime.datetime.now().year

    if "bac si" in role.lower() or "bác sĩ" in role.lower():
        return (
            f"Thời điểm hiện tại: Ngày {now_str} (Năm {current_year}).\n"
            "Bạn là Trợ lý AI chuyên môn y tế và dịch tễ học, hỗ trợ bác sĩ và nhân viên y tế.\n"
            "Bạn có thể tra cứu thông tin thực tế, báo cáo dịch tễ mới nhất qua công cụ tìm kiếm.\n"
            "Trả lời bằng Tiếng Việt, sử dụng thuật ngữ y khoa chuẩn xác, căn cứ vào hướng dẫn lâm sàng và dữ liệu thực tế."
        )
    else:
        return (
            f"Thời điểm hiện tại: Ngày {now_str} (Năm {current_year}).\n"
            "Bạn là Trợ lý AI thông minh, hỗ trợ giải đáp mọi câu hỏi của người dùng.\n"
            "Bạn có thể tra cứu thông tin thực tế mới nhất qua Google Search.\n"
            "Luôn trả lời bằng Tiếng Việt thân thiện, rõ ràng, dễ hiểu.\n"
            "Đối với câu hỏi y tế, hãy cung cấp thông tin hữu ích và khuyên người bệnh đi khám khi cần thiết."
        )


# ---------------------------------------------------------------------------
# High-precision Emergency Detection
# (Only triggers on explicit severe clinical emergencies in user queries)
# ---------------------------------------------------------------------------
_SEVERE_PATIENT_SIGNS = [
    "chảy máu chân răng", "chay mau chan rang",
    "chảy máu cam", "chay mau cam",
    "nôn ra máu", "non ra mau",
    "đi cầu phân đen", "di cau phan den", "tiểu ra máu", "tieu ra mau",
    "đau bụng dữ dội", "dau bung du doi", "đau bụng liên tục", "dau bung lien tuc",
    "nôn liên tục", "non lien tuc", "nôn nhiều lần", "non nhieu lan",
    "lì bì", "li bi", "vật vã", "vat va", "bứt rứt", "but rut", "hôn mê", "hon me",
    "tay chân lạnh ngắt", "tay chan lanh ngat", "chân tay lạnh", "chan tay lanh",
    "tụt huyết áp", "tut huyet ap", "sốc sốt xuất huyết", "soc sot xuat huyet",
    "khó thở dữ dội", "kho tho du doi",
]

_EMERGENCY_MSG = (
    "\n\n---\n"
    "🚨 **CẢNH BÁO NGUY HIỂM:** Câu hỏi của bạn có chứa dấu hiệu cảnh báo sốt xuất huyết nặng!\n"
    "**Người bệnh cần đến ngay bệnh viện hoặc khoa Cấp cứu gần nhất để được xử trí kịp thời.**\n"
    "Gọi ngay **115** nếu người bệnh li bì, trụy mạch hoặc chân tay lạnh."
)


# ---------------------------------------------------------------------------
# Offline keyword fallback
# ---------------------------------------------------------------------------
_OFFLINE_KB = {
    "trieu chung": (
        "**Triệu chứng Sốt xuất huyết:**\n\n"
        "- Sốt cao đột ngột 39-40°C liên tục 2-7 ngày, đau đầu, đau hốc mắt, đau cơ\n"
        "- Phát ban, nốt xuất huyết dưới da sau ngày thứ 3\n"
        "- **Dấu hiệu nặng cần cấp cứu:** Đau bụng dữ dội, nôn nhiều, chảy máu cam/chân răng, chân tay lạnh"
    ),
    "triệu chứng": (
        "**Triệu chứng Sốt xuất huyết:**\n\n"
        "- Sốt cao đột ngột 39-40°C liên tục 2-7 ngày, đau đầu, đau hốc mắt, đau cơ\n"
        "- Phát ban, nốt xuất huyết dưới da sau ngày thứ 3\n"
        "- **Dấu hiệu nặng cần cấp cứu:** Đau bụng dữ dội, nôn nhiều, chảy máu cam/chân răng, chân tay lạnh"
    ),
    "phong ngua": (
        "**Phòng ngừa Sốt xuất huyết:**\n\n"
        "1. Diệt lăng quăng/bọ gậy, đậy kín tất cả dụng cụ chứa nước\n"
        "2. Mặc quần áo dài tay, ngủ màn kể cả ban ngày\n"
        "3. Dùng kem xua muỗi, vợt muỗi, bình xịt côn trùng"
    ),
    "phòng ngừa": (
        "**Phòng ngừa Sốt xuất huyết:**\n\n"
        "1. Diệt lăng quăng/bọ gậy, đậy kín tất cả dụng cụ chứa nước\n"
        "2. Mặc quần áo dài tay, ngủ màn kể cả ban ngày\n"
        "3. Dùng kem xua muỗi, vợt muỗi, bình xịt côn trùng"
    ),
    "dieu tri": (
        "**Chăm sóc & Điều trị tại nhà:**\n\n"
        "- Nghỉ ngơi hoàn toàn, uống nhiều nước (Oresol, nước dừa, nước ép trái cây)\n"
        "- **Hạ sốt:** Chỉ dùng **Paracetamol** đúng liều. **TUYỆT ĐỐI KHÔNG** dùng Aspirin / Ibuprofen\n"
        "- Tái khám xét nghiệm máu hàng ngày theo chỉ định của bác sĩ"
    ),
    "điều trị": (
        "**Chăm sóc & Điều trị tại nhà:**\n\n"
        "- Nghỉ ngơi hoàn toàn, uống nhiều nước (Oresol, nước dừa, nước ép trái cây)\n"
        "- **Hạ sốt:** Chỉ dùng **Paracetamol** đúng liều. **TUYỆT ĐỐI KHÔNG** dùng Aspirin / Ibuprofen\n"
        "- Tái khám xét nghiệm máu hàng ngày theo chỉ định của bác sĩ"
    ),
    "hạ sốt": (
        "**Chăm sóc & Hạ sốt an toàn:**\n\n"
        "- Nghỉ ngơi hoàn toàn, uống nhiều nước (Oresol, nước dừa, nước ép trái cây)\n"
        "- **Chỉ dùng Paracetamol** để hạ sốt. TUYỆT ĐỐI KHÔNG dùng Aspirin, Ibuprofen."
    ),
}


def _offline_answer(query: str) -> str:
    q = query.lower()
    for kw, ans in _OFFLINE_KB.items():
        if kw in q:
            return ans
    return (
        "**Chế độ Offline** — Chưa kết nối được Gemini API.\n\n"
        "Vui lòng kiểm tra `GEMINI_API_KEY` trong file `.env` và khởi động lại.\n\n"
        "Bạn có thể hỏi nhanh về: **triệu chứng**, **phòng ngừa**, **điều trị**."
    )


def _build_history(chat_history: list) -> list:
    """Convert [{role, content}] list to google.genai Content objects."""
    try:
        from google.genai import types as _gt
        result = []
        for msg in chat_history:
            role    = msg.get("role", "")
            content = msg.get("content", "")
            if not content:
                continue
            if role == "user":
                result.append(_gt.Content(role="user",  parts=[_gt.Part.from_text(text=content)]))
            elif role in ("assistant", "model"):
                result.append(_gt.Content(role="model", parts=[_gt.Part.from_text(text=content)]))
        return result
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Public Engine Class
# ---------------------------------------------------------------------------
class GeminiChatEngine:
    """
    General-purpose AI chat engine using Google Gemini API with Google Search Grounding.
    No topic restrictions — answers any question with live real-time knowledge.
    """

    def __init__(self, api_key: str | None = None):
        global _genai_client
        if api_key and _genai_client is None:
            try:
                from google import genai
                _genai_client = genai.Client(api_key=api_key)
            except Exception as exc:
                logger.warning(f"Custom key init failed: {exc}")

    def process_query_stream(
        self,
        query: str,
        role: str = "Nguoi dan",
        chat_history: list | None = None,
    ) -> Generator[str, None, None]:
        """
        Streaming generator — yields text chunks from Gemini with live Google Search.
        Compatible with Streamlit st.write_stream().
        """
        chat_history = chat_history or []
        system_prompt = _get_system_prompt(role)

        if _genai_client is None:
            yield _offline_answer(query)
            return

        try:
            from google.genai import types as _gt

            history = _build_history(chat_history)
            config  = _gt.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[_gt.Tool(google_search=_gt.GoogleSearch())],
                thinking_config=_gt.ThinkingConfig(thinking_level="low"),
                max_output_tokens=2048,
            )

            # Use chat session for proper multi-turn conversation and AFC support
            chat = _genai_client.chats.create(
                model=GEMINI_MODEL,
                config=config,
                history=history,
            )

            response = chat.send_message_stream(query)
            for chunk in response:
                try:
                    delta = chunk.text
                except Exception:
                    continue
                if delta:
                    yield delta

        except Exception as exc:
            logger.error(f"Gemini streaming error: {exc}")
            yield f"**Lỗi API:** {exc}\n\nVui lòng kiểm tra kết nối và GEMINI_API_KEY."

    def process_query(
        self,
        query: str,
        role: str = "Nguoi dan",
        chat_history: list | None = None,
        session_id: str = "default",
    ) -> dict:
        """
        Non-streaming method returning response dictionary.
        """
        chunks = list(self.process_query_stream(query, role, chat_history))
        answer = "".join(chunks)

        q_lower = query.lower()
        is_emergency = any(kw in q_lower for kw in _SEVERE_PATIENT_SIGNS)
        if is_emergency and _EMERGENCY_MSG not in answer:
            answer += _EMERGENCY_MSG

        return {
            "answer":       answer,
            "intent":       "GENERAL",
            "sources":      [f"Google Gemini ({GEMINI_MODEL}) + Google Search"],
            "tokens_used":  len(answer) // 4,
            "is_emergency": is_emergency,
            "web_searched": _genai_client is not None,
        }


# Backward-compat alias
DengueChatEngine = GeminiChatEngine
