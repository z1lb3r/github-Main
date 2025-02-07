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
    # Для последних версий openai можно использовать: response.data[0].embedding
    return response.data[0].embedding

def search_chunks(query: str, index, chunks):
    query_emb = get_embedding(query)
    query_emb_np = np.array([query_emb], dtype='float32')
    distances, indices = index.search(query_emb_np, TOP_K)
    results = [chunks[idx] for idx in indices[0]]
    return results

def answer_with_rag(query: str, holos_data: dict, mode: str = "free") -> str:
    """
    Формирует prompt для ChatGPT, используя релевантные фрагменты из книги (book1.pdf)
    и данные, полученные через API.
    
    Если mode=="4_aspects", ChatGPT должен:
      1. Определить тип личности пользователя на основе данных (дата, время, место рождения, полученных через API, и фрагментов из книги),
      2. В первом предложении явно указать этот тип личности и дать краткое описание,
      3. Затем дать подробное описание с практическими рекомендациями по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья.
    Ответ должен быть не длиннее 350 слов.
    
    Если mode=="free", ответ формируется свободно по теме.
    """
    index, chunks = load_index_and_chunks()
    top_fragments = search_chunks(query, index, chunks)
    context_text = "\n\n".join(top_fragments)
    holos_text = f"Данные с сайта Holos:\n{holos_data}" if holos_data else ""
    
    if mode == "4_aspects":
        system_msg = (
            "Ты — опытный консультант по Human Design и эзотерике. "
            "На основе предоставленных данных, которые включают сведения о дате, времени и месте рождения пользователя (полученные через API) "
            "и релевантные фрагменты из книги, определи тип личности пользователя и укажи его в первом предложении, давая краткое описание его особенностей. "
            "Затем предоставь подробное описание с практическими рекомендациями по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья. "
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
