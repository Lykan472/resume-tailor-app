import streamlit as st
import openai
import os
from fpdf import FPDF
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document
import tempfile

# Load API key securely
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4"

def extract_text(file):
    ext = file.name.split('.')[-1].lower()
    if ext == "pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.read())
            return extract_pdf_text(tmp_file.name)
    elif ext == "docx":
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif ext == "txt":
        return file.read().decode("utf-8")
    else:
        st.error("Unsupported file format.")
        return None

def chatgpt_refine_resume(resume_text, job_description):
    prompt = f"""
You are an expert resume writer.

Here is the resume:
--- RESUME START ---
{resume_text}
--- RESUME END ---

And here is the job description:
--- JOB DESCRIPTION START ---
{job_description}
--- JOB DESCRIPTION END ---

Please rewrite the resume tailored to this job. Make it:
- One page
- ATS-friendly
- Clearly formatted (e.g., Experience, Education, Skills)
- Strong and relevant to the job

Return the full rewritten resume only.
"""
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

def generate_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)

    pdf_path = "tailored_resume.pdf"
    pdf.output(pdf_path)
    return pdf_path

# === Streamlit App ===
st.set_page_config(page_title="Smart Resume Tailor", layout="centered")
st.title("📄 Smart Resume Tailor")
st.write("Upload your resume and a job description — get a tailored resume powered by ChatGPT!")

resume_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
job_input_option = st.radio("How would you like to provide the job description?", ("Upload a file", "Paste text"))

job_description = ""
if job_input_option == "Upload a file":
    job_file = st.file_uploader("Upload Job Description (TXT, DOCX, or PDF)", type=["txt", "docx", "pdf"])
    if job_file:
        job_description = extract_text(job_file)
else:
    job_description = st.text_area("Paste the job description here")

if st.button("Generate Tailored Resume"):
    if not resume_file or not job_description:
        st.warning("Please upload both a resume and job description.")
    else:
        with st.spinner("⏳ Generating resume..."):
            resume_text = extract_text(resume_file)
            improved_resume = chatgpt_refine_resume(resume_text, job_description)
            pdf_path = generate_pdf(improved_resume)
            with open(pdf_path, "rb") as f:
                st.success("✅ Resume generated!")
                st.download_button("📥 Download Your Tailored Resume", f, file_name="tailored_resume.pdf", mime="application/pdf")
