import uuid
from fastapi import APIRouter, Response, Request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/conference", tags=["Conference"])
base_url = settings.base_url + "/v1/conference"

client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
sessionID_to_callsid = {}


@router.post("/start")
async def start_conference(to: str):
    conference_id = uuid.uuid4()
    logger.debug(f"## Start Conference {conference_id} to {to}")

    call = client.calls.create(
        to=to,
        from_=settings.twilio_phone_number,
        url=f"{base_url}/create/{conference_id}",
        method="POST",
    )

    sessionID_to_callsid[conference_id] = call.sid

    return {"conference_id": conference_id, "call_sid": call.sid}


@router.post("/create/{conference_id}")
async def create_conference(conference_id: str, request: Request):
    logger.debug(f"## Create Conference {conference_id}")
    logger.debug(await request.form())
    resp = VoiceResponse()
    resp.say(
        "Olá! Você está conectado à conferência.",
        voice="Polly.Camila",
        language="pt-BR",
    )
    dial = Dial()
    dial.conference(
        conference_id,
        wait_url="",
        status_callback=f"{base_url}/leave/{conference_id}",
        status_callback_event="leave",
        status_callback_method="POST",
    )
    resp.append(dial)

    return Response(content=str(resp), media_type="application/xml")

@router.post("/leave/{conference_id}")
async def leave_conference(conference_id: str, request: Request):
    logger.debug(f"## Leave Conference {conference_id}")
    logger.debug(await request.form())
    
    return {"message": "Desconectar da conferência"}


@router.post("/join/{conference_id}")
async def join_conference(conference_id: str, to: str):
    logger.debug(f"## Join Conference {conference_id} to {to}")
    
    # Precisa de um número do Twilio ou um número verificado para fazer a ligação
    # do novo participante
    participant = client.conferences(conference_id).participants.create(
        from_=settings.twilio_phone_number,
        to=to,
        conference_status_callback=f"{base_url}/leave/{conference_id}",
        conference_status_callback_event="leave join",
        conference_status_callback_method="POST"
    )
    
    return {"conference_id": conference_id, "call_sid": participant.call_sid}