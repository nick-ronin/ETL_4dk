"""
Модуль для сопоставления и фильтрации колонок (source_mapper)

Назначение:
- Принимает Excel-файл из папки output (результат работы source_loader)
- Оставляет только колонки, соответствующие ERD
- Добавляет отсутствующие колонки с пустыми значениями
- Сохраняет отфильтрованный результат в Excel

Вход:  output/standard_<имя>_<дата>.xlsx
Выход: output/filtered_<имя>_<дата>.xlsx

Автор: Шалатонин Кирилл Витальевич
Дата: 08.07.2026
"""

import pandas as pd
import os
from datetime import datetime
from pathlib import Path


# ============================================================
# 1. СПИСОК КОЛОНОК ИЗ ERD
# ============================================================

ERD_COLUMNS = {
    # === company ===
    'company': [
        'short_name',
        'full_name',
        'status',
        'opf',
        'inn',
        'kpp',
        'ogrn',
        'okpo',
        'okato',
        'oktmo',
        'okfs',
        'tax_system',
    ],
    
    # === company_details ===
    'company_details': [
        'registration_date',
        'authorized_capital',
        'employee_count',
        'msp_category',
        'source_url',
        'ifns_reg_date',
        'ifns_code',
        'ifns_name',
        'fss_reg_date',
        'fss_code',
        'fss_name',
        'pfr_reg_date',
        'pfr_code',
        'pfr_name',
        'special_tax_regimes',
        'average_headcount',
    ],
    
    # === financial_performance ===
    'financial_performance': [
        'year',
        'revenue',
        'sales_profit',
        'pretax_profit',
        'net_profit',
        'receivables',
        'payables',
        'inventory',
        'fixed_assets',
        'liquidity_abs',
        'liquidity_curr',
        'solvency_recovery',
        'fin_stability',
    ],
    
    # === address ===
    'address': [
        'address_type',
        'address',
        'city',
        'postal_index',
    ],
    
    # === activity_type ===
    'activity_type': [
        'okved_code',
        'activity_name',
        'is_main',
    ],
    
    # === director ===
    'director': [
        'director_full_name',
        'director_position',
        'director_inn',
        'director_year',
        'director_is_current',
    ],
    
    # === contact ===
    'contact': [
        'contact_type',
        'contact_value',
    ],
}

# Плоский список всех колонок из ERD (для фильтрации)
ALL_ERD_COLUMNS = []
for table, columns in ERD_COLUMNS.items():
    ALL_ERD_COLUMNS.extend(columns)

# Список колонок для MVP (базовый набор для быстрой работы)
MVP_COLUMNS = [
    'inn', 'kpp', 'ogrn',
    'short_name', 'full_name',
    'email', 'phone',
    'region', 'city', 'address',
    'contact_person', 'position',
    'source_name', 'source_date',
]


# ============================================================
# 2. ФУНКЦИЯ ПОИСКА ФАЙЛОВ
# ============================================================

def find_input_files(folder_path: str = "output", prefix: str = "standard_") -> list:
    """
    Находит все Excel-файлы в папке, которые начинаются с указанного префикса.
    
    Параметры:
        folder_path (str): путь к папке
        prefix (str): префикс для поиска
    
    Возвращает:
        list: список путей к найденным файлам
    """
    
    if not os.path.exists(folder_path):
        print(f"Папка не найдена: {folder_path}")
        return []
    
    found_files = []
    for file in os.listdir(folder_path):
        if file.startswith(prefix) and file.endswith('.xlsx'):
            file_path = os.path.join(folder_path, file)
            found_files.append(file_path)
            print(f"Найден файл: {file}")
    
    return found_files


# ============================================================
# 3. ОСНОВНЫЕ ФУНКЦИИ
# ============================================================

def load_file(file_path: str) -> pd.DataFrame:
    """Загружает Excel-файл."""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    df = pd.read_excel(file_path)
    print(f"Загружен файл: {os.path.basename(file_path)}")
    print(f"  Строк: {len(df)}, колонок: {len(df.columns)}")
    return df


