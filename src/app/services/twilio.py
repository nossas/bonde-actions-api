from twilio.rest import Client
from twilio.twiml.voice_response import Dial, VoiceResponse

from app.database import save_call, save_call_event
from app.models.phone_pressure import PhoneCall, PhoneCallResponse
from app.models.twilio_callback import TwilioVoiceEvent
from app.settings import Settings, get_settings

def get_twilio_client(settings: Settings) -> Client:
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)

def twilio_call(input: PhoneCall) -> PhoneCallResponse:
    activist_number = f"+55 {input.activist_number}"

    settings = get_settings()
    client = get_twilio_client(settings)

    response = VoiceResponse()
    dial = Dial(input.target_number, callerId=activist_number)
    response.append(dial)

    call = client.calls.create(
        from_=settings.twilio_phone_number,
        to=activist_number,
        status_callback=f"{settings.callback_url}/phone/status_callback",
        status_callback_method="POST",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        twiml=response,
    )

    save_call(input, call)

    return PhoneCallResponse(call=call.sid, status=call.status)

def twilio_voice_callback(event: TwilioVoiceEvent) -> PhoneCallResponse:
    save_call_event(event)

    return PhoneCallResponse(call=event.CallSid, status=event.CallStatus)
