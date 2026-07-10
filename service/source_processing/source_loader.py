"""
Модуль загрузки и нормализации источников данных (MVP)

Назначение:
- Загружает Excel/CSV файлы
- Приводит названия колонок к единому стандарту
- Проверяет наличие обязательных полей
- Сохраняет результат в Excel файл
- Возвращает данные в удобном для дальнейшей обработки виде

Автор: Шалатонин Кирилл Витальевич
Дата: 07.07.2026
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime


# ============================================================
# 1. СЛОВАРЬ СООТВЕТСТВИЙ КОЛОНОК (МАППИНГ)
# ============================================================

COLUMN_MAPPING = {
    # === ОСНОВНАЯ ИНФОРМАЦИЯ О КОМПАНИИ ===
    'client_id': ['ID клиента', 'Client ID', 'Уникальный ID', 'Внутренний ID'],
    'short_name': ['Сокращенное наименование', 'Краткое наименование', 'Название краткое', 'Short name', 'Название', 'Наименование организации', 'Название организации'],
    'full_name': ['Полное наименование', 'Полное название', 'Full name'],
    'status': ['Статус', 'Состояние', 'Действующее', 'Ликвидировано', 'В процессе реорганизации'],
    'opf': ['ОПФ', 'Организационная форма', 'Форма собственности', 'Тип юр. лица'],
    
    # === ИДЕНТИФИКАТОРЫ ===
    'inn': ['ИНН', 'инн', 'ИНН организации', 'ИНН контрагента', 'ИНН юр лица', 'ИНН клиента'],
    'kpp': ['КПП', 'кпп', 'КПП организации', 'КПП клиента'],
    'ogrn': ['ОГРН', 'огрн', 'ОГРН организации', 'ОГРН юр лица', 'ОГРН клиента'],
    'okpo': ['ОКПО', 'окпо', 'Код ОКПО'],
    'okato': ['ОКАТО', 'окато', 'Код ОКАТО'],
    'oktmo': ['ОКТМО', 'октмо', 'Код ОКТМО'],
    'okfs': ['ОКФС', 'окфс', 'Код ОКФС'],
    'tax_system': ['Система налогообложения', 'Налоговая система', 'СНО', 'Режим налогообложения'],

    # === РЕГИСТРАЦИОННЫЕ ДАННЫЕ ===
    'registration_date': ['Дата регистрации', 'Дата регистрации компании', 'Зарегистрирован'],
    'authorized_capital': ['Уставный капитал', 'Уставной капитал', 'Капитал'],
    'employee_count': ['Количество сотрудников', 'Численность сотрудников', 'Кол-во работников'],
    'msp_category': ['Категория МСП', 'МСП', 'Субъект МСП', 'Реестр МСП'],
    'source_url': ['Источник', 'URL источника', 'Ссылка', 'Веб-сайт', 'Сайт'],
    
    # === ИФНС ===
    'ifns_reg_date': ['Дата регистрации в ИФНС', 'Дата постановки на учет в ИФНС'],
    'ifns_code': ['Код ИФНС', 'ИФНС код', 'Код налоговой'],
    'ifns_name': ['ИФНС', 'Налоговая инспекция', 'Наименование ИФНС'],
    
    # === ФСС ===
    'fss_reg_date': ['Дата регистрации в ФСС', 'Дата постановки в ФСС'],
    'fss_code': ['Код ФСС', 'Код отделения ФСС'],
    'fss_name': ['ФСС', 'Наименование ФСС', 'Отделение ФСС'],
    
    # === ПФР ===
    'pfr_reg_date': ['Дата регистрации в ПФР', 'Дата постановки в ПФР'],
    'pfr_code': ['Код ПФР', 'Код отделения ПФР'],
    'pfr_name': ['ПФР', 'Наименование ПФР', 'Отделение ПФР'],
    
    # === НАЛОГИ И РЕЖИМЫ ===
    'special_tax_regimes': ['Специальные налоговые режимы', 'СНР', 'Спецрежимы'],
    'average_headcount': ['Среднесписочная численность', 'ССЧ', 'Средняя численность'],

    # === ФИНАНСОВЫЕ ПОКАЗАТЕЛИ ===
    'year': ['Год', 'Период', 'За год', 'Отчетный год'],
    'revenue': ['Выручка', 'Выручка от продаж', 'Доход'],
    'sales_profit': ['Прибыль от продаж', 'Прибыль от реализации'],
    'pretax_profit': ['Прибыль до налогообложения', 'Прибыль до налогов'],
    'net_profit': ['Чистая прибыль', 'Прибыль чистая'],
    'receivables': ['Дебиторская задолженность', 'Дебиторка'],
    'payables': ['Кредиторская задолженность', 'Кредиторка'],
    'inventory': ['Запасы', 'Товарные запасы', 'Материальные запасы'],
    'fixed_assets': ['Основные средства', 'ОС', 'Внеоборотные активы'],
    'liquidity_abs': ['Абсолютная ликвидность', 'Коэффициент абсолютной ликвидности'],
    'liquidity_curr': ['Текущая ликвидность', 'Коэффициент текущей ликвидности'],
    'solvency_recovery': ['Восстановление платежеспособности', 'Коэффициент восстановления платежеспособности'],
    'fin_stability': ['Финансовая устойчивость', 'Коэффициент финансовой устойчивости'],

    # === АДРЕСА ===
    'address_type': ['Тип адреса', 'Вид адреса', 'Юридический/фактический'],
    'address': ['Адрес', 'Юридический адрес', 'Фактический адрес', 'Адрес организации', 'Полный адрес'],
    'region': ['Регион', 'Область', 'Край', 'Субъект РФ', 'Республика', 'Регион РФ', 'Область/край'],
    'city': ['Город', 'Населенный пункт', 'Город/поселение', 'Нас. пункт', 'Город клиента'],
    'postal_index': ['Почтовый индекс', 'Индекс', 'Почт. индекс'],
    'district': ['Район', 'Район города', 'Округ'],

    # === ОКВЭД ===
    'okved_code': ['Код ОКВЭД', 'ОКВЭД', 'Код ОКВЭД-2', 'ОКВЭД-2'],
    'activity_name': ['Вид деятельности', 'Наименование деятельности', 'Название ОКВЭД'],
    'is_main': ['Основной вид деятельности', 'Основной ОКВЭД', 'Главный ОКВЭД'],

    # === РУКОВОДИТЕЛЬ ===
    'director_full_name': ['ФИО директора', 'Руководитель', 'Директор', 'Генеральный директор', 
                           'ФИО руководителя', 'Полное имя директора'],
    'contact_person': ['Контактное лицо', 'ФИО контакта', 'Ответственный', 
                       'Менеджер', 'ФИО менеджера', 'Контакт', 'Представитель'],
    'position': ['Должность', 'Должность контакта', 'Роль', 'Позиция в компании', 'Должность руководителя'],
    'director_inn': ['ИНН руководителя', 'ИНН директора'],
    'director_year': ['Год вступления на должность', 'Год назначения', 'Срок полномочий'],
    'director_is_current': ['Текущий руководитель', 'Действующий директор', 'Актуальный руководитель'],

    # === КОНТАКТЫ ===
    'email': ['Email', 'E-mail', 'Почта', 'Электронная почта', 'Адрес email', 
              'Эл. почта', 'Корпоративная почта', 'Электронный адрес'],
    'phone': ['Телефон', 'Телефоны', 'Мобильный телефон', 'Сотовый', 
              'Контактный телефон', 'Номер телефона', 'Телефон для связи', 
              'Рабочий телефон', 'Телефон основной', 'Немобильные'],
    'contact_phone_mobile': ['Мобильный', 'Мобильный телефон', 'Мобильный номер', 'Сотовый телефон', 'Мобильные'],
    'contact_website': ['Сайт', 'Веб-сайт', 'Website', 'URL', 'Ссылка на сайт'],
    'contact_whatsapp': ['whatsapp', 'WhatsApp', 'Ватсап', 'Whats App'],
    'contact_telegram': ['telegram', 'Telegram', 'ТГ', 'Телеграм'],
    'contact_vkontakte': ['vkontakte', 'Vkontakte', 'ВК', 'ВКонтакте', 'VK'],
    'contact_instagram': ['instagram', 'Instagram', 'Инстаграм', 'Инст'],

    # === СЛУЖЕБНЫЕ ПОЛЯ ===
    'source_name': ['Источник', 'Название источника', 'База данных', 'Система', 'Откуда выгрузка'],
    'source_type': ['Тип источника', 'Вид выгрузки', 'Формат источника', 'Тип данных'],
    'source_date': ['Дата выгрузки', 'Дата источника', 'Дата загрузки', 'Дата', 'Период'],

    # === ВЫЧИСЛЯЕМЫЕ ПОЛЯ ===
    'has_email': ['Есть email', 'Признак email', 'Email заполнен'],
    'has_phone': ['Есть телефон', 'Признак телефона', 'Телефон заполнен'],
    'duplicate_flag': ['Дубль', 'Признак дубля', 'Дубликат'],
    'data_quality_score': ['Оценка качества', 'DQ скор', 'Балл качества'],
    'processing_status': ['Статус обработки', 'Результат проверки', 'Валидность'],
    'processing_comment': ['Комментарий', 'Замечание', 'Ошибка валидации', 'Пояснение'],
}


# ============================================================
# 2. ФУНКЦИЯ ПОИСКА ФАЙЛОВ В ПАПКЕ
# ============================================================

def find_test_files(folder_path: str = "test_files") -> list:
    """
    Находит все Excel и CSV файлы в указанной папке.
    
    Параметры:
        folder_path (str): путь к папке (по умолчанию 'test_files')
    
    Возвращает:
        list: список путей к найденным файлам
    """
    
    if not os.path.exists(folder_path):
        print(f"Папка не найдена: {folder_path}")
        print("Создайте папку 'test_files' и положите в неё Excel или CSV файлы")
        return []
    
    supported_extensions = ['.xlsx', '.xls', '.csv']
    
    found_files = []
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            extension = Path(file_path).suffix.lower()
            if extension in supported_extensions:
                found_files.append(file_path)
                print(f"Найден файл: {file}")
    
    return found_files


# ============================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С КОЛОНКАМИ
# ============================================================

def map_columns(df_columns: list) -> dict:
    """
    Сопоставляет колонки из исходного файла с единым стандартом.
    """
    df_columns_clean = [col.strip() for col in df_columns]
    
    reverse_mapping = {}
    for standard, variants in COLUMN_MAPPING.items():
        for variant in variants:
            reverse_mapping[variant.lower()] = standard
    
    mapping_result = {}
    for col in df_columns_clean:
        col_lower = col.lower()
        if col_lower in reverse_mapping:
            mapping_result[col] = reverse_mapping[col_lower]
        else:
            mapping_result[col] = col
    
    return mapping_result


def get_standard_columns(mapping: dict) -> list:
    """Возвращает список стандартных названий колонок."""
    return list(mapping.values())


# ============================================================
# 4. ФУНКЦИЯ СОХРАНЕНИЯ В EXCEL
# ============================================================

def save_to_excel(df: pd.DataFrame, 
                  output_folder: str = "output",
                  base_filename: str = "standard_clients") -> str:
    """
    Сохраняет DataFrame в Excel файл с автоматическим именем.
    
    Параметры:
        df (pd.DataFrame): данные для сохранения
        output_folder (str): папка для сохранения (по умолчанию 'output')
        base_filename (str): основа имени файла (по умолчанию 'standard_clients')
    
    Возвращает:
        str: путь к сохранённому файлу
    
    Пример:
        >>> save_to_excel(df)
        'output/standard_clients_20260707_153045.xlsx'
    """
    
    # Создаём папку, если её нет
    os.makedirs(output_folder, exist_ok=True)
    
    # Формируем имя файла с датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_filename}_{timestamp}.xlsx"
    file_path = os.path.join(output_folder, filename)
    
    # Сохраняем DataFrame в Excel
    df.to_excel(file_path, index=False, engine='openpyxl')
    
    print(f"Файл сохранён: {file_path}")
    print(f"  Строк: {len(df)}, колонок: {len(df.columns)}")
    
    return file_path


# ============================================================
# 5. ОСНОВНЫЕ ФУНКЦИИ ЗАГРУЗКИ И ОБРАБОТКИ
# ============================================================

def load_file(file_path: str) -> pd.DataFrame:
    """Загружает Excel или CSV файл и возвращает pandas DataFrame."""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    file_extension = Path(file_path).suffix.lower()
    
    try:
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            print(f"Загружен Excel-файл: {os.path.basename(file_path)}")
        elif file_extension == '.csv':
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='windows-1251')
            print(f"Загружен CSV-файл: {os.path.basename(file_path)}")
        else:
            raise ValueError(f"Неподдерживаемый формат: {file_extension}. Используйте .xlsx, .xls или .csv")
        
        print(f"Строк: {len(df)}, колонок: {len(df.columns)}")
        return df
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла: {str(e)}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Приводит названия колонок к единому стандарту."""
    
    mapping = map_columns(df.columns.tolist())
    df_renamed = df.rename(columns=mapping)
    
    print(f"Сопоставлено колонок: {len(mapping)} из {len(df.columns)}")
    
    renamed_count = 0
    for original, standard in mapping.items():
        if original != standard:
            print(f"  {original} -> {standard}")
            renamed_count += 1
    
    if renamed_count == 0:
        print("  Все колонки уже в стандартном формате")
    
    return df_renamed


