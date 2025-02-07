import faiss
import numpy as np
import openai
from config import OPENAI_API_KEY

# Пути для book1 (уже имеются)
INDEX_FILE_BOOK = "book1.index"
CHUNKS_FILE_BOOK = "chunks.npy"
# Пути для key1 и key2 (подготовленные с помощью prepare_key_embeddings.py)
INDEX_FILE_KEY1 = "key1.index"
CHUNKS_FILE_KEY1 = "key1_chunks.npy"
INDEX_FILE_KEY2 = "key2.index"
CHUNKS_FILE_KEY2 = "key2_chunks.npy"

EMBED_MODEL = "text-embedding-ada-002"
CHAT_MODEL = "gpt-4o"  # или используйте модель, к которой у вас есть доступ
TOP_K = 3

openai.api_key = OPENAI_API_KEY

def load_index_and_chunks_for(source: str):
    if source == "book1":
        index = faiss.read_index(INDEX_FILE_BOOK)
        chunks = np.load(CHUNKS_FILE_BOOK, allow_pickle=True).tolist()
    elif source == "key1":
        index = faiss.read_index(INDEX_FILE_KEY1)
        chunks = np.load(CHUNKS_FILE_KEY1, allow_pickle=True).tolist()
    elif source == "key2":
        index = faiss.read_index(INDEX_FILE_KEY2)
        chunks = np.load(CHUNKS_FILE_KEY2, allow_pickle=True).tolist()
    else:
        index, chunks = None, []
    return index, chunks

def get_embedding(text: str):
    response = openai.embeddings.create(input=[text], model=EMBED_MODEL)
    return response.data[0].embedding

def search_chunks(query: str, index, chunks):
    query_emb = get_embedding(query)
    query_emb_np = np.array([query_emb], dtype="float32")
    distances, indices = index.search(query_emb_np, TOP_K)
    results = [chunks[idx] for idx in indices[0]]
    return results

def search_all(query: str) -> list:
    fragments = []
    for source in ["book1", "key1", "key2"]:
        index, chunks = load_index_and_chunks_for(source)
        fragments += search_chunks(query, index, chunks)
    return fragments

def answer_with_rag(query: str, holos_data: dict, mode: str = "free") -> str:
    """
    Формирует prompt для ChatGPT, используя релевантные фрагменты из всех источников:
    - book1.pdf,
    - key1.docx,
    - key2.docx,
    а также данные, полученные через API (holos_data).

    Если mode=="4_aspects", ChatGPT должен:
      1. На основе предоставленных данных (сведения о дате, времени и месте рождения, полученные через API)
         и фрагментов из книги и документов key1, key2, определить тип личности пользователя.
      2. В первой строке ответа явно указать: "Ваш тип личности: <тип>" с кратким описанием.
      3. Затем дать подробное описание с практическими рекомендациями по 4 аспектам:
         отношения/любовь, финансы, здоровье, источники счастья.
    Ответ не должен превышать 350 слов.

    Если mode=="free", ответ формируется свободно по теме.
    """
    combined_fragments = search_all(query)
    context_text = "\n\n".join(combined_fragments)
    holos_text = f"Данные с сайта Holos:\n{holos_data}" if holos_data else "[Нет данных с сайта Holos]"
    
    if mode == "4_aspects":
        system_msg = (
            "Ты — интеллектуальный чат-бот, работающий на принципах рефлектора 5/1 из системы Дизайна Человека и генетических ключей. "
            "Используя предоставленные данные, которые включают сведения о дате, времени и месте рождения пользователя (из API) "
            "и релевантные фрагменты из книги (book1.pdf) и документов (key1.docx, key2.docx), определи тип личности пользователя. "
            "В первой строке ответа обязательно укажи: 'Ваш тип личности: <тип>' с кратким описанием его особенностей. "
            "Затем дай подробное описание с практическими рекомендациями по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья. "
            "Не используй фразы типа 'я не знаю' или 'не являюсь экспертом'. "
            "Ответ должен быть не длиннее 350 слов."
        )
    else:
        system_msg = (
            "Ты — эксперт по Human Design и эзотерике. "
            "Ответь на вопрос пользователя, используя предоставленные данные. "
            "Ответ должен быть полезным и информативным."
        )
    
    user_prompt = f"""
--- Данные, полученные через API ---
{holos_text}

--- Фрагменты из книги и документов (book1.pdf, key1.docx, key2.docx) ---
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
