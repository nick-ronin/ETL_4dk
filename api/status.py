import json
import os
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["status"])

# Путь к deployment.json с инфой по последнему push 
DEPLOYMENT_FILE = "/var/www/db.vodalchuk.ru/deployment.json"


@router.get("/health")
async def health():
    # Простая проверка, что приложение отвечает
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    # Готовность к работе
    # тута в будущем проверка что бд поднялась и тд
    return {"status": "ready"}


@router.get("/deployment")
async def deployment():
    # Возвращает данные последнего деплоя из JSON-файла
    if not os.path.exists(DEPLOYMENT_FILE):
        return {"error": "deployment.json not found"}

    with open(DEPLOYMENT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data