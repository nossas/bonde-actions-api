from types import SimpleNamespace
from sqlmodel import select
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.config import settings
from app.models import Call, TwilioCall, TwilioCallEvent
from app.enum import TwilioCallStatus


def get_mock_call(attrs = {}):
    values = {
        "sid": "fake_sid",
        "status": TwilioCallStatus.INITIATED,
        "answered_by": None,
        "direction": "outbound-api",
        "api_version": "2010-04-01",
        "date_created": "2025-08-22T14:00:00Z",
        "duration": 0,
        "_from": "+5531998899876",
        "to": "+5531998899875",
        "start_time": "2025-08-22T14:00:00Z",
        "uri": "/Calls/fake_sid.json",
        **attrs
    }
    return SimpleNamespace(**values)


def test_call_success(client, mocker, session):
    mock_client = mocker.patch("app.api.routes.call.client")
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    resp = client.post("/v1/phone/call", json={"from_phone_number": "+5531998899876", "to_phone_number": "+5531998899875"})
    call = session.exec(select(Call)).first()

    assert resp.status_code == 200
    assert resp.json()["call_id"] == call.id
    assert resp.json()["twilio_call_sid"] == mock_response.sid


def test_call_create_event(client, mocker, session):
    mock_client = mocker.patch("app.api.routes.call.client")
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    client.post("/v1/phone/call", json={"from_phone_number": "+5531998899876", "to_phone_number": "+5531998899875"})
    call = session.exec(select(Call)).first()
    twilio_call = session.exec(select(TwilioCall)).first()
    twilio_call_event = session.exec(select(TwilioCallEvent)).first()


    assert twilio_call.parent_call.id == call.id
    assert twilio_call_event.twilio_call_sid == twilio_call.sid


def test_call_twilio_instruction_gather(client, mocker, session):
    mock_client = mocker.patch("app.api.routes.call.client")
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    client.post("/v1/phone/call", json={"from_phone_number": "+5531998899876", "to_phone_number": "+5531998899875"})
    call = session.exec(select(Call)).first()
    
    resp = VoiceResponse()
    resp.say("Olá! Para confirmar o redirecionamento informe seu nome.", voice="Polly.Camila", language="pt-BR")
    resp.append(Gather(input="speech", timeout=5, action=f"{settings.base_url}/v1/phone/dial/{call.id}", method="POST"))
    resp.hangup()
    expected_twiml = str(resp)
    
    mock_client.calls.create.assert_called_once_with(
        to="+5531998899876",
        from_=settings.twilio_phone_number,
        status_callback=f"{settings.base_url}/v1/phone/status-callback/{call.id}",
        status_callback_method="POST",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        machine_detection="Enable",
        async_amd=True,
        async_amd_status_callback=f"{settings.base_url}/v1/phone/amd-status-callback/{call.id}",
        async_amd_status_callback_method="POST",
        twiml=expected_twiml,
    )