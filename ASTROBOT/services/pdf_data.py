"""
Сервис для извлечения текста из PDF-файлов.
"""

import os
import PyPDF2

def get_pdf_content(pdf_path: str) -> str:
    """
    Извлекает и возвращает текст из PDF-файла по указанному пути.
    
    Args:
        pdf_path (str): Путь к PDF-файлу
        
    Returns:
        str: Извлеченный текст или сообщение об ошибке, если файл не найден
    """
    # Проверяем, существует ли файл
    if not os.path.isfile(pdf_path):
        return f"Файл {pdf_path} не найден. Проверьте путь."
    
    text_output = []
    
    # Открываем PDF-файл и извлекаем текст
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_output.append(page_text)
    
    # Объединяем текст всех страниц
    full_text = "\n".join(text_output)
    return full_text