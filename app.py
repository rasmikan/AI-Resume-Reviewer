import streamlit as st
import pdfplumber
from docx import Document
from dotenv import load_dotenv
import os
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import re

# ------------------------------------------------
# CONFIG
# ------------------------------------------------

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

st.set_page_config(
    page_title="AI Resume Reviewer",
    page_icon="📄",
    layout="wide"
)

# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------

with st.sidebar:

    st.title("📄 AI Resume Reviewer")

    st.markdown("---")

    st.write("### Features")

    st.write("✅ PDF Resume Upload")
    st.write("✅ DOCX Resume Upload")
    st.write("✅ ATS Score")
    st.write("✅ Keyword Match")
    st.write("✅ AI Suggestions")
    st.write("✅ Missing Skills")
    st.write("✅ Download PDF Report")

    st.markdown("---")

    st.info(
        "Analyze your resume against any Job Description using AI."
    )

# ------------------------------------------------
# MAIN
# ------------------------------------------------

st.title("📄 AI Resume Reviewer")

st.caption(
    "AI-powered ATS resume analysis using LLMs."
)

company = st.selectbox(
    "Target Company",
    [
        "Custom JD",
        "Google",
        "Microsoft",
        "Amazon"
    ]
)

resume = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx"]
)

jd = st.text_area(
    "Paste Job Description"
)

# ------------------------------------------------
# SESSION HISTORY
# ------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

# ------------------------------------------------
# PDF EXTRACTION
# ------------------------------------------------

def extract_pdf(file):

    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


# ------------------------------------------------
# DOCX EXTRACTION
# ------------------------------------------------

def extract_docx(file):

    doc = Document(file)

    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text


# ------------------------------------------------
# PDF REPORT GENERATION
# ------------------------------------------------

def generate_pdf(content):

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    doc = SimpleDocTemplate(
        temp.name
    )

    styles = getSampleStyleSheet()

    story = []

    title = Paragraph(
        "AI Resume Analysis Report",
        styles["Title"]
    )

    story.append(title)

    story.append(
        Spacer(1, 20)
    )

    for line in content.split("\n"):

        story.append(
            Paragraph(
                line,
                styles["BodyText"]
            )
        )

        story.append(
            Spacer(1, 6)
        )

    doc.build(story)

    return temp.name


# ------------------------------------------------
# ANALYZE
# ------------------------------------------------

if st.button("Analyze Resume"):

    if resume is None:
        st.error(
            "Please upload a resume."
        )

    elif jd.strip() == "":
        st.error(
            "Please paste a Job Description."
        )

    else:

        if resume.name.endswith(".pdf"):
            resume_text = extract_pdf(
                resume
            )
        else:
            resume_text = extract_docx(
                resume
            )

        resume_text = resume_text[:10000]
        jd = jd[:5000]

        # ----------------------------------------
        # Keyword Match
        # ----------------------------------------

        resume_words = set(
            resume_text.lower().split()
        )

        jd_words = set(
            jd.lower().split()
        )

        common = resume_words.intersection(
            jd_words
        )

        keyword_match = (
            len(common)
            / max(
                len(jd_words),
                1
            )
        ) * 100

        st.subheader(
            "Keyword Match"
        )

        st.progress(
            min(
                int(keyword_match),
                100
            )
        )

        st.metric(
            "Keyword Match",
            f"{keyword_match:.1f}%"
        )

        # ----------------------------------------
        # Resume Preview
        # ----------------------------------------

        with st.expander(
            "View Extracted Resume"
        ):
            st.write(
                resume_text
            )

        # ----------------------------------------
        # Prompt
        # ----------------------------------------

        prompt = f"""
You are an expert ATS Resume Reviewer.

Target Company:
{company}

Evaluate the following resume against the Job Description.

Generate:

# ATS Score

# JD Match Percentage

# Matching Skills

# Missing Skills

# Strengths

# Weaknesses

# Resume Improvement Suggestions

# Suggested Resume Summary

# Top 5 Keywords To Add

Format using Markdown.

Resume:

{resume_text}

Job Description:

{jd}
"""

        try:

            with st.spinner(
                "Analyzing..."
            ):

                response = (
                    client.chat.completions.create(
                        model="openrouter/auto",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.3,
                        max_tokens=1200
                    )
                )

            result = (
                response
                .choices[0]
                .message
                .content
            )

            match = re.search(
                r'ATS Score.*?(\d+)',
                result,
                re.IGNORECASE | re.DOTALL
            )

            if match:

                score = int(
                    match.group(1)
                )

                st.metric(
                    "ATS Score",
                    f"{score}/100"
                )

            st.success(
                "Analysis Complete!"
            )

            st.subheader(
                "AI Analysis"
            )

            st.markdown(
                result
            )

            st.session_state.history.append(
                result
            )

            pdf_path = generate_pdf(
                result
            )

            with open(
                pdf_path,
                "rb"
            ) as pdf_file:

                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_file,
                    file_name="ATS_Report.pdf",
                    mime="application/pdf"
                )

        except Exception as e:

            st.error(
                str(e)
            )

# ------------------------------------------------
# HISTORY
# ------------------------------------------------

if len(
    st.session_state.history
) > 0:

    with st.expander(
        "Previous Analyses"
    ):

        for i, item in enumerate(
            reversed(
                st.session_state.history
            ),
            1
        ):

            st.write(
                f"### Analysis {i}"
            )

            st.markdown(
                item
            )

            st.markdown(
                "---"
            )