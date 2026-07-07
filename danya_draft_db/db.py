from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Путь к SQLite файлу (можно изменить)
SQLALCHEMY_DATABASE_URL = "sqlite:///./company_data.db"

# Для SQLite нужно отключить проверку внешних ключей (включаем её)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # необходимо для SQLite
    echo=False  # для отладки можно включить True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# База для моделей (импортируем из models.py)
Base = declarative_base()

# Зависимость FastAPI для получения сессии БД
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


