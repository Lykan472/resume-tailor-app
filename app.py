import streamlit as st
from openai import OpenAI
import os
import tempfile
from PyPDF2 import PdfReader
from fpdf import FPDF

# Load OpenAI client using Streamlit secrets
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Set GPT model
MODEL = "gpt-3.5-turbo"

# Function to extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to call ChatGPT and improve the resume
def chatgpt_refine_resume(resume_text, job_description):
    prompt = f"""
    I am applying for the following job:
    {job_description}

    My current resume is:
    {resume_text}

    Please rewrite my resume tailored to this job role. Make it ATS-friendly, impactful, and optimized for the job description.
    Output the full updated resume in plain text format.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Function to create PDF from text
def generate_pdf_from_text(text, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    pdf.output(temp_path)
    return temp_path

# --- Streamlit App ---
st.set_page_config(page_title="Resume Tailor", page_icon="📝")

st.title("🧠 Resume Tailor using ChatGPT")
st.write("Upload your **resume** and a **job description**, and get a **customized, ATS-friendly resume** back!")

resume_file = st.file_uploader("📄 Upload your resume (PDF)", type=["pdf"])
job_file = st.file_uploader("📝 Upload job description (PDF or TXT)", type=["pdf", "txt"])

if st.button("✨ Generate Tailored Resume") and resume_file and job_file:
    try:
        with st.spinner("Extracting your resume and job description..."):
            resume_text = extract_text_from_pdf(resume_file)

            if job_file.type == "application/pdf":
                job_description = extract_text_from_pdf(job_file)
            else:
                job_description = job_file.read().decode("utf-8")

        with st.spinner("Talking to ChatGPT..."):
            improved_resume = chatgpt_refine_resume(resume_text, job_description)

        st.success("✅ Resume tailored successfully!")
        st.text_area("📋 Tailored Resume", improved_resume, height=400)

        pdf_path = generate_pdf_from_text(improved_resume, "tailored_resume.pdf")
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📥 Download as PDF",
                data=f,
                file_name="tailored_resume.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Something went wrong: {e}")
