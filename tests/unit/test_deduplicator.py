import pandas as pd

from service.deduplicator.get_duplicates import (
    get_duplicates,
)


# дубликаты отсутствуют
def test_duplicates_none(tmp_path):

    df = pd.DataFrame(
        {
            "inn": ["1", "2", "3"]
        }
    )
    result = get_duplicates(
        df,
        ["inn"],
        output_dir=tmp_path,
    )
    assert result["rows_affected"] == 0

# поиск частичных дубликатов
def test_duplicates_partial(tmp_path):

    df = pd.DataFrame(
        {
            "inn": ["1", "1", "2"]
        }
    )
    result = get_duplicates(
        df,
        ["inn"],
        output_dir=tmp_path,
    )
    assert result["rows_affected"] == 4

# поиск полных дубликатов
def test_duplicates_full(tmp_path):

    df = pd.DataFrame(
        {
            "inn": ["1", "1"],
            "phone": ["123", "123"],
        }
    )
    result = get_duplicates(
        df,
        ["inn"],
        output_dir=tmp_path,
    )
    assert result["rows_affected"] > 0

def test_duplicates_with_nan(tmp_path):
    df = pd.DataFrame(
        {
            "inn": [None, "1", "1"]
            }
    )
    result = get_duplicates(
        df, ["inn"], output_dir=tmp_path
        )
    assert result["rows_affected"] == 4
    # частичные дубликаты по "1" (2 строки) + полные дубликаты по "1" (ещё 2)

# Пустой датафрейм
def test_duplicates_empty_df(tmp_path):
    df = pd.DataFrame()
    result = get_duplicates(df, ["inn"], output_dir=tmp_path)
    assert result["rows_affected"] == 0