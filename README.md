# 📝 Resume Generator

A simple and elegant web application built with *Streamlit* that allows users to generate a one-page professional resume in PDF format. Users can fill out a form with their personal, academic, and professional details, optionally upload a passport-size photo, and download the final resume as a PDF.

## 🚀 Features

- User-friendly form to enter resume details
- Optional passport-size photo upload
- Supports multiple education entries
- Sections for:
  - Career Objective
  - Academic Qualifications
  - Other Qualifications
  - Work Experience
  - Personal Details
  - Declaration
- Automatically formats the information into a clean one-page PDF
- Download resume directly from the app

## 🛠 Tech Stack

- [Streamlit](https://streamlit.io/) – for building the interactive web UI
- [FPDF](https://pyfpdf.github.io/fpdf2/) – for generating PDF documents
- [Pillow (PIL)](https://python-pillow.org/) – for image processing
- Python's tempfile and os – for secure file handling

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sdpandya007/Resume-Generator.git
   cd resume-generator-streamlit
   ```

2. Create virtual environment in folder's cmd:
   ```bash
    python -m venv myenv
    ```

3. Activate the virtual environment:
   ```bash
   myenv\Scripts\activate
   ```
 
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the app:
   ```bash
   streamlit run app.py
   ```
6. Open your browser and navigate to `http://localhost:8501` to access the app.
--- 

## 🚀 Live Demo
👉 (https://resume-generator-ma7cgjqmzse25o5rbqtilm.streamlit.app/)

## 📌 Customization

Modify style.css to change the visual theme of the app

Adjust PDF layout by editing the create_pdf() function in app.py

## 📄 License

This project is licensed under the MIT License. Feel free to use and modify.

---
