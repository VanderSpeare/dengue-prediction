from __future__ import annotations
import base64
import html as _html
import io
import json
import re
import unicodedata
from pathlib import Path
import streamlit as st

_HERE = Path(__file__).resolve().parent
ASSETS = _HERE / "assets"
CONTENT = _HERE / "content"
COVERS = ASSETS / "covers"

_FONTS = (
    "@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700"
    "&family=Space+Grotesk:wght@500;700&display=swap');"
)

_DEFAULT_CFG = {
    "default_mode": "day",
    "default_accent": "blue",
    "default_effects": "calm",
    "default_font": "large",
    "default_cover": {"day": "aurora-day.svg", "night": "signal-night.svg"},
    "cover_scope": "banner",
    "hero_video": {"youtube_id": "", "mode": "off"},
    "hero": {"title_en": "DENGUE WATCH", "title_vi": "Giám sát Dịch Sốt xuất huyết", "subtitle": ""},
    "loader": {"line1": "ĐANG TRUY CẬP", "line2": "ĐANG TẢI..."},
    "ticker": ["DENGUE WATCH 🔻"],
    "accents": {
        "blue": {
            "label": "Xanh dương",
            "day": {"main": "#1D4ED8", "strong": "#1E40AF", "soft": "#DBEAFE", "on": "#FFFFFF"},
            "night": {"main": "#60A5FA", "strong": "#93C5FD", "soft": "#12234F", "on": "#04122E"},
        }
    },
    "presets": {"off": [], "calm": ["loader", "ticker", "zoom", "glow", "shine"], "full": []},
    "effect_labels": {},
}

_FONT_SCALES = {"standard": ("Vừa", 0.95), "large": ("Lớn", 1.05), "xlarge": ("Rất lớn", 1.2)}
_MODE_LABELS = {"day": "☀️ Ngày", "night": "🌙 Đêm"}
_PRESET_LABELS = {"off": "Tắt", "calm": "Nhẹ", "full": "Đầy đủ"}
_DISCLAIMER = (
    "Thông tin mang tính tham khảo chung, không thay thế chẩn đoán hay chỉ định của bác sĩ. "
    "Nếu nghi ngờ mắc bệnh hoặc có dấu hiệu nguy hiểm, hãy đến cơ sở y tế ngay."
)
# ---------------------------------------------------------------------------
# Đọc tệp
# ---------------------------------------------------------------------------
def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
def _cfg() -> dict:
    cfg = dict(_DEFAULT_CFG)
    try:
        data = json.loads(_read(ASSETS / "theme.json") or "{}")
        cfg.update({k: v for k, v in data.items() if not k.startswith("_")})
    except (ValueError, TypeError):
        pass
    return cfg
_TEMPLATE_FILES = ("hero.html", "badge.html")
_BLOCK_RE = re.compile(r"<!--\s*@template\s+(\w+)\s*-->(.*?)<!--\s*@end\s*-->", re.S)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
@st.cache_data(show_spinner=False)

def _parse_templates(mtimes: tuple) -> dict:
    """Tách các khối  @template ten ... @end  trong hero.html và badge.html thành {ten: html một dòng}."""
    out: dict = {}
    for fname in _TEMPLATE_FILES:
        for m in _BLOCK_RE.finditer(_read(ASSETS / fname)):
            body = _COMMENT_RE.sub("", m.group(2))  # bỏ chú thích giải thích
            # Gộp thành một dòng: tránh Markdown hiểu nhầm dòng thụt lề là khối mã
            out[m.group(1)] = "".join(line.strip() for line in body.splitlines())
    return out

def _templates() -> dict:
    mtimes = tuple((ASSETS / f).stat().st_mtime if (ASSETS / f).exists() else 0 for f in _TEMPLATE_FILES)
    return _parse_templates(mtimes)

def render_html(_tpl: str, **values) -> str:
    """Lấy khuôn `_tpl` (trong hero.html hoặc badge.html) và thay {{ten}} bằng giá trị.
    Khóa kết thúc bằng _html được giữ nguyên, còn lại được escape. Chấp nhận 'header' hoặc 'header.html'."""
    raw = _templates().get(_tpl[:-5] if _tpl.endswith(".html") else _tpl, "")
    if not raw:
        return ""
    for key, val in values.items():
        text = str(val) if key.endswith("_html") else _html.escape(str(val))
        raw = raw.replace("{{" + key + "}}", text)
    return raw


