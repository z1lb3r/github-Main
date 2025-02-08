import faiss
import numpy as np
import openai
from config import OPENAI_API_KEY

# Пути для эмбеддингов для book1 и для key1
INDEX_FILE_BOOK = "book1.index"
CHUNKS_FILE_BOOK = "chunks.npy"
INDEX_FILE_KEY1 = "key1.index"
CHUNKS_FILE_KEY1 = "key1_chunks.npy"

EMBED_MODEL = "text-embedding-ada-002"
CHAT_MODEL = "gpt-4o"  # или используйте ту модель, к которой есть доступ
TOP_K = 3

openai.api_key = OPENAI_API_KEY

def load_index_and_chunks_for(source: str):
    if source == "book1":
        index = faiss.read_index(INDEX_FILE_BOOK)
        chunks = np.load(CHUNKS_FILE_BOOK, allow_pickle=True).tolist()
    elif source == "key1":
        index = faiss.read_index(INDEX_FILE_KEY1)
        chunks = np.load(CHUNKS_FILE_KEY1, allow_pickle=True).tolist()
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
    combined_fragments = []
    for source in ["book1", "key1"]:
        index, chunks = load_index_and_chunks_for(source)
        combined_fragments += search_chunks(query, index, chunks)
    return combined_fragments

def answer_with_rag(query: str, holos_data: dict, mode: str = "free", conversation_history: str = "", max_tokens: int = 1200) -> str:
    """
    Формирует prompt для ChatGPT, используя релевантные фрагменты из источников:
      - book1.pdf,
      - key1.docx,
    а также данные, полученные через API (holos_data) и историю диалога (conversation_history).

    Если mode=="4_aspects", ChatGPT должен:
      1. На основе предоставленных данных (сведения о дате, времени и месте рождения, полученные через API) и фрагментов из источников
         определить тип личности пользователя.
      2. В первой строке ответа явно указать: "Ваш тип личности: <тип>" с кратким описанием.
      3. Затем дать подробное описание с практическими рекомендациями по 4 аспектам:
         отношения/любовь, финансы, здоровье, источники счастья.
    Ответ не должен превышать 350 слов.

    Если mode=="free", ответ формируется свободно по теме.

    Параметр max_tokens определяет максимальное число токенов в ответе.
    """
    combined_fragments = search_all(query)
    context_text = "\n\n".join(combined_fragments)
    
    # Выводим читаемые фрагменты для отладки
    print("Релевантные фрагменты из источников (book1, key1):")
    print(context_text)
    
    holos_text = f"Данные с сайта Holos:\n{holos_data}" if holos_data else "[Нет данных]"
    
    if conversation_history:
        history_text = f"История диалога:\n{conversation_history}"
    else:
        history_text = ""
    
    if mode == "4_aspects":
        system_msg = (
            "Ты — интеллектуальный чат-бот, работающий на принципах рефлектора 5/1 из системы Дизайна Человека и генетических ключей. "
            "Используя предоставленные данные, включающие сведения о дате, времени и месте рождения пользователя (из API), "
            "а также релевантные фрагменты из книги (book1.pdf) и ключевого документа (key1.docx), определи тип личности пользователя. "
            "В первой строке ответа обязательно укажи: 'Ваш тип личности: <тип>' с кратким описанием его особенностей. "
            "Затем предоставь подробное описание с практическими рекомендациями по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья. "
            "Не используй фразы типа 'я не знаю' или 'не являюсь экспертом'. "
            "Ответ должен быть не длиннее 350 слов."
        )
    else:
        system_msg = (
            "Ты — эксперт по Human Design и эзотерике. "
            "Ответь на вопрос пользователя, используя предоставленные данные, историю диалога и фрагменты из источников. "
            "Ответ должен быть полезным и информативным."
        )
    
    user_prompt = f"""
--- Данные пользователя (БД и API) ---
{holos_text}

--- Фрагменты из источников (book1.pdf, key1.docx) ---
{context_text}

--- История диалога ---
{history_text}

Вопрос: {query}
"""
    response = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.7
    )
    return response.choices[0].message.content
