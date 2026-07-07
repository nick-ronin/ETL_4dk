from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import io
from typing import List

from db import get_db, SessionLocal
from .models import Company, Address, Contact, ActivityType
from .schemas import CompanySchema, AddressSchema, ContactSchema, ActivityTypeSchema
from .pand import twoGis_cleaning  

router = APIRouter(prefix="/models", tags=["models"])

@router.get("/users")
async def get_users():
    return {"Hello": "routers"}

@router.post("/upload_csv_twoGis_cleaning")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загружает CSV-файл, очищает телефоны и индексы, затем распределяет
    данные по таблицам: Company, Address, Contact, ActivityType.
    """
    # Проверка типа файла
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате CSV")

    try:
        # Читаем содержимое файла в pandas
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')), sep=',', encoding='utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка чтения CSV: {str(e)}")

    # Очистка данных
    try:
        cleaned_df = twoGis_cleaning(df)  # функция возвращает DataFrame с нужными колонками
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки данных: {str(e)}")

    # Проверка наличия обязательных колонок
    required_cols = {'Название', 'Город', 'Адрес', 'Индекс', 'Телефон', 
                     'Мобильный телефон', 'Email', 'Сайт', 'Подрубрика', 
                     'whatsapp', 'telegram', 'vkontakte'}
    if not required_cols.issubset(cleaned_df.columns):
        missing = required_cols - set(cleaned_df.columns)
        raise HTTPException(status_code=400, detail=f"Отсутствуют колонки: {missing}")

    # Обработка каждой строки
    for _, row in cleaned_df.iterrows():
        # 1. Создаём компанию
        company = Company(
            short_name=row['Название'],
            # Остальные поля модели Company остаются NULL
        )
        db.add(company)
        db.flush()  # чтобы получить company.id

        # 2. Адрес
        address = Address(
            company_id=company.id,
            address_type='фактический',
            address=row['Адрес'] if pd.notna(row['Адрес']) else None,
            city=row['Город'] if pd.notna(row['Город']) else None,
            postal_index=int(row['Индекс']) if pd.notna(row['Индекс']) else None
        )
        db.add(address)

        # 3. Контакты
        # Словарь: тип -> значение (может содержать несколько номеров через ', ')
        contacts_map = {
            'phone': row['Телефон'],
            'mobile': row['Мобильный телефон'],
            'email': row['Email'],
            'website': row['Сайт'],
            'whatsapp': row['whatsapp'],
            'telegram': row['telegram'],
            'vkontakte': row['vkontakte']
        }

        for contact_type, value in contacts_map.items():
            if pd.isna(value) or not str(value).strip():
                continue
            value = str(value).strip()
            # Для телефонов разбиваем по ', ' (если несколько номеров)
            if contact_type in ('phone', 'mobile'):
                # Если разделитель - запятая с пробелом, разбиваем
                parts = [p.strip() for p in value.split(', ') if p.strip()]
                for part in parts:
                    contact = Contact(
                        company_id=company.id,
                        contact_type=contact_type,
                        value=part
                    )
                    db.add(contact)
            else:
                # Остальные контакты (email, сайт, мессенджеры) – одно значение
                contact = Contact(
                    company_id=company.id,
                    contact_type=contact_type,
                    value=value
                )
                db.add(contact)

        # 4. Деятельность (подрубрика)
        if pd.notna(row['Подрубрика']) and str(row['Подрубрика']).strip():
            activity = ActivityType(
                company_id=company.id,
                activity_name=str(row['Подрубрика']).strip(),
                is_main=False  # так как это подрубрика, не основная (можно уточнить)
            )
            db.add(activity)

    # Фиксируем все изменения
    db.commit()

    return {
        "status": "success",
        "message": f"Загружено {len(cleaned_df)} записей",
        "rows_processed": len(cleaned_df)
    }