def _md_html(html_str: str) -> None:
    st.markdown(html_str, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Ảnh bìa
# ---------------------------------------------------------------------------
_MIME = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _shrink(data: bytes, suffix: str) -> tuple[bytes, str]:
    """Ảnh điểm ảnh lớn được thu nhỏ để trang tải nhanh. SVG giữ nguyên."""
    if suffix == ".svg" or len(data) < 400_000:
        return data, suffix
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((1920, 1080))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80, optimize=True)
        return buf.getvalue(), ".jpg"
    except Exception:
        return data, suffix


@st.cache_data(show_spinner=False)
def _cover_uri_from_file(path_str: str, mtime: float) -> str:
    p = Path(path_str)
    data, suffix = _shrink(p.read_bytes(), p.suffix.lower())
    return f"data:{_MIME.get(suffix, 'image/jpeg')};base64,{base64.b64encode(data).decode()}"


def _cover_uri(cfg: dict, mode: str) -> str:
    choice = st.session_state.get("ui_cover", "auto")
    upload = st.session_state.get("ui_cover_upload")
    try:
        if upload is not None:
            suffix = Path(upload.name).suffix.lower()
            data, suffix = _shrink(upload.getvalue(), suffix)
            return f"data:{_MIME.get(suffix, 'image/jpeg')};base64,{base64.b64encode(data).decode()}"
        name = cfg["default_cover"].get(mode) if choice == "auto" else choice
        path = COVERS / str(name)
        if path.is_file():
            return _cover_uri_from_file(str(path), path.stat().st_mtime)
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Trạng thái & thanh bên
# ---------------------------------------------------------------------------
def _init_state(cfg: dict) -> None:
    ss = st.session_state
    ss.setdefault("ui_mode", cfg["default_mode"])
    ss.setdefault("ui_accent", cfg["default_accent"])
    ss.setdefault("ui_effects", cfg["default_effects"])
    ss.setdefault("ui_font", cfg["default_font"])
    ss.setdefault("ui_cover", "auto")
    ss.setdefault("ui_scope", cfg["cover_scope"])
    hv = cfg.get("hero_video", {})
    ss.setdefault("ui_video", hv.get("mode", "off") if hv.get("youtube_id") else "off")
    ss.setdefault("ui_video_src", hv.get("youtube_id", ""))


def mode() -> str:
    return st.session_state.get("ui_mode", "day")


def map_style() -> str:
    """Nền bản đồ: dùng OpenStreetMap cho mọi chế độ (tránh lỗi API key của Carto)."""
    return "open-street-map"


def _enabled_effects(cfg: dict) -> list[str]:
    """Lấy danh sách hiệu ứng đang bật từ session_state theo mức hiện tại."""
    presets = cfg["presets"]
    labels = cfg.get("effect_labels", {})
    preset = st.session_state["ui_effects"]
    all_fx = list(labels) or sorted({fx for lst in presets.values() for fx in lst})
    default = [fx for fx in presets.get(preset, []) if fx in all_fx]
    return list(st.session_state.get(f"ui_fx_{preset}", default))


