import fitz  # PyMuPDF
from docx import Document
import io

def extract_text_from_file(file_bytes, file_ext):
    ext = file_ext.lower()

    if ext == '.pdf':
        return extract_from_pdf(file_bytes)
    elif ext == '.docx':
        return extract_from_docx(file_bytes)
    elif ext == '.txt':
        return file_bytes.decode('utf-8')
    else:
        raise ValueError("Unsupported file type")

def extract_from_pdf(file_bytes):
    text = ""
    # Open PDF from bytes stream
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text

def extract_from_docx(file_bytes):
    # Read DOCX from bytes stream
    doc = Document(io.BytesIO(file_bytes))
    text = "\n".join([para.text for para in doc.paragraphs])
    return text
