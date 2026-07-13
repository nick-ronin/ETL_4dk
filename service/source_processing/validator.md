# validator – валидация данных

Модуль для проверки наличия обязательных колонок в DataFrame.

---

## Назначение

Модуль `validator` проверяет, что в DataFrame присутствуют все обязательные колонки (по умолчанию — `inn`). Используется внутри `source_mapper` после переименования колонок.

---

## Основная функция

```python
from service.source_processing.validator import validate_required_columns

result = validate_required_columns(df, required_columns=['inn'])
```

**Параметры:**
- `df` (pd.DataFrame) — данные для проверки
- `required_columns` (list) — список обязательных колонок (по умолчанию `['inn']`)

**Возвращает:**
```python
{
    'status': 'OK',                    # OK / WARNING
    'required_columns': ['inn'],
    'existing_columns': ['inn'],
    'missing_columns': [],
    'message': 'Найдено 1 из 1 обязательных колонок'
}
```

---

## Статусы ответов

| Статус | Описание |
|--------|----------|
| `OK` | Все обязательные колонки присутствуют |
| `WARNING` | Одна или несколько обязательных колонок отсутствуют |

---

## Пример использования

```python
from service.source_processing.validator import validate_required_columns

# Проверка наличия ИНН и телефона
result = validate_required_columns(df, required_columns=['inn', 'phone'])

if result['status'] == 'WARNING':
    print(f"Отсутствуют: {result['missing_columns']}")
```

---

## Связанные модули

| Модуль | Связь |
|--------|-------|
| **source_mapper** | Вызывает валидатор после переименования колонок |

---