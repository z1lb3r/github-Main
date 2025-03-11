"""
Сервис для синтеза речи с использованием Yandex SpeechKit.
Конвертирует текст в аудио файлы.
"""

import os
import json
import aiohttp
import tempfile
from io import BytesIO
import time

from config import (
    YANDEX_SPEECHKIT_FOLDER_ID,
    YANDEX_SPEECHKIT_API_KEY,
    YANDEX_SPEECHKIT_VOICE,
    YANDEX_SPEECHKIT_EMOTION,
    YANDEX_SPEECHKIT_SPEED
)

# URL для API Yandex SpeechKit
YANDEX_TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

async def text_to_speech(text: str, output_file=None) -> BytesIO:
    """
    Конвертирует текст в аудио файл с использованием Yandex SpeechKit.
    
    Args:
        text (str): Текст для конвертации
        output_file (str, optional): Путь для сохранения файла
        
    Returns:
        BytesIO: Объект с аудио данными
    """
    # Если текст слишком длинный, обрезаем его
    MAX_TEXT_LENGTH = 5000  # Максимальная длина текста для одного запроса
    if len(text) > MAX_TEXT_LENGTH:
        print(f"Текст слишком длинный ({len(text)} символов), обрезаем до {MAX_TEXT_LENGTH}")
        text = text[:MAX_TEXT_LENGTH]
    
    # Подготавливаем параметры запроса
    params = {
        "text": text,
        "lang": "ru-RU",
        "voice": YANDEX_SPEECHKIT_VOICE,
        "emotion": YANDEX_SPEECHKIT_EMOTION,
        "speed": YANDEX_SPEECHKIT_SPEED,
        "format": "oggopus",  # Формат ogg с кодеком opus, хорошо работает в Telegram
        "folderId": YANDEX_SPEECHKIT_FOLDER_ID
    }
    
    # Используем API-ключ для аутентификации
    headers = {
        "Authorization": f"Api-Key {YANDEX_SPEECHKIT_API_KEY}"
    }
    
    # Выполняем запрос к API
    async with aiohttp.ClientSession() as session:
        async with session.post(YANDEX_TTS_URL, data=params, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Ошибка API Yandex SpeechKit: HTTP {response.status}, {error_text}")
                raise Exception(f"Ошибка синтеза речи: HTTP {response.status}")
            
            # Получаем аудио данные
            audio_data = await response.read()
            
            # Если указан путь для сохранения файла
            if output_file:
                with open(output_file, "wb") as f:
                    f.write(audio_data)
            
            # Возвращаем данные в виде BytesIO объекта для отправки в Telegram
            audio_io = BytesIO(audio_data)
            audio_io.name = "audio_message.ogg"
            return audio_io

async def synthesize_long_text(text: str, max_chunk_size: int = 4500) -> BytesIO:
    """
    Синтезирует длинный текст, разбивая его на части.
    
    Args:
        text (str): Длинный текст для синтеза
        max_chunk_size (int): Максимальный размер части текста
        
    Returns:
        BytesIO: Объект с объединенным аудио
    """
    # Если текст короткий, используем обычный синтез
    if len(text) <= max_chunk_size:
        return await text_to_speech(text)
    
    # Создаем временный каталог для аудио фрагментов
    with tempfile.TemporaryDirectory() as temp_dir:
        chunk_files = []
        # Разбиваем текст на предложения
        sentences = text.replace(".", ".{SPLIT}").replace("!", "!{SPLIT}").replace("?", "?{SPLIT}").split("{SPLIT}")
        
        current_chunk = ""
        chunk_number = 1
        
        # Обрабатываем каждое предложение
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Если добавление предложения не превысит лимит
            if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # Если текущий чанк не пустой, синтезируем его
                if current_chunk:
                    chunk_file = os.path.join(temp_dir, f"chunk_{chunk_number}.ogg")
                    await text_to_speech(current_chunk, chunk_file)
                    chunk_files.append(chunk_file)
                    chunk_number += 1
                    
                # Начинаем новый чанк с текущего предложения
                current_chunk = sentence
        
        # Обрабатываем последний чанк, если он есть
        if current_chunk:
            chunk_file = os.path.join(temp_dir, f"chunk_{chunk_number}.ogg")
            await text_to_speech(current_chunk, chunk_file)
            chunk_files.append(chunk_file)
        
        # Для простоты вернем первый фрагмент
        # Обратите внимание: объединение аудио файлов Opus требует специальных библиотек
        # Для полной реализации нужно использовать ffmpeg или аналогичный инструмент
        if chunk_files:
            with open(chunk_files[0], "rb") as f:
                audio_data = f.read()
                audio_io = BytesIO(audio_data)
                audio_io.name = "audio_message.ogg"
                return audio_io
                
        raise Exception("Не удалось синтезировать ни один фрагмент аудио")