```markdown
# Модуль exporter

Модуль для выгрузки данных в Excel.

---

## Назначение

Модуль `exporter` предназначен для сохранения обработанных данных в Excel-файл.

**Что делает модуль:**
- Принимает готовый DataFrame с данными
- Сохраняет его в Excel-файл с временной меткой
- Формирует служебный отчёт с информацией о выгрузке


## Как использовать

### Способ 1: Экспорт после source_mapper (основной)

```python
from Exporter.src.exporter import export_from_mapper

# mapper_result — результат работы source_mapper
result = export_from_mapper(
    mapper_result=mapper_result,
    output_folder="output"
)

if result['status'] == 'OK':
    logger.info(f"Файл сохранён: {result['main_file']}")
    logger.info(f"Отчёт сохранён: {result['report_file']}")
```

### Способ 2: Экспорт любого DataFrame

```python
from Exporter.src.exporter import export_to_excel

result = export_to_excel(
    df=df,
    output_folder="output",
    filename="my_data"
)

logger.info(f"Сохранён: {result['file_path']}")
```

### Способ 3: Экспорт с отчётом

```python
from Exporter.src.exporter import export_with_report

result = export_with_report(
    df=df,
    output_folder="output",
    filename_main="standard_clients",
    filename_report="processing_report"
)

logger.info(f"Основной файл: {result['main_file']}")
logger.info(f"Файл отчёта: {result['report_file']}")
```

### Способ 4: Простой экспорт одного файла

```python
from Exporter.src.exporter import export_simple

file_path = export_simple(
    df=df,
    output_folder="output",
    filename="data_export"
)

logger.info(f"Сохранён: {file_path}")
```

---

## Выходные файлы

### standard_clients_<дата>.xlsx

Основной файл с данными. Содержит все колонки из переданного DataFrame.

### processing_report_<дата>.xlsx

Служебный отчёт с информацией о выгрузке:

| Параметр | Значение |
|----------|----------|
| Имя файла | standard_clients_20260710_153045.xlsx |
| Дата обработки | 20260710_153045 |
| Количество строк | 1057 |
| Количество колонок | 55 |
| Список колонок | inn, kpp, ogrn, ... |

---

## API

### `export_to_excel(df, output_folder="output", filename="standard_clients")`

Сохраняет DataFrame в Excel.

**Параметры:**
- `df` — pandas DataFrame с данными
- `output_folder` — папка для сохранения (по умолчанию `"output"`)
- `filename` — имя файла без расширения

**Возвращает:**
```python
{
    'status': 'OK',           # OK / ERROR
    'file_path': 'output/standard_clients_20260710_153045.xlsx',
    'timestamp': '20260710_153045',
    'rows': 1057,
    'columns': 55
}
```

---

### `export_with_report(df, output_folder="output", filename_main="standard_clients", filename_report="processing_report")`

Сохраняет данные и формирует служебный отчёт.

**Параметры:**
- `df` — pandas DataFrame с данными
- `output_folder` — папка для сохранения
- `filename_main` — имя основного файла
- `filename_report` — имя файла отчёта

**Возвращает:**
```python
{
    'status': 'OK',
    'main_file': 'output/standard_clients_20260710_153045.xlsx',
    'report_file': 'output/processing_report_20260710_153045.xlsx',
    'rows': 1057,
    'columns': 55
}
```

---

### `export_from_mapper(mapper_result, output_folder="output")`

Принимает результат source_mapper и экспортирует в Excel.

**Параметры:**
- `mapper_result` — результат работы source_mapper
- `output_folder` — папка для сохранения

**Возвращает:** то же, что и `export_with_report()`

---

### `export_simple(df, output_folder="output", filename="data_export")`

Простой экспорт одного DataFrame.

**Параметры:**
- `df` — pandas DataFrame с данными
- `output_folder` — папка для сохранения
- `filename` — имя файла без расширения

**Возвращает:** строку с путём к файлу

---

## Интеграция с другими модулями

### source_loader

```python
from SourceLoader.src.source_loader import process_uploaded_file
from Exporter.src.exporter import export_from_loader

# Загружаем и нормализуем
loader_result = process_uploaded_file(
    file_path="test_files/ваш_файл.xlsx",
    required_columns=['inn'],
    save_output=True
)

# Экспортируем
export_result = export_from_loader(
    loader_result=loader_result,
    output_folder="output"
)
```

### source_mapper

```python
from SourceLoader.src.source_mapper import process_file, ALL_ERD_COLUMNS
from Exporter.src.exporter import export_from_mapper

# Фильтруем колонки
mapper_result = process_file(
    input_file_path="output/standard_Источники_данных_20260708_153045.xlsx",
    required_columns=ALL_ERD_COLUMNS
)

# Экспортируем
export_result = export_from_mapper(
    mapper_result=mapper_result,
    output_folder="output"
)
```

### Полный пайплайн

```python
from SourceLoader.src.source_loader import process_uploaded_file
from SourceLoader.src.source_mapper import process_file, ALL_ERD_COLUMNS
from Exporter.src.exporter import export_from_mapper

# Шаг 1: source_loader
loader_result = process_uploaded_file(
    file_path="test_files/ваш_файл.xlsx",
    required_columns=['inn'],
    save_output=True,
    output_folder="SourceLoader/output"
)

# Шаг 2: source_mapper
mapper_result = process_file(
    input_file_path=loader_result['saved_file'],
    required_columns=ALL_ERD_COLUMNS,
    output_folder="SourceLoader/output"
)

# Шаг 3: exporter
export_result = export_from_mapper(
    mapper_result=mapper_result,
    output_folder="Exporter/output"
)

logger.info(f"Готово! Файлы в Exporter/output/")
```

---

## Статусы обработки

| Статус | Описание |
|--------|----------|
| `OK` | Экспорт завершён успешно |
| `ERROR` | Ошибка при экспорте (нет данных, ошибка записи) |

---

## Частые ошибки и их решение

| Ошибка | Решение |
|--------|---------|
| `ModuleNotFoundError: No module named 'pandas'` | Установи: `pip install pandas openpyxl` |
| `ModuleNotFoundError: No module named 'openpyxl'` | Установи: `pip install openpyxl` |
| `DataFrame пуст` | Проверь, что данные переданы корректно |
| `PermissionError` | Закрой файл, если он открыт в Excel |
| `FileNotFoundError` | Проверь путь к папке `output` |

---
