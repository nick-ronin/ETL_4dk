import pandas as pd

from service.source_processing.source_loader import (
    map_columns,
    normalize_columns,
    validate_required_columns,
)

# ============================================================
# map_columns()
# ============================================================

def test_map_columns_known_fields():
    columns = [
        "ИНН",
        "Телефон",
        "Email",
    ]

    mapping = map_columns(columns)

    assert mapping["ИНН"] == "inn"
    assert mapping["Телефон"] == "phone"
    assert mapping["Email"] == "email"

# Неизвестные поля не меняются
def test_map_columns_unknown_field():
    columns = [
        "Возраст"
    ]

    mapping = map_columns(columns)

    assert mapping["Возраст"] == "Возраст"

# ============================================================
# normalize_columns()
# ============================================================

def test_normalize_columns(sample_dataframe):
    df = normalize_columns(sample_dataframe)

    assert "inn" in df.columns
    assert "phone" in df.columns
    assert "email" in df.columns

    assert "ИНН" not in df.columns
    assert "Телефон" not in df.columns

# ============================================================
# validate_required_columns()
# ============================================================

# есть обяз. колонка
def test_validate_required_columns_ok():

    df = pd.DataFrame(
        {
            "inn": ["7707083893"]
        }
    )

    result = validate_required_columns(df)

    assert result["status"] == "OK"

# нет обяз. колонка
def test_validate_required_columns_warning():

    df = pd.DataFrame(
        {
            "phone": ["79991234567"]
        }
    )

    result = validate_required_columns(df)

    assert result["status"] == "WARNING"
    assert "inn" in result["missing_columns"]

# несколько обяз. полей
def test_validate_multiple_required_columns():

    df = pd.DataFrame(
        {
            "inn": ["7707083893"]
        }
    )

    result = validate_required_columns(
        df,
        required_columns=[
            "inn",
            "ogrn",
            "phone",
        ]
    )

    assert result["status"] == "WARNING"

    assert "ogrn" in result["missing_columns"]
    assert "phone" in result["missing_columns"]
