"""
Утилита для извлечения текста из DOCX-файлов.
Используется для подготовки данных из файлов key1.docx и key2.docx.
"""

import os
import docx

def get_docx_content(docx_path: str) -> str:
    """
    Извлекает и возвращает текст из DOCX-файла.
    
    Args:
        docx_path (str): Путь к DOCX-файлу
        
    Returns:
        str: Извлеченный текст или сообщение об ошибке, если файл не найден
    """
    # Проверяем, существует ли файл
    if not os.path.isfile(docx_path):
        return f"Файл {docx_path} не найден. Проверьте путь."
    
    # Открываем DOCX-файл
    doc = docx.Document(docx_path)
    
    # Извлекаем текст из всех параграфов
    text_output = []
    for para in doc.paragraphs:
        if para.text:  # Если параграф не пустой
            text_output.append(para.text)
            
    # Объединяем все параграфы, разделяя их переносом строки
    return "\n".join(text_output)