def render_customize_panel() -> None:
    """Vẽ các tùy chỉnh giao diện & hiệu ứng bên trong mục '⋮ Tùy chỉnh'."""
    cfg = _cfg()
    _init_state(cfg)
    accents = cfg["accents"]
    presets = cfg["presets"]
    labels = cfg.get("effect_labels", {})
    covers = sorted(p.name for p in COVERS.glob("*") if p.suffix.lower() in _MIME) if COVERS.is_dir() else []

    st.radio("🌓 Chế độ", list(_MODE_LABELS), format_func=_MODE_LABELS.get, key="ui_mode", horizontal=True)
    st.radio("🎨 Màu nhấn", list(accents), format_func=lambda k: accents[k].get("label", k), key="ui_accent", horizontal=True)
    st.select_slider("🔠 Cỡ chữ", list(_FONT_SCALES), format_func=lambda k: _FONT_SCALES[k][0], key="ui_font")
    st.selectbox("🖼️ Ảnh bìa", ["auto"] + covers, format_func=lambda k: "Tự động (theo chế độ)" if k == "auto" else k, key="ui_cover")
    st.file_uploader("📤 Tải ảnh bìa", type=["png", "jpg", "jpeg", "webp", "svg"], key="ui_cover_upload")
    st.radio("📐 Ảnh bìa phủ", ["banner", "page"], format_func=lambda k: "Chỉ banner" if k == "banner" else "Toàn trang", key="ui_scope", horizontal=True)

    st.radio(
        "🎬 Video nền",
        ["off", "banner", "page"],
        format_func=lambda k: {"off": "Tắt", "banner": "Banner", "page": "Toàn trang"}[k],
        key="ui_video",
        horizontal=True,
    )
    st.text_input("🔗 Link YouTube", key="ui_video_src", placeholder="https://www.youtube.com/watch?v=...")

    preset_keys = [k for k in ("off", "calm", "full") if k in presets] or list(presets)
    st.select_slider("✨ Mức hiệu ứng", preset_keys, format_func=lambda k: _PRESET_LABELS.get(k, k), key="ui_effects")
    preset = st.session_state["ui_effects"]
    all_fx = list(labels) or sorted({fx for lst in presets.values() for fx in lst})
    st.multiselect(
        "🎛️ Tinh chỉnh hiệu ứng",
        all_fx,
        default=[fx for fx in presets.get(preset, []) if fx in all_fx],
        format_func=lambda k: labels.get(k, k),
        key=f"ui_fx_{preset}",
    )


def youtube_id() -> str:
    """Lấy mã video 11 ký tự từ link hoặc mã người dùng nhập. Rỗng nếu không hợp lệ."""
    raw = str(st.session_state.get("ui_video_src", "")).strip()
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", raw) or re.fullmatch(r"([A-Za-z0-9_-]{11})", raw)
    return m.group(1) if m else ""


_STYLE_BLOCK_RE = re.compile(r"/\*\s*@(mode|fx):(\w+)\s*\*/(.*?)/\*\s*@end\s*\*/", re.S)
# Các tệp CSS được ghép lại: giao diện chính + các hiệu ứng bật/tắt được.
_STYLE_FILES = (ASSETS / "style.css", _HERE / "sidebar" / "base.css", _HERE / "sidebar" / "effects.css")


@st.cache_data(show_spinner=False)
def _parse_style(mtimes: tuple) -> tuple[dict, dict, str]:
    """Tách style.css + sidebar/*.css thành: các khối màu {day/night}, các khối hiệu ứng {ten}, và phần chính (luôn nạp)."""
    text = "\n".join(_read(p) for p in _STYLE_FILES)
    modes: dict = {}
    effects: dict = {}
    for m in _STYLE_BLOCK_RE.finditer(text):
        (modes if m.group(1) == "mode" else effects)[m.group(2)] = m.group(3)
    return modes, effects, _STYLE_BLOCK_RE.sub("", text)


def _style_css(mode_name: str, enabled: list[str]) -> str:
    """Ghép CSS cần nạp: khối màu của chế độ đang chọn + phần chính + các hiệu ứng đang bật."""
    mtimes = tuple(p.stat().st_mtime if p.exists() else 0 for p in _STYLE_FILES)
    modes, effects, base = _parse_style(mtimes)
    return "\n".join([modes.get(mode_name, ""), base] + [effects[k] for k in enabled if k in effects])


def _vars_css(cfg: dict, m: str, cover: str, scale: float) -> str:
    accents = cfg["accents"]
    acc = accents.get(st.session_state["ui_accent"]) or next(iter(accents.values()))
    a = acc[m]
    css = (
        ":root{"
        f"--accent:{a['main']};--accent-strong:{a['strong']};--accent-soft:{a['soft']};--on-accent:{a['on']};"
        f"--fs-scale:{scale};"
        + (f'--cover:url("{cover}");' if cover else "--cover:none;")
        + "}"
    )
    if st.session_state.get("ui_scope") == "page" and cover:
        css += (
            ".stApp{background-image:linear-gradient(var(--veil),var(--veil)),var(--cover) !important;"
            "background-size:cover !important;background-position:center !important;background-attachment:fixed !important;}"
        )
    return css


