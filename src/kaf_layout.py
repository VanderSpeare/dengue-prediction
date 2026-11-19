"""
kaf_layout.py - Dựng cả trang theo bố cục trang sự kiện KAF (yokohamawars2026.kamitsubaki.jp/kaf).

Thứ tự khối giữ đúng như trang gốc (nhãn đã Việt hóa trong assets/kaf_content.json):
  loader -> header cố định -> hero (MV) -> outline -> ticket -> venue bonus item
  -> streaming ticket -> streaming bonus item -> news -> special (+ modal)
  -> q&a -> profile -> partners -> footer

Các khối "ticket / bonus item / streaming" được dùng làm khung cho các chức năng thật của ứng dụng.
`build_kaf_page()` trả về các container; dashboard.py đổ nội dung chức năng cũ vào đó (không đổi logic).
Toàn bộ chữ nằm ở assets/kaf_content.json, toàn bộ giãn cách/màu ở assets/css/kaf.css (khối :root đầu file).
"""
from __future__ import annotations

import base64
import html as _html
import json

import streamlit as st

import ui_theme as ui

_ESC = _html.escape


def _content() -> dict:
    try:
        return json.loads(ui._read(ui.ASSETS / "kaf_content.json") or "{}")
    except ValueError:
        return {}


def _h(_tpl: str, **values) -> str:
    return ui.render_html(_tpl, **values)


def _md(html_str: str) -> None:
    st.markdown(html_str, unsafe_allow_html=True)


_SVG_VARS = {
    "--model": "mv-model.svg",          # hình HUD ở giữa-phải banner
    "--fx-ring": "fx/ring.svg",         # vòng chia độ xoay (hiệu ứng orbit)
    "--fx-halftone": "fx/halftone.svg", # mảng chấm góc khối (hiệu ứng dots)
}


@st.cache_data(show_spinner=False)
def _asset_css_text(mtimes: tuple) -> str:
    out = []
    for var, rel in _SVG_VARS.items():
        try:
            uri = "data:image/svg+xml;base64," + base64.b64encode((ui.ASSETS / rel).read_bytes()).decode()
            out.append(f'{var}:url("{uri}");')
        except OSError:
            out.append(f"{var}:none;")
    return "<style>:root{" + "".join(out) + "}</style>"


def _model_css() -> None:
    """Các hình SVG tự vẽ (HUD banner + ảnh cho hiệu ứng) nhúng thành biến CSS."""
    mtimes = tuple((ui.ASSETS / r).stat().st_mtime if (ui.ASSETS / r).exists() else 0 for r in _SVG_VARS.values())
    _md(_asset_css_text(mtimes))


# ---------------------------------------------------------------------------
# Từng khối nhỏ
# ---------------------------------------------------------------------------
def _loader(c: dict) -> None:
    if (
        st.session_state.get("ui_effects", "calm") != "full"
        or "loader" not in st.session_state.get("_ui_fx_enabled", [])
        or st.session_state.get("_ui_loader_done")
    ):
        return
    st.session_state["_ui_loader_done"] = True
    ld = c.get("loader", {})
    unit = (
        f"<span>{_ESC(ld.get('text', ''))}</span><span class=\"e\">{_ESC(ld.get('emoji', ''))}</span>"
        f"<span>{_ESC(ld.get('word', 'ĐANG TẢI'))}</span><span>{_ESC(ld.get('dots', ''))}</span>"
    )
    rows = "".join(
        f'<div class="kaf-loader__row kaf-loader__row--{"l" if i % 2 == 0 else "r"}">'
        f'<div class="kaf-loader__track">{unit * 8}</div></div>'
        for i in range(int(ld.get("rows", 7)))
    )
    _md(_h("loader.html", rows_html=rows))


def _header(c: dict) -> None:
    b = c.get("brand", {})
    nav = "".join(
        f'<li><a href="#{_ESC(anchor)}">{_ESC(label)}</a></li>' for label, anchor in c.get("nav", [])
    )
    _md(
        _h(
            "header.html",
            left=b.get("left", ""),
            year=b.get("year", ""),
            right=b.get("right", ""),
            right_href=b.get("right_href", "#"),
            nav_html=nav,
        )
    )


