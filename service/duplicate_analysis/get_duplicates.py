import pandas as pd

table_path = "tables.xlsx"

table = pd.read_excel(table_path, sheet_name="Чекко") # можно вставить любое название листа

"""
На вход получает таблицу, из которой достаёт колонки и ищет количество дубликатов по каждой.
Выводит список количества дубликатов.
"""
def get_duplicates(table):
    columns = ["ИНН", "Email", "Телефоны", "Сокращенное наименование"]
    result = dict()
    for column in columns:
        table[column] = table[column].dropna()
        duplicate = table[table.duplicated(subset=[column], keep=False)]
        duplicate_count = table[column].duplicated().sum()
        result[column] = duplicate, int(duplicate_count)
    return result

duplicate_report = get_duplicates(table)

with open("example.txt", "w", encoding="utf-8") as file:
    for data in duplicate_report:
        file.write(data + " " + str(duplicate_report[data]) + "\n")