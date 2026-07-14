import pandas as pd
import os
from datetime import datetime

def get_duplicates(df, columns, source_name="uploaded_file", output_dir="output"):
    """
    Создаёт отчёт о коллизиях (дубликатах) с номерами строк в исходном файле.
    """
    df = df.copy()
    df['Номер строки'] = df.index + 2

    collisions = []
    summary = {}

    # 1. Частичные дубликаты (по каждой колонке отдельно)
    for col in columns:
        if col not in df.columns:
            continue

        series = df[col].dropna()
        counts = series.value_counts()
        dupl_values = counts[counts > 1]

        if dupl_values.empty:
            summary[col] = {'Всего групп': 0, 'Всего строк': 0}
            continue

        group_counter = 0
        # убрал count из цикла ⬇️⬇↓ тк он просто считал кол-во повторений значения
        for value in dupl_values.index:
            dupl_rows = df[df[col] == value].copy()

            dupl_rows['Источник'] = source_name
            dupl_rows['Поле'] = col
            dupl_rows['Значение дубликата'] = str(value)
            dupl_rows['Тип дубликата'] = 'частичный'
            dupl_rows['Группа дубликата'] = f"{col}_{group_counter}"

            collisions.append(dupl_rows)
            group_counter += 1

        summary[col] = {
            'Всего групп': group_counter,
            'Всего строк': sum(len(c) for c in collisions[-group_counter:]) if group_counter > 0 else 0
        }

    # 2. Полные дубликаты (по всем колонкам)
    # Исключаем служебную колонку из сравнения
    cols_for_full = [c for c in df.columns if c != 'Номер_строки']
    full_dupl_mask = df[cols_for_full].duplicated(keep=False)

    if full_dupl_mask.any():
        full_dupl = df[full_dupl_mask].copy()

        groups = full_dupl.groupby(cols_for_full)
        group_counter = 0
        for values_tuple, group_df in groups:
            group_df = group_df.copy()
            group_df['Источник'] = source_name
            group_df['Поле'] = 'ВСЕ'
            group_df['Значение дубликата'] = 'ПОЛНОЕ СОВПАДЕНИЕ'
            group_df['Тип дубликата'] = 'полный'
            group_df['Группа дубликата'] = f"FULL_{group_counter}"

            collisions.append(group_df)
            group_counter += 1

        summary['Полные дубликаты'] = {
            'Всего групп': group_counter,
            'Всего строк': sum(len(c) for c in collisions[-group_counter:]) if group_counter > 0 else 0
        }
    else:
        summary['Полные дубликаты'] = {'Всего групп': 0, 'Всего строк': 0}

    # Объединяем все коллизии в одну таблицу
    if collisions:
        collisions_df = pd.concat(collisions, ignore_index=False)
        # Переставляем служебные колонки в начало
        service_cols = ['Источник', 'Номер строки', 'Группа дубликата', 'Тип дубликата', 'Поле', 'Значение дубликата']
        other_cols = [c for c in collisions_df.columns if c not in service_cols]
        collisions_df = collisions_df[service_cols + other_cols]
        # Сортируем для удобства
        collisions_df = collisions_df.sort_values(['Тип дубликата', 'Поле', 'Группа дубликата'])
    else:
        collisions_df = pd.DataFrame()

    # Сводка в DataFrame
    summary_df = pd.DataFrame(summary).T
    summary_df.index.name = 'Поле'
    summary_df = summary_df.reset_index()

    os.makedirs(output_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in source_name)
    base_name = os.path.splitext(safe_name)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"collisions_{base_name}_{timestamp}.xlsx")

    # Сохраняем в Excel с разными листами
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
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
            full_collisions = collisions_df[collisions_df['Тип дубликата'] == 'полный']
            if not full_collisions.empty:
                full_collisions.to_excel(writer, sheet_name='Полные дубликаты', index=False)
            else:
                pd.DataFrame({"Результат": ["Полные дубликаты не найдены"]}).to_excel(
                    writer, sheet_name='Полные дубликаты', index=False
                )
        else:
            pd.DataFrame({"Результат": ["Коллизии не найдены"]}).to_excel(
                writer, sheet_name='Полные дубликаты', index=False
            )

    return {
        'collisions_file': file_path,
        'summary': summary,
        'rows_affected': len(collisions_df) if not collisions_df.empty else 0
    }