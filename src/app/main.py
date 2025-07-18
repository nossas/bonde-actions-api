from typing import Annotated

from fastapi import Depends, FastAPI
from starlette.requests import Request

from app.models.phone_pressure import PhoneCall
from app.models.twilio_callback import TwilioCallEvent
from app.services.twilio import twilio_call, twilio_voice_callback
from app.settings import get_settings, Settings
from app.utils import get_server_url

app = FastAPI()

@app.get("/ping")
def root(request: Request):
    return get_server_url(request)

@app.post("/phone/call")
def make_phone_call(
    request: Request,
    phone_call: PhoneCall,
    settings: Annotated[Settings, Depends(get_settings)],
):
    return twilio_call(
        input=phone_call,
        settings=settings,
        server_url=get_server_url(request),
    )

@app.post("/phone/status_callback")
def receive_phone_callback(
    event: TwilioCallEvent,
):
    return twilio_voice_callback(event)
