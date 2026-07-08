"""
API для загрузки Excel/CSV файлов.

Автор: Михаил
"""
import math
import os
import tempfile

import pandas as pd
from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from service.SourceLoader.src.source_loader import process_uploaded_file

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)


def clean_json_value(obj):
    """
    Рекурсивно заменяет float('nan'), float('inf'), float('-inf') на None,
    чтобы гарантировать совместимость с JSON (allow_nan=False).
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {key: clean_json_value(val) for key, val in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_value(item) for item in obj]
    return obj


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """
    Принимает Excel/CSV файл, нормализует колонки и возвращает данные в JSON.
    """
    extension = os.path.splitext(file.filename)[1]
    temp_path = None                         # инициализируем заранее, чтобы избежать NameError

    try:
        # Сохраняем загруженный файл во временный файл
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:
            temp.write(await file.read())
            temp_path = temp.name

        # Обрабатываем через SourceLoader
        result = process_uploaded_file(
            file_path=temp_path,
            required_columns=["inn"],
            save_output=False
        )

        if result["status"] == "ERROR":
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )

        df = result["df"]

        # Подготавливаем безопасные для JSON данные
        raw_data = df.to_dict(orient="records")
        clean_data = clean_json_value(raw_data)   # убираем все NaN и Infinity

        return {
            "status": result["status"],
            "validation": result["validation_result"],
            "rows": len(df),
            "columns": list(df.columns),
            "data": clean_data
        }

    finally:
        # Гарантированно удаляем временный файл, если он был создан
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)