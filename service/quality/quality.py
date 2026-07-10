# services/quality.py
import pandas as pd
from typing import Dict, Any, List

# Импортируем список обязательных колонок, которые использует маппер
# (чтобы проверять полноту только по ним, а не по всем)
from service.source_processing.source_mapper import MVP_COLUMNS

def calculate_data_quality_score(df: pd.DataFrame, dedup_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Публичный метод для расчета качества данных.
    Принимает: очищенный DataFrame (после нормализации) и результат дедупликации.
    Возвращает: детальные метрики и общий скор.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {"error": "Empty dataset", "overall_quality_score": 0}

    # 1. COMPLETENESS (Полнота) - проверяем только обязательные колонки из ERD
    # Какая доля ячеек в обязательных колонках НЕ пустая?
    existing_mvp = [col for col in MVP_COLUMNS if col in df.columns]
    if existing_mvp:
        # Считаем общее кол-во ячеек в этих колонках
        total_cells = len(existing_mvp) * total_rows
        # Считаем, сколько из них не пустые (не NaN и не пустая строка)
        non_empty_cells = 0
        for col in existing_mvp:
            non_empty_cells += df[col].notna().sum()  # pandas считает не-NaN
            # Дополнительно убираем пустые строки ""
            if df[col].dtype == 'object':
                non_empty_cells -= (df[col] == "").sum()
        completeness_score = non_empty_cells / total_cells if total_cells > 0 else 0
    else:
        completeness_score = 0

    # 2. UNIQUENESS (Уникальность) - берем готовый результат от Ника
    # dedup_result["rows_affected"] — это сколько строк оказались в коллизиях (дубли)
    rows_affected = dedup_result.get("rows_affected", 0)
    # Уникальность = 1 - (доля строк-дублей)
    uniqueness_score = 1 - (rows_affected / total_rows) if total_rows > 0 else 0
    # Если rows_affected == 0, то скор = 1.0

    # 3. ACCURACY (Точность / Валидность) - проверяем, как сработали чистильщики
    # Логика: если после очистки в колонке остались пустые значения (None или ""),
    # значит исходные данные были невалидными (например, мусорный телефон).
    # Считаем долю валидных (непустых) записей в ключевых колонках.
    accuracy_checks = []
    for col in ['inn', 'phone', 'email', 'address']:
        if col in df.columns:
            # Считаем, сколько строк в этой колонке НЕ пустые после очистки
            non_empty = df[col].notna().sum()
            # Если в колонке строки, убираем пустые строки ""
            if df[col].dtype == 'object':
                non_empty -= (df[col] == "").sum()
            ratio = non_empty / total_rows
            accuracy_checks.append(ratio)
    
    # Если в данных вообще не было этих колонок — ставим среднюю оценку 0.8
    accuracy_score = sum(accuracy_checks) / len(accuracy_checks) if accuracy_checks else 0.8

    # 4. CONSISTENCY (Согласованность) - проверяем формат ключевых полей через готовые методы
    # Мы уже прогнали clean_inn, clean_phone и т.д. Если они вернули не None — формат ок.
    # Но проще: проверим, есть ли в этих колонках мусор (цифры/буквы вне шаблона).
    # Сделаем прокси-проверку: если длина строки в колонке "нормальная" (не выбивается)
    consistency_scores = []
    for col in ['inn', 'phone', 'email']:
        if col in df.columns:
            # Переводим в строку и считаем длину
            lengths = df[col].astype(str).str.len()
            # Убираем бесконечности/NaN
            lengths = lengths[lengths > 0]
            if len(lengths) > 1:
                # Если стандартное отклонение маленькое (или средняя длина ~10 для ИНН/телефона)
                mean_len = lengths.mean()
                # Если средняя длина в районе ожидаемой (ИНН ~10, телефон ~11, email ~15-20)
                if ('inn' in col and 8 < mean_len < 14) or \
                   ('phone' in col and 9 < mean_len < 14) or \
                   ('email' in col and 8 < mean_len < 30):
                    col_score = 0.95  # почти идеально
                else:
                    # Считаем % записей, длина которых близка к средней (в пределах 3 сигм)
                    std = lengths.std()
                    if std > 0:
                        within = ((lengths - mean_len).abs() <= 3 * std).sum()
                        col_score = within / len(lengths)
                    else:
                        col_score = 1.0
                consistency_scores.append(col_score)
            else:
                consistency_scores.append(0.5)  # мало данных
    
    consistency_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.8

    # 5. ИТОГОВЫЙ СКОР (среднее арифметическое)
    overall = (completeness_score + uniqueness_score + accuracy_score + consistency_score) / 4

    return {
        "total_rows": total_rows,
        "metrics": {
            "completeness": round(completeness_score, 4),   # Насколько заполнены поля
            "uniqueness": round(uniqueness_score, 4),       # Насколько нет дублей
            "accuracy": round(accuracy_score, 4),           # Насколько данные валидны
            "consistency": round(consistency_score, 4),     # Насколько единообразны
        },
        "overall_quality_score": round(overall, 4),
        "details": {
            "duplicate_rows_affected": rows_affected,
            "checked_columns": existing_mvp
        }
    }