def filter_columns(df: pd.DataFrame, 
                   required_columns: list = None) -> dict:
    """
    Оставляет в DataFrame только нужные колонки из ERD.
    Добавляет отсутствующие колонки с пустыми значениями.
    
    Параметры:
        df (pd.DataFrame): исходный DataFrame
        required_columns (list): список нужных колонок
    
    Возвращает:
        dict: результат с данными и отчётом
    """
    
    if required_columns is None:
        required_columns = ALL_ERD_COLUMNS
    
    # Определяем, какие колонки из нужного списка уже есть в DataFrame
    existing_columns = []
    missing_columns = []
    
    for col in required_columns:
        if col in df.columns:
            existing_columns.append(col)
        else:
            missing_columns.append(col)
    
    print(f"\n--- СОПОСТАВЛЕНИЕ КОЛОНОК ---")
    print(f"Всего в ERD: {len(required_columns)} колонок")
    print(f"Найдено в файле: {len(existing_columns)}")
    print(f"Будет добавлено пустых: {len(missing_columns)}")
    
    # Оставляем только нужные колонки (те, что есть в файле)
    df_filtered = df[existing_columns].copy() if existing_columns else pd.DataFrame()
    
    # Добавляем отсутствующие колонки с пустыми значениями
    for col in missing_columns:
        df_filtered[col] = None
    
    # Выводим информацию о сопоставлении по таблицам ERD
    print(f"\n--- СОПОСТАВЛЕНИЕ ПО ТАБЛИЦАМ ERD ---")
    for table, columns in ERD_COLUMNS.items():
        found = [col for col in columns if col in existing_columns]
        missing = [col for col in columns if col not in df.columns]
        if found or missing:
            print(f"  {table}: найдено {len(found)}/{len(columns)}")
            if missing:
                print(f"    отсутствуют: {', '.join(missing)}")
    
    return {
        'df': df_filtered,
        'stats': {
            'required_columns': len(required_columns),
            'existing_columns': len(existing_columns),
            'missing_columns': len(missing_columns),
            'added_columns': missing_columns,
            'removed_columns': [col for col in df.columns if col not in required_columns]
        }
    }


def save_to_excel(df: pd.DataFrame, 
                  output_folder: str = "output",
                  base_filename: str = "filtered") -> str:
    """
    Сохраняет DataFrame в Excel файл с автоматическим именем.
    """
    
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_filename}_{timestamp}.xlsx"
    file_path = os.path.join(output_folder, filename)
    
    df.to_excel(file_path, index=False, engine='openpyxl')
    print(f"\nФайл сохранён: {file_path}")
    print(f"  Строк: {len(df)}, колонок: {len(df.columns)}")
    
    return file_path


def process_file(input_file_path: str,
                 required_columns: list = None,
                 output_folder: str = "output") -> dict:
    """
    ГЛАВНАЯ ФУНКЦИЯ: загружает файл, фильтрует колонки, сохраняет результат.
    
    Параметры:
        input_file_path (str): путь к входному файлу
        required_columns (list): список нужных колонок (по умолчанию ALL_ERD_COLUMNS)
        output_folder (str): папка для сохранения результата
    
    Возвращает:
        dict: результат обработки
    """
    
    print("\n" + "=" * 60)
    print("ЗАПУСК source_mapper")
    print("=" * 60)
    
    if required_columns is None:
        required_columns = ALL_ERD_COLUMNS
    
    try:
        # ШАГ 1: Загружаем файл
        df = load_file(input_file_path)
        
        # ШАГ 2: Фильтруем колонки
        filter_result = filter_columns(df, required_columns)
        df_filtered = filter_result['df']
        
        # ШАГ 3: Сохраняем результат
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        base_name = base_name.replace('standard_', 'filtered_')
        saved_file_path = save_to_excel(df_filtered, output_folder, base_name)
        
        # ШАГ 4: Формируем результат
        result = {
            'status': 'OK',
            'input_file': input_file_path,
            'output_file': saved_file_path,
            'df': df_filtered,
            'stats': filter_result['stats']
        }
        
        print("\n" + "=" * 60)
        print(f"ОБРАБОТКА ЗАВЕРШЕНА. СТАТУС: OK")
        print(f"  Входной файл: {os.path.basename(input_file_path)}")
        print(f"  Выходной файл: {os.path.basename(saved_file_path)}")
        print(f"  Было колонок: {len(df.columns)}")
        print(f"  Стало колонок: {len(df_filtered.columns)}")
        print("=" * 60 + "\n")
        
        return result
    
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"ОШИБКА: {str(e)}")
        print("=" * 60 + "\n")
        
        return {
            'status': 'ERROR',
            'input_file': input_file_path,
            'output_file': None,
            'df': None,
            'stats': None,
            'error': str(e)
        }


