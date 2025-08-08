from twilio.rest import Client
from twilio.twiml.voice_response import Dial, VoiceResponse

from app.database import save_call, save_call_event
from app.models.phone_pressure import PhoneCallResponse, PhonePressureAction
from app.models.twilio_callback import TwilioVoiceEvent
from app.services.bonde_graphql import create_widget_action
from app.settings import Settings, get_settings

def get_twilio_client(settings: Settings) -> Client:
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)

def twilio_call(action: PhonePressureAction) -> PhoneCallResponse:
    activist_number = f"+55 {action.activist.phone}"
    target_number = action.input.custom_fields.target.phone

    settings = get_settings()
    client = get_twilio_client(settings)

    response = VoiceResponse()
    dial = Dial(callerId=activist_number)
    dial.number(
        target_number,
        status_callback=f"{settings.callback_url}/phone/dial_callback",
        status_callback_method="POST",
        status_callback_event="initiated ringing answered completed",
    )
    response.append(dial)

    call = client.calls.create(
        from_=settings.twilio_phone_number,
        to=activist_number,
        status_callback=f"{settings.callback_url}/phone/status_callback",
        status_callback_method="POST",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        twiml=response,
    )

    action.input.custom_fields.call = call.sid
    action.input.custom_fields.status = call.status
    save_call(action, call)

    create_widget_action(action)

    return PhoneCallResponse(call=call.sid, status=call.status)

def twilio_dial_callback(event: TwilioVoiceEvent) -> PhoneCallResponse:
    print(vars(event))

    return PhoneCallResponse(call=event.CallSid, status=event.CallStatus)

def twilio_voice_callback(event: TwilioVoiceEvent) -> PhoneCallResponse:
    save_call_event(event)

    return PhoneCallResponse(call=event.CallSid, status=event.CallStatus)
