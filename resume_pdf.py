"""
resume_pdf.py - PDF engine for the Resume Builder.

* Text-based, single-column layouts (readable by Applicant Tracking Systems).
* Automatic text wrapping, page breaks and "fit to one page" shrinking.
* Clickable links (e-mail, LinkedIn, GitHub, portfolio, website).
* Three templates: Modern, Professional, Classic.
"""
from __future__ import annotations

import io
import re
from xml.sax.saxutils import escape

from PIL import Image, ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PAGE_SIZES = {"A4": A4, "Letter": letter}

TEMPLATES = {
    "Modern": {
        "font": "Helvetica", "bold": "Helvetica-Bold", "italic": "Helvetica-Oblique",
        "header": "band",
        "about": "Coloured header band with your name. Clean and contemporary.",
    },
    "Professional": {
        "font": "Helvetica", "bold": "Helvetica-Bold", "italic": "Helvetica-Oblique",
        "header": "left",
        "about": "Left-aligned header with an accent rule. Safe choice for any industry.",
    },
    "Classic": {
        "font": "Times-Roman", "bold": "Times-Bold", "italic": "Times-Italic",
        "header": "center",
        "about": "Serif font and centred header. Traditional - law, finance, government, academia.",
    },
}

ACCENT_PRESETS = {
    "Navy": "#1F4E79",
    "Teal": "#0F766E",
    "Crimson": "#9B1C31",
    "Forest": "#1F6F43",
    "Purple": "#5B3E96",
    "Charcoal": "#2B2B2B",
}

DARK = colors.HexColor("#1F2933")
GREY = colors.HexColor("#52606D")

# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
# Built-in PDF fonts only cover Latin-1/cp1252. Swap a few common symbols and
# drop anything else so users never see black boxes in the PDF.
_REPLACE = {"\u20b9": "Rs. ", "\u00a0": " ", "\u2011": "-", "\u2192": "->", "\t": " "}
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f]")
_BULLET_LEAD = re.compile(r"^[\s\-\*\u2022\u00b7\u25aa\u25cf\u2013\u2014]+")


def clean(text) -> str:
    t = str(text or "")
    for a, b in _REPLACE.items():
        t = t.replace(a, b)
    t = _CTRL.sub("", t)
    return t.encode("cp1252", "ignore").decode("cp1252")


def esc(text) -> str:
    return escape(clean(text), {'"': "&quot;"})


def find_unsupported(data) -> list[str]:
    """Characters in the user's data that the PDF fonts cannot print."""
    found: set[str] = set()

    def walk(x):
        if isinstance(x, str):
            t = x
            for a in _REPLACE:
                t = t.replace(a, "")
            for ch in t:
                try:
                    ch.encode("cp1252")
                except UnicodeEncodeError:
                    found.add(ch)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)

    walk(data)
    return sorted(found)


def lines(text) -> list[str]:
    out = []
    for ln in (text or "").splitlines():
        ln = _BULLET_LEAD.sub("", ln).strip()
        if ln:
            out.append(ln)
    return out


def normalize_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    return u if re.match(r"^(https?://|mailto:)", u, re.I) else "https://" + u


def display_url(u: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", (u or "").strip(), flags=re.I).rstrip("/")


def _hex(c) -> str:
    return "#%02x%02x%02x" % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))


def _lum(c) -> float:
    return 0.2126 * c.red + 0.7152 * c.green + 0.0722 * c.blue


def _tint(c, t: float):
    return colors.Color(c.red + (1 - c.red) * t, c.green + (1 - c.green) * t, c.blue + (1 - c.blue) * t)


