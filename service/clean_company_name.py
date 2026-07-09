import re

import pandas as pd


def clean_company_name(company_name):
    """
    Автор: Ажима Нимаева

    Метод очистки краткого названия компании для сопоставления
    данных из разных CSV перед загрузкой в БД.

    Принимает:
        company_name (str) - краткое название компании.

    Выполняет:
        - удаляет организационно-правовые формы (ООО, АО и т.д.);
        - удаляет кавычки;
        - приводит название к нижнему регистру;
        - заменяет ё на е;
        - удаляет лишние символы и пробелы.

    Возвращает:
        str - нормализованное название компании
        для поиска совпадений между таблицами.
    """

    if pd.isna(company_name) or not isinstance(company_name, str):
        return company_name

    # приводим к нижнему регистру
    company_name = company_name.lower()

    # приводим ё к е
    company_name = company_name.replace("ё", "е")

    # убираем кавычки
    company_name = re.sub(r'["\'«»]', '', company_name)

    # сокращенные организационно-правовые формы
    opf = [
        "ооо",
        "зао",
        "оао",
        "пао",
        "ао",
        "ип",
        "нко",
        "гуп",
        "муп"
    ]

    # удаляем ОПФ, только если это отдельное слово
    pattern = r'\b(' + '|'.join(opf) + r')\b'
    company_name = re.sub(pattern, '', company_name)

    # убираем все символы кроме букв, цифр, пробелов и дефиса
    company_name = re.sub(
        r'[^a-zа-я0-9\s-]',
        ' ',
        company_name
    )

    # убираем лишние пробелы
    company_name = re.sub(r'\s+', ' ', company_name)

    return company_name.strip()