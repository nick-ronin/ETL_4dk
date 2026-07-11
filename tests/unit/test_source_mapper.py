import pandas as pd

from service.source_processing.source_mapper import (
    filter_columns,
    load_file,
    process_file
)

# ============================================================
# filter_columns
# ============================================================

# удаление лишних колонок
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

# добавление отсутствующих
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

# ============================================================
# load_file()
# ============================================================

#КРИВОЙ ТЕСТ!!!!
def test_load_file_mapper(tmp_path): #⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅⬅
    df = pd.DataFrame({"inn": ["123"]})
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)
    result = load_file(str(file_path))
    assert result.equals(df)

# ============================================================
# process_file()
# ============================================================

# создадим минимальный Excel с колонкой inn
def test_process_file(tmp_path):
    df = pd.DataFrame({"inn": ["1234567890"]})
    input_path = tmp_path / "standard_test.xlsx"
    df.to_excel(input_path, index=False)
    result = process_file(str(input_path), required_columns=["inn"], output_folder=str(tmp_path))
    assert result["status"] == "OK"
    assert result["df"] is not None