import os
import openai
import PyPDF2
import faiss
import numpy as np

openai.api_key = "k-proj-WgHDLFHDIuXsVr5fKKbCP00GM8QffgnewdciZf1OFgFdxdxIr54w1dJl-jBd_CtjhNMbkTB4bqT3BlbkFJxd-hJJ2G61Y-vikmNDpV1qrFGSHszuVi8M9JnwHi8O4cAUnU5kifsMQXJzYHeAReKgFOLFn08A"  # Замените на ваш ключ из config.py, если нужно
PDF_PATH = "book1.pdf"
EMBED_MODEL = "text-embedding-ada-002"
CHUNK_SIZE = 3000  # Примерный размер куска текста
INDEX_FILE = "book1.index"
CHUNKS_FILE = "chunks.npy"

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
    response = openai.Embedding.create(input=[text], model=EMBED_MODEL)
    return response.data[0].embedding

def main():
    if not os.path.isfile(PDF_PATH):
        print(f"Файл {PDF_PATH} не найден.")
        return
    full_text = read_pdf(PDF_PATH)
    chunks = chunk_text(full_text, CHUNK_SIZE)
    print(f"Всего {len(chunks)} фрагментов")
    embeddings = [get_embedding(ch) for ch in chunks]
    embeddings_np = np.array(embeddings, dtype="float32")
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    faiss.write_index(index, INDEX_FILE)
    np.save(CHUNKS_FILE, np.array(chunks, dtype=object))
    print("Векторный индекс сохранён!")

if __name__ == "__main__":
    main()
