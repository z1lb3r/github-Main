"""
Сервис для работы с API CrystalPay v3.
Создание платежей, проверка статуса платежей.
"""

import time
import json
import hashlib
import aiohttp
from typing import Dict, Optional, Tuple, List

from config import (
    CRYSTALPAY_SECRET_KEY,
    CRYSTALPAY_SALT,
    CRYSTALPAY_API_URL,
    CRYSTALPAY_CASHIER_URL,
    CRYSTALPAY_WALLET_ID,
    BOT_USERNAME
)
from logger import api_logger as logger

async def create_payment(user_id: int, amount: int = None, email: str = None) -> Tuple[bool, Dict]:
    """
    Создает платеж в CrystalPay для пополнения баланса.
    
    Args:
        user_id (int): ID пользователя в Telegram
        amount (int, optional): Сумма пополнения в рублях
        email (str, optional): Email пользователя, если доступен
        
    Returns:
        Tuple[bool, Dict]: Кортеж (успех, результат)
            - успех (bool): True, если платеж успешно создан, иначе False
            - результат (Dict): Результат запроса (данные платежа или ошибка)
    """
    # Проверяем, что сумма пополнения указана и находится в допустимых пределах
    if amount is None or amount < 100 or amount > 10000000:
        logger.warning(f"Недопустимая сумма пополнения: {amount} (должна быть от 100 до 10 000 000 руб.)")
        return False, {"error": "Недопустимая сумма пополнения (должна быть от 100 до 10 000 000 руб.)"}
    
    # Генерируем уникальный ID для платежа
    order_id = f"sub_{user_id}_{int(time.time())}"
    
    # Параметры для API запроса
    params = {
        "auth_login": CRYSTALPAY_WALLET_ID,
        "auth_secret": CRYSTALPAY_SECRET_KEY,
        "amount": amount,  # Используем переданную сумму в рублях
        "type": "purchase",  # Тип операции: purchase или topup
        "lifetime": 1440,  # Время жизни счета в минутах (24 часа)
        "description": f"Пополнение баланса бота @{BOT_USERNAME} на {amount} баллов",
        "redirect_url": f"https://t.me/{BOT_USERNAME}",  # URL для перенаправления после оплаты
        "extra": f"{order_id}:{amount}"  # Сохраняем order_id и сумму как дополнительную информацию
    }
    
    if email:
        params["payer_details"] = email
    
    try:
        # Отправляем запрос к API CrystalPay
        logger.info(f"Создание платежа для пользователя {user_id} на сумму {amount} руб.")
        response_data = await _make_request("invoice/create/", params)
        
        if response_data.get("error") is False:  # API возвращает {"error": false} при успехе
            logger.info(f"Платеж успешно создан: {response_data.get('id', 'ID не указан')}")
            return True, response_data
        else:
            error_message = response_data.get("message", "Unknown error")
            if "errors" in response_data:
                error_message = ", ".join(response_data["errors"])
            logger.error(f"Ошибка при создании платежа: {error_message}")
            return False, {"error": error_message}
            
    except Exception as e:
        logger.error(f"Исключение при создании платежа: {str(e)}")
        return False, {"error": str(e)}

async def check_payment(invoice_id: str) -> Tuple[bool, Dict]:
    """
    Проверяет статус платежа в CrystalPay.
    
    Args:
        invoice_id (str): ID счета в CrystalPay
        
    Returns:
        Tuple[bool, Dict]: Кортеж (успех, результат)
            - успех (bool): True, если операция успешна, иначе False
            - результат (Dict): Результат запроса
    """
    params = {
        "auth_login": CRYSTALPAY_WALLET_ID,
        "auth_secret": CRYSTALPAY_SECRET_KEY,
        "id": invoice_id
    }
    
    try:
        # Отправляем запрос к API CrystalPay
        logger.info(f"Проверка статуса платежа: {invoice_id}")
        response_data = await _make_request("invoice/info/", params)
        
        if response_data.get("error") is False:
            # Проверяем статус платежа
            state = response_data.get("state", "")
            
            # В CrystalPay v3 успешный статус обозначается как "success" или "paid"
            is_paid = state == "success" or state == "payed" or state == "paid"
            
            logger.info(f"Статус платежа {invoice_id}: {state} (оплачен: {is_paid})")
            return True, {
                "is_paid": is_paid,
                "state": state,
                "invoice_data": response_data
            }
        else:
            error_message = response_data.get("message", "Unknown error")
            if "errors" in response_data:
                error_message = ", ".join(response_data["errors"])
            logger.error(f"Ошибка при проверке платежа: {error_message}")
            return False, {"error": error_message}
            
    except Exception as e:
        logger.error(f"Исключение при проверке платежа: {str(e)}")
        return False, {"error": str(e)}

