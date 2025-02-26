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
    return chunks

def get_embedding(text: str):
    """
    Получает векторное представление (эмбеддинг) текста с помощью API OpenAI.
    
    Args:
        text (str): Текст для векторизации
        
    Returns:
        list: Векторное представление текста
    """
    response = openai.embeddings.create(input=[text], model=EMBED_MODEL)
    return response.data[0].embedding

def prepare_embeddings(docx_path: str, index_file: str, chunks_file: str):
    """
    Подготавливает эмбеддинги из DOCX-файла и сохраняет их в виде индекса FAISS и массива фрагментов.
    
    Args:
        docx_path (str): Путь к DOCX-файлу
        index_file (str): Имя файла для сохранения индекса FAISS
        chunks_file (str): Имя файла для сохранения фрагментов текста
    """
    # Получаем текст из DOCX-файла
    text = get_docx_content(docx_path)
    
    # Разбиваем текст на фрагменты
    chunks = chunk_text(text, CHUNK_SIZE)
    print(f"Всего {len(chunks)} фрагментов для файла {docx_path}")
    
    # Получаем эмбеддинги для каждого фрагмента
    embeddings = [get_embedding(ch) for ch in chunks]
    
    # Преобразуем список эмбеддингов в массив NumPy
    embeddings_np = np.array(embeddings, dtype="float32")
    
    # Получаем размерность эмбеддингов
    dimension = embeddings_np.shape[1]
    
    # Создаем индекс FAISS для быстрого поиска
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    
    # Сохраняем индекс и фрагменты
    faiss.write_index(index, index_file)
    np.save(chunks_file, np.array(chunks, dtype=object))
    
    print(f"Векторный индекс сохранён: {index_file}")
    print(f"Файл с фрагментами сохранён: {chunks_file}")

if __name__ == "__main__":
    # Устанавливаем API ключ для OpenAI
    openai.api_key = OPENAI_API_KEY
    
    # Подготовка эмбеддингов для key1.docx
    prepare_embeddings(KEY1_DOCX_PATH, "key1.index", "key1_chunks.npy")
    
    # Подготовка эмбеддингов для key2.docx
    prepare_embeddings(KEY2_DOCX_PATH, "key2.index", "key2_chunks.npy")