def process_photo(raw: bytes) -> bytes:
    """Square-crop (slightly top-biased, for portraits) and shrink to a JPEG."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    w, h = img.size
    m = min(w, h)
    left = (w - m) // 2
    top = int((h - m) * 0.2)
    img = img.crop((left, top, left + m, top + m)).resize((360, 360), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=88)
    return out.getvalue()


# --------------------------------------------------------------------------- #
# Story builder
# --------------------------------------------------------------------------- #
def _no_pad(extra=()):
    return TableStyle(
        [
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            *extra,
        ]
    )


def _build_story(d, th, accent, width, scale, photo, order):
    s = scale
    f, fb, fi = th["font"], th["bold"], th["italic"]
    base = 9.7 * s
    lead = base * 1.33

    body = ParagraphStyle("body", fontName=f, fontSize=base, leading=lead, textColor=DARK)
    bullet = ParagraphStyle(
        "bullet", parent=body, leftIndent=11, bulletIndent=1, bulletFontName=f, bulletFontSize=base,
        spaceAfter=0.6,
    )
    role = ParagraphStyle("role", parent=body, fontName=fb, fontSize=base + 0.5)
    right = ParagraphStyle("right", parent=body, fontName=fb, alignment=TA_RIGHT, textColor=GREY, fontSize=base - 0.2)
    sub = ParagraphStyle("sub", parent=body, fontName=fi, textColor=GREY)
    head = ParagraphStyle(
        "head", parent=body, fontName=fb, fontSize=base + 1.8, leading=(base + 1.8) * 1.2,
        textColor=accent, charSpace=0.7,
    )
    cellb = ParagraphStyle("cellb", parent=body, fontName=fb, fontSize=base - 0.3, leading=(base - 0.3) * 1.25)
    cell = ParagraphStyle("cell", parent=body, fontSize=base - 0.3, leading=(base - 0.3) * 1.25)

    kind = th["header"]
    on_band = kind == "band"
    band_text = DARK if _lum(accent) >= 0.6 else colors.white
    htxt = band_text if on_band else DARK
    link_col = _hex(band_text) if on_band else _hex(accent)

    def link(url, label):
        return f'<link href="{esc(normalize_url(url))}" color="{link_col}">{esc(label)}</link>'

    # ------------------------------------------------------------- header
    align = TA_CENTER if kind == "center" else TA_LEFT
    name_style = ParagraphStyle(
        "name", fontName=fb, fontSize=(24 if kind == "center" else 22) * s, leading=28 * s, alignment=align,
        textColor=htxt if on_band else (accent if kind == "left" else DARK),
    )
    title_style = ParagraphStyle(
        "title", fontName=fi if kind == "center" else f, fontSize=11.5 * s, leading=15 * s, alignment=align,
        textColor=htxt if on_band else GREY,
    )
    contact_style = ParagraphStyle(
        "contact", fontName=f, fontSize=base - 0.3, leading=(base - 0.3) * 1.45, alignment=align,
        textColor=htxt if on_band else colors.HexColor("#323F4B"),
    )

    sep = " &nbsp;|&nbsp; "
    contact = []
    if d.get("phone"):
        contact.append(esc(d["phone"]))
    if d.get("email"):
        contact.append(f'<link href="mailto:{esc(d["email"])}" color="{link_col}">{esc(d["email"])}</link>')
    addr = ", ".join(x.strip() for x in (d.get("address") or "").splitlines() if x.strip())
    if addr:
        contact.append(esc(addr))
    links = []
    for label, key in (("LinkedIn", "linkedin"), ("GitHub", "github"), ("Portfolio", "portfolio"), ("Website", "website")):
        if d.get(key, "").strip():
            links.append(f"<b>{label}:</b> " + link(d[key], display_url(d[key])))

    text_block = [Paragraph(esc(d.get("name", "")), name_style)]
    if d.get("title"):
        text_block.append(Paragraph(esc(d["title"]), title_style))
    text_block.append(Spacer(1, 3 * s))
    if contact:
        text_block.append(Paragraph(sep.join(contact), contact_style))
    if links:
        text_block.append(Paragraph(sep.join(links), contact_style))

    pw = 27 * mm
    img = RLImage(io.BytesIO(photo), pw, pw) if photo else None
    story = []
    if on_band:
        cells, widths = ([[text_block, img]], [width - pw, pw]) if img else ([[text_block]], [width])
        t = Table(cells, colWidths=widths, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(t)
    else:
        if img and kind == "center":
            cells, widths = [[None, text_block, img]], [pw, width - 2 * pw, pw]
        elif img:
            cells, widths = [[text_block, img]], [width - pw - 4 * mm, pw + 4 * mm]
        else:
            cells, widths = [[text_block]], [width]
        t = Table(cells, colWidths=widths, hAlign="LEFT")
        t.setStyle(_no_pad([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story += [t, Spacer(1, 3), HRFlowable(width="100%", thickness=1.4, color=accent, spaceAfter=1)]

    # ------------------------------------------------------------ helpers
    def section(title, entries):
        """entries: list of lists of flowables. Heading stays with first entry."""
        if not entries:
            return []
        hd = [
            Paragraph(esc(title.upper()), head),
            HRFlowable(width="100%", thickness=0.7, color=accent, spaceBefore=1.5, spaceAfter=3.5),
        ]
        out = [Spacer(1, 6 * s), KeepTogether(hd + entries[0])]
        for e in entries[1:]:
            out.append(Spacer(1, 3.2 * s))
            out.append(KeepTogether(e))
        return out

    def row(left_html, right_html, rw=42 * mm):
        t = Table(
            [[Paragraph(left_html, role), Paragraph(right_html, right)]],
            colWidths=[width - rw, rw], hAlign="LEFT",
        )
        t.setStyle(_no_pad())
        return t

    def bullets(items):
        return [Paragraph(esc(x), bullet, bulletText="\u2022") for x in items]

    # ----------------------------------------------------------- sections
    def sec_summary():
        txt = (d.get("summary") or "").strip()
        if not txt:
            return []
        return section(d.get("summary_heading") or "Professional Summary", [[Paragraph(esc(txt).replace("\n", "<br/>"), body)]])

    def sec_skills():
        entries = []
        for ln in lines(d.get("skills")):
            if ":" in ln:
                cat, items = ln.split(":", 1)
                entries.append([Paragraph(f"<b>{esc(cat.strip())}:</b> {esc(items.strip())}", body)])
            else:
                entries.append([Paragraph(esc(ln), body)])
        if not entries:
            return []
        out = section("Skills", entries[:1])
        for e in entries[1:]:
            out += [Spacer(1, 1.5 * s)] + e
        return out

    def sec_experience():
        entries = []
        for e in d.get("experience", []):
            dates = " - ".join(x for x in (e.get("start", "").strip(), "Present" if e.get("current") else e.get("end", "").strip()) if x)
            dates = dates.replace(" - ", " \u2013 ")
            blk = [row(esc(e.get("role", "")), esc(dates))]
            who = ", ".join(x for x in (e.get("company", "").strip(), e.get("location", "").strip()) if x)
            if who:
                blk.append(Paragraph(esc(who), sub))
            blk.append(Spacer(1, 1.5 * s))
            blk += bullets(lines(e.get("bullets")))
            entries.append(blk)
        return section("Work Experience", entries)

    def sec_projects():
        entries = []
        for p in d.get("projects", []):
            left = f"<b>{esc(p.get('name', ''))}</b>"
            if p.get("tech", "").strip():
                left += f' <font name="{fi}" color="{_hex(GREY)}">| {esc(p["tech"])}</font>'
            right_html = link(p["link"], display_url(p["link"])) if p.get("link", "").strip() else ""
            rs = ParagraphStyle("rl", parent=right, textColor=accent)
            t = Table([[Paragraph(left, body), Paragraph(right_html, rs)]], colWidths=[width - 55 * mm, 55 * mm], hAlign="LEFT")
            t.setStyle(_no_pad())
            blk = [t, Spacer(1, 1.2 * s)] + bullets(lines(p.get("desc")))
            entries.append(blk)
        return section("Projects", entries)

    def sec_education():
        rows = [d_ for d_ in d.get("education", [])]
        if not rows:
            return []
        data = [[Paragraph(h, cellb) for h in ("Qualification", "Institution / Board", "Year", "Score")]]
        for e in rows:
            data.append([
                Paragraph(esc(e.get("degree", "")), cell),
                Paragraph(esc(e.get("institution", "")), cell),
                Paragraph(esc(e.get("year", "")), cell),
                Paragraph(esc(e.get("score", "")), cell),
            ])
        t = Table(data, colWidths=[width * x for x in (0.30, 0.42, 0.11, 0.17)], hAlign="LEFT", repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _tint(accent, 0.88)),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C0CC")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
                ]
            )
        )
        return section("Education", [[t]])

    def bullet_section(title, key):
        items = lines(d.get(key))
        return section(title, [bullets(items)]) if items else []

    def sec_personal():
        if not d.get("show_personal"):
            return []
        pairs = [
            ("Father's Name", d.get("father_name")), ("Date of Birth", d.get("dob")),
            ("Gender", d.get("gender")), ("Marital Status", d.get("marital_status")),
            ("Nationality", d.get("nationality")), ("Languages Known", d.get("languages")),
        ]
        pairs = [(a, b) for a, b in pairs if (b or "").strip()]
        if not pairs:
            return []
        t = Table(
            [[Paragraph(f"<b>{a}</b>", body), Paragraph(":&nbsp; " + esc(b), body)] for a, b in pairs],
            colWidths=[38 * mm, width - 38 * mm], hAlign="LEFT",
        )
        t.setStyle(_no_pad([("BOTTOMPADDING", (0, 0), (-1, -1), 1.2)]))
        return section("Personal Details", [[t]])

    def sec_languages():
        # Languages shown as their own line when personal block is hidden.
        if d.get("show_personal") or not (d.get("languages") or "").strip():
            return []
        return section("Languages", [[Paragraph(esc(d["languages"]), body)]])

    def sec_declaration():
        if not d.get("show_declaration"):
            return []
        place = (d.get("place") or "").strip()
        date = (d.get("decl_date") or "").strip()
        left = []
        if place:
            left.append(f"<b>Place:</b> {esc(place)}")
        if date:
            left.append(f"<b>Date:</b> {esc(date)}")
        sig = ParagraphStyle("sig", parent=body, alignment=TA_RIGHT)
        t = Table(
            [[Paragraph("<br/>".join(left), body), Paragraph(f"<br/><br/><b>({esc(d.get('name', ''))})</b>", sig)]],
            colWidths=[width / 2, width / 2], hAlign="LEFT",
        )
        t.setStyle(_no_pad())
        decl = Paragraph("I hereby declare that the information given above is true and correct to the best of my knowledge.", body)
        return section("Declaration", [[decl, Spacer(1, 4 * s), t]])

    builders = {
        "summary": sec_summary,
        "skills": sec_skills,
        "experience": sec_experience,
        "projects": sec_projects,
        "education": sec_education,
        "certifications": lambda: bullet_section("Certifications & Training", "certifications"),
        "achievements": lambda: bullet_section("Achievements & Activities", "achievements"),
        "languages": sec_languages,
        "personal": sec_personal,
        "declaration": sec_declaration,
    }
    if order == "Fresher":
        seq = ["summary", "education", "skills", "projects", "experience", "certifications", "achievements"]
    else:
        seq = ["summary", "skills", "experience", "projects", "education", "certifications", "achievements"]
    seq += ["languages", "personal", "declaration"]
    for key in seq:
        story += builders[key]()
    return story


def _build_once(d, template, accent, pagesize, scale, photo, order):
    th = TEMPLATES[template]
    margin = (16 if scale >= 0.95 else 13 if scale >= 0.88 else 11) * mm
    width = pagesize[0] - 2 * margin
    buf = io.BytesIO()
    name = clean(d.get("name", "")).strip()
    doc = SimpleDocTemplate(
        buf, pagesize=pagesize, leftMargin=margin, rightMargin=margin, topMargin=margin,
        bottomMargin=margin, title=f"{name} - Resume" if name else "Resume", author=name, subject="Resume",
    )

    def footer(canvas, dc):
        canvas.saveState()
        canvas.setFont(th["font"], 7.5)
        canvas.setFillColor(GREY)
        canvas.drawCentredString(pagesize[0] / 2, 7 * mm, f"{name} - Page {dc.page}" if name else f"Page {dc.page}")
        canvas.restoreState()

    story = _build_story(d, th, accent, width, scale, photo, order)
    doc.build(story, onLaterPages=footer)
    return buf.getvalue(), doc.page


def build_resume(
    data: dict,
    template: str = "Modern",
    accent: str = "#1F4E79",
    paper: str = "A4",
    font_scale: float = 1.0,
    fit_one_page: bool = True,
    order: str = "Experienced",
    photo: bytes | None = None,
):
    """Return (pdf_bytes, page_count, scale_used)."""
    pagesize = PAGE_SIZES.get(paper, A4)
    try:
        acc = colors.HexColor(accent)
    except Exception:
        acc = colors.HexColor("#1F4E79")
    scales = [font_scale]
    if fit_one_page:
        scales = [font_scale] + [x for x in (0.96, 0.92, 0.88, 0.84, 0.80, 0.76) if x < font_scale]
    result = None
    for sc in scales:
        pdf, pages = _build_once(data, template, acc, pagesize, sc, photo, order)
        result = (pdf, pages, sc)
        if pages <= 1:
            break
    return result
