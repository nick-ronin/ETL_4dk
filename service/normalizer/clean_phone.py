import pandas as pd
import re

def clean_phone(phone_raw):
    """
    Приводит номера телефонов к формату +7XXXXXXXXXX.
    Поддерживает разделители: ; , / |.
    Номера, начинающиеся с 8, заменяются на +7.
    Если номер уже содержит +, он сохраняется.
    Несколько номеров в одной ячейке объединяются через ', '.
    """
    if pd.isna(phone_raw):
        return phone_raw

    # Разбиваем по основным разделителям (точка с запятой, запятая, слэш, вертикальная черта)
    parts = re.split(r'[;,/|]\s*', phone_raw.strip())
    cleaned_parts = []

    for part in parts:
        if not part.strip():
            continue

        # Проверяем, есть ли '+' в начале
        has_plus = part.strip().startswith('+')

        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', part)

        if not digits:
            continue

        # Если номер начинается с 8, заменяем на 7 (для российских номеров)
        if digits.startswith('8'):
            digits = '7' + digits[1:]

        # Добавляем '+' в зависимости от исходного формата
        if has_plus:
            # Если уже был плюс, но номер начинался с 8 после очистки, мы уже исправили
            cleaned = '+' + digits
        else:
            # Если номер начинается с 7, добавляем '+'
            if digits.startswith('7'):
                cleaned = '+' + digits
            else:
                # На случай, если номер не содержит кода страны – добавляем '+7' (можно изменить по необходимости)
                cleaned = '+7' + digits

        cleaned_parts.append(cleaned)

    # Объединяем части через запятую с пробелом
    return ', '.join(cleaned_parts) if cleaned_parts else None