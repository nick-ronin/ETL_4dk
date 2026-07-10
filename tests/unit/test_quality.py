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
