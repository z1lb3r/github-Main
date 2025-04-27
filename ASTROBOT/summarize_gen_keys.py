"""
Скрипт для создания сводок (саммари) из PDF-файлов.
Извлекает текст из PDF, отправляет его на суммаризацию в ChatGPT
и сохраняет результат в новый PDF файл.
"""

import os
import openai
from services.pdf_data import get_pdf_content
from config import OPENAI_API_KEY
from fpdf import FPDF
from logger import services_logger as logger

# Устанавливаем API ключ для OpenAI
openai.api_key = OPENAI_API_KEY
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def summarize_text(text, max_tokens=300, chunk_threshold=5000):
    """
    Отправляет запрос к ChatGPT для суммаризации переданного текста.
    Если текст длиннее chunk_threshold символов, он разбивается на части,
    каждая из которых суммаризуется отдельно. Затем промежуточные 
    суммаризации объединяются и, при необходимости, суммаризуются повторно.
    
    Args:
        text (str): Текст для суммаризации
        max_tokens (int): Максимальное количество токенов в ответе
        chunk_threshold (int): Пороговое значение для разбиения текста
        
    Returns:
        str: Суммаризированный текст
    """
    logger.info(f"Начало суммаризации текста длиной {len(text)} символов")
    
    if len(text) <= chunk_threshold:
        # Если текст достаточно короткий, суммаризируем его целиком
        logger.debug("Текст помещается в один чанк, выполняем прямую суммаризацию")
        prompt = (
            "Сделай краткое резюме следующего текста, выделив только основную ценную информацию, "
            "не превышающее 1000 слов:\n\n" + text
        )
        try:
            logger.debug(f"Отправка запроса в OpenAI, max_tokens={max_tokens}")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Ты помощник по суммаризации текста."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.5
            )
            summary = response.choices[0].message.content.strip()
            logger.debug(f"Получена суммаризация длиной {len(summary)} символов")
            return summary
        except Exception as e:
            logger.error(f"Ошибка при суммаризации: {str(e)}")
            return "[Ошибка суммаризации]"
    else:
        # Если текст слишком длинный, разбиваем его на части
        logger.info(f"Текст слишком длинный, разбиваем на части с порогом {chunk_threshold} символов")
        chunks = [text[i:i+chunk_threshold] for i in range(0, len(text), chunk_threshold)]
        logger.debug(f"Текст разбит на {len(chunks)} частей")
        
        intermediate_summaries = []
        
        # Суммаризируем каждую часть отдельно
        for i, chunk in enumerate(chunks):
            logger.debug(f"Суммаризация части {i+1} из {len(chunks)}")
            prompt = (
                f"Сделай краткое резюме части {i+1} из {len(chunks)} следующего текста, выделив основную ценную информацию, "
                "не превышающее 1000 слов:\n\n" + chunk
            )
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Ты помощник по суммаризации текста."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.5
                )
                intermediate_summary = response.choices[0].message.content.strip()
                logger.debug(f"Получена промежуточная суммаризация части {i+1}, длина: {len(intermediate_summary)} символов")
                intermediate_summaries.append(intermediate_summary)
            except Exception as e:
                logger.error(f"Ошибка при суммаризации промежуточного чанка {i+1}: {str(e)}")
                intermediate_summaries.append("[Ошибка суммаризации]")
        
        # Объединяем все промежуточные суммаризации
        combined_summary_text = "\n".join(intermediate_summaries)
        logger.debug(f"Объединенный текст промежуточных суммаризаций: {len(combined_summary_text)} символов")
        
        # Если объединенный текст всё ещё слишком длинный, суммаризуем его повторно
        if len(combined_summary_text) > chunk_threshold:
            logger.info(f"Объединенный текст превышает порог, выполняем финальную суммаризацию")
            prompt = (
                "Сделай краткое резюме следующего текста, выделив только основную ценную информацию, "
                "не превышающее 1000 слов:\n\n" + combined_summary_text
            )
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Ты помощник по суммаризации текста."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.5
                )
                final_summary = response.choices[0].message.content.strip()
                logger.debug(f"Получена финальная суммаризация длиной {len(final_summary)} символов")
                return final_summary
            except Exception as e:
                logger.error(f"Ошибка при финальной суммаризации: {str(e)}")
                return combined_summary_text
        else:
            logger.info("Объединенный текст в пределах порога, возвращаем без финальной суммаризации")
            return combined_summary_text

