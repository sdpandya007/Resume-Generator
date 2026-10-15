from __future__ import annotations

import base64
import datetime
import json
import re
from pathlib import Path

import streamlit as st

import resume_pdf as rp
from sample import SAMPLE

try:
    import pypdfium2 as pdfium
except Exception:  # preview falls back to an embedded PDF viewer
    pdfium = None

APP_DIR = Path(__file__).parent
st.set_page_config(page_title="Resume Builder", page_icon="📄", layout="wide")

TODAY = datetime.date.today().strftime("%d %b %Y")
SS = st.session_state

# --------------------------------------------------------------------------- #
# State model
# --------------------------------------------------------------------------- #
SIMPLE_DEFAULTS = {
    "name": "", "title": "", "email": "", "phone": "", "address": "",
    "linkedin": "", "github": "", "portfolio": "", "website": "",
    "summary_heading": "Professional Summary", "summary": "",
    "skills": "", "certifications": "", "achievements": "", "languages": "",
    "show_personal": False, "father_name": "", "dob": "", "gender": "",
    "marital_status": "", "nationality": "",
    "show_declaration": False, "place": "", "decl_date": TODAY,
}
ENTRY = {
    "exp": {"role": "", "company": "", "location": "", "start": "", "end": "", "current": False, "bullets": ""},
    "edu": {"degree": "", "institution": "", "year": "", "score": ""},
    "proj": {"name": "", "tech": "", "link": "", "desc": ""},
}
ENTRY_JSON_KEY = {"exp": "experience", "edu": "education", "proj": "projects"}
OPTIONS = {
    "gender": ["", "Male", "Female", "Other"],
    "marital_status": ["", "Unmarried", "Married", "Other"],
    "summary_heading": ["Professional Summary", "Career Objective", "Profile"],
}


def init_state():
    for k, v in SIMPLE_DEFAULTS.items():
        SS.setdefault(k, v)
    SS.setdefault("n_exp", 1)
    SS.setdefault("n_edu", 1)
    SS.setdefault("n_proj", 0)
    SS.setdefault("opt_template", "Modern")
    SS.setdefault("opt_accent_name", "Navy")
    SS.setdefault("opt_accent_custom", "#1F4E79")
    SS.setdefault("opt_paper", "A4")
    SS.setdefault("opt_scale", 1.0)
    SS.setdefault("opt_fit", True)
    SS.setdefault("opt_order", "Experienced")


def _clear_entry_keys():
    for k in list(SS.keys()):
        if re.match(r"^(exp|edu|proj)_\d+_", k):
            del SS[k]


def load_data(d: dict):
    _clear_entry_keys()
    for k, default in SIMPLE_DEFAULTS.items():
        v = d.get(k, default)
        if k in OPTIONS and v not in OPTIONS[k]:
            v = OPTIONS[k][0]
        SS[k] = bool(v) if isinstance(default, bool) else str(v if v is not None else "")
    if not SS["decl_date"]:
        SS["decl_date"] = TODAY
    for kind, fields in ENTRY.items():
        items = d.get(ENTRY_JSON_KEY[kind], []) or []
        SS[f"n_{kind}"] = len(items)
        for i, item in enumerate(items):
            for f, dv in fields.items():
                v = item.get(f, dv)
                SS[f"{kind}_{i}_{f}"] = bool(v) if isinstance(dv, bool) else str(v or "")


def collect() -> dict:
    data = {k: SS.get(k, v) for k, v in SIMPLE_DEFAULTS.items()}
    for kind, fields in ENTRY.items():
        items = []
        for i in range(SS.get(f"n_{kind}", 0)):
            item = {f: SS.get(f"{kind}_{i}_{f}", dv) for f, dv in fields.items()}
            if any(bool(v) and str(v).strip() for f, v in item.items() if f != "current") :
                items.append(item)
        data[ENTRY_JSON_KEY[kind]] = items
    return data


def add_entry(kind):
    SS[f"n_{kind}"] = SS.get(f"n_{kind}", 0) + 1


def remove_entry(kind, idx):
    n = SS.get(f"n_{kind}", 0)
    for j in range(idx, n - 1):
        for f, dv in ENTRY[kind].items():
            SS[f"{kind}_{j}_{f}"] = SS.get(f"{kind}_{j + 1}_{f}", dv)
    for f in ENTRY[kind]:
        SS.pop(f"{kind}_{n - 1}_{f}", None)
    SS[f"n_{kind}"] = max(0, n - 1)


