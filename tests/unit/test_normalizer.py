import pandas as pd

from service.normalizer.normalizer import (
    clean_phone,
    clean_email,
    clean_inn,
    clean_short_name,
    clean_full_name,
    clean_address,
)

# ============================================================
# clean_phone()
# ============================================================

# замена 8 на +7
def test_clean_phone_replace_8():

    result = clean_phone(
        "89991234567"
    )

    assert result == "+79991234567"

# корректный номер не изменяется
def test_clean_phone_keep_plus():

    result = clean_phone(
        "+79991234567"
    )

    assert result == "+79991234567"

# несколько телефонов объединяются через запятую
def test_clean_phone_multiple():

    result = clean_phone(
        "+79991234567;+79001112233"
    )

    assert result == "+79991234567, +79001112233"

# поддержка разных разделителей
def test_clean_phone_separators():

    result = clean_phone(
        "+79991234567|+79001112233/+79112223344"
    )

    assert result == (
        "+79991234567, +79001112233, +79112223344"
    )

# пустая строка
def test_clean_phone_empty():

    result = clean_phone(
        ""
    )
    assert result is None

# строка без цифр
def test_clean_phone_invalid():

    result = clean_phone(
        "мусор"
    )
    assert result is None

def test_clean_phone_comment():
    result = clean_phone("+7 (925) 001-16-10 Андрей, Андрей")
    assert result == "+79250011610"  
    # комментарий удаляется

def test_clean_phone_short():
    result = clean_phone("112")
    assert result == "112"
    # текущая логика добавляет +7 - +7112

def test_clean_phone_8_800():
    result = clean_phone("8-800-777-85-21")
    assert result == "88007778521"
    # текущая логика сделает +78007778521

def test_clean_phone_multiple_mixed():
    result = clean_phone("8-800-777-85-21;+7 (495) 123-45-67")
    assert result == "88007778521, +74951234567"
    # текущая логика сделает +78007778521, +74951234567

# вроде не нашел такого в паспорте источников
'''
def test_clean_phone_dobav():
    result = clean_phone("123-45-67 доб. 89")
    assert result == "+71234567"   # оставляет только цифры, добавляет +7
'''

# ============================================================
# clean_email()
# ============================================================

# один email
def test_clean_email_single():

    result = clean_email(
        "Test@Mail.Ru"
    )

    assert result == "test@mail.ru"

# несколько email
def test_clean_email_multiple():

    result = clean_email(
        "a@mail.ru;b@gmail.ru"
    )

    assert result == "a@mail.ru, b@gmail.ru"

# удаление дубликатов
def test_clean_email_duplicates():

    result = clean_email(
        "a@mail.ru;a@mail.ru"
    )

    assert result == "a@mail.ru"

# некорректный email
def test_clean_email_invalid():

    result = clean_email(
        "не почта"
    )

    assert result is None

def test_clean_email_cyrillic():
    result = clean_email("почта@почта.рф")                          #⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅
    assert result == "почта@почта.рф"
    # регулярка не поддерживает кириллицу и вернет none?


# ============================================================
# clean_inn()
# ============================================================

# корректный ИНН
def test_clean_inn_ok():

    result = clean_inn(
        "7707083893"
    )

    assert result == "7707083893"

# очистка лишних символов
def test_clean_inn_symbols():

    result = clean_inn(
        "77 07-083893"
    )

    assert result == "7707083893"

# неверная длина
def test_clean_inn_wrong_length():

    result = clean_inn(
        "123"
    )

    assert result == "Неверный формат ИНН"

# запрещенный префикс
def test_clean_inn_zero_prefix():

    result = clean_inn(
        "0012345678"
    )

    assert result == "Неверный формат ИНН"


# ============================================================
# clean_short_name()
# ============================================================

# удаление ООО
def test_clean_short_name():

    result = clean_short_name(
        'ООО "СТАНКОИМПОРТ"'
    )
    assert result == "СТАНКОИМПОРТ"

# удаление ИП
def test_clean_short_name_ip():
    result = clean_short_name("ИП Иванов И.И.")
    assert result == "ИВАНОВ И.И."

# обрезка по запятой
def test_clean_short_name_comma():

    result = clean_short_name(
        "ЕДС-Щелково, ООО, единая диспетчерская"
    )
    assert result == "ЕДС-ЩЕЛКОВО"

# ООО в конце а не в начале - такое есть в паспорте?        #⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅
def test_clean_short_name_opf_end():
    result = clean_short_name("Рога и копыта ООО")
    assert result == "РОГА И КОПЫТА"


# ============================================================
# clean_full_name()
# ============================================================

# расшифровка ООО
def test_clean_full_name_expand():

    result = clean_full_name(
        'ООО "СТАНКОИМПОРТ"'
    )

    assert result.startswith(
        "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ"
    )

def test_clean_full_name_already_expanded():
    result = clean_full_name("" \
    "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ СТАНКОИМПОРТ"
    )
    assert result == "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ СТАНКОИМПОРТ"

def test_clean_full_name_quotes():
    result = clean_full_name('' \
    'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СТАНКОИМПОРТ"'
    )
    assert result == "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ СТАНКОИМПОРТ"


"""
!!!
!!!
!!!
"""
'''
⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇
'''
# ============================================================
# clean_address() - нормализация адреса
# ============================================================
def test_clean_address():

    result = clean_address(
        "ул. Ленина, д. 5 корп.2"
    )

    #assert result == "Ленина, 5 корп2"             ⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅
    # ИЛИ??
    assert result == "ул. Ленина, 5 корп2"


# clean_address() - удаление переносов строк
def test_clean_address_newline():

    result = clean_address(
        "ул.\nЛенина,\nд.5"
    )

    #assert result == "Ленина, 5"                   ⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅
    # ИЛИ??
    assert result == "ул. Ленина, 5"
'''
⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆⬆
'''
"""
!!!
!!!
!!!
"""
# тут вопрос к каждому
def test_clean_address_flat():
    result = clean_address("ул. Ленина, д. 5, кв. 13")
    assert result == "ул. Ленина, 5, кв. 13"  # ул. не удаляется, кв. не обрабатывается

def test_clean_address_vladenie():
    result = clean_address("вл13с1кБ")
    assert result == "вл13с1кБ"

def test_clean_address_index_city():
    result = clean_address("123458, г. Москва, ул. Маршала Катукова, д. 24")
    assert result == "123458, г. Москва, ул. Маршала Катукова, 24"

def test_clean_address_prospekt():
    result = clean_address("проспект Мира, д. 10")
    assert result == "проспект Мира, 10"