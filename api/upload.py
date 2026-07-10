"""
API для загрузки Excel/CSV файлов.

Автор: Михаил
"""
import math
import os
import tempfile
import mimetypes
from datetime import datetime

import pandas as pd
from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

# loader, mapper, validator
from service.source_processing.source_loader import process_uploaded_file
from service.source_processing.source_mapper import process_file, MVP_COLUMNS

# normalizer 
from service.normalizer.normalizer import clean_inn, clean_phone, clean_email, normalize_company_names, clean_address

# deduplicator
from service.deduplicator.get_duplicates import get_duplicates

# data quality score
from service.quality.quality import calculate_data_quality_score

from service.exporter.exporter import export_with_report

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
    ПАЙПЛАЙН ОБРАБОТКИ ФАЙЛА:
    1. Загрузка и нормализация колонок (SourceLoader)
    2. Валидация обязательных полей
    3. Фильтрация под ERD (SourceMapper)
    4. Нормализация данных (очистка ИНН, телефонов, названий)
    5. Поиск коллизий/дубликатов
    6. Оценка качества результата
    7. Возврат результата в Excel-файлах
    """
    extension = os.path.splitext(file.filename)[1]
    temp_path = None  # инициализируем заранее, чтобы избежать NameError

    source_name = file.filename
    source_type = source_name.split('.')[1]
    now = datetime.now()
    source_date = now.strftime("%d-%m-%Y")

    try:
        # Сохраняем загруженный файл во временный файл
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:
            temp.write(await file.read())
            temp_path = temp.name

        # ================================================
        # ШАГ 1: SourceLoader — загрузка и маппинг колонок
        # ================================================
        
        print("\n" + "="*60)
        print("ШАГ 1/4: SourceLoader — загрузка и маппинг колонок")
        print("="*60)

        upload_result = process_uploaded_file(
            file_path=temp_path,
            required_columns=MVP_COLUMNS, #TODO: протестить с erd_columns
            save_output=True, 
            output_folder="output"
        )

        # ================================================
        # ШАГ 2: Валидация (уже внутри process_uploaded_file)
        # ================================================

        if upload_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=upload_result["error"])
        validation_info = upload_result.get("validation_result", "Нет данных")

        # Получаем путь к нормализованному файлу
        normalised_file_path = upload_result.get("saved_file")
        if not normalised_file_path or not os.path.exists(normalised_file_path):
            raise HTTPException(status_code=500, detail="Не удалось получить выходной файл после нормализации")

        # ================================================
        # ШАГ 3: SourceMapper — фильтрация под ERD
        # ================================================

        print("\n" + "="*60)
        print("ШАГ 2/4: SourceMapper — фильтрация колонок под ERD")
        print("="*60)

        mapper_result = process_file(
            input_file_path=normalised_file_path,
            required_columns=MVP_COLUMNS, #TODO: протестить с erd_columns
            output_folder="output"
        )

        if mapper_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=mapper_result.get("error", "Ошибка маппера"))

        df = mapper_result["df"]

        # ================================================
        # ШАГ 4: Нормализация данных
        # ================================================

        print("\n" + "="*60)
        print("ШАГ 3/4: Нормализатор — очистка данных")
        print("="*60)
        
        df = normalize_company_names(df)
        print("✓ Названия компаний нормализованы")

        # точно посмотреть че делает apply
        df['inn'] = df['inn'].apply(clean_inn)
        print("✓ ИНН очищены")
        
        df['phone'] = df['phone'].apply(clean_phone)
        print("✓ Телефоны очищены")
        
        df['email'] = df['email'].apply(clean_email)
        print("✓ Email очищены")

        df['address'] = df['address'].apply(clean_address)
        print("✓ Адреса очищены")

        # ================================================
        # ШАГ 5: Дедупликация
        # ================================================
        print("\n" + "="*60)
        print("ШАГ 4/4: Дедупликатор — поиск коллизий")
        print("="*60)

        dup_columns = ['inn', 'email', 'phone', 'short_name']
        
        # ХЗ ЧЕ ЗА КОД
        dup_columns = [c for c in dup_columns if c in df.columns]

        dedup_result = get_duplicates(
            df,
            columns=dup_columns,
            source_name=file.filename,           # имя исходного файла
            output_dir="output"
        )

        print(f"✓ Отчёт сохранён: {dedup_result['collisions_file']}")
        print(f"✓ Строк с коллизиями: {dedup_result['rows_affected']}")

        # ================================================
        # ШАГ 6: Расчёт качества данных
        # ================================================
        print("\n" + "="*60)
        print("Расчёт качества данных")
        print("="*60)
         
        quality_report = calculate_data_quality_score(df, dedup_result)
        print(f'''✓ Quality Score рассчитан: {quality_report['overall_quality_score']}
        Детально:
        COMPLETENESS (Полнота) = {quality_report['metrics'].get("completeness")}
        UNIQUENESS (Уникальность) = {quality_report['metrics'].get("uniqueness")}
        ACCURACY (Точность / Валидность) = {quality_report['metrics'].get("accuracy")}
        CONSISTENCY (Согласованность) = {quality_report['metrics'].get("consistency")}''')
        
        raw_data = df.to_dict(orient="records")

        for item in raw_data:
            item["source_type"] = source_type
            item["source_name"] = source_name
            item["source_date"] = source_date

        # TODO: формировать id по сегодняшней дате и порядковому номеру

        # clean_data = clean_json_value(raw_data)

        clean_data = export_with_report(df)

        if normalised_file_path and os.path.exists(normalised_file_path):
            os.remove(normalised_file_path)
            print(f"Удалён промежуточный файл: {normalised_file_path}")

        mapper_output_file = mapper_result.get("output_file")
        if mapper_output_file and os.path.exists(mapper_output_file):
            os.remove(mapper_output_file)
            print(f"Удалён промежуточный файл маппера: {mapper_output_file}")

        return {
            "status": mapper_result["status"],
            "validation": str(validation_info),
            "rows": len(df),
            "columns": list(df.columns),
            "quality": quality_report,
            "data": clean_data
        }
        

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)