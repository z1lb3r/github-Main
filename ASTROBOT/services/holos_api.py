import aiohttp
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
from config import HOLOS_API_KEY

async def convert_to_utc(date_str, latitude, longitude):
    """
    Преобразует локальное время в UTC на основе координат.
    
    Args:
        date_str (str): Строка даты и времени (формат: ГГГГ-ММ-ДД ЧЧ:ММ)
        latitude (float): Широта
        longitude (float): Долгота
        
    Returns:
        str: Строка даты и времени в UTC формате
    """
    try:
        # Определяем временную зону по координатам
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
        
        if not timezone_str:
            # Если временная зона не найдена, используем UTC
            print(f"Временная зона не найдена для координат {latitude}, {longitude}. Используем UTC.")
            timezone_str = 'UTC'
        
        # Получаем объект временной зоны
        timezone = pytz.timezone(timezone_str)
        
        # Преобразуем строку даты и времени в объект datetime
        local_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        
        # Привязываем к локальной временной зоне
        local_dt_with_tz = timezone.localize(local_dt)
        
        # Конвертируем в UTC
        utc_dt = local_dt_with_tz.astimezone(pytz.UTC)
        
        # Форматируем в строку
        utc_date_str = utc_dt.strftime('%Y-%m-%d %H:%M')
        
        print(f"Преобразование времени: Локальное [{timezone_str}]: {date_str} -> UTC: {utc_date_str}")
        
        return utc_date_str
    except Exception as e:
        print(f"Ошибка при преобразовании времени в UTC: {str(e)}")
        # В случае ошибки возвращаем исходное время
        return date_str

async def send_request_to_holos(holos_url, date_str, latitude, longitude, altitude):
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
    try:
        # Преобразуем локальное время в UTC
        utc_date_str = await convert_to_utc(date_str, latitude, longitude)
        
        # Формируем JSON для запроса в оригинальном формате
        payload = {
            "key": HOLOS_API_KEY,
            "datetime": utc_date_str,  # Используем UTC время
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude
        }
        
        print(f"Отправка запроса к API Holos с датой/временем (UTC): {utc_date_str}")
        
        # Отправляем POST-запрос к API
        async with aiohttp.ClientSession() as session:
            async with session.post(holos_url, json=payload) as response:
                response_data = await response.json()
                return response_data
    except Exception as e:
        print(f"Ошибка при обращении к API: {str(e)}")
        return {"status": "error", "message": str(e)}