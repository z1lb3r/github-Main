import requests
from asyncio import to_thread

# Константы для работы с TRON
WALLET_ADDRESS = "THWugDaRTn6orsM7cuy77w7GqUAfizRrkv"
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Правильный контракт USDT TRC20
API_KEY = "04f04ee4-b03e-4965-bea8-a229a6e42a64"
PRIVATE_KEY = "16d842e72c9abf5da85f56a5f2b0cdeac09b31e77aa04f99a5325ebce10c288c"
BASE_URL = "https://api.trongrid.io"

def check_deposit_by_amount(amount: float):
    """
    Синхронная функция для проверки поступления депозита USDT с заданной суммой.
    Возвращает txid найденной транзакции, либо None.
    """
    amount_int = int(amount * 10**6)
    url = f"{BASE_URL}/v1/accounts/{WALLET_ADDRESS}/transactions/trc20"
    params = {
        "limit": 50,
        "contract_address": USDT_CONTRACT,
        "only_to": True,
        "only_confirmed": True
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if not data.get("data"):
            return None
        for tx in data["data"]:
            tx_value = int(tx.get("value", "0"))
            if tx_value == amount_int:
                return tx.get("transaction_id")
    except Exception as e:
        print("Error checking deposit:", e)
    return None

async def check_deposit_by_amount_async(amount: float):
    return await to_thread(check_deposit_by_amount, amount)

# Попытка использовать tronpy для отправки транзакций
try:
    from tronpy import Tron
    from tronpy.keys import PrivateKey
    client = Tron()
except ImportError:
    client = None

async def send_usdt(recipient_address: str, amount: float):
    if client:
        try:
            amount_int = int(amount * 10**6)
            priv_key = PrivateKey(bytes.fromhex(PRIVATE_KEY))
            txn = (
                client.trx.transfer_token(WALLET_ADDRESS, recipient_address, amount_int, USDT_CONTRACT)
                .build()
                .inspect()
                .sign(priv_key)
            )
            result = txn.broadcast().wait()
            if result.get("result"):
                return txn.txid
            else:
                print("Withdrawal transaction failed:", result)
                return None
        except Exception as e:
            print("Error sending USDT via tronpy:", e)
            return None
    else:
        try:
            function_selector = "transfer(address,uint256)"
            url = f"{BASE_URL}/wallet/triggersmartcontract"
            params = {
                "contract_address": USDT_CONTRACT,
                "function_selector": function_selector,
                "parameter": "",  # Здесь требуется правильное кодирование параметров
                "owner_address": WALLET_ADDRESS,
                "visible": True,
                "apikey": API_KEY
            }
            response = requests.post(url, json=params, timeout=10)
            tx_data = response.json()
            if not tx_data.get("result") or not tx_data["result"].get("result"):
                print("Error in trigger smart contract:", tx_data)
                return None
            unsigned_tx = tx_data["transaction"]
            sign_url = f"{BASE_URL}/wallet/gettransactionsign"
            sign_params = {
                "transaction": unsigned_tx,
                "privateKey": PRIVATE_KEY
            }
            sign_response = requests.post(sign_url, json=sign_params, timeout=10)
            signed_tx = sign_response.json()
            broadcast_url = f"{BASE_URL}/wallet/broadcasttransaction"
            broadcast_response = requests.post(broadcast_url, json=signed_tx, timeout=10)
            broadcast_result = broadcast_response.json()
            if broadcast_result.get("result"):
                return signed_tx.get("txID")
            else:
                print("Broadcast failed:", broadcast_result)
                return None
        except Exception as e:
            print("Error in send_usdt fallback:", e)
            return None
