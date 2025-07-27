from dotenv import load_dotenv
load_dotenv()

import base64
import streamlit as st
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError
from docx import Document # Import for handling Word documents

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_prompt, file_content, job_description):
    model = genai.GenerativeModel('gemini-1.5-flash')
    # The content passed to generate_content needs to be a list of parts.
    # We need to handle whether file_content is an image part (from PDF) or text (from DOCX).
    parts = [input_prompt, job_description]
    if isinstance(file_content, dict) and "mime_type" in file_content: # It's an image part from PDF
        parts.insert(1, file_content) # Insert image part at the second position
    elif isinstance(file_content, str): # It's text from DOCX
        parts.insert(1, f"Resume Content:\n{file_content}") # Insert text content
    else:
        st.error("Unsupported content format for LLM.")
        return "Error: Unsupported file content."

    response = model.generate_content(parts)
    return response.text

def input_file_setup(uploaded_file):
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_extension == "pdf":
            try:
                # Explicitly set the path to Poppler's bin directory
                # Replace 'YOUR_POPPLER_BIN_PATH' with the actual path on your system
                # For deployment, consider setting Poppler in your server's PATH or using a Docker image.
                poppler_path = r"E:\Poppler\Release-24.08.0-0\poppler-24.08.0\Library\bin" # Use raw string (r"...")

                ## Convert the PDF to image
                # We'll stick to image for now, but text extraction from PDF is also possible
                ##images = pdf2image.convert_from_bytes(uploaded_file.read(), poppler_path=poppler_path)
                images = pdf2image.convert_from_bytes(uploaded_file.read())
                first_page = images[0]

                # Convert to bytes
                img_byte_arr = io.BytesIO()
                first_page.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()

                pdf_parts = {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
                }
                return pdf_parts
            except PDFInfoNotInstalledError:
                st.error("Error: Poppler is not installed or not in your system's PATH. Please install Poppler to process PDFs.")
                st.markdown("""
                    **How to install Poppler:**
                    - **Windows:** Download from [Poppler for Windows releases](https://github.com/oschwartz10612/poppler-windows/releases), extract, and add the `bin` folder to your system's PATH.
                    - **macOS:** Open Terminal and run `brew install poppler`
                    - **Linux (Ubuntu/Debian):** Open Terminal and run `sudo apt-get install poppler-utils`
                    Then, restart VS Code and your terminal.
                """)
                st.stop()
            except PDFPageCountError:
                st.error("Error: Could not determine PDF page count. The PDF file might be corrupted or malformed.")
                st.stop()
            except Exception as e:
                st.error(f"An unexpected error occurred while processing the PDF: {e}")
                st.stop()

        elif file_extension == "docx":
            try:
                doc = Document(uploaded_file)
                full_text = []
                for para in doc.paragraphs:
                    full_text.append(para.text)
                return "\n".join(full_text)
            except Exception as e:
                st.error(f"An error occurred while processing the Word document: {e}")
                st.stop()
        else:
            st.error("Unsupported file type. Please upload a PDF or DOCX file.")
            st.stop()
    else:
        raise FileNotFoundError("No file uploaded")

## Streamlit App

st.set_page_config(page_title="ATS Resume EXpert")
st.header("ATS Tracking System")
input_text = st.text_area("Job Description: ", key="input")
# Allow both PDF and DOCX file types
uploaded_file = st.file_uploader("Upload your resume (PDF or Word)...", type=["pdf", "docx"])


if uploaded_file is not None:
    st.write("File Uploaded Successfully")


submit1 = st.button("Tell Me About the Resume")
submit3 = st.button("Percentage match")

input_prompt1 = """
 You are an experienced Technical Human Resource Manager,your task is to review the provided resume against the job description.
 Please share your professional evaluation on whether the candidate's profile aligns with the role.
 Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
"""

input_prompt3 = """
You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality,
your task is to evaluate the resume against the provided job description. give me the percentage of match if the resume matches
the job description. First the output should come as percentage and then keywords missing and last final thoughts.
"""

if submit1:
    if uploaded_file is not None:
        file_content = input_file_setup(uploaded_file)
        if file_content: # Only proceed if file_content was successfully returned
            response = get_gemini_response(input_prompt1, file_content, input_text)
            st.subheader("The Response is")
            st.write(response)
    else:
        st.write("Please upload the resume")

elif submit3:
    if uploaded_file is not None:
        file_content = input_file_setup(uploaded_file)
        if file_content: # Only proceed if file_content was successfully returned
            response = get_gemini_response(input_prompt3, file_content, input_text)
            st.subheader("The Response is")
            st.write(response)
    else:
        st.write("Please upload the resume")