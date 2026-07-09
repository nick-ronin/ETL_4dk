import re

import pandas as pd


def clean_address(address):
    """

    Принимает:
        address (str) - исходный адрес из CSV.

    Выполняет:
        - удаляет лишние пробелы и переносы строк;
        - приводит адрес к нижнему регистру;
        - нормализует обозначения улиц;
        - приводит дом, корпус и строение к единому виду;
        - сохраняет номер дома, корпуса и строения.

    Возвращает:
        str - очищенный адрес формата:
        "название улицы, номер дома стрномер корпномер"
    """

    if pd.isna(address) or not isinstance(address, str):
        return address

    address = address.lower()

    # убираем переносы и лишние пробелы
    address = re.sub(r'[\n\r\t]+', ' ', address)
    address = re.sub(r'\s+', ' ', address).strip()

    # нормализуем тип улицы
    address = re.sub(
        r'\b(улица|ул\.)\b',
        '',
        address
    )

    # приводим строение к стр1
    address = re.sub(
        r'\b(строение|стр\.?|ст\.?|с)\s*(\d+\w*)',
        r'стр\2',
        address
    )

    # приводим корпус к корп1
    address = re.sub(
        r'\b(корпус|корп\.?|к\.)\s*(\d+\w*)',
        r'корп\2',
        address
    )

    # убираем обозначение дома
    address = re.sub(
        r'\b(дом|д\.)\s*',
        '',
        address
    )

    # нормализуем запятые
    address = re.sub(r'\s*,\s*', ', ', address)

    # убираем лишние пробелы
    address = re.sub(r'\s+', ' ', address)

    return address.strip(" ,")