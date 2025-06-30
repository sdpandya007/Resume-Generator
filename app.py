import streamlit as st
from fpdf import FPDF
import base64
import tempfile
import os
from PIL import Image

# Custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Generate PDF
def create_pdf(data, photo_path=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "RESUME", ln=1, align='C')
    pdf.ln(10)
    
    # Photo (top right corner)
    if photo_path:
        try:
            pdf.image(photo_path, x=160, y=20, w=30, h=30)
        except:
            st.warning("Could not add photo to PDF")
    
    # Name and Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 7, data['name'], ln=1, align='C')
    pdf.set_font('Arial', 'I', 12)
    pdf.cell(0, 7, data['title'], ln=1, align='C')
    pdf.ln(5)
    
    # Contact Information
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, data['address'], ln=1)
    pdf.cell(0, 5, f"Mob No.: {data['phone']}", ln=1)
    pdf.cell(0, 5, f"Email Id: {data['email']}", ln=1)
    pdf.ln(10)
    
    # Horizontal line
    pdf.cell(0, 0, '', ln=1, border='T')
    pdf.ln(10)
    
    # Career Objective
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, "CAREER OBJECTIVE", ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, data['objective'])
    pdf.ln(10)
    
    # Academic Qualification
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, "ACADEMIC QUALIFICATION", ln=1)
    pdf.set_font('Arial', '', 10)
    
    # Table header
    col_widths = [15, 45, 60, 20, 20]
    headers = ["S.No.", "Qualification", "University/Board", "Year", "Per %"]
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 7, header, border=1)
    pdf.ln()
    
    # Table rows
    for i, edu in enumerate(data['education']):
        pdf.cell(col_widths[0], 7, str(i+1), border=1)
        pdf.cell(col_widths[1], 7, edu['qualification'], border=1)
        pdf.cell(col_widths[2], 7, edu['board'], border=1)
        pdf.cell(col_widths[3], 7, edu['year'], border=1)
        pdf.cell(col_widths[4], 7, edu['percentage'], border=1)
        pdf.ln()
    
    pdf.ln(10)
    
    # Other Qualifications
    if data['other_qualifications']:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 7, "OTHER QUALIFICATION", ln=1)
        pdf.set_font('Arial', '', 10)
        for qual in data['other_qualifications'].split('\n'):
            pdf.cell(0, 5, f"- {qual.strip()}", ln=1)
        pdf.ln(10)
    
    # Work Experience
    if data['experience']:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 7, "WORK EXPERIENCE", ln=1)
        pdf.set_font('Arial', '', 10)
        for exp in data['experience'].split('\n'):
            pdf.cell(0, 5, f"- {exp.strip()}", ln=1)
        pdf.ln(10)
    
    # Personal Information
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, "PERSONAL INFORMATION", ln=1)
    pdf.set_font('Arial', '', 10)
    
    personal_info = [
        ("Father's Name", data['father_name']),
        ("Date of Birth", data['dob']),
        ("Language Known", data['languages']),
        ("Gender", data['gender']),
        ("Nationality", data['nationality']),
        ("Marital Status", data['marital_status'])
    ]
    
    for label, value in personal_info:
        pdf.cell(50, 5, f"{label} :", ln=0)
        pdf.cell(0, 5, value, ln=1)
    
    pdf.ln(15)
    
    # Declaration
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, "DECLARATION", ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, "I hereby declare that the above information given by me is true to best of my Knowledge.")
    pdf.ln(10)
    
    # Date and Place
    pdf.cell(0, 5, f"Place : {data['place']}", ln=1)
    pdf.ln(20)
    
    return pdf

