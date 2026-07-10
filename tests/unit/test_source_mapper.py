import pandas as pd

from service.source_processing.source_mapper import (
    filter_columns,
)

# filter_columns() - удаление лишних колонок
def test_filter_columns_removes_extra():

    df = pd.DataFrame(
        {
            "inn": ["123"],
            "случайный заголовок1": [123],
            "случайный_заголовок2": ["123"],
        }
    )

    result = filter_columns(
        df,
        required_columns=["inn"]
    )

    filtered = result["df"]

    assert "inn" in filtered.columns

    assert "случайный заголовок1" not in filtered.columns
    assert "случайный_заголовок2" not in filtered.columns

# filter_columns() - добавление отсутствующих
def test_filter_columns_adds_missing():

    df = pd.DataFrame(
        {
            "inn": ["123"]
        }
    )

    result = filter_columns(
        df,
        required_columns=[
            "inn",
            "email",
            "phone",
        ]
    )

    filtered = result["df"]

    assert "email" in filtered.columns
    assert "phone" in filtered.columns

    assert filtered["email"].isna().all()
    assert filtered["phone"].isna().all()
