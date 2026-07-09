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

from service.source_processing.src.source_loader import process_uploaded_file
from service.source_processing.src.source_mapper import process_file, MVP_COLUMNS

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
    temp_path = None  # инициализируем заранее, чтобы избежать NameError

    try:
        # Сохраняем загруженный файл во временный файл
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:
            temp.write(await file.read())
            temp_path = temp.name

        # Обрабатываем через SourceLoader
        upload_result = process_uploaded_file(
            file_path=temp_path,
            required_columns=MVP_COLUMNS,
            save_output=True, 
            output_folder="output"
        )

        if upload_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=upload_result["error"])
        
        normalised_file_path = upload_result.get("saved_file")
        if not normalised_file_path or not os.path.exists(normalised_file_path):
            raise HTTPException(status_code=500, detail="Не удалось получить выходной файл после нормализации")
        
        validation_info = upload_result.get("validation_result", "Нет данных")

        mapper_result = process_file(
            input_file_path=normalised_file_path,
            required_columns=MVP_COLUMNS,
            output_folder="output"
        )

        if mapper_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=mapper_result.get("error", "Ошибка маппера"))

        df = mapper_result["df"]
        raw_data = df.to_dict(orient="records")
        clean_data = clean_json_value(raw_data)

        return {
            "status": mapper_result["status"],
            "validation": str(validation_info),
            "rows": len(df),
            "columns": list(df.columns),
            "data": clean_data
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)