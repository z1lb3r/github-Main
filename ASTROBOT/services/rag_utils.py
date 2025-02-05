import faiss
import numpy as np
import openai
from config import OPENAI_API_KEY

INDEX_FILE = "book1.index"
CHUNKS_FILE = "chunks.npy"
EMBED_MODEL = "text-embedding-ada-002"
CHAT_MODEL = "gpt-4o"  # Или используйте нужную модель
TOP_K = 3

openai.api_key = OPENAI_API_KEY

def load_index_and_chunks():
    index = faiss.read_index(INDEX_FILE)
    chunks = np.load(CHUNKS_FILE, allow_pickle=True)
    return index, chunks

def get_embedding(text: str):
    response = openai.embeddings.create(input=[text], model=EMBED_MODEL)
    return response.data[0].embedding

def search_chunks(query: str, index, chunks):
    query_emb = get_embedding(query)
    query_emb_np = np.array([query_emb], dtype='float32')
    distances, indices = index.search(query_emb_np, TOP_K)
    results = [chunks[idx] for idx in indices[0]]
    return results

def answer_with_rag(query: str, holos_data: dict) -> str:
    """
    Формирует prompt для ChatGPT, используя релевантные фрагменты из книги (book1.pdf)
    и данные, полученные через API. Теперь ChatGPT должен дать описание и практические рекомендации
    по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья.
    Ответ должен быть не длиннее 350 слов.
    """
    index, chunks = load_index_and_chunks()
    top_fragments = search_chunks(query, index, chunks)
    context_text = "\n\n".join(top_fragments)
    holos_text = f"Данные с сайта Holos:\n{holos_data}" if holos_data else ""
    
    system_msg = (
        "Ты — опытный консультант по Human Design и эзотерике. "
        "Дай подробное описание и практические рекомендации по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья. "
        "Не используй фразы типа 'я не знаю' или 'не являюсь экспертом'. "
        "Ответ должен быть не длиннее 350 слов."
    )
    user_prompt = f"""
{holos_text}

Вот релевантные фрагменты из книги:
{context_text}

Вопрос: {query}
"""
    response = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1200,
        temperature=0.7
    )
    return response.choices[0].message.content
