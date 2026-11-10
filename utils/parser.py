import os
import io
from docx import Document
from pypdf import PdfReader


def extract_text_from_pdf(file_storage_or_path) -> str:
    text = ""
    try:
        if hasattr(file_storage_or_path, "read"):
            file_bytes = file_storage_or_path.read()
            filename = getattr(file_storage_or_path, "filename", "").lower()
            file_storage_or_path.seek(0)

            if filename.endswith('.docx') or file_bytes.startswith(b'PK\x03\x04'):
                doc = Document(io.BytesIO(file_bytes))
                for para in doc.paragraphs:
                    if para.text:
                        text += para.text + "\n"
                return text if text.strip() else "[Warning: Empty docx]"
            else:
                reader = PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text if text.strip() else "[Warning: Empty PDF]"
        else:
            filename = str(file_storage_or_path).lower()
            if filename.endswith('.docx'):
                doc = Document(file_storage_or_path)
                for para in doc.paragraphs:
                    if para.text:
                        text += para.text + "\n"
                return text if text.strip() else "[Warning: Empty docx]"
            else:
                reader = PdfReader(file_storage_or_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text if text.strip() else "[Warning: Empty PDF]"
    except Exception as e:
        return f"[Error extracting text: {str(e)}]"
