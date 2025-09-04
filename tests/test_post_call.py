from types import SimpleNamespace
from sqlmodel import select
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.config import settings
from app.models import Call, TwilioCall, TwilioCallEvent
from app.enum import TwilioCallStatus
from app.graphql import create_widget_action_gql, get_widget_gql


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

def get_payload():
    return {
        "activist": { "first_name": "Test", "last_name": "Unit", "name": "Test Unit", "phone": "+5531998899876", "email": "test@unit.devel" },
        "target": {"name": "Target Name", "phone": "+5531998899875"},
        "widget_id": 12
    }


def test_call_success(client, mocker, session, mock_graphql_client):
    payload = get_payload()
    mock_client = mocker.patch("app.api.routes.call.client")
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=dict(id=0, kind="phone", settings=dict(targets=[payload.get("target")])))
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    resp = client.post("/v1/phone/call", json=payload)
    call = session.exec(select(Call)).first()

    assert resp.status_code == 200
    assert resp.json()["call_id"] == call.id
    assert resp.json()["twilio_call_sid"] == mock_response.sid


def test_call_create_event(client, mocker, session, mock_graphql_client):
    payload = get_payload()
    mock_client = mocker.patch("app.api.routes.call.client")
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=dict(id=0, kind="phone", settings=dict(targets=[payload.get("target")])))
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    client.post("/v1/phone/call", json=payload)
    call = session.exec(select(Call)).first()
    twilio_call = session.exec(select(TwilioCall)).first()
    twilio_call_event = session.exec(select(TwilioCallEvent)).first()


    assert twilio_call.parent_call.id == call.id
    assert twilio_call_event.twilio_call_sid == twilio_call.sid


def test_call_twilio_instruction_gather(client, mocker, session, mock_graphql_client):
    payload = get_payload()
    mock_client = mocker.patch("app.api.routes.call.client")
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=dict(id=0, kind="phone", settings=dict(targets=[payload.get("target")])))
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    client.post("/v1/phone/call", json=payload)
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


def test_call_graphql_execute(client, mocker, mock_graphql_client, session):
    payload = get_payload()
    mock_client = mocker.patch("app.api.routes.call.client")
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=dict(id=0, kind="phone", settings=dict(targets=[payload.get("target")])))
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    client.post("/v1/phone/call", json=payload)
    
    call = session.exec(select(Call)).first()
    
    first_call_args, first_call_kwargs = mock_graphql_client.execute.call_args_list[1]
    assert create_widget_action_gql == first_call_args[0]
    assert {
        "widget_id": payload.get("widget_id"),
        "activist": payload.get("activist"),
        "input": {
            "custom_fields": { "call": call.id }
        }
    } == first_call_kwargs.get("variable_values")


def test_call_search_widget(client, mocker, mock_graphql_client, session):
    payload = get_payload()
    mock_client = mocker.patch("app.api.routes.call.client")
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=dict(id=0, kind="phone", settings=dict(targets=[payload.get("target")])))
    
    
    # Simula a resposta completa do Twilio
    mock_response = get_mock_call()
    mock_client.calls.create.return_value = mock_response
    
    client.post("/v1/phone/call", json=payload)
    
    call = session.exec(select(Call)).first()
    
    # Pega os argumentos da primeira chamada
    first_call_args, first_call_kwargs = mock_graphql_client.execute.call_args_list[0]
    assert first_call_args[0] == get_widget_gql
    assert first_call_kwargs.get("variable_values") == {"widget_id": payload["widget_id"]}


def test_call_without_widget(client, mocker, mock_graphql_client):
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=None)
    
    payload = get_payload()
    resp = client.post("/v1/phone/call", json=payload)
    
    assert resp.status_code == 422
    assert resp.json()["detail"][0]["msg"] == "Widget not found."


def test_call_widget_not_phone(client, mocker, mock_graphql_client):
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=dict(kind="draft"))
    
    payload = get_payload()
    resp = client.post("/v1/phone/call", json=payload)
    
    assert resp.status_code == 422
    assert resp.json()["detail"][0]["msg"] == "Widget is not a 'phone' kind."
    
    
def test_call_widget_target_not_in_phone(client, mocker, mock_graphql_client):
    payload = get_payload()
    mock_graphql_client.execute.return_value = dict(widgets_by_pk=dict(kind="phone", settings=dict(targets=[
        dict(name="Alvo Teste", phone=payload.get("target").get("phone").replace("5", "7"))
    ])))
    resp = client.post("/v1/phone/call", json=payload)
    
    assert resp.status_code == 422
    assert resp.json()["detail"][0]["msg"] == "Target is not present in Widget settings."