def load_sample():
    load_data(SAMPLE)


def reset_all():
    for k in list(SS.keys()):
        del SS[k]


def load_uploaded():
    f = SS.get("json_up")
    if not f:
        return
    try:
        load_data(json.loads(f.getvalue().decode("utf-8")))
        SS["_load_msg"] = ("success", "Saved resume loaded.")
    except Exception:
        SS["_load_msg"] = ("error", "That file is not a valid saved resume (.json).")


# --------------------------------------------------------------------------- #
# Review / ATS checks
# --------------------------------------------------------------------------- #
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def review(data: dict, pages: int, photo_used: bool):
    """Return list of (ok: bool, message)."""
    checks = []
    checks.append((bool(data["name"].strip()), "Full name added"))
    checks.append((bool(data["title"].strip()), "Professional title added (recruiters scan this first)"))
    checks.append((bool(EMAIL_RE.match(data["email"].strip())), "Valid e-mail address"))
    digits = re.sub(r"\D", "", data["phone"])
    checks.append((len(digits) >= 8, "Phone number added"))
    words = len(data["summary"].split())
    checks.append((20 <= words <= 80, f"Summary of 20-80 words (currently {words})"))
    checks.append((bool(rp.lines(data["skills"])), "Skills listed (ATS matches keywords from the job post)"))
    exp = data["experience"]
    if exp:
        checks.append((all(len(rp.lines(e["bullets"])) >= 2 for e in exp), "Every job has at least 2 achievement bullets"))
        checks.append((any(re.search(r"\d", e["bullets"]) for e in exp), "Achievements include numbers (%, \u20b9, users, time saved)"))
    checks.append((bool(data["education"]), "Education added"))
    checks.append((any(data[k].strip() for k in ("linkedin", "github", "portfolio", "website")), "At least one professional link"))
    checks.append((pages <= 1, "Fits on one page" if pages <= 1 else f"Resume runs to {pages} pages - trim older/less relevant items"))
    return checks


# --------------------------------------------------------------------------- #
# UI helpers
# --------------------------------------------------------------------------- #
def local_css(name: str):
    css = (APP_DIR / name).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def entries_ui(kind: str, label: str, render, add_label: str):
    for i in range(SS.get(f"n_{kind}", 0)):
        with st.container(border=True):
            h1, h2 = st.columns([8, 1])
            h1.markdown(f"**{label} {i + 1}**")
            h2.button("✕", key=f"rm_{kind}_{i}", help="Remove this entry", on_click=remove_entry, args=(kind, i))
            render(i)
    st.button(add_label, key=f"add_{kind}", on_click=add_entry, args=(kind,))


def render_exp(i):
    k = lambda f: f"exp_{i}_{f}"
    c1, c2 = st.columns(2)
    c1.text_input("Job title", key=k("role"), placeholder="e.g., Marketing Executive")
    c2.text_input("Company", key=k("company"), placeholder="e.g., Tata Consultancy Services")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    c1.text_input("Location", key=k("location"), placeholder="City")
    c2.text_input("Start", key=k("start"), placeholder="Jan 2022")
    c3.text_input("End", key=k("end"), placeholder="Dec 2024", disabled=SS.get(k("current"), False))
    c4.checkbox("Currently working here", key=k("current"))
    st.text_area(
        "Achievements / responsibilities (one per line)", key=k("bullets"), height=130,
        placeholder="Increased monthly leads by 35% through targeted email campaigns\nManaged a team of 4 and a ₹12L annual budget",
        help="Start with an action verb (Led, Built, Reduced...) and add numbers wherever possible.",
    )


def render_edu(i):
    k = lambda f: f"edu_{i}_{f}"
    c1, c2, c3, c4 = st.columns([3, 4, 1.4, 2])
    c1.text_input("Qualification", key=k("degree"), placeholder="B.Com / 12th / 10th")
    c2.text_input("Institution / Board", key=k("institution"), placeholder="University / CBSE Board")
    c3.text_input("Year", key=k("year"), placeholder="2022")
    c4.text_input("Score", key=k("score"), placeholder="8.2 CGPA / 82%")


def render_proj(i):
    k = lambda f: f"proj_{i}_{f}"
    c1, c2 = st.columns(2)
    c1.text_input("Project name", key=k("name"), placeholder="e.g., Online Store")
    c2.text_input("Technologies / tools", key=k("tech"), placeholder="Python, MySQL")
    st.text_input("Link (optional)", key=k("link"), placeholder="github.com/you/project")
    st.text_area("What it does / your impact (one per line)", key=k("desc"), height=90)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
