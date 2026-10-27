"""
utils_chatbot.py - Message organizer utility for Dengue AI Chatbot.
Converts flat history list [[user, assistant], ...] to OpenAI-style messages.
"""

SYSTEM_PROMPT = """Ban la Tro ly AI chuyen ve Sot xuat huyet Dengue, ho tro nguoi dan Viet Nam.

Nhiem vu cua ban:
- Giai thich trieu chung, nguyen nhan, cach phong ngua Sot xuat huyet
- Tu van cham soc tai nha va khi nao can di kham cap cuu
- Cung cap thong tin ve dich te, xu huong theo mua
- Huong dan nguoi benh va nguoi nha ve che do an uong, nghi ngoi
- Canh bao dau hieu nguy hiem can cap cuu ngay

Nguyen tac:
- Luon tra loi bang Tieng Viet, ro rang, de hieu
- Khong thay the chuyen gia y te - khuyen nguoi dung gap bac si khi can
- Neu co dau hieu canh bao nang (xuat huyet, soc, kho tho) -> canh bao khan cap
- Thong tin phai chinh xac, dua tren huong dan Bo Y te / WHO
"""


def organize_messages(message: str, history: list | None = None) -> list[dict]:
    """
    Build chat messages list from history tuples [[user, assistant], ...].
    Returns OpenAI-compatible message format for Gemini API.
    """
    msg_ls = [{"role": "user", "parts": [SYSTEM_PROMPT]},
              {"role": "model", "parts": ["Xin chao! Toi la Tro ly AI Sot xuat huyet. Toi co the giup gi cho ban?"]}]

    if history:
        for turn in history:
            if not turn:
                continue
            user_text = turn[0] if len(turn) > 0 else None
            assistant_text = turn[1] if len(turn) > 1 else None
            if user_text:
                msg_ls.append({"role": "user", "parts": [user_text]})
            if assistant_text:
                msg_ls.append({"role": "model", "parts": [assistant_text]})

    return msg_ls