import aiohttp
from config import HOLOS_API_KEY

async def send_request_to_holos(
    holos_url: str,
    date_str: str,
    latitude: float,
    longitude: float,
    altitude: float
) -> dict:
    payload = {
        "key": HOLOS_API_KEY,
        "datetime": date_str,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(holos_url, json=payload) as response:
                response_data = await response.json()
                return response_data
    except Exception as e:
        print("Ошибка при обращении к API:", e)
        return {"status": "error", "message": str(e)}