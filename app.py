import streamlit as st
from openai import OpenAI
import os
from PyPDF2 import PdfReader
from fpdf import FPDF
import tempfile

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
You are an expert resume writer. Based on the job description below, tailor the resume content to better fit the role.

Job Description:
{job_description}

Resume:
{resume_text}

Respond with an improved version of the resume only. Do not include explanations.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# Create PDF (default font)
import unicodedata

def clean_text_for_pdf(text):
    # Normalize and replace special characters with ASCII equivalents or remove them
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("latin-1", errors="ignore").decode("latin-1")
    return ascii_text

def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    cleaned_text = clean_text_for_pdf(text)

    for line in cleaned_text.split("\n"):
        pdf.multi_cell(0, 10, line)

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
