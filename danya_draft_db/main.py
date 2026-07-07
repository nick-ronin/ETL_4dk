from fastapi import FastAPI
import pandas as pd
from all_models.router import router as models_router
from db import Base, engine

import all_models.models   

app = FastAPI()
app.include_router(models_router)
Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

