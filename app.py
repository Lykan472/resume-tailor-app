import streamlit as st
from openai import OpenAI
import os
from PyPDF2 import PdfReader
from fpdf import FPDF
import tempfile
import unicodedata

# Set up OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Extract text from uploaded resume
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

# Use ChatGPT to refine resume
def tailor_resume(resume_text, job_description):
    prompt = f"""
You are an expert resume writer. Rewrite the resume professionally, keeping in mind the expectations of top Indian and global recruiters.

Create a **one-page, ATS-friendly resume** tailored for roles in **Supply Chain and Production Planning**. Focus on showcasing impactful achievements using **quantified metrics** and **strong action verbs**. Ensure the content is concise, well-structured, and highly relevant to the role.

Format must be **clean, modern, and readable**, with **clear section headings** and **bullet points**.

Highlight skills including:
- SAP (PP/MM)
- Excel automation
- MRP
- MIS reporting
- Inventory control
- Lean manufacturing
- Other relevant supply chain tools and practices

Also include:
- Any **significant projects**
- **Education**
- **Recognitions or achievements** that demonstrate value

Optimize the resume for companies like **Adani, Tata, ITC, Flipkart, HUL**, and similar MNCs or startups.

The final output should be a **polished one-page resume**, **suitable for online applications and recruiter reviews**. Respond with the **improved resume only** — do **not** include explanations or notes.

Resume:
{resume_text}

Job Description:
{job_description}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# Normalize unicode text for PDF
def clean_text_for_pdf(text):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("latin-1", errors="ignore").decode("latin-1")
    return ascii_text

# Improved PDF formatting
class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=10)
        self.add_page()
        self.set_font("Arial", size=11)
        self.set_margins(15, 15, 15)

    def add_resume_content(self, text):
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                self.ln(5)  # Add vertical space between sections
                continue
            if line.endswith(":"):  # Treat as section heading
                self.set_font("Arial", "B", 12)
                self.cell(0, 8, line, ln=True)
                self.set_font("Arial", "", 11)
            elif line.startswith("-"):
                self.cell(5)
                self.multi_cell(0, 6, f"{line}")
            else:
                self.multi_cell(0, 6, line)

def generate_pdf(text):
    cleaned_text = clean_text_for_pdf(text)
    pdf = PDF()
    pdf.add_resume_content(cleaned_text)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

# Streamlit UI
st.title("🎯 Resume Tailor (ChatGPT-Powered)")

with st.form("resume_form"):
    resume_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])
    job_description = st.text_area("Paste the Job Description here", height=250)
    submitted = st.form_submit_button("Generate Tailored Resume")

if submitted:
    if not resume_file or not job_description.strip():
        st.error("Please upload your resume and enter a job description.")
    else:
        try:
            with st.spinner("Tailoring your resume..."):
                resume_text = extract_text_from_pdf(resume_file)
                improved_resume = tailor_resume(resume_text, job_description)
                pdf_path = generate_pdf(improved_resume)

            with open(pdf_path, "rb") as f:
                st.success("Done! Download your tailored resume below.")
                st.download_button(
                    label="📥 Download Tailored Resume (PDF)",
                    data=f,
                    file_name="tailored_resume.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Something went wrong: {e}")
