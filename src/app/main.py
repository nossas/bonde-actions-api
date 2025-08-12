from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    create_database_and_tables,
    select_twilio_calls,
    update_twilio_call_event
)
from app.models.phone_pressure import PhoneCallResponse, PhonePressureAction
from app.models.twilio_callback import TwilioVoiceEvent
from app.services.twilio import twilio_call


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
def make_phone_call(phone_call: PhonePressureAction) -> PhoneCallResponse:
    return twilio_call(phone_call)


@app.post("/phone/status_callback")
def receive_phone_callback(
    event: Annotated[TwilioVoiceEvent, Form()],
) -> PhoneCallResponse:
    
    update_twilio_call_event(event)
    
    return PhoneCallResponse(call=event.CallSid, status=event.CallStatus)


@app.get("/phone/status")
def get_current_call_status(call: str) -> PhoneCallResponse:
    activist_call, target_call = select_twilio_calls(call)

    if activist_call is None:
        raise HTTPException(status_code=404)

    call_sid = activist_call.sid
    status = "queued"

    if activist_call.status == "failed":
        status = "canceled"
    elif activist_call.status in ("queued", "initiated", "ringing"):
        status = "initiated"
    elif activist_call.status == "in-progress" and target_call.status in ("queued", "initiated", "ringing"):
        status = "ringing"
    elif activist_call.status == "in-progress" and target_call.status == "in-progress":
        status = "in-progress"
    elif activist_call.status == "completed" and target_call.status == "failed":
        status = "failed"
    elif activist_call.status == "completed" and target_call.status == "busy":
        status = "busy"
    elif activist_call.status == "completed" and target_call.status == "no-answer":
        status = "no-answer"
    elif activist_call.status == "completed" and target_call.status == "completed":
        status = "completed"
    
    return PhoneCallResponse(call=call_sid, status=status)
