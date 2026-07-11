import os

import pandas as pd

from service.exporter.exporter import (
    export_to_excel,
)

# export_to_excel() - ???
def test_export_to_excel(tmp_path):

    df = pd.DataFrame(
        {
            "inn": ["123"]
        }
    )

    result = export_to_excel(
        df,
        output_folder=tmp_path,
        filename="test"
    )

    assert result["status"] == "OK"

    assert os.path.exists(result["file_path"])
