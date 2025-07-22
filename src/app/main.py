from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_database_and_tables, select_latest_call_event
from app.models.phone_pressure import PhoneCall, PhoneCallResponse, PhonePressureAction
from app.models.twilio_callback import TwilioVoiceEvent
from app.services.bonde_graphql import create_widget_action
from app.services.twilio import twilio_call, twilio_voice_callback

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)

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

@app.post("/phone/widget_action")
async def save_widget_action(action: PhonePressureAction):
    return create_widget_action(action)
