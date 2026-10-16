# 📄 Resume Builder

A Streamlit web app that turns a simple form into a clean, professional, **ATS-friendly PDF resume**, with a live preview that updates as you type.

## Features

- **Live preview** next to the editor, with one-click PDF download
- **3 templates**: Modern (colour header band), Professional (accent rule), Classic (serif, centred)
- **Accent colours**: 6 presets plus a custom colour picker
- **Experienced / Fresher layouts**: work history first, or education first
- **Shrink to fit one page**: spacing and text size reduce automatically if content overflows
- **Sections**: summary/objective, skills, work experience, projects, education table, certifications, achievements, languages
- **Personal details and declaration block** (optional, common on Indian resumes)
- **Clickable links** for e-mail, LinkedIn, GitHub, portfolio and website
- **Optional photo**, auto square-cropped
- **Resume check**: a checklist covering name, valid e-mail, summary length, achievement bullets with numbers, links and page count
- **Save / load progress** as a `.json` file
- **Sample data** button to see a finished resume instantly
- Text-based PDF, single column: readable by Applicant Tracking Systems (ATS)

## Project structure

```
resume_generator/
├── app.py            # Streamlit UI (tabs, state, preview, download)
├── resume_pdf.py     # PDF engine (ReportLab): templates, layout, page fitting
├── sample.py         # Sample resume data
├── style.css         # Page styling (sticky preview, buttons, etc.)
├── requirements.txt
└── .streamlit/
    └── config.toml   # Theme
```

## Getting started

Requires **Python 3.9+**.

```bash
# 1. (optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## How to use

1. Click **Fill with sample data** in the sidebar to see how it works, or start typing in the tabs.
2. Work through **Basics → Experience → Education → Skills & Projects → Personal → Design**.
3. Watch the preview on the right and open **Resume check** for improvement tips.
4. Click **Download PDF resume**.
5. Use **Save as .json** to continue editing later (upload it via *Load saved progress*).

## Tips for a resume that gets interviews

- Tailor the **Skills** section to keywords in each job post
- Start bullets with action verbs and **add numbers** (e.g. "Reduced load time by 45%")
- Keep it to **one page** unless you have 8+ years of experience
- Skip the photo and personal-details section for US/UK/Canada applications
- Use a professional e-mail address and name the file `YourName_Resume.pdf`

## Deployment

**Streamlit Community Cloud**

1. Push this folder to a GitHub repository.
2. Go to <https://share.streamlit.io>, choose the repo, and set the main file to `app.py`.

**Docker (example)**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

## Customisation

| Want to change | Where |
|---|---|
| Add an accent colour | `ACCENT_PRESETS` in `resume_pdf.py` |
| Add or edit a template | `TEMPLATES` in `resume_pdf.py` (header styles: `band`, `left`, `center`) |
| Add a new section | Add a builder in `_build_story` and include it in the section order list, then add inputs in `app.py` |
| Change the app look | `style.css` and `.streamlit/config.toml` |
| Change the sample resume | `sample.py` |

## Known limitations

- PDFs use built-in fonts (Helvetica / Times), which cover Latin characters only. Other scripts (e.g. Hindi, Chinese) and the ₹ symbol in PDF text are not supported; `₹` is converted to `Rs.` and unsupported characters are removed, with a warning shown in the app. To support other scripts, register a Unicode TTF font (e.g. Noto Sans) with ReportLab.
- PDF output only (no Word/DOCX export).
- Data lives only in the browser session; nothing is stored on a server.

## Tech stack

[Streamlit](https://streamlit.io) · [ReportLab](https://www.reportlab.com/) · [Pillow](https://python-pillow.org/) · [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) (preview rendering)

## License

Free to use and modify for personal and commercial projects.
