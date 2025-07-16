from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI
from twilio.rest import Client

from .settings import Settings

app = FastAPI()

@lru_cache
def get_settings():
    return Settings()

def get_twilio_client(settings: Settings):
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)

@app.get("/")
def read_root(
    settings: Annotated[Settings, Depends(get_settings)],
):
    client = get_twilio_client(settings)
    return client.accounts.credentials.public_key.list()
