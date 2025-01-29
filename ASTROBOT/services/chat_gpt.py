import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def get_esoteric_astrology_response(user_input: str, pdf_content: str, holos_data: dict) -> str:
    """
    Генерирует ответ ChatGPT на вопрос пользователя, с учётом:
    - pdf_content: текст из PDF (экспертная информация),
    - holos_data: данные, полученные от geo.holos.house
    """
    system_message = (
        "Ты — виртуальный эзотерический и астрологический консультант, "
        "который также разбирается в Human Design. "
        "Используй предоставленные материалы из PDF (экспертная информация) "
        "и сведения, полученные из holos_data, чтобы давать точные и полезные ответы."
    )

    holos_text = ""
    if holos_data:
        holos_text = f"Данные c сайта Holos: {holos_data}"

    user_content = (
        f"Пользователь спрашивает: '{user_input}'.\n\n"
        f"Экспертные материалы из PDF:\n{pdf_content}\n\n"
        f"{holos_text}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_content}
            ],
            max_tokens=2000,
            temperature=0.7,
        )
        answer = response["choices"][0]["message"]["content"]
        return answer
    except Exception as e:
        print("Ошибка при запросе к ChatGPT:", e)
        return "Произошла ошибка при получении ответа от ChatGPT. Попробуйте позже."

def get_section_comment(section_name: str, pdf_content: str, holos_data: dict) -> str:
    """
    Генерирует краткий комментарий в зависимости от выбранного раздела
    (композит / Dream Rave) и полученных данных (holos_data).
    """
    # Допустим, используем ту же логику ChatGPT, но формируем особую prompt
    # чтобы получить именно КРАТКИЙ комментарий.
    system_message = (
        "Ты — виртуальный эзотерический и астрологический консультант, "
        "эксперт по Human Design. Дай краткий комментарий к результатам, "
        "основанный на PDF и данных Holos."
    )
    section_text = "композита" if "композит" in section_name else "Dream Rave"
    user_content = (
        f"Пользователь выполнил расчёт {section_text}. "
        f"Вот данные из Holos: {holos_data}\n\n"
        f"Экспертная информация из PDF:\n{pdf_content}\n\n"
        "Сформулируй краткий комментарий по итогам вычислений."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_content}
            ],
            max_tokens=700,
            temperature=0.7,
        )
        comment = response["choices"][0]["message"]["content"]
        return comment
    except Exception as e:
        print("Ошибка при формировании комментария ChatGPT:", e)
        return "Произошла ошибка при подготовке комментария. Попробуйте позже."