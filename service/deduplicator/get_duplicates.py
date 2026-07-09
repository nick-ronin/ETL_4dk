import pandas as pd

table_path = "tables.xlsx"
table = pd.read_excel(table_path, sheet_name="Чекко")

# Добавляем колонку с номером строки в исходном файле
# +2 потому что: строка 1 = заголовок, данные начинаются со строки 2
table['Номер_строки_источник'] = table.index + 2

columns = ["ИНН", "Email", "Телефоны", "Сокращенное наименование"]

def get_duplicates(df, columns, source_name="tables.xlsx", dropna=True):
    """
    Создаёт отчёт о коллизиях (дубликатах) с номерами строк в исходном файле.
    """
    collisions = []
    summary = {}

    # 1. Частичные дубликаты (по каждой колонке отдельно)
    for col in columns:
        if col not in df.columns:
            continue

        series = df[col].dropna() if dropna else df[col]
        counts = series.value_counts()
        dupl_values = counts[counts > 1]

        if dupl_values.empty:
            summary[col] = {'всего_групп': 0, 'всего_строк': 0}
            continue

        group_counter = 0
        for value, count in dupl_values.items():
            dupl_rows = df[df[col] == value].copy()

            dupl_rows['Источник'] = source_name
            dupl_rows['Поле'] = col
            dupl_rows['Значение_дубликата'] = str(value)
            dupl_rows['Тип_дубликата'] = 'частичный'
            dupl_rows['Группа_дубликата'] = f"{col}_{group_counter}"

            collisions.append(dupl_rows)
            group_counter += 1

        summary[col] = {
            'всего_групп': group_counter,
            'всего_строк': sum(len(c) for c in collisions[-group_counter:]) if group_counter > 0 else 0
        }

    # 2. Полные дубликаты (по всем колонкам)
    # Исключаем служебную колонку из сравнения
    cols_for_full = [c for c in df.columns if c != 'Номер_строки_источник']
    full_dupl_mask = df[cols_for_full].duplicated(keep=False)

    if full_dupl_mask.any():
        full_dupl = df[full_dupl_mask].copy()

        groups = full_dupl.groupby(cols_for_full)
        group_counter = 0
        for values_tuple, group_df in groups:
            group_df = group_df.copy()
            group_df['Источник'] = source_name
            group_df['Поле'] = 'ВСЕ'
            group_df['Значение_дубликата'] = 'ПОЛНОЕ СОВПАДЕНИЕ'
            group_df['Тип_дубликата'] = 'полный'
            group_df['Группа_дубликата'] = f"FULL_{group_counter}"

            collisions.append(group_df)
            group_counter += 1

        summary['Полные дубликаты'] = {
            'всего_групп': group_counter,
            'всего_строк': sum(len(c) for c in collisions[-group_counter:]) if group_counter > 0 else 0
        }
    else:
        summary['Полные дубликаты'] = {'всего_групп': 0, 'всего_строк': 0}

    # Объединяем все коллизии в одну таблицу
    if collisions:
        collisions_df = pd.concat(collisions, ignore_index=False)
        # Переставляем служебные колонки в начало
        service_cols = ['Источник', 'Номер_строки_источник', 'Группа_дубликата', 'Тип_дубликата', 'Поле', 'Значение_дубликата']
        other_cols = [c for c in collisions_df.columns if c not in service_cols]
        collisions_df = collisions_df[service_cols + other_cols]
        # Сортируем для удобства
        collisions_df = collisions_df.sort_values(['Тип_дубликата', 'Поле', 'Группа_дубликата'])
    else:
        collisions_df = pd.DataFrame()

    # Сводка в DataFrame
    summary_df = pd.DataFrame(summary).T
    summary_df.index.name = 'Поле'
    summary_df = summary_df.reset_index()

    return collisions_df, summary_df

# Формируем отчёт
collisions_df, summary_df = get_duplicates(table, columns, source_name="tables.xlsx (Чекко)")

# Сохраняем в Excel с разными листами
with pd.ExcelWriter("collisions_report.xlsx", engine='openpyxl') as writer:
    # Лист 1: Все коллизии
    if not collisions_df.empty:
        # Убираем индекс pandas, чтобы не путать с номерами строк
        collisions_df.to_excel(writer, sheet_name='Коллизии', index=False)
    else:
        pd.DataFrame({"Результат": ["Коллизии не найдены"]}).to_excel(
            writer, sheet_name='Коллизии', index=False
        )

    # Лист 2: Сводка по полям
    summary_df.to_excel(writer, sheet_name='Сводка', index=False)

    # Лист 3: Полные дубликаты отдельно
    if not collisions_df.empty:
        full_collisions = collisions_df[collisions_df['Тип_дубликата'] == 'полный']
        if not full_collisions.empty:
            full_collisions.to_excel(writer, sheet_name='Полные_дубликаты', index=False)
        else:
            pd.DataFrame({"Результат": ["Полные дубликаты не найдены"]}).to_excel(
                writer, sheet_name='Полные_дубликаты', index=False
            )
    else:
        pd.DataFrame({"Результат": ["Коллизии не найдены"]}).to_excel(
            writer, sheet_name='Полные_дубликаты', index=False
        )