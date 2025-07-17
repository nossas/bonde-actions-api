from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI
from twilio.rest import Client

from app.models.phone_pressure import PhoneCall
from app.services.twilio import twilio_call
from app.settings import Settings

app = FastAPI()

@lru_cache
def get_settings():
    return Settings()

@app.post("/phone_pressure/call")
def make_phone_call(
    phone_call: PhoneCall,
    settings: Annotated[Settings, Depends(get_settings)],
):
    return twilio_call(
        phone_call.activist_number,
        phone_call.target_number,
        settings,
    )
