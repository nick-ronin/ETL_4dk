# source_loader – загрузка файлов

Модуль для чтения Excel/CSV файлов и приведения их к единому стандарту.

---

## Назначение

Модуль `source_loader` загружает файлы из внешних источников (Excel/CSV), определяет формат и кодировку, приводит идентификаторы (ИНН, КПП, ОГРН) к строковому типу и возвращает сырой `DataFrame` с оригинальными заголовками.

**Используется ТОЛЬКО внутри FastAPI эндпоинта.**

---

## Принцип работы

1. Принимает путь к файлу на диске.
2. Определяет расширение (`.xlsx`, `.xls`, `.csv`).
3. Определяет кодировку для CSV (UTF-8 → Windows-1251 при ошибке).
4. Загружает данные в pandas DataFrame.
5. Приводит идентификаторы к строковому типу (список `STRING_COLUMNS` из `source_mapper`).
6. Возвращает словарь со статусом и DataFrame.

---

## Основная функция

```python
from service.source_processing.source_loader import process_uploaded_file

result = process_uploaded_file(file_path="/tmp/upload.xlsx")
```

**Параметры:**
- `file_path` (str) — путь к временному файлу на диске

**Возвращает:**
```python
{
    'status': 'OK',                    # OK / ERROR
    'df': <DataFrame>,                 # pandas DataFrame с данными
    'error': None,                     # текст ошибки (если есть)
    'mapping_info': {                  # информация о загрузке
        'total_columns': 12,
        'original_columns': ['ИНН', 'Наименование', ...]
    }
}
```

---

## Приведение к строке

Модуль принудительно задаёт `dtype=str` для колонок из списка `STRING_COLUMNS` (ИНН, КПП, ОГРН, телефоны и др.). Это сохраняет ведущие нули и предотвращает экспоненциальную запись.

**Пример:**
```python
# Без приведения к строке
ИНН: 7707083893 → 7707083893.0 (float)

# С приведением к строке
ИНН: 7707083893 → "7707083893" (str)
```

---

## Поддерживаемые форматы

| Формат | Расширение | Кодировка |
|--------|------------|-----------|
| Excel | `.xlsx`, `.xls` | Автоматически |
| CSV | `.csv` | UTF-8 / Windows-1251 |

---

## Статусы ответов

| Статус | Описание |
|--------|----------|
| `OK` | Файл успешно загружен |
| `ERROR` | Критическая ошибка (файл не читается, повреждён и т.п.) |

---

## Пример использования

```python
from service.source_processing.source_loader import process_uploaded_file

result = process_uploaded_file(file_path="/tmp/upload.xlsx")

if result['status'] == 'ERROR':
    print(f"Ошибка: {result['error']}")
else:
    df = result['df']
    print(f"Загружено {len(df)} строк, {len(df.columns)} колонок")
```

---

## Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `ModuleNotFoundError: No module named 'pandas'` | `pip install pandas openpyxl` |
| `FileNotFoundError` | Проверь, что файл существует |
| `Неподдерживаемый формат` | Используй `.xlsx`, `.xls` или `.csv` |
| `UnicodeDecodeError` | Автоматически переключается на Windows-1251 |

---

## Связанные модули

| Модуль | Связь |
|--------|-------|
| **source_mapper** | Принимает результат для фильтрации колонок |
| **FastAPI** | Вызывает source_loader для загрузки файла |

---