# service/quality/quality.py
import pandas as pd
from typing import Dict, Any, List

# Импортируем список обязательных колонок, которые использует маппер
# (чтобы проверять полноту только по ним, а не по всем)
from service.source_processing.source_mapper import MVP_COLUMNS


def calculate_data_quality_score(df: pd.DataFrame, dedup_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Вычисляет обобщённую метрику качества данных на основе четырёх аспектов:
    - Полнота (completeness) – доля заполненных ячеек среди обязательных колонок MVP_COLUMNS
    - Уникальность (uniqueness) – на основе количества затронутых дубликатов из dedup_result
    - Точность (accuracy) – доля непустых значений после очистки в ключевых полях (inn, phone, email, address)
    - Согласованность (consistency) – единообразие длин значений в полях inn, phone, email

    Параметры
    ----------
    df : pd.DataFrame
        Очищенный (после нормализации) датафрейм с данными.
    dedup_result : Dict[str, Any]
        Результат работы дедубликатора; должен содержать ключ 'rows_affected' –
        количество строк, участвовавших в коллизиях (дубликатах).

    Возвращает
    ----------
    Dict[str, Any]
        Словарь со следующими ключами:
        - 'total_rows': общее количество строк в df
        - 'metrics': словарь с оценками по шкале 0.0–1.0 для каждого аспекта:
            'completeness', 'uniqueness', 'accuracy', 'consistency'
        - 'overall_quality_score': итоговая оценка (среднее арифметическое четырёх метрик)
        - 'details': дополнительная информация (число затронутых дубликатов, проверенные колонки)
        Если датафрейм пуст, возвращается {'error': 'Пустой датасет', 'overall_quality_score': 0}.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {"error": "Пустой датасет", "overall_quality_score": 0}

    # ------------------------------------------------------------------
    # 1. ПОЛНОТА (COMPLETENESS)
    # Проверяем только колонки из MVP_COLUMNS (обязательные поля маппера).
    # Считаем долю непустых ячеек среди этих колонок.
    # ------------------------------------------------------------------
    existing_mvp = [col for col in MVP_COLUMNS if col in df.columns]
    if existing_mvp:
        total_cells = len(existing_mvp) * total_rows
        non_empty_cells = 0
        for col in existing_mvp:
            # notna() даёт True для всего, что не NaN
            filled = df[col].notna().sum()
            # Вычитаем пустые строки и прочерки (типичный мусор)
            if df[col].dtype == 'object':
                filled -= (df[col] == "").sum()
                filled -= (df[col] == "-").sum()
            non_empty_cells += filled
        completeness_score = non_empty_cells / total_cells if total_cells > 0 else 0
    else:
        completeness_score = 0

    # ------------------------------------------------------------------
    # 2. УНИКАЛЬНОСТЬ (UNIQUENESS)
    # Основываемся на результате дедубликации: rows_affected – количество строк,
    # попавших в коллизии. Уникальность = 1 - (доля затронутых строк).
    # ------------------------------------------------------------------
    rows_affected = dedup_result.get("rows_affected", 0)
    uniqueness_score = 1 - (rows_affected / total_rows) if total_rows > 0 else 0

    # ------------------------------------------------------------------
    # 3. ТОЧНОСТЬ (ACCURACY)
    # После работы очистителей (нормализаторов) в ключевых полях не должно
    # оставаться пустых значений. Считаем долю непустых строк в полях
    # inn, phone, email, address. Если поля отсутствуют – fallback 0.8.
    # ------------------------------------------------------------------
    accuracy_checks = []
    for col in ['inn', 'phone', 'email', 'address']:
        if col in df.columns:
            non_empty = df[col].notna().sum()
            if df[col].dtype == 'object':
                non_empty -= (df[col] == "").sum()
                non_empty -= (df[col] == "-").sum()
            ratio = non_empty / total_rows
            accuracy_checks.append(ratio)
    accuracy_score = sum(accuracy_checks) / len(accuracy_checks) if accuracy_checks else 0.8

    # ------------------------------------------------------------------
    # 4. СОГЛАСОВАННОСТЬ (CONSISTENCY)
    # Проверяем единообразие длин строк в полях inn, phone, email.
    # Если все значения пустые (NaN) – считаем консистентность = 1.0,
    # так как отсутствие данных не говорит о неконсистентности.
    # ------------------------------------------------------------------
    consistency_scores = []
    for col in ['inn', 'phone', 'email']:
        if col in df.columns:
            # Берем только реально непустые значения: не NaN, не "", не "-"
            valid_mask = df[col].notna() & (df[col] != "") & (df[col] != "-")
            valid_series = df.loc[valid_mask, col]

            # Если после фильтрации ничего не осталось или всего одна запись –
            # не на чем оценивать вариативность, считаем консистентными.
            if len(valid_series) <= 1:
                consistency_scores.append(1.0)
                continue

            # Вычисляем длины строк
            lengths = valid_series.astype(str).str.len()
            mean_len = lengths.mean()

            # Если средняя длина попадает в ожидаемые диапазоны для типа поля,
            # считаем поле идеально консистентным.
            if ('inn' in col and 8 < mean_len < 14) or \
               ('phone' in col and 9 < mean_len < 14) or \
               ('email' in col and 5 < mean_len < 50):   # email может быть коротким (a@b.c) или длинным
                col_score = 1.0
            else:
                # В противном случае оцениваем долю значений, длина которых
                # лежит в пределах трёх стандартных отклонений от среднего.
                std = lengths.std()
                if std > 0:
                    within = ((lengths - mean_len).abs() <= 3 * std).sum()
                    col_score = within / len(lengths)
                else:
                    # Все длины одинаковы
                    col_score = 1.0
            consistency_scores.append(col_score)

    consistency_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0

    # ------------------------------------------------------------------
    # 5. ИТОГОВАЯ ОЦЕНКА
    # Простое среднее арифметическое четырёх метрик.
    # ------------------------------------------------------------------
    overall = (completeness_score + uniqueness_score + accuracy_score + consistency_score) / 4

    return {
        "total_rows": total_rows,
        "metrics": {
            "completeness": round(completeness_score, 2),
            "uniqueness": round(uniqueness_score, 2),
            "accuracy": round(accuracy_score, 2),
            "consistency": round(consistency_score, 2),
        },
        "overall_quality_score": round(overall, 2),
        "details": {
            "duplicate_rows_affected": rows_affected,
            "checked_columns": existing_mvp
        }
    }