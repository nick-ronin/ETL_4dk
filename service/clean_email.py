import re
import pandas as pd

def clean_email(email_str):
    """
    Метод очистки адресов электронной почты.

    Принимает:
        email_str (str) - строку с одним или несколькими email.
        Email могут быть разделены символами ';', ',', '/', '|'
        или переносом строки.

    Выполняет:
        - проверяет корректность входных данных;
        - приводит email к нижнему регистру;
        - удаляет лишние пробелы;
        - извлекает корректные email;
        - удаляет повторяющиеся адреса;
        - объединяет найденные email через запятую.

    Возвращает:
        str  - строку с очищенными email;
        None - если корректные email не найдены;
        исходное значение - если оно не является строкой или равно NaN.
    """

    # Если в ячейке пусто (NaN) или там не текст (например, число)
    # то ничего не делаем и возвращаем как есть, чтобы не было ошибки
    if pd.isna(email_str) or not isinstance(email_str, str):
        return email_str

    # Шаблон, который описывает, как должен выглядеть правильный email
    pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

    # Режем длинную строку на кусочки, если там используются разделители: ; , / | или перенос строки
    parts = re.split(r'[;,/|\n]+', email_str)

    cleaned_parts = []  # Сюда будем складывать только хорошие email
    seen = set()        # Список "уже увиденных", чтобы не повторяться

    for part in parts:
        # Убираем лишние пробелы по бокам и делаем все буквы маленькими
        part = part.strip().lower()

        # Если после очистки кусок оказался пустым — пропускаем его
        if not part:
            continue

        # Ищем внутри этого кусочка всё, что похоже на email по нашему шаблону
        emails = re.findall(pattern, part)

        for email in emails:
            # Если мы этот email еще не встречали раньше...
            if email not in seen:
                seen.add(email)          # Запоминаем его, чтобы не брать повторно
                cleaned_parts.append(email)  # Добавляем в наш список чистых email

    # Если нашли хоть один email — склеиваем их через запятую
    # Если ничего не нашли — возвращаем "Ничего" (None)
    return ', '.join(cleaned_parts) if cleaned_parts else None



# print(clean_email(""))
# print(clean_email("testexample.com; user@domain.org, admin@company.com / support@service.net | info@business.info, test.com"))
