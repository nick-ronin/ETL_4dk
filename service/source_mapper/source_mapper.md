# source_mapper – маппинг и фильтрация колонок

Модуль для сопоставления колонок с единым стандартом и фильтрации по ERD.

---

## Назначение

Модуль `source_mapper` принимает DataFrame, приводит названия колонок к единому стандарту (`COLUMN_MAPPING`), проверяет наличие обязательных полей, оставляет только колонки из списка ERD/MVP и добавляет недостающие пустыми.

**Используется ТОЛЬКО внутри FastAPI эндпоинта.**

---

## Принцип работы

1. **Переименование колонок** по `COLUMN_MAPPING` — все варианты русских и английских названий сводятся к стандартным (`inn`, `kpp` и т.д.)
2. **Валидация** — проверка, что в наборе есть хотя бы одна из обязательных колонок (по умолчанию `['inn']`)
3. **Фильтрация** — удаление колонок, не входящих в `required_columns`, и добавление отсутствующих со значением `None`
4. Возврат очищенного DataFrame, готового к нормализации (`normalizer`), дедупликации и расчёту качества

---

## Основная функция

```python
from service.source_processing.source_mapper import process_file, MVP_COLUMNS

# df_raw получен из source_loader
mapper_result = process_file(
    df=df_raw,
    required_columns=MVP_COLUMNS
)
```

**Параметры:**
- `df` (pd.DataFrame) — DataFrame после source_loader
- `required_columns` (list) — список нужных полей (по умолчанию `ALL_ERD_COLUMNS`)

**Возвращает:**
```python
{
    'status': 'OK',                    # OK / WARNING / ERROR
    'df': <DataFrame>,                 # отфильтрованный DataFrame
    'validation_result': {             # результат проверки обязательных колонок
        'status': 'OK',
        'required_columns': ['inn'],
        'existing_columns': ['inn'],
        'missing_columns': [],
        'message': 'Найдено 1 из 1 обязательных колонок'
    },
    'stats': {                         # статистика фильтрации
        'required_columns': 55,
        'existing_columns': 12,
        'missing_columns': 43,
        'added_columns': [...],
        'removed_columns': [...]
    },
    'error': None                      # текст ошибки (если есть)
}
```

---

## Важные константы (экспортируются)

| Константа | Описание |
|-----------|----------|
| `COLUMN_MAPPING` | Словарь соответствий исходных названий → стандартные |
| `STRING_COLUMNS` | Список стандартных полей, которые должны быть строками (используется и source_loader) |
| `ERD_COLUMNS` | Полный набор колонок по таблицам ERD (55 полей) |
| `ALL_ERD_COLUMNS` | Плоский список всех колонок ERD |
| `MVP_COLUMNS` | Урезанный набор для быстрой обработки (15 полей) |

---

## Статусы ответов

| Статус | Описание |
|--------|----------|
| `OK` | Маппинг и фильтрация успешны |
| `WARNING` | Данные загружены, но отсутствуют обязательные колонки (например, `inn`) |
| `ERROR` | Критическая ошибка (DataFrame пуст, повреждён и т.п.) |

---

## Пример использования в API (из upload.py)

```python
from service.source_processing.source_loader import process_uploaded_file
from service.source_processing.source_mapper import process_file, MVP_COLUMNS

# 1. Загрузка
upload_result = process_uploaded_file(file_path=temp_path)
if upload_result['status'] == 'ERROR':
    raise HTTPException(400, detail=upload_result['error'])

# 2. Маппинг + фильтрация
df_raw = upload_result['df']
mapper_result = process_file(
    df=df_raw,
    required_columns=MVP_COLUMNS
)
if mapper_result['status'] == 'ERROR':
    raise HTTPException(400, detail=mapper_result.get('error'))

df = mapper_result['df']   # готов к очистке, дедупликации и т.д.
```

---

## Список ERD-колонок (для справки)

**company** (12): `short_name`, `full_name`, `status`, `opf`, `inn`, `kpp`, `ogrn`, `okpo`, `okato`, `oktmo`, `okfs`, `tax_system`

**company_details** (16): `registration_date`, `authorized_capital`, `employee_count`, `msp_category`, `source_url`, `ifns_reg_date`, `ifns_code`, `ifns_name`, `fss_reg_date`, `fss_code`, `fss_name`, `pfr_reg_date`, `pfr_code`, `pfr_name`, `special_tax_regimes`, `average_headcount`

**financial_performance** (13): `year`, `revenue`, `sales_profit`, `pretax_profit`, `net_profit`, `receivables`, `payables`, `inventory`, `fixed_assets`, `liquidity_abs`, `liquidity_curr`, `solvency_recovery`, `fin_stability`

**address** (4): `address_type`, `address`, `city`, `postal_index`

**activity_type** (3): `okved_code`, `activity_name`, `is_main`

**director** (5): `director_full_name`, `director_position`, `director_inn`, `director_year`, `director_is_current`

**contact** (2): `contact_type`, `contact_value`

---

## Связанные модули

| Модуль | Связь |
|--------|-------|
| **source_loader** | Предоставляет DataFrame для маппинга |
| **validator** | Используется для проверки обязательных колонок |
| **normalizer** | Принимает результат для очистки значений |

---
