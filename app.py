import streamlit as st
import pandas as pd
import fitz  # PyMuPDF for PDFs
import csv
import os
from openpyxl import load_workbook
import ezodf
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Q/A PDF Bot", layout="wide")
st.title("📄 Q/A Bot for CSV, PDF, XLSX, ODS")

uploaded_file = st.file_uploader(
    "Upload a file (CSV, PDF, XLSX, ODS)", 
    type=["csv", "pdf", "xlsx", "ods"]
)

# Store chat history
if "history" not in st.session_state:
    st.session_state.history = []

if uploaded_file:
    file_text = ""

    # CSV
    if uploaded_file.name.endswith(".csv"):
        file_text = uploaded_file.read().decode("utf-8")

    # PDF
    elif uploaded_file.name.endswith(".pdf"):
        pdf_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in pdf_doc:
            file_text += page.get_text()

    # XLSX
    elif uploaded_file.name.endswith(".xlsx"):
        wb = load_workbook(uploaded_file)
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=True):
                file_text += " ".join([str(cell) for cell in row if cell is not None]) + "\n"

    # ODS
    elif uploaded_file.name.endswith(".ods"):
        ods_doc = ezodf.opendoc(uploaded_file)
        for sheet in ods_doc.sheets:
            for row in sheet.rows():
                cells = [cell.plaintext() for cell in row if cell.plaintext()]
                if cells:
                    file_text += " ".join(cells) + "\n"

    # First question only if no history yet
    if len(st.session_state.history) == 0:
        question = st.text_input("Ask a question about your file:", key="first_q")
        if question:
            full_prompt = f"Answer the following question based on the given file content:\n\n{file_text}\n\nQuestion: {question}\nAnswer in detail."
            response = model.generate_content(full_prompt)
            answer = response.text
            st.session_state.history.append({"q": question, "a": answer, "source": file_text[:1000] + "..."})
            st.rerun()

    # Display chat history
    for i, chat in enumerate(st.session_state.history):
        with st.container():
            st.markdown(f"**You:** {chat['q']}")
            st.markdown(f"**Bot:** {chat['a']}")
            with st.expander("📌 Source"):
                st.text(chat["source"])

        # Show a new text box only after the last answer
        if i == len(st.session_state.history) - 1:
            question = st.text_input("Ask another question:", key=f"q_{i}")
            if question:
                full_prompt = f"Answer the following question based on the given file content:\n\n{file_text}\n\nQuestion: {question}\nAnswer in detail."
                response = model.generate_content(full_prompt)
                answer = response.text
                st.session_state.history.append({"q": question, "a": answer, "source": file_text[:1000] + "..."})
                st.rerun()
