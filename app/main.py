# app/main.py
from fastapi import FastAPI
from app.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

@app.get("/")
def root():
    return {"message": "Hello from FastAPI + uv"}