async def get_available_methods() -> Tuple[bool, List[Dict]]:
    """
    Получает список доступных методов оплаты.
    
    Returns:
        Tuple[bool, List[Dict]]: Кортеж (успех, результат)
            - успех (bool): True, если операция успешна, иначе False
            - результат (List[Dict]): Список доступных методов оплаты или ошибка
    """
    params = {
        "auth_login": CRYSTALPAY_WALLET_ID,
        "auth_secret": CRYSTALPAY_SECRET_KEY
    }
    
    try:
        # Отправляем запрос к API CrystalPay
        logger.info("Запрос доступных методов оплаты")
        response_data = await _make_request("method/list/", params)
        
        if response_data.get("error") is False:
            # Структура ответа в v3 отличается от v2
            methods = response_data.get("items", {})
            logger.info(f"Получено {len(methods)} методов оплаты")
            return True, methods
        else:
            error_message = response_data.get("message", "Unknown error")
            if "errors" in response_data:
                error_message = ", ".join(response_data["errors"])
            logger.error(f"Ошибка при получении методов оплаты: {error_message}")
            return False, [{"error": error_message}]
            
    except Exception as e:
        logger.error(f"Исключение при получении методов оплаты: {str(e)}")
        return False, [{"error": str(e)}]

async def _make_request(endpoint: str, params: Dict) -> Dict:
    """
    Отправляет запрос к API CrystalPay.
    
    Args:
        endpoint (str): Конечная точка API
        params (Dict): Параметры для запроса
        
    Returns:
        Dict: Ответ от API
    """
    url = f"{CRYSTALPAY_API_URL}/{endpoint}"
    
    logger.debug(f"Отправка запроса к {url}")
    if logger.isEnabledFor(10):  # DEBUG = 10
        logger.debug(f"Параметры: {json.dumps(params, indent=2)}")
    
    try:
        # Используем правильный формат для JSON-запросов
        headers = {
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            # Сериализуем params в JSON с помощью json=params вместо data=params
            async with session.post(url, headers=headers, json=params) as response:
                logger.debug(f"Статус ответа: {response.status}")
                response_data = await response.json()
                if logger.isEnabledFor(10):  # DEBUG = 10
                    logger.debug(f"Ответ: {json.dumps(response_data, indent=2)}")
                return response_data
    except Exception as e:
        logger.error(f"Ошибка запроса: {str(e)}")
        return {"error": True, "message": str(e)}

def generate_payment_link(invoice_id: str) -> str:
    """
    Генерирует ссылку для оплаты счета.
    
    Args:
        invoice_id (str): ID счета
        
    Returns:
        str: URL для оплаты
    """
    # URL формат в v3 изменился
    return f"{CRYSTALPAY_CASHIER_URL}/{invoice_id}"

def verify_signature(data: Dict, signature: str) -> bool:
    """
    Проверяет подпись вебхука от CrystalPay.
    
    Args:
        data (Dict): Данные вебхука
        signature (str): Подпись из заголовка запроса
        
    Returns:
        bool: True, если подпись верна, иначе False
    """
    # В v3 формат подписи изменился на {id}:{salt}
    invoice_id = data.get("id", "")
    data_str = f"{invoice_id}:{CRYSTALPAY_SALT}"
    
    # Вычисляем SHA-1 хеш (v3 использует SHA-1)
    calculated_signature = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
    
    is_valid = calculated_signature == signature
    if not is_valid:
        logger.warning(f"Недействительная подпись: ожидалось {calculated_signature}, получено {signature}")
    
    return is_valid