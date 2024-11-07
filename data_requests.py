import requests
from requests.exceptions import RequestException
from model import OrderData, ZoneData, ExecuterProfile, ConfigMap, TollRoadsData
import json
import redis

# Инициализируем клиент Redis (по умолчанию Redis запускается на порту 6379)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

config_http = 'http://localhost:3629/configs'
CACHE_KEY = "config_cache"
CACHE_TTL = 60  # Кэш живет 60 секунд (1 минута)


class RequestHandler:
    @staticmethod
    def fetch_data(url: str, params: dict = None) -> dict:
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Проверка кода ответа
            data = response.json()       # Парсинг JSON
            return data
        except RequestException as e:
            print(f"Network error while fetching data from {url}: {e}")
            raise
        except ValueError as e:
            print(f"Error parsing JSON data from {url}: {e}")
            raise
        except KeyError as e:
            print(f"Missing expected data field in response from {url}: {e}")
            raise


order_http = 'http://localhost:3629/order-data'
zone_http = 'http://localhost:3629/zone-data'
executer_http = 'http://localhost:3629/executer-profile'
config_http = 'http://localhost:3629/configs'
toll_roads_http = 'http://localhost:3629/toll-roads'


def get_order_data(order_id: str) -> OrderData:
    data = RequestHandler.fetch_data(order_http, params={'id': order_id})
    return OrderData(
        id=order_id,
        zone_id=data.get('zone_id', ''),
        user_id=data.get('user_id', ''),
        base_coin_amount=data.get('base_coin_amount', 0.0)
    )


def get_zone_info(zone_id: str) -> ZoneData:
    data = RequestHandler.fetch_data(zone_http, params={'id': zone_id})
    return ZoneData(
        id=zone_id,
        coin_coeff=data.get('coin_coeff', 1.0),
        display_name=data.get('display_name', 'Unknown')
    )


def get_executer_profile(executer_id: str) -> ExecuterProfile:
    data = RequestHandler.fetch_data(executer_http, params={'id': executer_id})
    return ExecuterProfile(
        id=executer_id,
        tags=data.get('tags', []),
        rating=data.get('rating', 0.0)
    )


def get_configs() -> ConfigMap:
    # Проверяем кэш в Redis
    cached_data = redis_client.get(CACHE_KEY)

    if cached_data:
        # Декодируем и возвращаем кэшированные данные
        print("Fetching configs from cache.")
        config_data = json.loads(cached_data)
        return ConfigMap(config_data)

    # Если кэш пустой или устарел, получаем данные через HTTP
    print("Fetching configs from HTTP and updating cache.")
    config_data = RequestHandler.fetch_data(config_http)

    # Сохраняем данные в Redis с временем жизни (TTL)
    redis_client.set(CACHE_KEY, json.dumps(config_data), ex=CACHE_TTL)

    return ConfigMap(config_data)


def get_toll_roads(zone_display_name: str) -> TollRoadsData:
    data = RequestHandler.fetch_data(toll_roads_http, params={'zone_display_name': zone_display_name})
    return TollRoadsData(
        bonus_amount=data.get('bonus_amount', 0.0)
    )