def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            img = Image.open(uploaded_file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(tmp_file.name, "JPEG", quality=90)
            return tmp_file.name
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def main():
    # Load CSS
    local_css("style.css")
    
    st.title("Resume Generator")
    st.markdown("Fill in your details below to generate a professional one-page resume in PDF format.")
    
    with st.form("resume_form"):
        st.header("Personal Information")
        name = st.text_input("Full Name*", placeholder="Ankita Kumari")
        title = st.text_input("Job Title*", placeholder="Computer Operator")
        
        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input("Phone Number*", placeholder="+91 1234567890")
        with col2:
            email = st.text_input("Email*", placeholder="sachinkumar@gmail.com")
        
        address = st.text_area("Full Address*", placeholder="P - 171 Gali No. 5\nBajjeet Nagar, Patel Nagar\nNew Delhi - 110008")
        
        # Photo Upload (optional)
        st.header("Passport Size Photo (Optional)")
        photo = st.file_uploader("Upload passport photo (2x2 inches, JPG/PNG)", 
                               type=["jpg", "jpeg", "png"])
        
        st.header("Career Objective")
        objective = st.text_area("Objective*", 
                               placeholder="To make contribution in the organization with best of my ability...")
        
        st.header("Education")
        education = []
        with st.expander("Add Education Details"):
            num_education = st.number_input("Number of Education Entries", min_value=1, max_value=5, value=3)
            
            for i in range(num_education):
                st.subheader(f"Education {i+1}")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    qualification = st.text_input(f"Qualification {i+1}", key=f"qual_{i}", placeholder="10th")
                with col2:
                    board = st.text_input(f"Board/University {i+1}", key=f"board_{i}", placeholder="CBSE Board")
                with col3:
                    year = st.text_input(f"Year {i+1}", key=f"year_{i}", placeholder="2014")
                with col4:
                    percentage = st.text_input(f"Percentage {i+1}", key=f"per_{i}", placeholder="82%")
                
                education.append({
                    'qualification': qualification,
                    'board': board,
                    'year': year,
                    'percentage': percentage
                })
        
        st.header("Other Qualifications")
        other_qualifications = st.text_area("List your other qualifications (one per line)", 
                                          placeholder="Basic Knowledge of Computer\nAdv. Microsoft Excel")
        
        st.header("Work Experience")
        experience = st.text_area("Describe your work experience (one per line)", 
                                placeholder="2 Years of Experience as a Computer Operator in XYZ Pvt. Ltd Company")
        
        st.header("Personal Details")
        col1, col2 = st.columns(2)
        with col1:
            father_name = st.text_input("Father's Name", placeholder="Pramod Kumar")
            dob = st.text_input("Date of Birth", placeholder="1999-08-07")
            gender = st.selectbox("Gender", ["Female", "Male", "Other"])
        with col2:
            languages = st.text_input("Languages Known", placeholder="Hindi And English")
            nationality = st.text_input("Nationality", placeholder="Indian")
            marital_status = st.selectbox("Marital Status", ["Unmarried", "Married", "Other"])
        
        place = st.text_input("Place*", placeholder="New Delhi")
        
        # Form submission
        submitted = st.form_submit_button("Generate Resume")
        
        if submitted:
            if not name or not title or not phone or not email or not address or not objective or not place:
                st.error("Please fill in all required fields (marked with *)")
            else:
                resume_data = {
                    'name': name,
                    'title': title,
                    'phone': phone,
                    'email': email,
                    'address': address,
                    'objective': objective,
                    'education': education,
                    'other_qualifications': other_qualifications,
                    'experience': experience,
                    'father_name': father_name,
                    'dob': dob,
                    'languages': languages,
                    'gender': gender,
                    'nationality': nationality,
                    'marital_status': marital_status,
                    'place': place
                }
                
                # Process photo if provided
                photo_path = save_uploaded_file(photo) if photo else None
                
                # Generate PDF
                pdf = create_pdf(resume_data, photo_path)
                
                # Save to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                    pdf.output(tmpfile.name)
                
                # Display download link
                with open(tmpfile.name, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    download_link = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{name}_Resume.pdf">Download Your Resume</a>'
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.success("Resume generated successfully!")
                
                # Clean up temporary files
                os.unlink(tmpfile.name)
                if photo_path:
                    os.unlink(photo_path)

if __name__ == "__main__":
    main()
