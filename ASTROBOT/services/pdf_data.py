import os
import PyPDF2
from config import PDF_FILE_PATH

_pdf_cache = None

def get_pdf_content() -> str:
    global _pdf_cache
    if _pdf_cache is not None:
        return _pdf_cache

    if not os.path.isfile(PDF_FILE_PATH):
        return "Файл PDF не найден. Проверьте путь."

    text_output = []
    with open(PDF_FILE_PATH, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_output.append(page_text)
    full_text = "\n".join(text_output)
    _pdf_cache = full_text
    return full_text
