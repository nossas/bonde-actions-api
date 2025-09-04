# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes.call import router as call_router

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permite todos os domínios
    allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST"],  # permite todos os métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # permite todos os headers
)

# Prefixo para versão da API
app.include_router(call_router, prefix="/v1")


@app.get("/")
def root():
    return {"message": "Hello from FastAPI + uv"}