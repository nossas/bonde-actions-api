from twilio.rest import Client
from twilio.twiml.voice_response import Dial, VoiceResponse

from app.settings import Settings

def get_twilio_client(settings: Settings):
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)

def twilio_call(activist_number: str, target_number: str,  settings: Settings):
    client = get_twilio_client(settings)

    response = VoiceResponse()
    dial = Dial(target_number)
    response.append(dial)

    call = client.calls.create(
        from_=settings.twilio_phone_number,
        to=activist_number,
        twiml=response,
    )

    return {
        "activist_number": activist_number,
        "target_number": target_number,
        "call": call.sid,
    }
