import pandas as pd

from service.exporter.exporter import (
    export_simple,
    export_from_mapper,
)

# export_simple() - простой экспорт
def test_export_simple(tmp_path):

    df = pd.DataFrame(
        {
            "inn": ["123"]
        }
    )

    path = export_simple(
        df,
        output_folder=tmp_path,
    )

    assert path.endswith(".xlsx")

# export_from_mapper() - ошибка mapper
def test_export_mapper_error():

    result = export_from_mapper(
        {
            "status": "ERROR"
        }
    )

    assert result["status"] == "ERROR"

# export_from_mapper() - пустой DataFrame
def test_export_mapper_empty():

    result = export_from_mapper(
        {
            "status": "OK",
            "df": pd.DataFrame(),
        }
    )

    assert result["status"] == "ERROR"

# export_from_mapper() - успешный экспорт
def test_export_mapper_ok(tmp_path):

    result = export_from_mapper(
        {
            "status": "OK",
            "df": pd.DataFrame(
                {
                    "inn": ["123"]
                }
            )
        },
        output_folder=tmp_path,
    )

    assert result["status"] == "OK"

