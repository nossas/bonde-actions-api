from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form

from app.database import create_database_and_tables
from app.models.phone_pressure import PhoneCall
from app.models.twilio_callback import TwilioVoiceEvent
from app.services.twilio import twilio_call, twilio_voice_callback

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/phone/call")
def make_phone_call(phone_call: PhoneCall):
    return twilio_call(phone_call)

@app.post("/phone/status_callback")
def receive_phone_callback(event: Annotated[TwilioVoiceEvent, Form()]):
    return twilio_voice_callback(event)