def validate_required_columns(df: pd.DataFrame, required_columns: list = None) -> dict:
    """
    Проверяет наличие обязательных колонок в DataFrame.
    
    Параметры:
        df (pd.DataFrame): данные для проверки
        required_columns (list): список обязательных колонок
    
    Возвращает:
        dict: результат проверки со статусом и списками колонок
    """
    
    if required_columns is None:
        required_columns = ['inn']
    
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
        print(f"ВНИМАНИЕ! Отсутствуют колонки: {', '.join(missing_columns)}")
    else:
        result['message'] += ". Все обязательные колонки присутствуют"
        print("Все обязательные колонки присутствуют")
    
    return result


def process_uploaded_file(file_path: str, 
                          required_columns: list = None,
                          save_output: bool = True,
                          output_folder: str = "output") -> dict:
    """
    ГЛАВНАЯ ФУНКЦИЯ: загружает файл, нормализует колонки, проверяет обязательные поля.
    
    Параметры:
        file_path (str): путь к файлу на диске
        required_columns (list): список обязательных колонок (по умолчанию ['inn'])
        save_output (bool): сохранять ли результат в Excel (по умолчанию True)
        output_folder (str): папка для сохранения (по умолчанию 'output')
    
    Возвращает:
        dict: результат обработки со статусом, данными и отчётом
    """
    
    print("\n" + "=" * 60)
    print("ЗАПУСК ОБРАБОТКИ ФАЙЛА")
    print("=" * 60)
    
    if required_columns is None:
        required_columns = ['inn']
    
    try:
        # ШАГ 1: Загружаем файл
        df = load_file(file_path)
        
        # ШАГ 2: Приводим колонки к стандарту
        df = normalize_columns(df)
        
        # ШАГ 3: Проверяем обязательные колонки
        validation_result = validate_required_columns(df, required_columns)
        
        # ШАГ 4: Сохраняем результат в Excel (если нужно)
        saved_file_path = None
        if save_output and df is not None:
            # Формируем имя файла на основе исходного
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            saved_file_path = save_to_excel(df, output_folder, f"standard_{base_name}")
        
        # ШАГ 5: Формируем результат
        result = {
            'status': 'OK' if validation_result['status'] == 'OK' else 'WARNING',
            'df': df,
            'validation_result': validation_result,
            'error': None,
            'saved_file': saved_file_path,
            'mapping_info': {
                'total_columns': len(df.columns),
                'standard_columns': list(df.columns)
            }
        }
        
        print("\n" + "=" * 60)
        print(f"ОБРАБОТКА ЗАВЕРШЕНА. СТАТУС: {result['status']}")
        if saved_file_path:
            print(f"РЕЗУЛЬТАТ СОХРАНЁН: {saved_file_path}")
        print("=" * 60 + "\n")
        
        return result
    
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"ОШИБКА: {str(e)}")
        print("=" * 60 + "\n")
        
        return {
            'status': 'ERROR',
            'df': None,
            'validation_result': None,
            'error': str(e),
            'saved_file': None,
            'mapping_info': None
        }