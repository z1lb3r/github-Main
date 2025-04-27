"""
Скрипт для подготовки эмбеддингов (векторных представлений) из DOCX-файлов.
Создает индексы FAISS для быстрого поиска по контенту файлов key1.docx и key2.docx.
"""

import os
import openai
import faiss
import numpy as np
from config import KEY1_DOCX_PATH, KEY2_DOCX_PATH, OPENAI_API_KEY
from docx_data import get_docx_content
from logger import services_logger as logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Константы
CHUNK_SIZE = 3000  # Размер фрагмента текста для эмбеддинга
EMBED_MODEL = "text-embedding-ada-002"  # Модель OpenAI для создания эмбеддингов

def chunk_text(full_text: str, chunk_size: int):
    """
    Разбивает полный текст на фрагменты указанного размера.
    
    Args:
        full_text (str): Полный текст для разбиения
        chunk_size (int): Размер фрагмента в символах
        
    Returns:
        list: Список фрагментов текста
    """
    chunks = []
    start = 0
    while start < len(full_text):
        end = start + chunk_size
        chunks.append(full_text[start:end])
        start = end
    
    logger.debug(f"Текст разбит на {len(chunks)} фрагментов по {chunk_size} символов")
    return chunks

def get_embedding(text: str):
    """
    Получает векторное представление (эмбеддинг) текста с помощью API OpenAI.
    
    Args:
        text (str): Текст для векторизации
        
    Returns:
        list: Векторное представление текста
    """
    logger.debug(f"Получение эмбеддинга для текста длиной {len(text)} символов")
    
    try:
        response = openai.embeddings.create(input=[text], model=EMBED_MODEL)
        logger.debug("Эмбеддинг успешно получен")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Ошибка при получении эмбеддинга: {str(e)}")
        raise

def prepare_embeddings(docx_path: str, index_file: str, chunks_file: str):
    """
    Подготавливает эмбеддинги из DOCX-файла и сохраняет их в виде индекса FAISS и массива фрагментов.
    
    Args:
        docx_path (str): Путь к DOCX-файлу
        index_file (str): Имя файла для сохранения индекса FAISS
        chunks_file (str): Имя файла для сохранения фрагментов текста
    """
    logger.info(f"Начало подготовки эмбеддингов для файла {docx_path}")
    
    # Получаем текст из DOCX-файла
    text = get_docx_content(docx_path)
    
    # Разбиваем текст на фрагменты
    chunks = chunk_text(text, CHUNK_SIZE)
    logger.info(f"Всего {len(chunks)} фрагментов для файла {docx_path}")
    
    # Получаем эмбеддинги для каждого фрагмента
    logger.info("Начало создания эмбеддингов для фрагментов")
    embeddings = []
    for i, ch in enumerate(chunks):
        logger.debug(f"Обработка фрагмента {i+1}/{len(chunks)}")
        embedding = get_embedding(ch)
        embeddings.append(embedding)
    
    # Преобразуем список эмбеддингов в массив NumPy
    embeddings_np = np.array(embeddings, dtype="float32")
    
    # Получаем размерность эмбеддингов
    dimension = embeddings_np.shape[1]
    logger.debug(f"Размерность эмбеддингов: {dimension}")
    
    # Создаем индекс FAISS для быстрого поиска
    logger.info("Создание индекса FAISS")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    
    # Сохраняем индекс и фрагменты
    logger.info(f"Сохранение индекса в файл {index_file}")
    faiss.write_index(index, index_file)
    
    logger.info(f"Сохранение фрагментов в файл {chunks_file}")
    np.save(chunks_file, np.array(chunks, dtype=object))
    
    logger.info(f"Векторный индекс сохранён: {index_file}")
    logger.info(f"Файл с фрагментами сохранён: {chunks_file}")

if __name__ == "__main__":
    # Устанавливаем API ключ для OpenAI
    openai.api_key = OPENAI_API_KEY
    logger.info("Установлен API ключ OpenAI")
    
    # Подготовка эмбеддингов для key1.docx
    logger.info("Начало подготовки эмбеддингов для key1.docx")
    prepare_embeddings(KEY1_DOCX_PATH, os.path.join(BASE_DIR, "key1.index"), os.path.join(BASE_DIR, "key1_chunks.npy"))

    # Подготовка эмбеддингов для key2.docx
    logger.info("Начало подготовки эмбеддингов для key2.docx")
    prepare_embeddings(KEY2_DOCX_PATH, os.path.join(BASE_DIR, "key2.index"), os.path.join(BASE_DIR, "key2_chunks.npy"))
    
    logger.info("Подготовка эмбеддингов успешно завершена")