# Dengue AI Chatbot Demo

Chatbot hoi dap Sot xuat huyet su dung **Google Gemini API** + **Gradio Server** + giao dien HTML tuy chinh.

## Cau truc

```
chatbot_demo/
├── app.py                # Main server (Gradio + FastAPI + streaming)
├── index.html            # Giao dien chat HTML (khong dung Gradio blocks)
├── utils_chatbot.py      # Tien xu ly message history
├── requirements_demo.txt # Dependencies
└── README.md             # File nay
```

## Yeu cau

- Python 3.10+
- Gemini API key (lay tai https://aistudio.google.com/app/apikey)

## Cai dat

```bash
# 1. Cai dependencies
pip install -r chatbot_demo/requirements_demo.txt

# 2. Them API key vao file .env o thu muc goc du an
# (file .env da co san, chi can thay gia tri)
# GEMINI_API_KEY=AIzaSy...your_actual_key

# 3. Chay app
python chatbot_demo/app.py
# => Mo trinh duyet tai: http://localhost:7860
```

## Tinh nang

| Tinh nang | Chi tiet |
|-----------|----------|
| Streaming | Van ban hien thi theo tung chunk tu Gemini |
| Chat history | Luu lich su hoi thoai trong session |
| Offline fallback | Tu dong tra loi co ban neu khong co API key |
| Emergency warning | Canh bao do khi phat hien tu khoa nguy hiem |
| Settings | Chinh temperature, top-p, max tokens truc tiep tren UI |
| Quick chips | Nut goi y cau hoi nhanh |

## Luong hoat dong

```
User nhap cau hoi
    -> Gradio client goi /predict (streaming)
    -> app.py: organize_messages() xay dung history
    -> Gemini API: stream response theo tung chunk
    -> index.html: hien thi tung chunk ngay lap tuc
    -> Kiem tra tu khoa nguy hiem -> hien canh bao do
```

## Ghi chu

- Khong su dung RAG, Knowledge Base, hay mo hinh cuc bo
- API key duoc doc tu file `.env` qua `src/config.py`
- Model mac dinh: `gemini-1.5-flash` (co the doi trong .env)
- De doi model: them `GEMINI_MODEL=gemini-2.0-flash` vao `.env`