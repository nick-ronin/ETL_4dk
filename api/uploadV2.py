import math
import os
import tempfile
import pandas as pd
from service.SourceLoader.src.source_loader import process_uploaded_file
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from io import BytesIO
from typing import Optional

from service.clean_phone import clean_phone
from service.clean_INN import clean_INN
from service.clean_email import clean_email
from service.clean_company_name import clean_company_name


router = APIRouter(
    prefix="/uploadV2",
    tags=["Upload"]
)


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    download: Optional[bool] = Query(False, description="Если True – вернуть Excel-файл, иначе JSON")
):
    """
    Принимает Excel/CSV файл, нормализует колонки, применяет очистку к полям:
    inn, phone, email, company_name (если они присутствуют).
    Возвращает либо JSON с очищенными данными, либо скачиваемый XLSX.
    """
    extension = os.path.splitext(file.filename)[1]
    temp_path = None

    try:
        # Сохраняем загруженный файл во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp:
            temp.write(await file.read())
            temp_path = temp.name

        # Обрабатываем через SourceLoader (твоя существующая функция)
        result = process_uploaded_file(
            file_path=temp_path,
            required_columns=["inn"],
            save_output=False
        )

        if result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=result["error"])

        df = result["df"]

        # ---------- ПРИМЕНЯЕМ ОЧИСТКУ ----------
        # Словарь соответствия колонка → функция
        clean_map = {
            "inn": clean_inn,
            "phone": clean_phone,
            "email": clean_email,
            "company_name": clean_company_name,
        }

        for col, func in clean_map.items():
            if col in df.columns:
                # Применяем функцию к колонке (обрабатываем пропуски)
                df[col] = df[col].apply(func)

        # ---------- ФОРМИРУЕМ ОТВЕТ ----------
        if download:
            # Возвращаем Excel-файл
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Cleaned Data")
            output.seek(0)

            headers = {
                "Content-Disposition": f"attachment; filename=cleaned_{file.filename.rsplit('.', 1)[0]}.xlsx"
            }
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers=headers
            )

        else:
            # Возвращаем JSON (очищенные данные)
            # Подготавливаем безопасные для JSON данные
            raw_data = df.to_dict(orient="records")
            clean_data = clean_json_value(raw_data)   # твоя функция, удаляющая NaN/Infinity

            return {
                "status": result["status"],
                "validation": result["validation_result"],
                "rows": len(df),
                "columns": list(df.columns),
                "data": clean_data
            }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)