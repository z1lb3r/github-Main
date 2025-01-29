import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

# def get_esoteric_astrology_response(user_input: str, pdf_content: str, holos_data: dict) -> str:
#     # Текст, который будет передан роли developer (ранее system).
#     # Это «старшие» инструкции к боту — его стиль, тон, возможности.
#     developer_message = (
#         "Ты — виртуальный эзотерический и астрологический консультант, "
#         "разбираешься в Human Design. "
#         "Используй материалы из PDF (экспертная информация) "
#         "и сведения из holos_data, чтобы давать точные и полезные ответы."
#     )

def get_esoteric_astrology_response(user_input: str,  holos_data: dict) -> str:
    # Текст, который будет передан роли developer (ранее system).
    # Это «старшие» инструкции к боту — его стиль, тон, возможности.
    developer_message = (
        "Ты — виртуальный эзотерический и астрологический консультант, "
        "Эксперт в области Human Design. "
        "Окажи максимально экспертную консультацию, используя данные по этой теме"
    )

    # Сформируем текст, который передаём роли user:
    holos_text = f"Данные c сайта Holos: {holos_data}" if holos_data else ""
    user_message = (
        f"Пользователь спрашивает: '{user_input}'.\n\n"
    #    f"Экспертные материалы из PDF:\n{pdf_content}\n\n"
        f"{holos_text}"
    )

    try:
        # Новый способ: openai.chat.completions.create(...)
        response = openai.chat.completions.create(
            model="gpt-4o",        # Имя модели (по документации)
            messages=[
                {"role": "developer", "content": developer_message},
                {"role": "user", "content": user_message}
            ],
            store=True,           # По примеру из новых документов
            max_tokens=2000,
            temperature=0.7,
        )
        # Актуальный способ извлечь текст:
        return response.choices[0].message.content
    except Exception as e:
        print("Ошибка при запросе к ChatGPT:", e)
        return "Произошла ошибка при получении ответа от ChatGPT. Попробуйте позже."