def _plotly_defaults(m: str) -> None:
    """Mọi biểu đồ Plotly tự theo chế độ Ngày/Đêm (nền trong suốt, chữ cùng màu trang)."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        night = m == "night"
        text = "#EEF2FF" if night else "#0B1530"
        grid = "#232E4D" if night else "#D6E2F5"
        tpl = go.layout.Template(pio.templates["plotly_dark" if night else "plotly_white"])
        tpl.layout.update(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Be Vietnam Pro, Segoe UI, sans-serif", color=text),
            xaxis=dict(gridcolor=grid, zerolinecolor=grid),
            yaxis=dict(gridcolor=grid, zerolinecolor=grid),
        )
        pio.templates["dengue_watch"] = tpl
        pio.templates.default = "dengue_watch"
    except Exception:
        pass


# ---------------------------------------------------------------------------
# API chính
# ---------------------------------------------------------------------------
def apply_theme() -> None:
    """Gọi 1 lần ngay sau st.set_page_config(). Nhúng CSS và hiệu ứng giao diện."""
    cfg = _cfg()
    _init_state(cfg)
    enabled = _enabled_effects(cfg)
    m = mode()
    st.session_state["_ui_fx_enabled"] = enabled

    scale = _FONT_SCALES.get(st.session_state["ui_font"], _FONT_SCALES["large"])[1]
    css = "\n".join([_vars_css(cfg, m, _cover_uri(cfg, m), scale), _style_css(m, enabled)])
    _md_html(f"<style>{_FONTS}\n{css}</style>")
    _plotly_defaults(m)


def status_badge(text: str, css_class: str) -> None:
    _md_html(render_html("badge.html", text=text, css_class=css_class))


def ticket_card(tk) -> None:
    """Phiếu hẹn dạng vé. `tk` là đối tượng phiếu của dịch vụ đặt lịch (chỉ đọc thuộc tính)."""
    symptoms = ""
    if getattr(tk, "symptoms", ""):
        symptoms = (
            '<div class="kaf-ticket__row"><b>📝 Triệu chứng</b><span>'
            f"{_html.escape(str(tk.symptoms))}</span></div>"
        )
    _md_html(
        render_html(
            "ticket.html",
            doctor=tk.doctor_name,
            specialty=tk.doctor_specialty,
            location=tk.clinic_location,
            time=tk.appointment_time,
            date=tk.appointment_date,
            patient=tk.patient_name,
            phone=tk.patient_phone,
            queue=f"{tk.queue_number:02d}",
            code=tk.booking_code,
            symptoms_html=symptoms,
        )
    )


def style_fig(fig):
    """Đồng bộ màu biểu đồ Plotly với chế độ Ngày/Đêm. Lỗi nào cũng bỏ qua để không ảnh hưởng ứng dụng."""
    try:
        night = mode() == "night"
        text = "#EEF2FF" if night else "#0F1E3D"
        grid = "#2A3358" if night else "#D6E2F5"
        fig.update_layout(
            template="plotly_dark" if night else "plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(size=15, color=text),
            title_font=dict(size=18, color=text),
            legend=dict(font=dict(size=14, color=text)),
        )
        fig.update_xaxes(gridcolor=grid, tickfont=dict(color=text), title_font=dict(color=text))
        fig.update_yaxes(gridcolor=grid, tickfont=dict(color=text), title_font=dict(color=text))
        fig.update_coloraxes(colorbar_tickfont_color=text, colorbar_title_font_color=text)
    except Exception:
        pass
    return fig


# ---------------------------------------------------------------------------
# Trang kiến thức kiểu Wiki (đọc từ content/*.md)
# ---------------------------------------------------------------------------
def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "muc"


def _parse_page(path: Path) -> dict | None:
    raw = _read(path)
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        return None
    meta: dict = {"id": path.stem, "sources": [], "related": []}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+-\s+", line) and key in ("sources", "related"):
            meta[key].append(re.sub(r"^\s+-\s+", "", line).strip())
        elif ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            key = k.strip()
            if key not in ("sources", "related"):
                meta[key] = v.strip()
    meta["body"] = m.group(2).strip()
    meta["order"] = int(meta.get("order", 99)) if str(meta.get("order", "99")).isdigit() else 99
    meta.setdefault("title", path.stem)
    meta.setdefault("icon", "📄")
    meta.setdefault("summary", "")
    return meta


def load_pages() -> list[dict]:
    pages = [p for p in (_parse_page(f) for f in sorted(CONTENT.glob("*.md"))) if p] if CONTENT.is_dir() else []
    return sorted(pages, key=lambda p: (p["order"], p["title"]))


def _inline(text: str) -> str:
    text = _html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)


def _callout_html(kind: str, title: str, lines: list[str]) -> str:
    out, in_list = [], False
    for ln in lines:
        if ln.lstrip().startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(ln.lstrip()[2:])}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            if ln.strip():
                out.append(f"<p>{_inline(ln.strip())}</p>")
    if in_list:
        out.append("</ul>")
    return render_html("callout.html", kind=kind, title=title, body_html="".join(out))


def _split_segments(body: str) -> list[tuple[str, str]]:
    """Tách thân bài thành (markdown, callout_html). Khối '> [!warn] Tiêu đề' thành hộp lưu ý."""
    segs: list[tuple[str, str]] = []
    buf: list[str] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^>\s*\[!(warn|tip|info)\]\s*(.*)$", lines[i])
        if m:
            if buf:
                segs.append(("md", "\n".join(buf)))
                buf = []
            quote = []
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            segs.append(("html", _callout_html(m.group(1), m.group(2), quote)))
            continue
        buf.append(lines[i])
        i += 1
    if buf:
        segs.append(("md", "\n".join(buf)))
    return segs


def _sections(body: str) -> list[tuple[str, str]]:
    parts = re.split(r"^##\s+(.+)$", body, flags=re.M)
    # parts = [intro, h1, body1, h2, body2, ...]
    return [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]


def _article_body(page: dict, secs: list[tuple[str, str]]) -> None:
    chips = [f"Cập nhật: {page.get('updated', '')}"] if page.get("updated") else []
    chips.append(f"{len(secs)} mục")
    _md_html(
        render_html(
            "article_head.html",
            title=page["title"],
            icon=page["icon"],
            summary=page["summary"],
            chips_html="".join(f'<span class="wiki-chip">{_html.escape(c)}</span>' for c in chips),
        )
    )
    for heading, body in secs:
        _md_html(f'<div class="wiki-anchor" id="{_slug(heading)}"></div>')
        st.markdown(f"## {heading}")
        for kind, content in _split_segments(body):
            if kind == "html":
                _md_html(content)
            elif content.strip():
                st.markdown(content)

    if page["related"]:
        st.markdown("### Xem tiếp")
        cards = []
        for n, rel in enumerate(page["related"], 1):
            label, _, hint = (s.strip() for s in rel.partition("|"))
            cards.append(
                f'<div class="wiki-related__i"><span class="n">{n:02d}</span>'
                f"<div><b>{_html.escape(label)}</b><small>{_html.escape(hint)}</small></div></div>"
            )
        _md_html(f'<div class="wiki-related">{"".join(cards)}</div>')

    src = ""
    if page["sources"]:
        li = []
        for s in page["sources"]:
            name, _, url = (x.strip() for x in s.partition("|"))
            li.append(
                f'<li><a href="{_html.escape(url)}" target="_blank" rel="noopener">{_html.escape(name)}</a></li>'
                if url.startswith("http")
                else f"<li>{_html.escape(name)}</li>"
            )
        src = "<p><b>Nguồn tham khảo</b></p><ul>" + "".join(li) + "</ul>"
    _md_html(render_html("article_meta.html", sources_html=src, disclaimer=_DISCLAIMER))


def render_article(page: dict, toc: bool = True) -> None:
    """Vẽ một bài kiến thức kiểu Wiki (dùng trong hộp thoại SPECIAL). toc=True thêm cột mục lục bên phải."""
    secs = _sections(page["body"])
    if not toc:
        _article_body(page, secs)
        return
    col_main, col_toc = st.columns([5, 2], gap="large")
    with col_toc:
        items = "".join(
            f'<li><a href="#{_slug(h)}"><span class="n">{n:02d}</span><span>{_html.escape(h)}</span></a></li>'
            for n, (h, _) in enumerate(secs, 1)
        )
        _md_html(render_html("toc.html", count=len(secs), items_html=items))
    with col_main:
        _article_body(page, secs)