from twilio.rest import Client
from twilio.twiml.voice_response import Dial, VoiceResponse

from app.models.phone_pressure import PhoneCall
from app.models.twilio_callback import TwilioCallEvent
from app.settings import Settings
from app.utils import get_logger

def get_twilio_client(settings: Settings):
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)

def twilio_call(input: PhoneCall, settings: Settings, server_url: str):
    activist_number = f"+55 {input.activist_number}"

    client = get_twilio_client(settings)

    response = VoiceResponse()
    dial = Dial(input.target_number, callerId=activist_number)
    response.append(dial)

    call = client.calls.create(
        from_=settings.twilio_phone_number,
        to=activist_number,
        status_callback=f"{server_url}/phone/status_callback",
        status_callback_method="POST",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        twiml=response,
    )

    return {
        "call": call.sid,
        "status": call.status,
    }

def twilio_voice_callback(event: TwilioCallEvent):
    logger = get_logger()
    logger.info(f"Voice Event: CallSid={event.CallSid}, Status={event.CallStatus}")

    return {
        "call": event.CallSid,
        "status": event.CallStatus,
    }
