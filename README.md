# 📄 Resume Builder

A Streamlit web app that builds **ATS-friendly, text-based PDF resumes** in minutes.
Fill in the tabs on the left, watch the live preview on the right, and download a
polished one-page PDF — all running locally in your browser session.

---

## ✨ Features

- **Live preview** — the PDF on the right updates as you type.
- **3 templates** — Modern (coloured header band), Professional (left-aligned
  with accent rule), Classic (serif, centred header for law/finance/academia).
- **6 accent colours** + custom colour picker.
- **A4 & Letter** paper sizes.
- **Auto-fit to one page** — automatically shrinks spacing and text size
  (down to ~76%) if content overflows.
- **Fresher / Experienced layouts** — reorder sections to put education first
  or work history first.
- **Clickable links** — e-mail, LinkedIn, GitHub, portfolio, and website are
  embedded as real hyperlinks in the PDF.
- **Photo support** (optional) — auto-cropped square, top-biased for portraits.
- **ATS-friendly** — text-based, single-column layouts, standard section
  headings, keyword matching hints.
- **Resume check** — a built-in checklist (name, contact, summary length,
  quantified achievements, one-page fit, etc.) with a pass score.
- **Personal details & declaration blocks** — common on Indian / Middle East
  resumes, easily toggled off for US/UK/Canada applications.
- **Save / load progress** — export your data as `.json` and reload it later.
- **Character sanitizer** — flags and strips characters the built-in PDF fonts
  can't print, so you never see black boxes.
- **No server storage** — everything stays in your Streamlit session.

---

## 🗂 Project structure
.
├── app.py # Streamlit UI + state management
├── resume_pdf.py # PDF engine (ReportLab)
├── sample.py # Sample data ("✨ Fill with sample data")
├── style.css # Custom styling for the Streamlit UI
├── requirements.txt # Python dependencies
└── README.md

text

---

## 🚀 Getting started

### 1. Requirements

- Python **3.9+** (3.10 or 3.11 recommended)
- pip

### 2. Install dependencies

```bash
pip install -r requirements.txt
If you don't have a requirements.txt yet, create one with:

txt
streamlit
reportlab
pillow
pypdfium2
pypdfium2 is optional — app.py falls back to an embedded PDF viewer
(iframe) if it isn't installed, but the in-app preview is nicer with it.

3. Run the app
bash
streamlit run app.py
Then open the URL Streamlit prints (usually http://localhost:8501).

🧭 How to use
Start with sample data (optional) — click ✨ Fill with sample data in
the sidebar to see a finished resume, then edit it.

Fill the tabs on the left:

👤 Basics — name, title, phone, e-mail, address, links, summary, photo.

💼 Experience — most recent job first; one achievement per line.

🎓 Education — qualification, institution, year, score; plus
certifications.

🛠 Skills & Projects — grouped skills (Category: item, item) and
optional project entries.

📋 Personal — optional personal details, languages, declaration block.

🎨 Design — template, accent colour, paper size, layout order, text
size, fit-to-one-page.

Watch the preview on the right and the Resume check score.

Download the PDF — it's named YourName_Resume.pdf.

Save your progress as .json from the sidebar if you want to come back
later.

📝 Tips that get interviews
Tailor skills to each job post — ATS matches keywords.

Quantify results: %, ₹, users, time saved, revenue.

Keep it to 1 page (2 if you have 8+ years of experience).

Use a professional e-mail address.

Name the file YourName_Resume.pdf, not resume_final_v3.pdf.

For US / UK / Canada applications: turn off Personal details,
Declaration, and leave the photo empty.

For India / Middle East applications: photo, personal details, and
declaration are common and can be left on.

🎨 Templates
Template	Font	Header	Best for
Modern	Helvetica	Coloured band	Tech, startups, product, design
Professional	Helvetica	Left-aligned with accent rule	Any industry — safe default
Classic	Times	Centred	Law, finance, government, academia
Accent presets: Navy, Teal, Crimson, Forest, Purple, Charcoal — or pick your own.

🧩 Section order
Experienced layout:
Summary → Skills → Experience → Projects → Education → Certifications → Achievements → Languages → Personal → Declaration

Fresher layout:
Summary → Education → Skills → Projects → Experience → Certifications → Achievements → Languages → Personal → Declaration

Switch between them in the 🎨 Design tab.

🔒 Privacy
Everything runs locally. Your data is kept only in your Streamlit session
(st.session_state) — nothing is written to disk or sent to a server. The
.json save file is generated in your browser and downloaded directly.

🛠 Troubleshooting
FileNotFoundError: style.css
Make sure style.css exists next to app.py. If you don't want to use it,
patch local_css in app.py to skip missing files:

python
def local_css(name: str):
    path = APP_DIR / name
    if not path.exists():
        return
    css = path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
Black boxes in the PDF
The built-in PDF fonts (Helvetica / Times) only cover Latin-1 / cp1252. The
app already swaps common symbols (₹ → Rs., → arrows, etc.) and warns you
about anything else it had to drop. Stick to English characters for best
results.

Preview is blank / shows an iframe instead of pages
Install pypdfium2:

bash
pip install pypdfium2
Photo doesn't appear
Use a JPG or PNG. The image is auto-cropped square and converted to JPEG.

"Resume runs to 2 pages" warning
Either trim older/less relevant items, or make sure Shrink to fit on one page
is enabled in the 🎨 Design tab.

📦 Dependencies
Package	Purpose
streamlit	Web UI
reportlab	PDF generation
pillow	Photo cropping / resizing
pypdfium2	In-app PDF page preview (optional)
📄 License
Add your preferred license here (MIT, Apache-2.0, etc.).
The sample data in sample.py is fictional and for demonstration only.

🙌 Contributing
Pull requests are welcome. Ideas for future templates, additional section
types, or export formats (DOCX, Markdown) are especially appreciated.

Built with Streamlit · ReportLab · Pillow

text

---

## Notes

- The **Troubleshooting** section covers the exact `FileNotFoundError` you hit, plus the common issues users run into with this app (font/character errors, missing `pypdfium2`, multi-page overflow).
- The **templates table** and **section order** reflect exactly what's defined in `resume_pdf.py` and `app.py` — no invented features.
- I marked `pypdfium2` as optional, matching the `try/except` in `app.py`.
- Add a real **license** line if you plan to publish this on GitHub.

Save it as `README.md` next to `app.py` and GitHub (or any Markdown viewer) will render it nicely.