def _video_iframe() -> str:
    """Khung phát YouTube làm nền: tắt tiếng, tự chạy, lặp, không điều khiển, không bấm được."""
    vid = ui.youtube_id()
    if not vid or st.session_state.get("ui_video", "off") == "off":
        return ""
    src = (
        f"https://www.youtube-nocookie.com/embed/{vid}?autoplay=1&mute=1&controls=0&loop=1&playlist={vid}"
        "&modestbranding=1&playsinline=1&rel=0&disablekb=1&fs=0&iv_load_policy=3"
    )
    return (
        f'<iframe src="{_ESC(src)}" title="Video nền" tabindex="-1" loading="eager" '
        'allow="autoplay; encrypted-media; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin"></iframe>'
    )


def _page_bg() -> None:
    """Nền toàn trang: mv-bg-left và mv-bg-right nằm ngang chia đều 2 nửa ở layer -100."""
    left_p = ui.ASSETS / "img" / "mv-bg-left.webp"
    right_p = ui.ASSETS / "img" / "mv-bg-right.webp"
    if not (left_p.is_file() and right_p.is_file()):
        return
    left_uri = ui._cover_uri_from_file(str(left_p), left_p.stat().st_mtime)
    right_uri = ui._cover_uri_from_file(str(right_p), right_p.stat().st_mtime)
    _md(
        '<div class="kaf-page-bg" aria-hidden="true">'
        f'<div class="kaf-page-bg__half kaf-page-bg__half--l" style="background-image:url(\'{left_uri}\')"></div>'
        f'<div class="kaf-page-bg__half kaf-page-bg__half--r" style="background-image:url(\'{right_uri}\')"></div>'
        "</div>"
    )


def _page_video() -> None:
    """Chế độ 'Toàn trang': một lớp video cố định phía sau mọi khối, phủ lớp mờ để chữ vẫn đọc được."""
    frame = _video_iframe()
    if not frame or st.session_state.get("ui_video") != "page":
        return
    _md(f'<div class="kaf-bgvideo" aria-hidden="true">{frame}</div>')
    _md(
        "<style>.stApp{background:transparent !important}"
        '[data-testid="stAppViewContainer"]{position:relative;z-index:1}'
        '[class*="st-key-sec-"]{background:color-mix(in srgb,var(--bg) 80%,transparent) !important;backdrop-filter:blur(6px)}'
        ".kaf-hero__bg{opacity:0 !important}</style>"
    )


def _hero(c: dict) -> None:
    hc = c.get("hero", {})
    # Mỗi đơn vị: chữ "CUỘN XUỐNG" + mũi tên xuống nằm giữa hai cụm chữ
    unit = f"<span>{_ESC(hc.get('marquee', 'CUỘN XUỐNG'))}</span><i class=\"kaf-marq__arr\" aria-hidden=\"true\"></i>"
    marquee = unit * int(hc.get("marquee_repeat", 11)) * 2
    video = ""
    if st.session_state.get("ui_video") == "banner":
        frame = _video_iframe()
        video = f'<div class="kaf-hero__video" aria-hidden="true">{frame}</div>' if frame else ""
    _md(
        _h(
            "hero.html",
            title_en=hc.get("title_en", ""),
            title_vi=hc.get("title_vi", ""),
            marquee_html=marquee,
            video_html=video,
        )
    )


def _head(section_id: str, label: str, en: str, ja: str) -> str:
    return _h("head.html", id=section_id, label=label, en=en, ja=ja)


def _cards(cards: list) -> str:
    out = []
    for name, sub, note, value in cards:
        out.append(
            '<div class="kaf-tcard"><div class="kaf-tcard__main">'
            f'<div class="kaf-tcard__name">{_ESC(name)}</div>'
            f'<div class="kaf-tcard__sub">{_ESC(sub)}</div>'
            f'<div class="kaf-tcard__note">{_ESC(note)}</div></div>'
            f'<div class="kaf-tcard__price"><b>{_ESC(value)}</b></div></div>'
        )
    return '<div class="kaf-tickets">' + "".join(out) + "</div>"


