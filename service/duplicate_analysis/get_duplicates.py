import pandas as pd

table_path = "tables.xlsx"

table = pd.read_excel(table_path, sheet_name="Чекко") # можно вставить любое название листа

"""
На вход получает таблицу, из которой достаёт колонки и ищет количество дубликатов по каждой.
Выводит список дубликатов.
"""
def get_duplicates(table):
    columns = table.columns.tolist()
    result = []
    for column in columns:
        duplicate_count = table[column].dropna().duplicated().sum()
        result.append(int(duplicate_count))
    return result

print(get_duplicates(table))