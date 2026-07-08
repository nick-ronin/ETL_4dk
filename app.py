from fastapi import FastAPI

from api.upload import router as upload_router

app = FastAPI(
    title="ETL 4DK",
    version="1.0.0"
)

app.include_router(upload_router)

@app.get("/")
def root():
    return {
        "message": "ETL 4DK",
        "status": "OK"
    }
    