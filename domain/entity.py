from dataclasses import dataclass, replace
from typing import Optional


@dataclass
class MakeDltReserveResponse:
    status: str  # OK, FAILED
    message: str
    executed_time: float


@dataclass
class KeyValuePair:
    key: str
    value: str


@dataclass
class DltReserveInfo:
    action: str
    mode: str
    group: str
    number_reserve: str
    open: str
    close: str
    confirm: str
    car_type: str
    FYIZ: str
    ip: str
    locationz: str
    vzh: str  # count keyboard
    recaptcha_response: str
    prefixZQ: str
    reserve_number: str

    name: Optional[KeyValuePair] = None
    lastname: Optional[KeyValuePair] = None
    id: Optional[KeyValuePair] = None
    car_body_number: Optional[KeyValuePair] = None
    phone_number: Optional[KeyValuePair] = None
    brand: Optional[KeyValuePair] = None

    def update(self, name: KeyValuePair, last_name: KeyValuePair, id_number: KeyValuePair, phone_number: KeyValuePair,
               car_body_number: KeyValuePair, brand: KeyValuePair) -> 'DltReserveInfo':
        return replace(self,
                       name=name,
                       lastname=last_name,
                       id=id_number,
                       phone_number=phone_number,
                       brand=brand,
                       car_body_number=car_body_number,
                       vzh=str(len(car_body_number.value) + 1))
