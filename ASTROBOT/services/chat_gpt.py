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


def get_expert_comment(user_input: str, holos_data: dict) -> str:
    """
    Формируем запрос к ChatGPT, где роль бота — эксперт по Human Design,
    использует данные holos_data, даёт практические комментарии (до 350 слов),
    без фраз вроде 'я не знаю', 'я не эксперт'.
    """
    system_message = (
        "Ты — опытный консультант по Human Design и эзотерике. "
        "Избегай фраз 'я не знаю', 'не являюсь экспертом' и подобных дисклеймеров. "
        "Дай конкретные практические советы, основываясь на предоставленных данных. "
        "Ответ должен быть не длиннее 350 слов."
    )

    # Превратим holos_data в человекочитаемый текст
    holos_text = f"Данные с сайта Holos:\n{holos_data}"

    user_content = (
        f"Вопрос пользователя: {user_input}\n\n"
        f"{holos_text}\n\n"
        "Пожалуйста, прокомментируй эти данные и дай практические рекомендации "
        "с учётом Human Design и эзотерики. Не используй формулировки вроде 'я не знаю', "
        "'я не эксперт'. Ответ не более 350 слов."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # Или другой, если есть доступ (gpt-4, gpt-4o и т.п.)
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1200,  # Примерно чтобы не уходило за ~350 слов
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Ошибка при запросе к ChatGPT:", e)
        return "Произошла ошибка при генерации комментария. Попробуйте позже."
    

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
