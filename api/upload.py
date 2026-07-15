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
#import hashlib
import uuid

from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from service.source_loader.source_loader import process_uploaded_file
from service.source_mapper.source_mapper import process_file
from service.source_mapper.constants import MVP_COLUMNS
from service.normalizer.normalizer import clean_inn, clean_phone, clean_email, normalize_company_names, clean_address
from service.deduplicator.get_duplicates import get_duplicates
from service.quality.quality import calculate_data_quality_score
from service.exporter.exporter import save_data, build_summary_text, save_report

from service.logger.logger import get_log_writer

from service.file_cleaner.cleaner import rotate_files


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
    download: Optional[bool] = Query(True, description="True - Excel-файл, False - JSON")):
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

    # получение метаданных об источнике
    source_name = file.filename
    source_type = source_name.split('.')[1]
    now = datetime.now()
    source_date = now.strftime("%d-%m-%Y")

    # формирование информации для логгирования в файл по конкретному файлу
    log_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    log_dir = "output/log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{log_id}.log")

    write = get_log_writer(log_path)

    try:
        # Сохраняем загруженный файл во временный файл
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:
            temp.write(await file.read())
            temp_path = temp.name

        # ================================================
        # ШАГ 1: Загрузка файла и получение DataFrame
        # ================================================
        
        write("="*60)
        write("ШАГ 1/6: Загрузка файла и получение DataFrame")
        write("="*60)

        upload_result = process_uploaded_file(file_path=temp_path, log_file_path=log_path)

        if upload_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=upload_result.get('error', "Ошибка загрузчика"))
        
        df_raw = upload_result['df']

        # ================================================
        # ШАГ 2: Маппинг, валидация обязательных колонок, фильтрация колонок
        # ================================================

        write("="*60)
        write("ШАГ 2/6: Маппинг, валидация обязательных колонок, фильтрация колонок")
        write("="*60)

        mapper_result = process_file(df=df_raw, required_columns=MVP_COLUMNS, log_file_path=log_path)

        if mapper_result["status"] == "ERROR":
            raise HTTPException(status_code=400, detail=mapper_result.get("error", "Ошибка маппера"))

        df = mapper_result["df"]

        # ================================================
        # ШАГ 3: Нормализация данных
        # ================================================

        write("="*60)
        write("ШАГ 3/6: Нормализатор — очистка данных")
        write("="*60)
        
        df = normalize_company_names(df)
        write("✓ Названия компаний нормализованы")

        df['inn'] = df['inn'].apply(clean_inn)
        write("✓ ИНН очищены")
        
        df['phone'] = df['phone'].apply(clean_phone)
        write("✓ Телефоны очищены")
        
        df['email'] = df['email'].apply(clean_email)
        write("✓ Email очищены")

        df['address'] = df['address'].apply(clean_address)
        write("✓ Адреса очищены")

        df['has_email'] = df['email'].notna() & (df['email'] != '') & (df['email'] != '-')
        df['has_phone'] = df['phone'].notna() & (df['phone'] != '') & (df['phone'] != '-')

        # ================================================
        # ШАГ 4: Дедупликация
        # ================================================
        write("="*60)
        write("ШАГ 4/6: Дедупликатор — поиск коллизий")
        write("="*60)

        dup_columns = ['inn', 'email', 'phone', 'short_name']
        
        dup_columns = [c for c in dup_columns if c in df.columns]

        dedup_result = get_duplicates(
            df,
            columns=dup_columns,
            source_name=file.filename,           # имя исходного файла
            output_dir="output/collisions"
        )

        if 'duplicate_indices' in dedup_result:
            df['duplicate_flag'] = df.index.isin(dedup_result['duplicate_indices'])

        rotate_files("output/collisions", max_files=10) # удаляем лишние файлы 

        write(f"✓ Отчёт сохранён: {dedup_result['collisions_file']}")
        write(f"✓ Строк с коллизиями: {dedup_result['rows_affected']}")

        # ================================================
        # ШАГ 5: Расчёт качества данных
        # ================================================
        write("="*60)
        write("ШАГ 5/6: Расчёт качества данных")
        write("="*60)
         
        quality_report = calculate_data_quality_score(df, dedup_result)
        write(f'''✓ Quality Score рассчитан: {quality_report['overall_quality_score']}
                            Детально:
                            COMPLETENESS (Полнота) = {quality_report['metrics'].get("completeness")}
                            UNIQUENESS (Уникальность) = {quality_report['metrics'].get("uniqueness")}
                            ACCURACY (Точность / Валидность) = {quality_report['metrics'].get("accuracy")}
                            CONSISTENCY (Согласованность) = {quality_report['metrics'].get("consistency")}''')
        
        df['source_type'] = source_type
        df['source_name'] = source_name
        df['source_date'] = source_date

        #source_hash = hashlib.sha256(source_name.encode("utf-8")).hexdigest()[:8]
        # заменил source_hash на гарантированно уникальный log_id
        df["id"] = [
            f"{log_id}-{i+1:05d}"
            for i in range(len(df))
        ]

        clean_data = df.to_dict(orient='records')

        # ================================================
        # ШАГ 6: Формирование архива на выдачу
        # ================================================
        write("="*60)
        write("ШАГ 6/6: Формирование архива для выдачи файлов")
        write("="*60)

        if download:
            # 1. Экспорт очищенных данных
            data_export = save_data(df, output_folder="output/cleaned_data", base_name="cleaned_data")
            rotate_files("output/cleaned_data", max_files=10) # удаляем лишние файлы 

            if data_export['status'] == 'ERROR':
                raise HTTPException(status_code=500, detail=data_export.get('error'))

            # 2. Формирование текстового отчёта
            report_text = build_summary_text(
                filename=file.filename,
                date=source_date,
                rows=len(df),
                mapper_result=mapper_result,
                quality=quality_report,
                dedup=dedup_result,
                log_file_path=log_path
            )

            # 3. Сохранение отчёта в файл
            report_export = save_report(report_text, output_folder="output/processing_report", base_name="processing_report")
            rotate_files("output/processing_report", max_files=10) # удаляем лишние файлы 

            if report_export['status'] == 'ERROR':
                raise HTTPException(status_code=500, detail=report_export.get('error'))

            # 4. Подготовка архива
            archive_files = [
                data_export['file_path'],          # cleaned_data.xlsx
                report_export['file_path'],        # processing_report.txt
                dedup_result.get('collisions_file') # collisions.xlsx
            ]

            # Проверяем, что все файлы существуют
            for path in archive_files:
                if not path or not os.path.exists(path):
                    raise HTTPException(status_code=500, detail=f"Файл не найден: {path}")

            # Создаём ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for file_path in archive_files:
                    zf.write(file_path, arcname=os.path.basename(file_path))
            zip_buffer.seek(0)

            rotate_files("output/log", max_files=11, reserved=["app.log"]) # удаляем лишние файлы (11 для защищенного app.log)


            # Отдаём ответ
            safe_filename = quote(f"cleaned_{file.filename.rsplit('.', 1)[0]}.zip", safe='')
            headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"}
            return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
        
        response = {
            "status": mapper_result["status"],
            "validation": str(mapper_result.get("validation_result")),
            "rows": len(df),
            "columns": list(df.columns),
            "quality": quality_report,
            "data": clean_data
        }
        response = clean_json_value(response)
        return response


    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)