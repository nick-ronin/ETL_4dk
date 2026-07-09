import pandas as pd

table_path = "tables.xlsx"
table = pd.read_excel(table_path, sheet_name="Чекко")

columns = ["ИНН", "Email", "Телефоны", "Сокращенное наименование"]

def get_duplicates_report(df, columns, dropna=True):
    """
    Возвращает словарь с отчётом по дубликатам для каждой колонки.
    Ключ - название колонки, значение - DataFrame с группировкой
    (значение, количество повторов, индексы строк, примеры названий).
    Если дубликатов нет - пустой DataFrame.
    Также ищет полные дубликаты, где все значения в строке совпадают.
    Заносит их на отдельный лист в Excel.
    """
    report = {}
    # 1. Поиск дубликатов по каждой указанной колонке (как раньше)
    for col in columns:
        if col not in df.columns:
            report[col] = f"Колонка '{col}' отсутствует в таблице"
            continue
        series = df[col].dropna() if dropna else df[col]
        counts = series.value_counts()
        dupl_values = counts[counts > 1]
        if dupl_values.empty:
            report[col] = pd.DataFrame()
            continue
        rows = []
        for value, count in dupl_values.items():
            idx = df.index[df[col] == value].tolist()
            sample_names = df.loc[idx, 'Сокращенное наименование'].tolist()
            rows.append({
                'Значение': value,
                'Повторов': count,
                'Индексы строк': idx,
                'Примеры организаций': sample_names
            })
        report[col] = pd.DataFrame(rows)

    # 2. Поиск полных дубликатов (по всем столбцам)
    # duplicated(keep=False) отмечает ВСЕ строки, которые имеют полную копию
    full_dupl_mask = df.duplicated(keep=False)
    if not full_dupl_mask.any():
        report['Полные дубликаты'] = pd.DataFrame()
    else:
        # Группируем строки по ВСЕМ значениям, превращённым в кортеж
        # Это надёжнее, чем duplicated, чтобы получить группы
        groups = df[full_dupl_mask].groupby(list(df.columns))
        rows_full = []
        for values_tuple, group_df in groups:
            idxs = group_df.index.tolist()
            # Берём название организации из первой строки группы
            sample_name = group_df['Сокращенное наименование'].iloc[0]
            rows_full.append({
                'Индексы строк': idxs,
                'Количество': len(idxs),
                'Пример организации': sample_name,
                # Опционально можно добавить любые ключевые поля, например ИНН
                'ИНН': group_df['ИНН'].iloc[0] if 'ИНН' in df.columns else ''
            })
        report['Полные дубликаты'] = pd.DataFrame(rows_full)
    return report

duplicate_report = get_duplicates_report(table, columns)

# Запись красивого текстового отчёта
with open("duplicates_report.txt", "w", encoding="utf-8") as f:
    for section, data in duplicate_report.items():
        f.write(f"{'='*50}\n")
        f.write(f"{section}\n")
        f.write(f"{'='*50}\n")
        if isinstance(data, str):
            f.write(data + "\n\n")
        elif data.empty:
            f.write("Дубликаты не найдены.\n\n")
        else:
            if section == 'Полные дубликаты':
                for _, row in data.iterrows():
                    f.write(f"Индексы строк: {row['Индексы строк']}\n")
                    f.write(f"Количество: {row['Количество']}\n")
                    f.write(f"Пример организации: {row['Пример организации']}\n")
                    if 'ИНН' in row:
                        f.write(f"ИНН: {row['ИНН']}\n")
                    f.write("-"*40 + "\n")
            else:
                for _, row in data.iterrows():
                    f.write(f"Значение: {row['Значение']}\n")
                    f.write(f"Повторов: {row['Повторов']}\n")
                    f.write(f"Индексы строк: {row['Индексы строк']}\n")
                    f.write(f"Организации: {row['Примеры организаций']}\n")
                    f.write("-"*40 + "\n")
            f.write("\n")

with pd.ExcelWriter("duplicates_full_report.xlsx") as writer:
    # Листы по каждой колонке
    for col in columns:
        if col not in table.columns:
            continue
        dupl_mask = table[col].duplicated(keep=False)
        dupl_rows = table[dupl_mask].sort_values(col)
        if not dupl_rows.empty:
            dupl_rows.to_excel(writer, sheet_name=col[:31], index=False)
        else:
            pd.DataFrame({"Результат": ["Дубликаты не найдены"]}).to_excel(
                writer, sheet_name=col[:31], index=False
            )

    # Лист с полными дубликатами
    full_dupl_mask = table.duplicated(keep=False)
    if full_dupl_mask.any():
        full_dupl = table[full_dupl_mask].copy()
        # Добавим столбец "ID_группы" для удобства
        full_dupl['Группа_дубликатов'] = full_dupl.groupby(list(table.columns)).ngroup()
        full_dupl = full_dupl.sort_values('Группа_дубликатов')
        full_dupl.to_excel(writer, sheet_name='Полные_дубликаты', index=False)
    else:
        pd.DataFrame({"Результат": ["Полные дубликаты отсутствуют"]}).to_excel(
            writer, sheet_name='Полные_дубликаты', index=False
        )