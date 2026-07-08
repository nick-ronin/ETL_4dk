import pandas as pd
import re # библиотека для регулярных выражений

def clean_INN(inn_raw: str ) -> str:

    # что будет возвращать
    inn_result = ""

    if pd.isna(inn_raw) or not isinstance(inn_raw, str):
        return inn_raw
    
    # Удаляем все нецифровые символы
    inn_result = re.sub(r'\D', '', inn_raw)
    
    if len(inn_result) != 10 and len(inn_result) != 12:
        return "Неверный формат ИНН"
    
    if inn_result[:2] == "00":
        return "Неверный формат ИНН"
    
    return inn_result


 # Ожидаемый результат: "771234567890"