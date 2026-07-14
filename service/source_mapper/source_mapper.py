"""
Модуль для сопоставления и фильтрации колонок (Source Mapper)

Назначение:
- Принимает DataFrame с данными (сырой, из source_loader)
- Сопоставляет поля источника с единым стандартом (COLUMN_MAPPING)
- Оставляет только колонки, соответствующие ERD / MVP
- Добавляет отсутствующие колонки с пустыми значениями

Автор: Шалатонин Кирилл Витальевич
Дата: 08.07.2026
"""

import pandas as pd
from datetime import datetime

from service.logger.logger import get_log_writer
from service.validator.validator import validate_required_columns

from service.source_mapper.constants import ERD_COLUMNS, COLUMN_MAPPING, ALL_ERD_COLUMNS


# ============================================================
# 1. ФУНКЦИИ МАППИНГА И ФИЛЬТРАЦИИ
# ============================================================

def map_columns(df_columns: list) -> dict:
    """
    Сопоставляет исходные названия колонок с единым стандартом.
    Возвращает словарь {исходное_название: стандартное_название}.
    """

    df_columns_clean = [col.strip() for col in df_columns]

    reverse_mapping = {}
    for standard, variants in COLUMN_MAPPING.items():
        for variant in variants:
            reverse_mapping[variant.lower()] = standard

    mapping_result = {}
    for col in df_columns_clean:
        col_lower = col.lower()
        mapping_result[col] = reverse_mapping.get(col_lower, col)

    return mapping_result


def normalize_columns(df: pd.DataFrame, log_file_path: str) -> pd.DataFrame:
    """
    Переименовывает колонки DataFrame согласно COLUMN_MAPPING.
    """
    write = get_log_writer(log_file_path)

    mapping = map_columns(df.columns.tolist())
    df_renamed = df.rename(columns=mapping)

    write(f"Сопоставлено колонок: {len(mapping)} из {len(df.columns)}")
    renamed_count = sum(1 for orig, std in mapping.items() if orig != std)
    if renamed_count:
        for orig, std in mapping.items():
            if orig != std:
                write(f"  {orig} -> {std}")
    else:
        write("  Все колонки уже в стандартном формате")

    return df_renamed


def filter_columns(df: pd.DataFrame,
                   log_file_path: str,
                   required_columns: list = None) -> dict:
    """
    Оставляет в DataFrame только нужные колонки,
    добавляет отсутствующие с пустыми значениями.
    """
    write = get_log_writer(log_file_path)

    if required_columns is None:
        required_columns = ALL_ERD_COLUMNS

    existing = [col for col in required_columns if col in df.columns]
    missing = [col for col in required_columns if col not in df.columns]

    write("--- СОПОСТАВЛЕНИЕ КОЛОНОК ---")
    write(f"Всего в ERD: {len(required_columns)} колонок")
    write(f"Найдено в файле: {len(existing)}")
    write(f"Будет добавлено пустых: {len(missing)}")

    df_filtered = df[existing].copy() if existing else pd.DataFrame()
    for col in missing:
        df_filtered[col] = None

    write("--- СОПОСТАВЛЕНИЕ ПО ТАБЛИЦАМ ERD ---")
    for table, columns in ERD_COLUMNS.items():
        found = [c for c in columns if c in existing]
        miss = [c for c in columns if c not in df.columns]
        if found or miss:
            write(f"  {table}: найдено {len(found)}/{len(columns)}")
            if miss:
                write(f"    отсутствуют: {', '.join(miss)}")

    return {
        'df': df_filtered,
        'stats': {
            'required_columns': len(required_columns),
            'existing_columns': len(existing),
            'missing_columns': len(missing),
            'added_columns': missing,
            'removed_columns': [col for col in df.columns if col not in required_columns]
        }
    }


# ============================================================
# 2. ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def process_file(df: pd.DataFrame,
                 log_file_path: str,
                 required_columns: list = None) -> dict:
    """
    Принимает DataFrame (сырой, после source_loader),
    переименовывает колонки, фильтрует под ERD/MVP.

    Параметры:
        df (pd.DataFrame): входные данные
        required_columns (list): список нужных колонок

    Возвращает:
        dict: с ключами 'status', 'df', 'validation_result', 'stats'
    """
    write = get_log_writer(log_file_path)

    write("=" * 60)
    write("ЗАПУСК source_mapper")
    write("=" * 60)

    if required_columns is None:
        required_columns = ALL_ERD_COLUMNS

    try:
        # Шаг 1: переименование
        df = normalize_columns(df, log_file_path)

        # Шаг 2: валидация обязательных колонок (вынесена в validator)
        validation_result = validate_required_columns(df, log_file_path, required_columns)

        # Шаг 3: фильтрация
        filter_result = filter_columns(df, log_file_path, required_columns)
        df_filtered = filter_result['df']

        result = {
            'status': 'OK' if validation_result['status'] == 'OK' else 'WARNING',
            'df': df_filtered,
            'validation_result': validation_result,
            'stats': filter_result['stats'],
        }

        write("=" * 60)
        write(f"МАППИНГ ЗАВЕРШЁН. СТАТУС: {result['status']}")
        write(f"  Итоговые колонки: {list(df_filtered.columns)}")
        write("=" * 60)

        return result

    except Exception as e:
        write(f"ОШИБКА: {str(e)}")
        return {
            'status': 'ERROR',
            'df': None,
            'validation_result': None,
            'stats': None,
            'error': str(e)
        }