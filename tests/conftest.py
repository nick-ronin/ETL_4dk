import pandas as pd
import pytest


@pytest.fixture
def sample_dataframe():
    """
    Небольшой DataFrame для unit-тестов.
    """

    return pd.DataFrame(
        {
            "ИНН": ["7707083893"],
            "Телефон": ["+7 (999) 123-45-67"],
            "Email": ["test@test.ru"],
            "Возраст": [20],
        }
    )