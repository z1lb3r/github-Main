import os
import openai
import faiss
import numpy as np
from config import KEY1_DOCX_PATH, KEY2_DOCX_PATH, OPENAI_API_KEY
from docx_data import get_docx_content

# Можно использовать тот же размер фрагмента, что и для book1
CHUNK_SIZE = 3000  
EMBED_MODEL = "text-embedding-ada-002"

def chunk_text(full_text: str, chunk_size: int):
    """
    Разбивает полный текст на фрагменты указанного размера.
    """
    chunks = []
    start = 0
    while start < len(full_text):
        end = start + chunk_size
        chunks.append(full_text[start:end])
        start = end
    return chunks

def get_embedding(text: str):
    response = openai.embeddings.create(input=[text], model=EMBED_MODEL)
    return response.data[0].embedding

def prepare_embeddings(docx_path: str, index_file: str, chunks_file: str):
    text = get_docx_content(docx_path)
    chunks = chunk_text(text, CHUNK_SIZE)
    print(f"Всего {len(chunks)} фрагментов для файла {docx_path}")
    embeddings = [get_embedding(ch) for ch in chunks]
    embeddings_np = np.array(embeddings, dtype="float32")
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    faiss.write_index(index, index_file)
    np.save(chunks_file, np.array(chunks, dtype=object))
    print(f"Векторный индекс сохранён: {index_file}")
    print(f"Файл с фрагментами сохранён: {chunks_file}")

if __name__ == "__main__":
    openai.api_key = OPENAI_API_KEY
    # Подготовка эмбеддингов для key1.docx
    prepare_embeddings(KEY1_DOCX_PATH, "key1.index", "key1_chunks.npy")
    # Подготовка эмбеддингов для key2.docx
    prepare_embeddings(KEY2_DOCX_PATH, "key2.index", "key2_chunks.npy")
