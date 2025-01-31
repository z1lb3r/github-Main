import os
import openai
import PyPDF2
import faiss
import numpy as np

openai.api_key = "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"
PDF_PATH = "book1.pdf"
EMBED_MODEL = "text-embedding-ada-002"
CHUNK_SIZE = 3000  # Примерный размер куска текста
INDEX_FILE = "book1.index"  # Файл, куда будем сохранять индекс
CHUNKS_FILE = "chunks.npy"   # Файл, где храним текстовые фрагменты

def read_pdf(pdf_path: str) -> str:
    text_output = []
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_output.append(page_text)
    return "\n".join(text_output)

def chunk_text(full_text: str, chunk_size: int):
    chunks = []
    start = 0
    while start < len(full_text):
        end = start + chunk_size
        chunk = full_text[start:end]
        chunks.append(chunk)
        start = end
    return chunks

def get_embedding(text: str):
    response = openai.embeddings.create(input=[text], model=EMBED_MODEL)
    emb = response.data[0].embedding
    return emb

def main():
    # 1) Читаем PDF
    if not os.path.isfile(PDF_PATH):
        print(f"Файл {PDF_PATH} не найден.")
        return
    full_text = read_pdf(PDF_PATH)

    # 2) Разбиваем на куски
    chunks = chunk_text(full_text, CHUNK_SIZE)
    print(f"Всего {len(chunks)} фрагментов")

    # 3) Создаём эмбеддинги
    embeddings = []
    for ch in chunks:
        emb = get_embedding(ch)
        embeddings.append(emb)

    embeddings_np = np.array(embeddings, dtype='float32')

    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)

    # 4) Сохраняем индекс на диск
    faiss.write_index(index, INDEX_FILE)
    # Сохраняем chunks
    np.save(CHUNKS_FILE, np.array(chunks, dtype=object))

    print("Векторный индекс сохранён!")

if __name__ == "__main__":
    main()