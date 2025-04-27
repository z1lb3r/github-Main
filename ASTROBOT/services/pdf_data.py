"""
Сервис для извлечения текста из PDF-файлов.
"""

import os
import PyPDF2
from logger import services_logger as logger

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
        error_msg = f"Файл {pdf_path} не найден. Проверьте путь."
        logger.error(error_msg)
        return error_msg
    
    logger.info(f"Извлечение текста из PDF-файла: {pdf_path}")
    
    text_output = []
    
    try:
        # Открываем PDF-файл и извлекаем текст
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            logger.debug(f"PDF содержит {total_pages} страниц")
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_output.append(page_text)
                logger.debug(f"Обработана страница {i+1}/{total_pages}, текст: {len(page_text) if page_text else 0} символов")
        
        # Объединяем текст всех страниц
        full_text = "\n".join(text_output)
        logger.debug(f"Всего извлечено текста: {len(full_text)} символов")
        return full_text
        
    except Exception as e:
        error_msg = f"Ошибка при извлечении текста из PDF-файла: {str(e)}"
        logger.error(error_msg)
        return error_msg