def _item(tag: str, icon: str, name: str, notes: list[str]) -> str:
    notes_html = "".join(f'<div class="kaf-item__note">{_ESC(n)}</div>' for n in notes)
    return _h("item.html", tag=tag, icon=icon, name=name, notes_html=notes_html)


def _btn(text: str, href: str) -> str:
    return f'<div class="kaf-btnrow"><a class="kaf-btn" href="{_ESC(href)}">{_ESC(text)}</a></div>'


def _note(text: str) -> str:
    return f'<div class="kaf-foot-note">{_ESC(text)}</div>'


def _outline(c: dict) -> None:
    o = c.get("outline", {})
    intro = "".join(f"<span>{_ESC(t)}</span>" for t in o.get("intro_normal", []))
    intro += "".join(f"<strong>{_ESC(t)}</strong>" for t in o.get("intro_bold", []))
    rows = "".join(
        f'<div class="kaf-summary__row"><div class="k">{_ESC(k)}</div><div class="v">{v}</div></div>'
        for k, v in o.get("rows", [])
    )
    _md(
        _h(
            "outline.html",
            label=o.get("label", ""),
            logo=o.get("logo", ""),
            intro_label=o.get("intro_label", ""),
            intro_html=intro,
            summary_label=o.get("summary_label", ""),
            summary_title=o.get("summary_title", ""),
            rows_html=rows,
            cta=o.get("cta", ""),
            cta_href=o.get("cta_href", "#"),
        )
    )


def _news(c: dict) -> None:
    n = c.get("news", {})
    rows = "".join(
        f'<li><a href="{_ESC(href)}"><time>{_ESC(date)}</time><span class="thumb" aria-hidden="true">{_ESC(icon)}</span>'
        f'<span class="t">{_ESC(title)}</span><span class="v">{_ESC(n.get("button", "XEM"))}</span></a></li>'
        for date, icon, title, href in n.get("items", [])
    )
    _md(
        _head("news", n.get("label", "tin tức"), n.get("en", ""), n.get("ja", ""))
        + f'<ul class="kaf-news">{rows}</ul>'
    )


def _open_article(page: dict) -> None:
    @st.dialog(page["title"], width="large")
    def _dlg() -> None:
        ui.render_article(page, toc=False)

    _dlg()


def _special(c: dict) -> None:
    sp = c.get("special", {})
    _md(_head("special", sp.get("label", "kiến thức"), sp.get("en", ""), sp.get("ja", "")))
    pages = ui.load_pages()
    per_row = 3
    for start in range(0, len(pages), per_row):
        cols = st.columns(per_row, gap="medium")
        for j, page in enumerate(pages[start : start + per_row]):
            with cols[j]:
                _md(
                    f'<div class="kaf-sp"><div class="kaf-sp__thumb" style="--i:{start + j}">'
                    f'<span>{_ESC(page["icon"])}</span></div><div class="kaf-sp__title">{_ESC(page["title"])}</div></div>'
                )
                if st.button(sp.get("button", "XEM ↗"), key=f"kaf_sp_{page['id']}", use_container_width=True):
                    _open_article(page)


def _qa(c: dict) -> None:
    q = c.get("qa", {})
    items = "".join(
        f'<li><div class="q"><b>{_ESC(q.get("q_mark", "Hỏi"))}</b><span>{_ESC(qq)}</span></div>'
        f'<div class="a"><b>{_ESC(q.get("a_mark", "Đáp"))}</b><span>{aa}</span></div></li>'
        for qq, aa in q.get("items", [])
    )
    contacts = "".join(
        f'<div class="kaf-contact"><div class="h">{_ESC(h)}</div><div class="v">{_ESC(v)}</div></div>'
        for h, v in q.get("contacts", [])
    )
    _md(
        _head("qa", q.get("label", "hỏi đáp"), q.get("en", ""), q.get("ja", ""))
        + f'<ul class="kaf-qa">{items}</ul><div class="kaf-contacts">{contacts}</div>'
    )


