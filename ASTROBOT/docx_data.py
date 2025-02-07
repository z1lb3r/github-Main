import os
import docx

def get_docx_content(docx_path: str) -> str:
    """
    Извлекает и возвращает текст из DOCX-файла.
    """
    if not os.path.isfile(docx_path):
        return f"Файл {docx_path} не найден. Проверьте путь."
    
    doc = docx.Document(docx_path)
    text_output = []
    for para in doc.paragraphs:
        if para.text:
            text_output.append(para.text)
    return "\n".join(text_output)