def save_summary_as_pdf(summary, output_path):
    """
    Сохраняет переданный текст в PDF-файл с поддержкой Unicode.
    
    Args:
        summary (str): Текст для сохранения
        output_path (str): Путь для сохранения PDF-файла
    """
    logger.info(f"Сохранение суммаризации в PDF-файл: {output_path}")
    
    pdf = FPDF()
    pdf.add_page()
    
    # Добавляем шрифт с поддержкой кириллицы
    font_path = os.path.join(BASE_DIR, "fonts", "dejavusanscondensed.ttf")
    if not os.path.isfile(font_path):
        logger.error(f"Шрифт не найден по пути: {font_path}")
        raise FileNotFoundError(f"Шрифт не найден по пути: {font_path}")
    
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)
    
    # Записываем текст в PDF
    for line in summary.split("\n"):
        pdf.multi_cell(0, 10, txt=line)
    
    # Сохраняем файл
    logger.debug(f"Сохранение PDF-файла по пути: {output_path}")
    pdf.output(output_path)
    logger.info(f"PDF-файл успешно сохранен: {output_path}")

def process_files(data_folder="data", summary_folder="data_summaries"):
    """
    Проходит по всем PDF-файлам в папке data, извлекает их текст и 
    генерирует для каждого суммаризацию. Результаты сохраняются в 
    папке summary_folder с именами вида <оригинальное имя>_summary.pdf.
    
    Args:
        data_folder (str): Путь к папке с исходными PDF-файлами
        summary_folder (str): Путь к папке для сохранения суммаризаций
    """
    # Создаем папку для суммаризаций,
    """
    Проходит по всем PDF-файлам в папке data, извлекает их текст и 
    генерирует для каждого суммаризацию. Результаты сохраняются в 
    папке summary_folder с именами вида <оригинальное имя>_summary.pdf.
    
    Args:
        data_folder (str): Путь к папке с исходными PDF-файлами
        summary_folder (str): Путь к папке для сохранения суммаризаций
    """
    # Создаем папку для суммаризаций, если её нет
    if not os.path.exists(summary_folder):
        logger.info(f"Создание папки для суммаризаций: {summary_folder}")
        os.makedirs(summary_folder)
    
    # Получаем список PDF-файлов в папке
    files = os.listdir(data_folder)
    pdf_files = [f for f in files if f.lower().endswith(".pdf")]
    logger.info(f"Найдено {len(pdf_files)} PDF-файлов в папке {data_folder}")
    
    # Обрабатываем каждый файл
    for pdf_file in pdf_files:
        pdf_path = os.path.join(data_folder, pdf_file)
        logger.info(f"Обрабатывается файл: {pdf_path}")
        
        try:
            # Извлекаем текст
            logger.debug(f"Извлечение текста из файла {pdf_file}")
            content = get_pdf_content(pdf_path)
            
            # Суммаризируем
            logger.info(f"Начало суммаризации файла {pdf_file}")
            summary = summarize_text(content)
            
            # Сохраняем суммаризацию
            summary_file = os.path.join(summary_folder, pdf_file.replace(".pdf", "_summary.pdf"))
            logger.debug(f"Сохранение суммаризации в файл {summary_file}")
            save_summary_as_pdf(summary, summary_file)
            
            logger.info(f"Файл {pdf_file} успешно суммаризован и сохранён как {summary_file}")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {pdf_file}: {str(e)}")

if __name__ == "__main__":
    logger.info("Запуск процесса суммаризации PDF-файлов")
    process_files()
    logger.info("Процесс суммаризации завершен")