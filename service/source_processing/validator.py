"""
Модуль валидации данных (validator)

Назначение:
- Проверяет наличие обязательных полей в DataFrame
- Возвращает статус валидации и список проблем

Автор: Шалатонин Кирилл Витальевич
Дата: 13.07.2026
"""

import pandas as pd
from logger.logger import logger


def validate_required_columns(df: pd.DataFrame,
                              required_columns: list = None) -> dict:
    """
    Проверяет наличие обязательных колонок в DataFrame.
    
    Параметры:
        df (pd.DataFrame): данные для проверки
        required_columns (list): список обязательных колонок
                                 (по умолчанию ['inn'])
    
    Возвращает:
        dict: результат проверки со статусом и списками колонок
    """
    
    if required_columns is None:
        required_columns = ['inn']
    
    df.columns = df.columns.str.strip()
    
    existing_columns = [col for col in required_columns if col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    result = {
        'status': 'OK' if len(missing_columns) == 0 else 'WARNING',
        'required_columns': required_columns,
        'existing_columns': existing_columns,
        'missing_columns': missing_columns,
        'message': f"Найдено {len(existing_columns)} из {len(required_columns)} обязательных колонок"
    }
    
    if missing_columns:
        result['message'] += f". Отсутствуют: {', '.join(missing_columns)}"
        logger.warning(f"ВНИМАНИЕ! Отсутствуют колонки: {', '.join(missing_columns)}")
    else:
        result['message'] += ". Все обязательные колонки присутствуют"
        logger.info("Все обязательные колонки присутствуют")
    
    return result