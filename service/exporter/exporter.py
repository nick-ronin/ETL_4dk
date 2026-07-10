"""
Модуль для выгрузки данных в Excel (exporter)

Назначение:
- Принимает готовый DataFrame с данными (уже с колонками качества, если они есть)
- Сохраняет его в Excel-файл
- Формирует служебный отчёт по обработке (количество строк, колонок, имена файлов)

Вход:  DataFrame с данными (может содержать колонки качества)
Выход: Excel-файл с данными

Автор: Шалатонин Кирилл Витальевич
Дата: 10.07.2026
"""

import pandas as pd
import os
from datetime import datetime


# ============================================================
# 1. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_timestamp() -> str:
    """Возвращает текущую дату и время в формате ГГГГММДД_ЧЧММСС"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_folder(folder_path: str) -> None:
    """Создаёт папку, если её нет"""
    os.makedirs(folder_path, exist_ok=True)


# ============================================================
# 2. ОСНОВНАЯ ФУНКЦИЯ ЭКСПОРТА
# ============================================================

def export_to_excel(df: pd.DataFrame,
                    output_folder: str = "output",
                    filename: str = "standard_clients") -> dict:
    """
    Экспортирует данные в Excel-файл.
    
    Параметры:
        df (pd.DataFrame): данные для экспорта (уже обработанные)
        output_folder (str): папка для сохранения
        filename (str): имя файла (без расширения)
    
    Возвращает:
        dict: статус и путь к сохранённому файлу
    """
    
    # Создаём папку, если её нет
    ensure_folder(output_folder)
    
    # Получаем временную метку
    timestamp = get_timestamp()
    
    # Формируем путь к файлу
    file_path = os.path.join(output_folder, f"{filename}_{timestamp}.xlsx")
    
    try:
        # Сохраняем данные в Excel
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        # Формируем результат
        result = {
            'status': 'OK',
            'file_path': file_path,
            'timestamp': timestamp,
            'rows': len(df),
            'columns': len(df.columns)
        }
        
        return result
    
    except Exception as e:
        return {
            'status': 'ERROR',
            'file_path': None,
            'error': str(e)
        }


def export_with_report(df: pd.DataFrame,
                       output_folder: str = "output",
                       filename_main: str = "standard_clients",
                       filename_report: str = "processing_report") -> dict:
    """
    Экспортирует данные в Excel и формирует простой служебный отчёт.
    
    Параметры:
        df (pd.DataFrame): данные для экспорта
        output_folder (str): папка для сохранения
        filename_main (str): имя основного файла
        filename_report (str): имя файла отчёта
    
    Возвращает:
        dict: статус и пути к файлам
    """
    
    ensure_folder(output_folder)
    timestamp = get_timestamp()
    
    main_file = os.path.join(output_folder, f"{filename_main}_{timestamp}.xlsx")
    report_file = os.path.join(output_folder, f"{filename_report}_{timestamp}.xlsx")
    
    try:
        # Сохраняем основные данные
        df.to_excel(main_file, index=False, engine='openpyxl')
        
        # Формируем простой служебный отчёт (только информация о файле)
        report_data = {
            'Параметр': [
                'Имя файла',
                'Дата обработки',
                'Количество строк',
                'Количество колонок',
                'Список колонок'
            ],
            'Значение': [
                os.path.basename(main_file),
                timestamp,
                len(df),
                len(df.columns),
                ', '.join(df.columns.tolist())
            ]
        }
        report_df = pd.DataFrame(report_data)
        report_df.to_excel(report_file, index=False, engine='openpyxl')
        
        return {
            'status': 'OK',
            'main_file': main_file,
            'report_file': report_file,
            'rows': len(df),
            'columns': len(df.columns)
        }
    
    except Exception as e:
        return {
            'status': 'ERROR',
            'main_file': None,
            'report_file': None,
            'error': str(e)
        }


def export_from_mapper(mapper_result: dict,
                       output_folder: str = "output") -> dict:
    """
    Принимает результат source_mapper и экспортирует в Excel.
    
    Параметры:
        mapper_result (dict): результат работы source_mapper
        output_folder (str): папка для сохранения
    
    Возвращает:
        dict: результат экспорта
    """
    
    if mapper_result['status'] == 'ERROR':
        return {
            'status': 'ERROR',
            'error': 'Нет данных для экспорта'
        }
    
    df = mapper_result['df']
    
    if df is None or len(df) == 0:
        return {
            'status': 'ERROR',
            'error': 'DataFrame пуст'
        }
    
    return export_with_report(
        df=df,
        output_folder=output_folder,
        filename_main="standard_clients",
        filename_report="processing_report"
    )


def export_simple(df: pd.DataFrame,
                  output_folder: str = "output",
                  filename: str = "data_export") -> str:
    """
    Простой экспорт одного DataFrame в Excel.
    
    Параметры:
        df (pd.DataFrame): данные для экспорта
        output_folder (str): папка для сохранения
        filename (str): имя файла
    
    Возвращает:
        str: путь к сохранённому файлу
    """
    
    ensure_folder(output_folder)
    timestamp = get_timestamp()
    file_path = os.path.join(output_folder, f"{filename}_{timestamp}.xlsx")
    
    df.to_excel(file_path, index=False, engine='openpyxl')
    
    return file_path