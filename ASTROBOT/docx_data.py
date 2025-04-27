"""
Утилита для извлечения текста из DOCX-файлов.
Используется для подготовки данных из файлов key1.docx и key2.docx.
"""

import os
import docx
from logger import services_logger as logger

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
        error_msg = f"Файл {docx_path} не найден. Проверьте путь."
        logger.error(error_msg)
        return error_msg
    
    logger.info(f"Извлечение текста из DOCX-файла: {docx_path}")
    
    try:
        # Открываем DOCX-файл
        doc = docx.Document(docx_path)
        
        # Извлекаем текст из всех параграфов
        text_output = []
        for para in doc.paragraphs:
            if para.text:  # Если параграф не пустой
                text_output.append(para.text)
        
        # Объединяем все параграфы, разделяя их переносом строки
        extracted_text = "\n".join(text_output)
        logger.debug(f"Извлечено {len(text_output)} параграфов, общий размер текста: {len(extracted_text)} символов")
        return extracted_text
        
    except Exception as e:
        error_msg = f"Ошибка при извлечении текста из файла {docx_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg