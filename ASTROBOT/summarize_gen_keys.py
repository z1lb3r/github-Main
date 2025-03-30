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
    if len(text) <= chunk_threshold:
        # Если текст достаточно короткий, суммаризируем его целиком
        prompt = (
            "Сделай краткое резюме следующего текста, выделив только основную ценную информацию, "
            "не превышающее 1000 слов:\n\n" + text
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
            return response.choices[0].message.content.strip()
        except Exception as e:
            print("Ошибка при суммаризации:", e)
            return "[Ошибка суммаризации]"
    else:
        # Если текст слишком длинный, разбиваем его на части
        chunks = [text[i:i+chunk_threshold] for i in range(0, len(text), chunk_threshold)]
        intermediate_summaries = []
        
        # Суммаризируем каждую часть отдельно
        for i, chunk in enumerate(chunks):
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
                intermediate_summaries.append(intermediate_summary)
            except Exception as e:
                print(f"Ошибка при суммаризации промежуточного чанка {i+1}:", e)
                intermediate_summaries.append("[Ошибка суммаризации]")
        
        # Объединяем все промежуточные суммаризации
        combined_summary_text = "\n".join(intermediate_summaries)
        
        # Если объединенный текст всё ещё слишком длинный, суммаризуем его повторно
        if len(combined_summary_text) > chunk_threshold:
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
                return final_summary
            except Exception as e:
                print("Ошибка при финальной суммаризации:", e)
                return combined_summary_text
        else:
            return combined_summary_text

def save_summary_as_pdf(summary, output_path):
    """
    Сохраняет переданный текст в PDF-файл с поддержкой Unicode.
    
    Args:
        summary (str): Текст для сохранения
        output_path (str): Путь для сохранения PDF-файла
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Добавляем шрифт с поддержкой кириллицы
    font_path = os.path.join(BASE_DIR, "fonts", "dejavusanscondensed.ttf")
    if not os.path.isfile(font_path):
        print(f"Шрифт не найден по пути: {font_path}")
        raise FileNotFoundError(f"Шрифт не найден по пути: {font_path}")
    
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)
    
    # Записываем текст в PDF
    for line in summary.split("\n"):
        pdf.multi_cell(0, 10, txt=line)
    
    # Сохраняем файл
    pdf.output(output_path)

def process_files(data_folder="data", summary_folder="data_summaries"):
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
        os.makedirs(summary_folder)
    
    # Получаем список PDF-файлов в папке
    files = os.listdir(data_folder)
    pdf_files = [f for f in files if f.lower().endswith(".pdf")]
    
    # Обрабатываем каждый файл
    for pdf_file in pdf_files:
        pdf_path = os.path.join(data_folder, pdf_file)
        print(f"Обрабатывается файл: {pdf_path}")
        
        try:
            # Извлекаем текст
            content = get_pdf_content(pdf_path)
            
            # Суммаризируем
            summary = summarize_text(content)
            
            # Сохраняем суммаризацию
            summary_file = os.path.join(summary_folder, pdf_file.replace(".pdf", "_summary.pdf"))
            save_summary_as_pdf(summary, summary_file)
            
            print(f"Файл {pdf_file} успешно суммаризован и сохранён как {summary_file}")
        except Exception as e:
            print(f"Ошибка при обработке файла {pdf_file}: {e}")

if __name__ == "__main__":
    process_files()