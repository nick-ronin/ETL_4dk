import pandas as pd

from service.quality.quality import (
    calculate_data_quality_score,
)

# calculate_data_quality_score() - ???
def test_quality_score_range():

    df = pd.DataFrame(
        {
            "inn": ["1234567890"],
            "phone": ["79991234567"],
            "email": ["test@test.ru"],
            "address": ["Москва"],
        }
    )

    dedup_result = {
        "rows_affected": 0
    }

    result = calculate_data_quality_score(
        df,
        dedup_result,
    )

    assert 0 <= result["overall_quality_score"] <= 1

# calculate_data_quality_score() - ???
def test_quality_metrics_exist():

    df = pd.DataFrame(
        {
            "inn": ["1234567890"]
        }
    )

    dedup_result = {
        "rows_affected": 0
    }

    result = calculate_data_quality_score(
        df,
        dedup_result,
    )

    assert "metrics" in result

    assert "completeness" in result["metrics"]
    assert "accuracy" in result["metrics"]
    assert "consistency" in result["metrics"]
    assert "uniqueness" in result["metrics"]

def test_quality_empty_df():
    df = pd.DataFrame()
    res = calculate_data_quality_score(df, {"rows_affected": 0})
    assert res == {"error": "Пустой датасет", "overall_quality_score": 0}

def test_quality_no_mvp_columns():
    df = pd.DataFrame({"name": ["a", "b"]})
    res = calculate_data_quality_score(df, {"rows_affected": 0})
    assert res["metrics"]["completeness"] == 0.0
    assert res["metrics"]["accuracy"] == 0.8   # нет проверяемых колонок → 0.8
    assert res["metrics"]["consistency"] == 0.8
    assert res["metrics"]["uniqueness"] == 1.0  # rows_affected=0
    assert abs(res["overall_quality_score"] - 0.65) < 0.01

def test_quality_all_nan():
    df = pd.DataFrame({"inn": [None, None], "phone": [None, None],
                       "email": [None, None], "address": [None, None]})
    res = calculate_data_quality_score(df, {"rows_affected": 0})
    assert res["metrics"]["completeness"] == 0.0
    assert res["metrics"]["accuracy"] == 0.0
    assert res["metrics"]["consistency"] == 1.0  # все "nan" -> длина 3, считается единообразным
    assert res["metrics"]["uniqueness"] == 1.0
    assert abs(res["overall_quality_score"] - 0.5) < 0.01