init_state()
local_css("style.css")

# ----- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📄 Resume Builder")
    st.caption("ATS-friendly PDF resumes in minutes.")
    st.button("✨ Fill with sample data", on_click=load_sample, help="See how a finished resume looks, then edit it.")
    st.button("🗑 Clear everything", on_click=reset_all)
    st.divider()
    st.markdown("**Save your progress**")
    st.download_button(
        "💾 Save as .json", json.dumps(collect(), indent=2, ensure_ascii=False),
        file_name="my_resume_data.json", mime="application/json",
    )
    st.file_uploader("Load saved progress", type="json", key="json_up", on_change=load_uploaded)
    if "_load_msg" in SS:
        kind, msg = SS.pop("_load_msg")
        getattr(st, kind)(msg)
    st.divider()
    st.markdown(
        "**Tips that get interviews**\n"
        "- Tailor skills to each job post\n"
        "- Quantify results (%, ₹, time saved)\n"
        "- Keep it to 1 page (2 if 8+ years)\n"
        "- Use a professional e-mail address\n"
        "- Send as PDF, name it *YourName_Resume.pdf*"
    )
    st.caption("Your data stays in your browser session - nothing is stored on a server.")

st.title("Professional Resume Builder")
st.caption("Fill the tabs on the left - the preview on the right updates as you type.")

left, right = st.columns([1.1, 1], gap="large")

# ----- Left: editor ------------------------------------------------------------
with left:
    t_basic, t_exp, t_edu, t_skill, t_extra, t_design = st.tabs(
        ["👤 Basics", "💼 Experience", "🎓 Education", "🛠 Skills & Projects", "📋 Personal", "🎨 Design"]
    )

    with t_basic:
        c1, c2 = st.columns(2)
        c1.text_input("Full name *", key="name", placeholder="e.g., Priya Sharma")
        c2.text_input("Professional title *", key="title", placeholder="e.g., Senior Accountant")
        c1, c2 = st.columns(2)
        c1.text_input("Phone *", key="phone", placeholder="+91 98765 43210")
        c2.text_input("E-mail *", key="email", placeholder="priya.sharma@gmail.com")
        st.text_area("Address", key="address", height=80, placeholder="City, State, Country (full street address is optional)")
        st.markdown("**Links** (optional - enter without `https://`)")
        c1, c2 = st.columns(2)
        c1.text_input("LinkedIn", key="linkedin", placeholder="linkedin.com/in/username")
        c2.text_input("GitHub", key="github", placeholder="github.com/username")
        c1.text_input("Portfolio", key="portfolio", placeholder="yourportfolio.com")
        c2.text_input("Website", key="website", placeholder="yourwebsite.com")
        st.selectbox("Summary heading", OPTIONS["summary_heading"], key="summary_heading",
                     help="Freshers often prefer 'Career Objective'.")
        st.text_area("Summary", key="summary", height=120,
                     placeholder="2-3 sentences: who you are, your strongest skills, and what you want next.")
        st.caption(f"{len(SS.get('summary', '').split())} words - aim for 30-60.")
        st.file_uploader(
            "Photo (optional)", type=["jpg", "jpeg", "png"], key="photo",
            help="Common in India, Middle East and parts of Europe. Leave empty for US/UK/Canada applications.",
        )

    with t_exp:
        st.caption("Most recent job first. Freshers can skip this tab and switch the layout in **Design**.")
        entries_ui("exp", "Experience", render_exp, "➕ Add experience")

    with t_edu:
        entries_ui("edu", "Education", render_edu, "➕ Add education")
        st.text_area("Certifications & training (one per line)", key="certifications", height=100,
                     placeholder="AWS Certified Cloud Practitioner (2023)\nAdvanced Excel - Coursera (2022)")

    with t_skill:
        st.text_area(
            "Skills (one group per line)", key="skills", height=120,
            placeholder="Languages: Python, SQL\nTools: Excel, Tally, Power BI\nSoft skills: Communication, Teamwork",
            help="Use 'Category: item, item' for grouped skills, or just one skill list per line.",
        )
        st.markdown("**Projects** (optional)")
        entries_ui("proj", "Project", render_proj, "➕ Add project")
        st.text_area("Achievements & activities (one per line)", key="achievements", height=90,
                     placeholder="Winner, Inter-college Hackathon 2023")

    with t_extra:
        st.caption("Common on Indian resumes. Switch it off for most international applications.")
        st.toggle("Include personal details section", key="show_personal")
        if SS.get("show_personal"):
            c1, c2 = st.columns(2)
            c1.text_input("Father's name", key="father_name")
            c2.text_input("Date of birth", key="dob", placeholder="07 Aug 1999")
            c1.selectbox("Gender", OPTIONS["gender"], key="gender", format_func=lambda x: x or "- not shown -")
            c2.selectbox("Marital status", OPTIONS["marital_status"], key="marital_status",
                         format_func=lambda x: x or "- not shown -")
            c1.text_input("Nationality", key="nationality", placeholder="Indian")
        st.text_input("Languages known", key="languages", placeholder="English, Hindi, Gujarati")
        st.toggle("Include declaration & signature block", key="show_declaration")
        if SS.get("show_declaration"):
            c1, c2 = st.columns(2)
            c1.text_input("Place", key="place", placeholder="Mumbai")
            c2.text_input("Date", key="decl_date")

    with t_design:
        st.selectbox("Template", list(rp.TEMPLATES), key="opt_template")
        st.caption(rp.TEMPLATES[SS["opt_template"]]["about"])
        names = list(rp.ACCENT_PRESETS) + ["Custom"]
        st.selectbox("Accent colour", names, key="opt_accent_name")
        if SS["opt_accent_name"] == "Custom":
            st.color_picker("Pick colour", key="opt_accent_custom")
        c1, c2 = st.columns(2)
        c1.selectbox("Paper size", list(rp.PAGE_SIZES), key="opt_paper")
        c2.selectbox("Layout", ["Experienced", "Fresher"], key="opt_order",
                     help="Experienced: work history first. Fresher: education first.")
        st.slider("Text size", 0.85, 1.15, key="opt_scale", step=0.05)
        st.toggle("Shrink to fit on one page", key="opt_fit",
                  help="Automatically reduces spacing/text size (down to about 76%) if content overflows.")

