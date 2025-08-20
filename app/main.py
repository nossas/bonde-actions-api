# app/main.py
from fastapi import FastAPI
from app.config import settings
from app.api.routes.conference import router as conference_router
from app.api.routes.call import router as call_router

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Prefixo para versão da API
app.include_router(conference_router, prefix="/v1")
app.include_router(call_router, prefix="/v1")


@app.get("/")
def root():
    return {"message": "Hello from FastAPI + uv"}