# ============================================================
# 4. ПАРТИЙНАЯ ОБРАБОТКА
# ============================================================

def process_all_files(input_folder: str = "output",
                      required_columns: list = None,
                      output_folder: str = "output") -> list:
    """
    Обрабатывает все Excel-файлы в папке, которые начинаются с standard_.
    
    Параметры:
        input_folder (str): папка с входными файлами
        required_columns (list): список нужных колонок
        output_folder (str): папка для сохранения результата
    
    Возвращает:
        list: результаты обработки каждого файла
    """
    
    print("\n" + "=" * 60)
    print("ПАРТИЙНАЯ ОБРАБОТКА ФАЙЛОВ")
    print("=" * 60)
    
    # Находим все файлы
    files = find_input_files(input_folder)
    
    if not files:
        print("\nВ папке output не найдено файлов с префиксом 'standard_'")
        print("Запустите source_loader сначала, чтобы создать файлы для обработки")
        print("\n" + "=" * 60)
        return []
    
    print(f"\nНайдено файлов для обработки: {len(files)}")
    print("-" * 40)
    
    results = []
    for i, file_path in enumerate(files, 1):
        print(f"\n--- Обработка файла {i}: {os.path.basename(file_path)} ---")
        result = process_file(file_path, required_columns, output_folder)
        results.append(result)
    
    print("\n" + "=" * 60)
    print(f"ОБРАБОТКА ВСЕХ ФАЙЛОВ ЗАВЕРШЕНА")
    print(f"  Обработано: {len(results)} файлов")
    print(f"  Успешно: {len([r for r in results if r['status'] == 'OK'])}")
    print("=" * 60 + "\n")
    
    return results


# # ============================================================
# # 5. ТЕСТИРОВАНИЕ
# # ============================================================

# if __name__ == "__main__":
#     print("\n" + "=" * 60)
#     print("ТЕСТИРОВАНИЕ МОДУЛЯ source_mapper")
#     print("=" * 60 + "\n")
    
#     # Проверка списка колонок
#     print("ПРОВЕРКА: Список колонок из ERD")
#     print("-" * 40)
#     print(f"Всего колонок: {len(ALL_ERD_COLUMNS)}")
#     print(f"Колонки: {ALL_ERD_COLUMNS}")
#     print()
    
#     # Проверка по таблицам
#     print("ПРОВЕРКА: Колонки по таблицам ERD")
#     print("-" * 40)
#     for table, columns in ERD_COLUMNS.items():
#         print(f"  {table}: {len(columns)} колонок")
    
#     print("\n" + "=" * 60)
#     print("ЗАПУСК ОБРАБОТКИ")
#     print("=" * 60)
    
#     # Обрабатываем все файлы из папки output
#     results = process_all_files(
#         input_folder="output",
#         required_columns=ALL_ERD_COLUMNS,
#         output_folder="output"
#     )
    
#     print("\n" + "=" * 60)
#     print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
#     print("=" * 60)