import streamlit as st
from openai import OpenAI
import os
from PyPDF2 import PdfReader
import tempfile
from xhtml2pdf import pisa

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

# Use ChatGPT to refine resume and return HTML
def tailor_resume(resume_text, job_description):
    prompt = f"""
You are an expert resume writer. Rewrite the resume professionally in clean, structured **HTML format**, keeping in mind the expectations of top Indian and global recruiters.

Create a **one-page, ATS-friendly resume** tailored for roles in **Supply Chain and Production Planning**. Focus on showcasing impactful achievements using **quantified metrics** and **strong action verbs**. Ensure the content is concise, well-structured, and highly relevant to the role.

Use this HTML structure and styling:

<html>
<head>
  <style>
    body {{ font-family: 'Arial', sans-serif; font-size: 10.5pt; margin: 2cm; color: #111; }}
    h1, h2 {{ color: #2c3e50; margin-bottom: 6px; }}
    h1 {{ font-size: 20pt; border-bottom: 2px solid #2c3e50; padding-bottom: 5px; margin-bottom: 15px; }}
    h2 {{ font-size: 14pt; margin-top: 20px; border-bottom: 1px solid #aaa; padding-bottom: 3px; }}
    p {{ margin: 4px 0; line-height: 1.4; }}
    ul {{ padding-left: 18px; margin: 6px 0; }}
    li {{ margin-bottom: 4px; }}
    .section {{ margin-bottom: 18px; }}
    .label {{ font-weight: bold; }}
    .line {{ border-top: 1px solid #ccc; margin: 15px 0; }}
    .header {{ text-align: center; margin-bottom: 25px; }}
    .name {{ font-size: 18pt; font-weight: bold; }}
    .contact {{ font-size: 10pt; color: #555; }}
    .bullet-section {{ margin-top: 8px; }}
  </style>
</head>
<body>
  <div class='header'>
    <div class='name'>Your Full Name</div>
    <div class='contact'>Email • Phone • LinkedIn • City, Country</div>
  </div>

  <!-- Resume Content Below -->

</body>
</html>

Rewrite resume in the HTML format shown above, inserting relevant content in place of placeholders.

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

# Generate PDF from HTML

def generate_pdf(html_resume):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(temp_file.name, "wb") as f:
        pisa.CreatePDF(html_resume, dest=f)
    return temp_file.name

# Streamlit UI
st.title("Resume Tailor (ChatGPT-Powered)")

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
                improved_resume_html = tailor_resume(resume_text, job_description)
                pdf_path = generate_pdf(improved_resume_html)

            with open(pdf_path, "rb") as f:
                st.success("Done! Download your tailored resume below.")
                st.download_button(
                    label="Download Tailored Resume (PDF)",
                    data=f,
                    file_name="tailored_resume.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Something went wrong: {e}")
