"""
Модуль для сопоставления и фильтрации колонок (Source Mapper)

Назначение:
- Принимает DataFrame с данными (сырой, из source_loader)
- Сопоставляет поля источника с единым стандартом (COLUMN_MAPPING)
- Оставляет только колонки, соответствующие ERD / MVP
- Добавляет отсутствующие колонки с пустыми значениями
- Опционально сохраняет результат в Excel

Автор: Шалатонин Кирилл Витальевич
Дата: 08.07.2026
"""

import pandas as pd
import os
from datetime import datetime

from logger.logger import logger


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

# Какие стандартные колонки должны быть строками (используется и лоадером)
STRING_COLUMNS = [
    'inn', 'kpp', 'ogrn', 'okpo', 'okato', 'oktmo', 'okfs',
    'director_inn',
    'ifns_code', 'fss_code', 'pfr_code',
    'phone', 'contact_phone_mobile'
]


# ============================================================
# 2. НАБОРЫ КОЛОНОК (ERD / MVP)
# ============================================================

ERD_COLUMNS = {
    'company': [
        'short_name', 'full_name', 'status', 'opf', 'inn', 'kpp', 'ogrn',
        'okpo', 'okato', 'oktmo', 'okfs', 'tax_system',
    ],
    'company_details': [
        'registration_date', 'authorized_capital', 'employee_count',
        'msp_category', 'source_url', 'ifns_reg_date', 'ifns_code',
        'ifns_name', 'fss_reg_date', 'fss_code', 'fss_name',
        'pfr_reg_date', 'pfr_code', 'pfr_name', 'special_tax_regimes',
        'average_headcount',
    ],
    'financial_performance': [
        'year', 'revenue', 'sales_profit', 'pretax_profit', 'net_profit',
        'receivables', 'payables', 'inventory', 'fixed_assets',
        'liquidity_abs', 'liquidity_curr', 'solvency_recovery', 'fin_stability',
    ],
    'address': ['address_type', 'address', 'city', 'postal_index'],
    'activity_type': ['okved_code', 'activity_name', 'is_main'],
    'director': [
        'director_full_name', 'director_position', 'director_inn',
        'director_year', 'director_is_current',
    ],
    'contact': ['contact_type', 'contact_value'],
}

ALL_ERD_COLUMNS = [col for cols in ERD_COLUMNS.values() for col in cols]

MVP_COLUMNS = [
    'id',
    'inn', 'kpp', 'ogrn',
    'full_name', 'short_name',
    'email', 'phone',
    'region', 'city', 'address',
    'contact_person', 'position',
    'source_type', 'source_name', 'source_date'
]


# ============================================================
# 3. ФУНКЦИИ МАППИНГА И ФИЛЬТРАЦИИ
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


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Переименовывает колонки DataFrame согласно COLUMN_MAPPING.
    """
    mapping = map_columns(df.columns.tolist())
    df_renamed = df.rename(columns=mapping)

    logger.info(f"Сопоставлено колонок: {len(mapping)} из {len(df.columns)}")
    renamed_count = sum(1 for orig, std in mapping.items() if orig != std)
    if renamed_count:
        for orig, std in mapping.items():
            if orig != std:
                logger.info(f"  {orig} -> {std}")
    else:
        logger.info("  Все колонки уже в стандартном формате")

    return df_renamed


def validate_required_columns(df: pd.DataFrame,
                              required_columns: list = None) -> dict:
    """
    Проверяет наличие обязательных колонок в DataFrame.
    """
    if required_columns is None:
        required_columns = ['inn']

    existing = [col for col in required_columns if col in df.columns]
    missing = [col for col in required_columns if col not in df.columns]

    result = {
        'status': 'OK' if not missing else 'WARNING',
        'required_columns': required_columns,
        'existing_columns': existing,
        'missing_columns': missing,
        'message': f"Найдено {len(existing)} из {len(required_columns)} обязательных колонок"
    }
    if missing:
        result['message'] += f". Отсутствуют: {', '.join(missing)}"
        logger.warning(f"ВНИМАНИЕ! Отсутствуют колонки: {', '.join(missing)}")
    else:
        logger.info("Все обязательные колонки присутствуют")

    return result


def filter_columns(df: pd.DataFrame,
                   required_columns: list = None) -> dict:
    """
    Оставляет в DataFrame только нужные колонки,
    добавляет отсутствующие с пустыми значениями.
    """
    if required_columns is None:
        required_columns = ALL_ERD_COLUMNS

    existing = [col for col in required_columns if col in df.columns]
    missing = [col for col in required_columns if col not in df.columns]

    logger.info("--- СОПОСТАВЛЕНИЕ КОЛОНОК ---")
    logger.info(f"Всего в ERD: {len(required_columns)} колонок")
    logger.info(f"Найдено в файле: {len(existing)}")
    logger.info(f"Будет добавлено пустых: {len(missing)}")

    df_filtered = df[existing].copy() if existing else pd.DataFrame()
    for col in missing:
        df_filtered[col] = None

    logger.info("--- СОПОСТАВЛЕНИЕ ПО ТАБЛИЦАМ ERD ---")
    for table, columns in ERD_COLUMNS.items():
        found = [c for c in columns if c in existing]
        miss = [c for c in columns if c not in df.columns]
        if found or miss:
            logger.info(f"  {table}: найдено {len(found)}/{len(columns)}")
            if miss:
                logger.info(f"    отсутствуют: {', '.join(miss)}")

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


def save_to_excel(df: pd.DataFrame,
                  output_folder: str = "output",
                  base_filename: str = "filtered") -> str:
    """Сохраняет DataFrame в Excel (опционально)."""
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_filename}_{timestamp}.xlsx"
    file_path = os.path.join(output_folder, filename)

    df.to_excel(file_path, index=False, engine='openpyxl')
    logger.info(f"Файл сохранён: {file_path}")
    logger.info(f"Строк: {len(df)}, колонок: {len(df.columns)}")
    return file_path


# ============================================================
# 4. ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def process_file(df: pd.DataFrame,
                 required_columns: list = None) -> dict:
    """
    Принимает DataFrame (сырой, после source_loader),
    переименовывает колонки, фильтрует под ERD/MVP.
    Опционально сохраняет результат в Excel.

    Параметры:
        df (pd.DataFrame): входные данные
        required_columns (list): список нужных колонок
        output_folder (str): если указан, сохраняет файл

    Возвращает:
        dict: с ключами 'status', 'df', 'stats', 'output_file'
    """
    logger.info("=" * 60)
    logger.info("ЗАПУСК source_mapper")
    logger.info("=" * 60)

    if required_columns is None:
        required_columns = ALL_ERD_COLUMNS

    try:
        # Шаг 1: переименование
        df = normalize_columns(df)

        # Шаг 2: валидация обязательных колонок
        validation_result = validate_required_columns(df, required_columns)

        # Шаг 3: фильтрация
        filter_result = filter_columns(df, required_columns)
        df_filtered = filter_result['df']

        result = {
            'status': 'OK' if validation_result['status'] == 'OK' else 'WARNING',
            'df': df_filtered,
            'validation_result': validation_result,
            'stats': filter_result['stats'],
        }

        logger.info("=" * 60)
        logger.info(f"МАППИНГ ЗАВЕРШЁН. СТАТУС: {result['status']}")
        logger.info(f"  Итоговые колонки: {list(df_filtered.columns)}")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.info("=" * 60)
        logger.info(f"ОШИБКА: {str(e)}")
        logger.info("=" * 60)
        return {
            'status': 'ERROR',
            'df': None,
            'validation_result': None,
            'stats': None,
            'output_file': None,
            'error': str(e)
        }