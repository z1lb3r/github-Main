"""
Сервис для отправки запросов к API Holos.
Получает астрологические данные по дате и месту рождения.
"""

import aiohttp
from config import HOLOS_API_KEY

async def send_request_to_holos(
    holos_url: str,
    date_str: str,
    latitude: float,
    longitude: float,
    altitude: float
) -> dict:
    """
    Отправляет запрос к API Holos для получения астрологических данных.
    
    Args:
        holos_url (str): URL API Holos
        date_str (str): Дата и время рождения (ГГГГ-ММ-ДД ЧЧ:ММ)
        latitude (float): Широта места рождения
        longitude (float): Долгота места рождения
        altitude (float): Высота места рождения
        
    Returns:
        dict: Ответ от API Holos в формате JSON или словарь с ошибкой
    """
    # Формируем JSON для запроса
    payload = {
        "key": HOLOS_API_KEY,
        "datetime": date_str,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude
    }
    
    try:
        # Отправляем POST-запрос к API
        async with aiohttp.ClientSession() as session:
            async with session.post(holos_url, json=payload) as response:
                response_data = await response.json()
                return response_data
    except Exception as e:
        print("Ошибка при обращении к API:", e)
        return {"status": "error", "message": str(e)}