def _partners(c: dict) -> None:
    pt = c.get("partners", {})
    items = "".join(
        f'<a href="{_ESC(u)}" target="_blank" rel="noopener">{_ESC(n)}</a>' for n, u in pt.get("items", [])
    )
    _md(_h("partners.html", title=pt.get("title", ""), sub=pt.get("sub", ""), items_html=items))


def _footer(c: dict) -> None:
    f = c.get("footer", {})
    _md(
        _h(
            "footer.html",
            brand=f.get("brand", ""),
            label=f.get("label", ""),
            button=f.get("button", ""),
            href=f.get("href", "#"),
            copy=f.get("copy", ""),
        )
    )


# ---------------------------------------------------------------------------
# Dựng toàn trang (Bento Grid Analytics & Minimalist GIS Dashboard)
# ---------------------------------------------------------------------------
def build_kaf_page() -> dict:
    """Vẽ toàn bộ khung trang Bento Dashboard. Trả về {'surveillance','forecast','assistant'} là các st.container."""
    c = _content()
    sec: dict = {}
    _model_css()
    _page_video()
    _loader(c)
    _header(c)
    _hero(c)

    # 1. TỔNG QUAN (Bento Header Strip)
    with st.container(key="sec-outline"):
        _outline(c)

    # 2. GIÁM SÁT DỊCH TỄ GIS (Bản đồ + KPI + Bento Analytics)
    s = c.get("surveillance", {})
    with st.container(key="sec-surveillance"):
        _md(_head("surveillance", s.get("label", ""), s.get("en", ""), s.get("ja", "")) + _cards(s.get("cards", [])))
        sec["surveillance"] = st.container(key="body-surveillance")
        _md(_btn(s.get("cta", ""), s.get("cta_href", "#")))

    # 2b. DỰ BÁO AI (Gemini)
    f = c.get("forecast", {})
    with st.container(key="sec-forecast"):
        _md(_head("forecast", f.get("label", ""), f.get("en", ""), f.get("ja", "")) + _cards(f.get("cards", [])))
        sec["forecast"] = st.container(key="body-forecast")

    # 3. TRỢ LÝ AI
    a = c.get("ai", {})
    with st.container(key="sec-ai"):
        _md(
            _head("ai-assistant", a.get("label", ""), a.get("en", ""), a.get("ja", ""))
            + _item(a.get("item_tag", ""), a.get("item_icon", ""), a.get("item_name", ""), [a.get("item_note", "")])
        )
        sec["assistant"] = st.container(key="body-ai")

    # 4. BENTO ROW: CẨM NANG CẤP CỨU + TIN TỨC CẬP NHẬT
    g = c.get("guide", {})
    with st.container(key="bento-row-guide-news"):
        col_g, col_n = st.columns([1, 1], gap="medium")
        with col_g:
            with st.container(key="sec-guide"):
                _md(
                    _head("guide", g.get("label", ""), g.get("en", ""), g.get("ja", ""))
                    + _item(g.get("item_tag", ""), g.get("item_icon", ""), g.get("item_name", ""), g.get("item_notes", []))
                    + _note(g.get("foot", ""))
                )
        with col_n:
            with st.container(key="sec-news"):
                _news(c)

    # 5. KIẾN THỨC CHUYÊN ĐỀ (Thẻ + Dialog)
    with st.container(key="sec-special"):
        _special(c)

    # 6. BENTO ROW: HỎI ĐÁP NHANH + NGUỒN THAM KHẢO Y TẾ
    with st.container(key="bento-row-qa-partners"):
        col_q, col_p = st.columns([1, 1], gap="medium")
        with col_q:
            with st.container(key="sec-qa"):
                _qa(c)
        with col_p:
            with st.container(key="sec-partners"):
                _partners(c)

    # 7. FOOTER
    with st.container(key="sec-footer"):
        _footer(c)

    return sec
