from fastapi import FastAPI

from api.upload import router as upload_router
from api.uploadV2 import router as upload_routerV2

app = FastAPI(
    title="ETL 4DK",
    version="1.0.0"
)

app.include_router(upload_router)
app.include_router(upload_routerV2)


@app.get("/")
def root():
    return {
        "message": "ETL 4DK",
        "status": "OK"
    }
    