"""
API для загрузки Excel/CSV файлов.

Автор: Михаил
"""
import math
import os
import tempfile
import zipfile
from datetime import datetime
from urllib.parse import quote
import uuid

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

from logger.logger import logger

# вывод файла
from io import BytesIO
from fastapi.responses import StreamingResponse
from typing import Optional
from fastapi import Query

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
async def upload_file(file: UploadFile = File(...),
    download: Optional[bool] = Query(False, description="True-Excel-файл, False-JSON")):
    """
    ПАЙПЛАЙН ОБРАБОТКИ ФАЙЛА:
    1. Загрузка и нормализация колонок (SourceLoader)
    2. Валидация обязательных полей
    3. Фильтрация под ERD (SourceMapper)
    4. Нормализация данных (очистка ИНН, телефонов, названий)
    5. Поиск коллизий/дубликатов
    6. Оценка качества результата
    7. Возврат архива файлов в качестве результата
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
        
        logger.info("="*60)
        logger.info("ШАГ 1/4: SourceLoader — загрузка и маппинг колонок")
        logger.info("="*60)

        upload_result = process_uploaded_file(file_path=temp_path)

        if upload_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=upload_result.get('error', "Ошибка загрузчика"))
        
        df_raw = upload_result['df']

        # ================================================
        # ШАГ 3: SourceMapper — фильтрация под ERD
        # ================================================

        logger.info("="*60)
        logger.info("ШАГ 2/4: SourceMapper — фильтрация колонок под ERD")
        logger.info("="*60)

        mapper_result = process_file(df=df_raw, required_columns=MVP_COLUMNS)

        if mapper_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=mapper_result.get("error", "Ошибка маппера"))

        df = mapper_result["df"]

        # ================================================
        # ШАГ 4: Нормализация данных
        # ================================================

        logger.info("="*60)
        logger.info("ШАГ 3/4: Нормализатор — очистка данных")
        logger.info("="*60)
        
        df = normalize_company_names(df)
        logger.info("✓ Названия компаний нормализованы")

        df['inn'] = df['inn'].apply(clean_inn)
        logger.info("✓ ИНН очищены")
        
        df['phone'] = df['phone'].apply(clean_phone)
        logger.info("✓ Телефоны очищены")
        
        df['email'] = df['email'].apply(clean_email)
        logger.info("✓ Email очищены")

        df['address'] = df['address'].apply(clean_address)
        logger.info("✓ Адреса очищены")

        df['has_email'] = df['email'].notna() & (df['email'] != '') & (df['email'] != '-')
        df['has_phone'] = df['phone'].notna() & (df['phone'] != '') & (df['phone'] != '-')

        # ================================================
        # ШАГ 5: Дедупликация
        # ================================================
        logger.info("="*60)
        logger.info("ШАГ 4/4: Дедупликатор — поиск коллизий")
        logger.info("="*60)

        dup_columns = ['inn', 'email', 'phone', 'short_name']
        
        dup_columns = [c for c in dup_columns if c in df.columns]

        dedup_result = get_duplicates(
            df,
            columns=dup_columns,
            source_name=file.filename,           # имя исходного файла
            output_dir="output"
        )

        if 'duplicate_indices' in dedup_result:
            df['duplicate_flag'] = df.index.isin(dedup_result['duplicate_indices'])

        logger.info(f"✓ Отчёт сохранён: {dedup_result['collisions_file']}")
        logger.info(f"✓ Строк с коллизиями: {dedup_result['rows_affected']}")

        # ================================================
        # ШАГ 6: Расчёт качества данных
        # ================================================
        logger.info("="*60)
        logger.info("Расчёт качества данных")
        logger.info("="*60)
         
        quality_report = calculate_data_quality_score(df, dedup_result)
        logger.info(f'''✓ Quality Score рассчитан: {quality_report['overall_quality_score']}
                            Детально:
                            COMPLETENESS (Полнота) = {quality_report['metrics'].get("completeness")}
                            UNIQUENESS (Уникальность) = {quality_report['metrics'].get("uniqueness")}
                            ACCURACY (Точность / Валидность) = {quality_report['metrics'].get("accuracy")}
                            CONSISTENCY (Согласованность) = {quality_report['metrics'].get("consistency")}''')
        
        df['source_type'] = source_type
        df['source_name'] = source_name
        df['source_date'] = source_date

        safe_name = "".join(c for c in source_name if c.isalnum())[:10]  # обрезаем до 10 символов
        df['id'] = [f"{safe_name}-{source_date}-{i+1:05d}" for i in range(len(df))]

        clean_data = df.to_dict(orient='records')

        mapper_output_file = mapper_result.get("output_file")
        if mapper_output_file and os.path.exists(mapper_output_file):
            os.remove(mapper_output_file)
            logger.info(f"Удалён промежуточный файл маппера: {mapper_output_file}")

        # ================================================
        # ШАГ 7: Формирование архива на выдачу
        # ================================================
        logger.info("="*60)
        logger.info("Формирование архива для выдачи файлов")
        logger.info("="*60)

        if download:
            export_result = export_with_report(
                df,
                output_folder="output",
                filename_main="cleaned_data",
                filename_report="processing_report"
            )

            if export_result["status"] == "ERROR":
                raise HTTPException(status_code=500, detail=export_result.get("error", "Ошибка экспорта Excel"))

            archive_files = [
                export_result.get("main_file"),
                export_result.get("report_file"),
                dedup_result.get("collisions_file"),
            ]

            missing_files = [path for path in archive_files if not path or not os.path.exists(path)]
            if missing_files:
                raise HTTPException(status_code=500, detail=f"Не удалось собрать ZIP: отсутствуют файлы {missing_files}")

            output = BytesIO()
            with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
                for file_path in archive_files:
                    archive.write(file_path, arcname=os.path.basename(file_path))
            output.seek(0)

            base_name = file.filename.rsplit('.', 1)[0]   # без расширения
            safe_filename = f"cleaned_{base_name}.zip"
            encoded_filename = quote(safe_filename, safe='')

            headers = {
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
            return StreamingResponse(
                output,
                media_type="application/zip",
                headers=headers
            )

        return {
            "status": mapper_result["status"],
            "validation": str(upload_result.validation_info),
            "rows": len(df),
            "columns": list(df.columns),
            "quality": quality_report,
            "data": clean_data
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)