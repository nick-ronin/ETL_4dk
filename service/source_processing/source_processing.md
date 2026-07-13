## source_loader – загрузка файлов

**Назначение:**  
Единственная точка входа для чтения Excel/CSV. Определяет формат, кодировку, принудительно загружает идентификаторы как строки (ИНН, КПП, ОГРН и др.), возвращает сырой `DataFrame` с оригинальными заголовками.

**Используется ТОЛЬКО внутри FastAPI эндпоинта.**

### Основная функция

```python
from service.source_processing.source_loader import process_uploaded_file

result = process_uploaded_file(file_path="/tmp/upload.xlsx")
# result = {
#     'status': 'OK',
#     'df': <DataFrame>,
#     'error': None,
#     'mapping_info': {'total_columns': 12, 'original_columns': [...]}
# }
```

- **Вход:** путь к временному файлу на диске.
- **Выход:** словарь со статусом и `df` (все ячейки – `object`, числовые идентификаторы уже строки).
- **Сохранения на диск не происходит** – промежуточные Excel не создаются.
- При ошибке `status = 'ERROR'`, поле `error` содержит описание.

### Как обеспечиваются строковые идентификаторы
Модуль при загрузке смотрит на заголовки и, используя список `STRING_COLUMNS` из `source_mapper`, принудительно задаёт `dtype=str` для колонок ИНН, КПП, ОГРН, телефонов и т.д. Это гарантирует сохранение ведущих нулей и отсутствие экспоненциальной записи.

---

## source_mapper – маппинг и фильтрация колонок

**Назначение:**  
Принимает **DataFrame**, приводит названия колонок к единому стандарту (`COLUMN_MAPPING`), проверяет наличие обязательных полей, оставляет только колонки из списка ERD/MVP, добавляет недостающие пустыми. Может опционально сохранить результат в Excel (используется только при `download=True` в API, через `exporter`).

**Используется ТОЛЬКО внутри FastAPI эндпоинта.**

### Основная функция

```python
from service.source_processing.source_mapper import process_file, MVP_COLUMNS

# df_raw получен из source_loader
mapper_result = process_file(
    df=df_raw,
    required_columns=MVP_COLUMNS,
    output_folder=None            # по умолчанию не сохраняем
)
# result = {
#     'status': 'OK',
#     'df': <DataFrame>,
#     'validation_result': {...},
#     'stats': {...},
#     'output_file': None
# }
```

- **Вход:**
  - `df` – DataFrame (после source_loader)
  - `required_columns` – список нужных полей (по умолчанию `ALL_ERD_COLUMNS`)
  - `output_folder` – если указан, сохранит Excel в эту папку (для отладки/экспорта)
- **Выход:** словарь с итоговым `df`, статистикой фильтрации и статусом валидации обязательных колонок.

### Что происходит внутри
1. **Переименование колонок** по `COLUMN_MAPPING` (все варианты русских и английских названий сводятся к стандартным `inn`, `kpp` и т.д.).
2. **Валидация** – проверка, что в наборе есть хотя бы одна из обязательных колонок (по умолчанию `['inn']`).
3. **Фильтрация** – удаление колонок, не входящих в `required_columns`, и добавление отсутствующих со значением `None`.
4. Возврат очищенного DataFrame, готового к нормализации (`normalizer`), дедупликации и расчёту качества.

### Важные константы (экспортируются)
- `COLUMN_MAPPING` – словарь соответствий исходных названий → стандартные.
- `STRING_COLUMNS` – список стандартных полей, которые должны быть строками (используется и source_loader).
- `ERD_COLUMNS` – полный набор колонок по таблицам ERD (55 полей).
- `ALL_ERD_COLUMNS` – плоский список всех колонок ERD.
- `MVP_COLUMNS` – урезанный набор для быстрой обработки (15 полей).

---

## Пример использования в API (из upload.py)

```python
# 1. Загрузка
with tempfile.NamedTemporaryFile(...) as temp:
    temp.write(await file.read())
    temp_path = temp.name

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

## Статусы ответов

| Статус | Описание |
|--------|----------|
| `OK` | Обработка успешна |
| `WARNING` | Данные загружены, но отсутствуют обязательные колонки (например, `inn`) |
| `ERROR` | Критическая ошибка (файл не читается, повреждён и т.п.) |
