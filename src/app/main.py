from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException

from app.database import create_database_and_tables, select_latest_call_event
from app.models.phone_pressure import PhoneCall, PhoneCallResponse
from app.models.twilio_callback import TwilioVoiceEvent
from app.services.twilio import twilio_call, twilio_voice_callback

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/phone/call")
def make_phone_call(phone_call: PhoneCall) -> PhoneCallResponse:
    return twilio_call(phone_call)

@app.get("/phone/status")
def get_current_call_status(call: str) -> PhoneCallResponse:
    if (event := select_latest_call_event(call_sid=call)) is not None:
        return event
    else:
        raise HTTPException(status_code=404)

@app.post("/phone/status_callback")
def receive_phone_callback(event: Annotated[TwilioVoiceEvent, Form()]) -> PhoneCallResponse:
    return twilio_voice_callback(event)
