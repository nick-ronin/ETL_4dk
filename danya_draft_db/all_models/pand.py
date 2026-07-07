import pandas as pd
import re

def clean_phone(phone_str):

    """
    Приводит номера телефонов к формату +7XXXXXXXXXX.
    Поддерживает разделители: ; , / |.
    Номера, начинающиеся с 8, заменяются на +7.
    Если номер уже содержит +, он сохраняется.
    Несколько номеров в одной ячейке объединяются через ', '.
    """
    if pd.isna(phone_str) or not isinstance(phone_str, str):
        return phone_str

    # Разбиваем по основным разделителям (точка с запятой, запятая, слэш, вертикальная черта)
    parts = re.split(r'[;,/|]\s*', phone_str.strip())
    cleaned_parts = []

    for part in parts:
        if not part.strip():
            continue

        # Проверяем, есть ли '+' в начале
        has_plus = part.strip().startswith('+')

        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', part)

        if not digits:
            continue

        # Если номер начинается с 8, заменяем на 7 (для российских номеров)
        if digits.startswith('8'):
            digits = '7' + digits[1:]

        # Добавляем '+' в зависимости от исходного формата
        if has_plus:
            # Если уже был плюс, но номер начинался с 8 после очистки, мы уже исправили
            cleaned = '+' + digits
        else:
            # Если номер начинается с 7, добавляем '+'
            if digits.startswith('7'):
                cleaned = '+' + digits
            else:
                # На случай, если номер не содержит кода страны – добавляем '+7' (можно изменить по необходимости)
                cleaned = '+7' + digits

        cleaned_parts.append(cleaned)

    # Объединяем части через запятую с пробелом
    return ', '.join(cleaned_parts) if cleaned_parts else None


def twoGis_cleaning(df):
    
    # df = pd.read_csv(str(twoGis_path), sep=',', encoding='utf-8')

    df['Телефон'] = df['Телефон'].apply(clean_phone)
    df['Мобильный телефон'] = df['Мобильный телефон'].apply(clean_phone)

    df['Индекс'] = df['Индекс'].astype('Int64')

    new_df = df[['Название', 'Город', 'Адрес', 'Индекс', 'Телефон', 
    'Мобильный телефон', 'Email', 'Сайт', 
    'Подрубрика', 'whatsapp', 'telegram', 'vkontakte' ]]

    # убрать потом
    new_df.to_csv('test.csv', index=False, encoding='utf-8')
    return new_df



# проверить, добавить ли id
# Добавить столбцы все сайты и все телефоны
def yandex_cleaning(yandex_path):
    df = pd.read_csv(str(yandex_path), sep=',', encoding='utf-8')

    df['Мобильные'] = df['Мобильные'].apply(clean_phone)
    df['Немобильные'] = df['Немобильные'].apply(clean_phone)
    # df['Все телефоны'] = df['Все телефоны'].apply(clean_phone)

    df['Индекс'] = df['Индекс'].astype('Int64')

    new_df = df[['Название', 'Категории', 'Индекс', 'Город', 'Полный адрес', 
    'Мобильные', 'Немобильные', 'Сайт', 
    # 'Все сайты', 'Все телефоны' 
    ]]

    # убрать потом
    new_df.to_csv('test.csv', index=False, encoding='utf-8')

    return new_df


# проверить, добавить ли id
def old_twoGis_cleaning(old_twoGis_path):
    
    df = pd.read_csv(str(old_twoGis_path), sep=',', encoding='utf-8')

    df['Мобильные'] = df['Мобильные'].apply(clean_phone)
    df['Немобильные'] = df['Немобильные'].apply(clean_phone)


    new_df = df[['Название', 'Полное название', 'Email', 'Сайт', 
    'Мобильные', 'Немобильные', 'Город', 'Адрес']]

    # убрать потом
    new_df.to_csv('test.csv', index=False, encoding='utf-8')

    return new_df



def chekko_cleaning(chekko_path):
    
    df = pd.read_csv(str(chekko_path), sep=',', encoding='utf-8')

    df['Телефоны'] = df['Телефоны'].apply(clean_phone)

    new_df = df[['Сокращенное наименование', 'Полное наименование', 'ОГРН', 'ИНН', 
    'КПП', 'Телефоны', 'Email', 'Веб-сайт', 
    'Статус', 'Дата регистрации', 'Юридический адрес', 'Код ОКВЭД-2' , 
    'Основной вид деятельности', 'Руководитель', 'Должность', 'ИНН руководителя' , 
    'ССЧ', 'Реестр МСП', 'Уставный капитал', 'Специальные налоговые режимы',
    'Уплаченные налоги']]

    # убрать потом
    new_df.to_csv('test.csv', index=False, encoding='utf-8')
    return new_df


# print(chekko_cleaning('chekko.csv'))