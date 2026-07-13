"""
Модуль загрузки файлов (Source Loader)

Назначение:
- Читает Excel/CSV файлы
- Определяет лист, кодировку, базовые ошибки
- Принудительно загружает идентификаторы как строки (dtype=str)
- Возвращает сырой DataFrame с оригинальными заголовками

Автор: Шалатонин Кирилл Витальевич
Дата: 07.07.2026
"""

import pandas as pd
import os
from pathlib import Path

from logger.logger import logger

# Импортируем маппинг из source_mapper, чтобы знать,
# какие колонки должны быть прочитаны как строки
from service.source_processing.source_mapper import COLUMN_MAPPING, STRING_COLUMNS


# ============================================================
# 1. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _build_string_variants() -> set:
    """
    Строит множество всех возможных исходных названий колонок
    (русских и английских), которые должны читаться как строки.
    Использует COLUMN_MAPPING и STRING_COLUMNS из source_mapper.
    """
    variants = set()
    for std_col in STRING_COLUMNS:
        if std_col in COLUMN_MAPPING:
            for v in COLUMN_MAPPING[std_col]:
                variants.add(v.lower())
        # Добавляем само стандартное название на случай,
        # если файл уже пришёл с ним
        variants.add(std_col.lower())
    return variants

# Кэшируем множество для производительности
STRING_VARIANTS = _build_string_variants()


def find_test_files(folder_path: str = "test_files") -> list:
    """
    Находит все Excel и CSV файлы в указанной папке.
    Используется только для отладки/тестирования.
    """
    if not os.path.exists(folder_path):
        logger.info(f"Папка не найдена: {folder_path}")
        logger.info("Создайте папку 'test_files' и положите в неё Excel или CSV файлы")
        return []

    supported_extensions = ['.xlsx', '.xls', '.csv']
    found_files = []

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            ext = Path(file_path).suffix.lower()
            if ext in supported_extensions:
                found_files.append(file_path)
                logger.info(f"Найден файл: {file}")

    return found_files


# ============================================================
# 2. ОСНОВНАЯ ФУНКЦИЯ ЗАГРУЗКИ
# ============================================================

def load_file(file_path: str) -> pd.DataFrame:
    """
    Загружает Excel или CSV файл.
    Идентификаторы (ИНН, КПП, ОГРН и т.д.) принудительно читаются как строки,
    чтобы сохранить ведущие нули и избежать экспоненциальной записи.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    file_extension = Path(file_path).suffix.lower()

    # ---------- 1. Читаем только заголовки ----------
    if file_extension in ['.xlsx', '.xls']:
        header_df = pd.read_excel(file_path, nrows=0)
    elif file_extension == '.csv':
        try:
            header_df = pd.read_csv(file_path, encoding='utf-8', nrows=0)
        except UnicodeDecodeError:
            header_df = pd.read_csv(file_path, encoding='windows-1251', nrows=0)
    else:
        raise ValueError(f"Неподдерживаемый формат: {file_extension}. Используйте .xlsx, .xls или .csv")

    raw_columns = header_df.columns.tolist()

    # ---------- 2. Определяем, какие колонки читать как строки ----------
    string_dtype = {}
    for col in raw_columns:
        if col.strip().lower() in STRING_VARIANTS:
            string_dtype[col] = str

    # ---------- 3. Загружаем файл с dtype ----------
    try:
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, dtype=string_dtype)
            logger.info(f"Загружен Excel-файл: {os.path.basename(file_path)}")
        elif file_extension == '.csv':
            try:
                df = pd.read_csv(file_path, encoding='utf-8', dtype=string_dtype)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='windows-1251', dtype=string_dtype)
            logger.info(f"Загружен CSV-файл: {os.path.basename(file_path)}")

        logger.info(f"Строк: {len(df)}, колонок: {len(df.columns)}")
        if string_dtype:
            logger.info(f"Колонки, прочитанные как строки: {list(string_dtype.keys())}")
        return df
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла: {str(e)}")


def process_uploaded_file(file_path: str) -> dict:
    """
    Загружает файл и возвращает результат в формате, удобном для пайплайна.
    """
    logger.info("=" * 60)
    logger.info("ЗАПУСК ЗАГРУЗКИ ФАЙЛА (source_loader)")
    logger.info("=" * 60)

    try:
        df = load_file(file_path)
        result = {
            'status': 'OK',
            'df': df,
            'error': None,
            'mapping_info': {
                'total_columns': len(df.columns),
                'original_columns': list(df.columns)
            }
        }
        logger.info("ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО")
        return result
    except Exception as e:
        logger.info(f"ОШИБКА: {str(e)}")
        return {
            'status': 'ERROR',
            'df': None,
            'error': str(e),
            'mapping_info': None
        }