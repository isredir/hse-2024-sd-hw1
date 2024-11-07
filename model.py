from dataclasses import dataclass
from abc import ABC, abstractmethod

from datetime import datetime


# Содержит в себе DTO (data transfer objects) / данные, получаемые из внешних источников


@dataclass
class OrderData:
    id: str
    user_id: str
    zone_id: str
    base_coin_amount: float


@dataclass
class ZoneData:
    id: str
    coin_coeff: float
    display_name: str


@dataclass
class ExecuterProfile:
    id: str
    tags: list[str]
    rating: float


@dataclass
class TollRoadsData:
    bonus_amount: float


@dataclass
class OrderAudit:
    assign_time: datetime
    acquire_time: datetime


@dataclass
class AssignedOrder:
    assign_order_id: str
    order_id: str
    executer_id: str
    coin_coeff: float
    coin_bonus_amount: float
    final_coin_amount: float
    route_information: str
    audit: OrderAudit


class Config(ABC):
    @abstractmethod
    def __getattr__(self, item):
        pass


class ConfigMap(Config):
    def __init__(self, data: dict):
        self._data = data
        for k, v in data.items():
            self.__setattr__(k, v)

    def __getattr__(self, item):
        return self._data.get(item, None)
