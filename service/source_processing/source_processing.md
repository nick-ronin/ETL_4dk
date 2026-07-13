## 📋 Назначение модулей

**source_loader**
- Загружает Excel/CSV файл
- Приводит ВСЕ колонки к единому стандарту (переименовывает)
- Проверяет наличие ИНН
- Сохраняет результат в папку output/

**source_mapper**
- Берёт результат работы source_loader
- Оставляет ТОЛЬКО колонки из ERD (55 полей)
- Добавляет пустые колонки, которых нет в файле
- Сохраняет отфильтрованный результат в папку output/

---

## 🚀 Как использовать

### Способ 1: Запуск по очереди (для тестирования)

**Шаг 1.** Запусти source_loader:
```bash
python src/source_loader.py
```

**Шаг 2.** Запусти source_mapper:
```bash
python src/source_mapper.py
```

**Результат:** в папке `output` появятся два файла:
- `standard_<имя>_<дата>.xlsx` — все колонки приведены к стандарту
- `filtered_<имя>_<дата>.xlsx` — только колонки из ERD

---

### Способ 2: Использование в коде (для FastAPI)

```python
from src.source_loader import process_uploaded_file
from src.source_mapper import process_file, ALL_ERD_COLUMNS

# Шаг 1: Загружаем и нормализуем
result_loader = process_uploaded_file(
    file_path="test_files/ваш_файл.xlsx",
    required_columns=['inn'],
    save_output=True,
    output_folder="output"
)

# Шаг 2: Фильтруем колонки по ERD
if result_loader['status'] != 'ERROR':
    result_mapper = process_file(
        input_file_path=result_loader['saved_file'],
        required_columns=ALL_ERD_COLUMNS,
        output_folder="output"
    )
    
    # Готовый DataFrame для следующих модулей
    df_final = result_mapper['df']
```

### Способ 3: Полный пайплайн в одном скрипте

Создай файл `run_pipeline.py`:

```python
from src.source_loader import process_uploaded_file
from src.source_mapper import process_file, ALL_ERD_COLUMNS

input_file = "test_files/ваш_файл.xlsx"

logger.info("Запуск source_loader...")
result_loader = process_uploaded_file(
    file_path=input_file,
    required_columns=['inn'],
    save_output=True,
    output_folder="output"
)

if result_loader['status'] != 'ERROR':
    logger.info("Запуск source_mapper...")
    result_mapper = process_file(
        input_file_path=result_loader['saved_file'],
        required_columns=ALL_ERD_COLUMNS,
        output_folder="output"
    )
    
    logger.info(f"Готово! Файл сохранён: {result_mapper['output_file']}")
```

Запуск:
```bash
python run_pipeline.py
```

---

## 📊 Входные и выходные данные

### source_loader

| Что | Описание |
|-----|----------|
| Вход | Excel/CSV файл с любыми названиями колонок |
| Выход | `output/standard_<имя>_<дата>.xlsx` |
| Обязательная колонка | `ИНН` (если нет → статус WARNING) |

### source_mapper

| Что | Описание |
|-----|----------|
| Вход | Excel-файл из папки `output/` (результат source_loader) |
| Выход | `output/filtered_<имя>_<дата>.xlsx` |
| Колонки | 55 полей из 7 таблиц ERD (список ниже) |

---

## 📋 Список колонок из ERD (55 полей)

**Таблица company (12 полей):**
`short_name`, `full_name`, `status`, `opf`, `inn`, `kpp`, `ogrn`, `okpo`, `okato`, `oktmo`, `okfs`, `tax_system`

**Таблица company_details (16 полей):**
`registration_date`, `authorized_capital`, `employee_count`, `msp_category`, `source_url`, `ifns_reg_date`, `ifns_code`, `ifns_name`, `fss_reg_date`, `fss_code`, `fss_name`, `pfr_reg_date`, `pfr_code`, `pfr_name`, `special_tax_regimes`, `average_headcount`

**Таблица financial_performance (13 полей):**
`year`, `revenue`, `sales_profit`, `pretax_profit`, `net_profit`, `receivables`, `payables`, `inventory`, `fixed_assets`, `liquidity_abs`, `liquidity_curr`, `solvency_recovery`, `fin_stability`

**Таблица address (4 поля):**
`address_type`, `address`, `city`, `postal_index`

**Таблица activity_type (3 поля):**
`okved_code`, `activity_name`, `is_main`

**Таблица director (5 полей):**
`director_full_name`, `director_position`, `director_inn`, `director_year`, `director_is_current`

**Таблица contact (2 поля):**
`contact_type`, `contact_value`

---

## 🔧 Как работает маппинг колонок

### source_loader

Словарь `COLUMN_MAPPING` сопоставляет различные варианты названий с единым стандартом.

**Примеры:**

| Исходное название | Стандартное название |
|-------------------|---------------------|
| `ИНН`, `инн`, `ИНН организации` | `inn` |
| `Телефон`, `Мобильный телефон`, `Телефоны` | `phone` |
| `Email`, `E-mail`, `Почта` | `email` |
| `Полное наименование`, `Название организации` | `full_name` |

**Как добавить новый вариант названия:**

Открой `src/source_loader.py`, найди словарь `COLUMN_MAPPING` и добавь новый вариант:

```python
'phone': ['Телефон', 'Мобильный телефон', 'Новый вариант названия'],
```

---

### source_mapper

Оставляет **только** колонки из списка `ALL_ERD_COLUMNS`. Все остальные колонки удаляются.

**Как добавить новую колонку в ERD:**

Открой `src/source_mapper.py`, найди словарь `ERD_COLUMNS` и добавь поле в нужную таблицу:

```python
'company': [
    'short_name',
    'full_name',
    'my_new_field',  # Добавить сюда
    ...
],
```

---

## 📈 Статусы обработки

| Статус | Описание |
|--------|----------|
| `OK` | Обработка завершена успешно |
| `WARNING` | Файл загружен, но отсутствуют обязательные колонки (например, `inn`) |
| `ERROR` | Ошибка при загрузке или обработке файла |

---

## 🐛 Частые ошибки и их решение

| Ошибка | Решение |
|--------|---------|
| `ModuleNotFoundError: No module named 'pandas'` | Установи: `pip install pandas openpyxl` |
| `FileNotFoundError` | Проверь, что файл существует |
| `Missing optional dependency 'openpyxl'` | Установи: `pip install openpyxl` |
| `В папке output не найдено файлов` | Сначала запусти `source_loader` |
| `Отсутствуют колонки: inn` | Добавь вариант названия в словарь `COLUMN_MAPPING` |

---

## 🛠️ Параметры функций

### source_loader: `process_uploaded_file()`

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `file_path` | `str` | **Обязательный** | Путь к файлу на диске |
| `required_columns` | `list` | `['inn']` | Список обязательных колонок |
| `save_output` | `bool` | `True` | Сохранять ли результат в Excel |
| `output_folder` | `str` | `'output'` | Папка для сохранения |

### source_mapper: `process_file()`

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `input_file_path` | `str` | **Обязательный** | Путь к файлу (из output/) |
| `required_columns` | `list` | `ALL_ERD_COLUMNS` | Список колонок из ERD |
| `output_folder` | `str` | `'output'` | Папка для сохранения |

---

## 👥 Интеграция с другими модулями

**FastAPI** — вызывает `process_uploaded_file()` и `process_file()` через API

**normalizer** — получает DataFrame с колонками в стандарте, очищает значения

**deduplicator** — работает с колонками `inn`, `phone`, `email` для поиска дублей

**data_quality** — анализирует заполненность полей

**exporter** — сохраняет итоговые файлы

---