# ----- Right: preview & download -----------------------------------------------
data = collect()
accent = rp.ACCENT_PRESETS.get(SS["opt_accent_name"]) or SS["opt_accent_custom"]

photo_bytes = None
up = SS.get("photo")
if up is not None:
    try:
        photo_bytes = rp.process_photo(up.getvalue())
    except Exception:
        st.sidebar.error("Could not read that photo - try a different JPG/PNG.")

try:
    pdf_bytes, pages, used_scale = rp.build_resume(
        data, template=SS["opt_template"], accent=accent, paper=SS["opt_paper"],
        font_scale=SS["opt_scale"], fit_one_page=SS["opt_fit"], order=SS["opt_order"], photo=photo_bytes,
    )
    build_error = None
except Exception as e:  # never crash the app on odd input
    pdf_bytes, pages, used_scale, build_error = b"", 1, 1.0, e

with right:
    st.markdown('<div class="preview-marker"></div>', unsafe_allow_html=True)
    if build_error:
        st.error(f"Could not build the PDF: {build_error}")
    else:
        safe = re.sub(r"[^A-Za-z0-9]+", "_", data["name"]).strip("_") or "My"
        ready = bool(data["name"].strip())
        st.download_button(
            "⬇ Download PDF resume", pdf_bytes, file_name=f"{safe}_Resume.pdf", mime="application/pdf",
            type="primary", disabled=not ready, help=None if ready else "Enter your name first",
        )
        info = f"{pages} page{'s' if pages != 1 else ''}"
        if used_scale < SS["opt_scale"]:
            info += f" · auto-shrunk to {int(used_scale * 100)}% to fit"
        st.caption(info)

        checks = review(data, pages, photo_bytes is not None)
        passed = sum(ok for ok, _ in checks)
        with st.expander(f"Resume check - {passed}/{len(checks)} passed", expanded=False):
            st.progress(passed / len(checks))
            for ok, msg in checks:
                st.markdown(f"{'✅' if ok else '⚠️'} {msg}")
        bad = rp.find_unsupported(data)
        if bad:
            st.warning("These characters can't be printed in the PDF and were removed: " + " ".join(bad[:15]))

        if pdfium is not None:
            pdf_doc = pdfium.PdfDocument(pdf_bytes)
            for i in range(len(pdf_doc)):
                st.image(pdf_doc[i].render(scale=1.6).to_pil())
        else:
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900" style="border:0"></iframe>',
                unsafe_allow_html=True,
            )
