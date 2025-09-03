from fastapi import APIRouter, Response, Request, HTTPException
from sqlmodel import select
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial, Gather

from app.config import settings
from app.logger import get_logger
from app.db import SessionDep
from app.graphql import GraphQLClientDep, create_widget_action_gql, get_widget_gql
from app.models import Call, TwilioCall, TwilioCallEvent
from app.enum import EventType, TwilioCallStatus, TwilioAnsweredBy, CallState
from app.machine import CallMachine
from app.api.typing import CreateCallPayload


logger = get_logger(__name__)

router = APIRouter(prefix="/phone", tags=["Phone"])
base_url = settings.base_url + "/v1/phone"

client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


@router.post("/call")
async def call(
    payload: CreateCallPayload,
    session: SessionDep,
    graphql_client: GraphQLClientDep
):
    """Inicia uma ligação lógica e dispara instrução Twiml

    Args:
        payload (CreateCallPayload): _description_
        session (SessionDep): _description_

    Returns:
        _type_: _description_
    """
    # Validações de dados no BONDE
    result = await graphql_client.execute(
        get_widget_gql, variable_values=dict(widget_id=payload.widget_id)
    )
    widget = result.get("widgets_by_pk")

    logger.debug("/call -> GraphQL result to get_widget")
    logger.debug(result)

    if not widget:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "widget_id"],
                    "msg": "Widget not found.",
                    "type": "value_error",
                }
            ],
        )
    elif widget and widget.get("kind") != "phone":
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "widget_id"],
                    "msg": "Widget is not a 'phone' kind.",
                    "type": "value_error",
                }
            ],
        )
    elif widget and not any(x.get("phone") == payload.target.phone for x in widget.get("settings", {}).get("targets", [])):
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "widget_id"],
                    "msg": "Target is not present in Widget settings.",
                    "type": "value_error",
                }
            ],
        )

    # Execução da função de ligar
    from_number = payload.activist.phone
    to_number = payload.target.phone

    # Criar ligação lógica
    call = Call(from_number=from_number, to_number=to_number)
    session.add(call)
    session.flush()

    # Preparar Instrução da Chamada no Twilio
    resp = VoiceResponse()
    resp.say(
        "Olá! Para confirmar o redirecionamento informe seu nome.",
        voice="Polly.Camila",
        language="pt-BR",
    )

    # Preparar Gather para fazer uma verificação de voz
    gather = Gather(
        input="speech", timeout=5, action=f"{base_url}/dial/{call.id}", method="POST"
    )
    resp.append(gather)

    # Se ninguém respondeu, desliga a ligação:
    resp.hangup()

    try:
        twilio_call_response = client.calls.create(
            to=payload.activist.phone,
            from_=settings.twilio_phone_number,
            status_callback=f"{base_url}/status-callback/{call.id}",
            status_callback_method="POST",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            machine_detection="Enable",
            async_amd=True,
            async_amd_status_callback=f"{base_url}/amd-status-callback/{call.id}",
            async_amd_status_callback_method="POST",
            twiml=str(resp),
        )

        # Criar TwilioCall
        twilio_call = TwilioCall(
            sid=twilio_call_response.sid,
            status=twilio_call_response.status,
            direction=twilio_call_response.direction,
            answered_by=twilio_call_response.answered_by,
            parent_call=call,
        )
        session.add(twilio_call)
        session.flush()

        logger.info("/call -> twilio_call")
        logger.info(twilio_call)

        # Criar TwilioCallEvent
        twilio_call_event = TwilioCallEvent(
            twilio_call=twilio_call,
            event_type=EventType.INSTRUCTION,
            twilio_response={
                "ApiVersion": twilio_call_response.api_version,
                "AnsweredBy": twilio_call_response.answered_by,
                "DateCreated": twilio_call_response.date_created,
                "Direction": twilio_call_response.direction,
                "Duration": twilio_call_response.duration,
                "From": twilio_call_response._from,
                "To": twilio_call_response.to,
                "CallSid": twilio_call_response.sid,
                "CallStatus": twilio_call_response.status,
                "StartTime": twilio_call_response.start_time,
                "Uri": twilio_call_response.uri,
            },
        )
        session.add(twilio_call_event)
        session.commit()

        logger.info("/call -> twilio_call_event")
        logger.info(twilio_call_event)

        # Insere uma ação na API do BONDE
        await graphql_client.execute(
            create_widget_action_gql,
            variable_values=dict(
                widget_id=payload.widget_id,
                activist=payload.activist.model_dump(),
                input=dict(custom_fields=dict(call=call.id)),
            ),
        )

        return {
            "call_id": call.id,
            "twilio_call_sid": twilio_call.sid,
            "twilio_call_status": twilio_call.status,
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error /call: {e}")
        raise


@router.post("/status-callback/{call_id}")
async def status_callback(call_id: str, request: Request, session: SessionDep):
    """Escuta os eventos da ligação de ORIGEM (outbound-api).

    Args:
        call_id (str): _description_
        request (Request): _description_
        session (SessionDep): _description_
    """
    payload = await request.form()

    twilio_call_sid = payload.get("CallSid")
    twilio_call_status = payload.get("CallStatus")

    # 1. Buscar TwilioCall
    statement = select(TwilioCall).where(TwilioCall.sid == twilio_call_sid)
    twilio_call = session.exec(statement).first()
    if not twilio_call:
        return {"error": "TwilioCall not found"}, 404

    # 2. Criar TwilioCallEvent
    twilio_call_event = TwilioCallEvent(
        twilio_call=twilio_call,
        event_type=EventType.STATUS_CALLBACK,
        twilio_response=dict(payload),
    )
    session.add(twilio_call_event)
    session.flush()

    # 3. Atualizar TwilioCall
    try:
        twilio_call.status = TwilioCallStatus(twilio_call_status)
        session.add(twilio_call)
        session.flush()
    except ValueError:
        logger.warning(f"Status inesperado do Twilio: {twilio_call_status}")
        session.rollback()
        raise

    # 4. Atualizar Call (via FSM)
    call = twilio_call.parent_call
    machine = CallMachine(call)
    logger.info(payload)

    match twilio_call_status:
        case TwilioCallStatus.INITIATED:
            # Ignoramos o status de iniciado, não serve pra nossa lógica
            pass
        case TwilioCallStatus.RINGING:
            machine.call()
        case TwilioCallStatus.IN_PROGRESS:
            machine.attend()
        case TwilioCallStatus.COMPLETED:
            machine.complete()
        case TwilioCallStatus.FAILED:
            machine.complete()
        case _:
            logger.info("@@ Diferente de INITIATED, RINGING, IN_PROGRESS, FAILED ou COMPLETED")

    session.add(call)
    session.commit()

    return {
        "call_id": call_id,
        "twilio_call_sid": twilio_call_sid,
        "twilio_call_status": twilio_call_status,
    }


@router.post("/amd-status-callback/{call_id}")
async def amd_status_callback(call_id: str, request: Request, session: SessionDep):
    """_summary_

    Args:
        call_id (str): _description_
        request (Request): _description_
        session (SessionDep): _description_
    """
    payload = await request.form()
    logger.info(payload)

    answered_by = payload.get("AnsweredBy")
    twilio_call_sid = payload.get("CallSid")

    # 1. Buscar TwilioCall
    statement = select(TwilioCall).where(TwilioCall.sid == twilio_call_sid)
    twilio_call = session.exec(statement).first()
    if not twilio_call:
        return {"error": "TwilioCall not found"}, 404

    # 2. Registrar evento
    twilio_call_event = TwilioCallEvent(
        twilio_call=twilio_call,
        event_type=EventType.AMD_CALLBACK,
        payload=dict(payload),
    )
    session.add(twilio_call_event)
    session.flush()

    # 3. Atualizar TwilioCall
    twilio_call.answered_by = answered_by
    session.add(twilio_call)

    # 3. Atualizar Call via FSM
    call = twilio_call.parent_call
    machine = CallMachine(call)

    if answered_by == TwilioAnsweredBy.HUMAN:
        machine.connect()
    else:
        machine.fail()

    session.add(call)
    session.commit()

    return {
        "call_id": call.id,
        "twilio_call_sid": twilio_call_sid,
        "twilio_call_answered_by": answered_by,
    }


@router.post("/dial/{call_id}")
async def dial(call_id: str, request: Request, session: SessionDep):
    """Confere o estada da ligação lógica para decidir fazer o redirecionamento ou encerrar.

    Args:
        call_id (str): _description_
        request (Request): _description_
        session (SessionDep): _description_

    Returns:
        _type_: _description_
    """
    payload = await request.form()
    logger.info("/dial ->> payload")
    logger.info(payload)

    twilio_call_sid = payload.get("CallSid")

    # 1. Buscar TwilioCall
    statement = select(TwilioCall).where(TwilioCall.sid == twilio_call_sid)
    twilio_call = session.exec(statement).first()
    if not twilio_call:
        return {"error": "TwilioCall not found"}, 404

    call = twilio_call.parent_call
    if call.state == CallState.REDIRECTING:
        # Preparar a instrução Twiml para fazer o redirecionamento
        resp = VoiceResponse()
        resp.say(
            "Obrigado! Vamos te conectar ao alvo, aguarde na linha",
            voice="Polly.Camila",
            language="pt-BR",
        )

        dial = Dial(caller_id=call.from_number)
        dial.number(
            call.to_number,
            status_callback=f"{base_url}/dial-status-callback/{call.id}",
            status_callback_event="initiated ringing answered completed",
            status_callback_method="POST",
            machine_detection="Enable",
            amd_status_callback=f"{base_url}/dial-amd-status-callback/{call.id}",
            amd_status_callback_method="POST",
        )
        resp.append(dial)
    else:
        logger.info("@@ Reconhecimento de voz humana falhou")
        logger.info(call)

        # Instrução para desligar a chamada
        resp = VoiceResponse()
        resp.hangup()

    return Response(content=str(resp), media_type="application/xml")


@router.post("/dial-status-callback/{call_id}")
async def dial_status_callback(call_id: str, request: Request, session: SessionDep):
    """Escuta os eventos da ligação de DESTINO (DIAL inbound).

    Args:
        call_id (str): _description_
        request (Request): _description_
        session (SessionDep): _description_
    """
    payload = await request.form()
    logger.info("/dial-status-callback ->> payload")
    logger.info(payload)

    twilio_call_sid = payload.get("CallSid")
    twilio_call_status = payload.get("CallStatus")

    # 1. Buscar ligação do twilio na base e caso não exista criar novo registro
    statement = select(TwilioCall).where(TwilioCall.sid == twilio_call_sid)
    twilio_call = session.exec(statement).first()
    if not twilio_call:
        twilio_call = TwilioCall(
            parent_call_id=call_id,
            status=twilio_call_status,
            sid=twilio_call_sid,
            direction=payload.get("Direction"),
            answered_by=payload.get("AnsweredBy"),
        )
        session.add(twilio_call)
        session.flush()
    else:
        twilio_call.status = twilio_call_status
        if payload.get("AnsweredBy"):
            twilio_call.answered_by = payload.get("AnsweredBy")

        session.add(twilio_call)

    # 2. Registrar evento
    twilio_call_event = TwilioCallEvent(
        twilio_call=twilio_call,
        event_type=EventType.STATUS_CALLBACK,
        payload=dict(payload),
    )
    session.add(twilio_call_event)
    session.flush()

    # 3. Atualizar Call via FSM
    call = twilio_call.parent_call
    machine = CallMachine(call)

    match twilio_call_status:
        case TwilioCallStatus.INITIATED:
            # Ignoramos o status de iniciado, não serve pra nossa lógica
            pass
        case TwilioCallStatus.QUEUED:
            # Ignoramos o status de iniciado, não serve pra nossa lógica
            pass
        case TwilioCallStatus.RINGING:
            machine.dial_call()
        case TwilioCallStatus.IN_PROGRESS:
            machine.dial_attend()
        case TwilioCallStatus.NO_ANSWER:
            machine.dial_voicemail()
        case TwilioCallStatus.COMPLETED:
            machine.complete()
        case _:
            logger.info(
                "@@ Diferente de INITIATED, QUEUED, RINGING, IN_PROGRESS ou COMPLETED"
            )

    session.add(call)
    session.commit()

    return {
        "call_id": call.id,
        "twilio_call_sid": twilio_call_sid,
        "twilio_call_status": twilio_call_status,
    }


@router.post("/dial-amd-status-callback/{call_id}")
async def dial_amd_status_callback(call_id: str, request: Request, session: SessionDep):
    """_summary_

    Args:
        call_id (str): _description_
        request (Request): _description_
        session (SessionDep): _description_
    """
    payload = await request.form()
    logger.info("/dial-amd-status-callback ->> payload")
    logger.info(payload)

    answered_by = payload.get("AnsweredBy")
    twilio_call_sid = payload.get("CallSid")

    # 1. Buscar TwilioCall
    statement = select(TwilioCall).where(TwilioCall.sid == twilio_call_sid)
    twilio_call = session.exec(statement).first()
    if not twilio_call:
        return {"error": "TwilioCall not found"}, 404

    # 2. Registrar evento
    twilio_call_event = TwilioCallEvent(
        twilio_call=twilio_call,
        event_type=EventType.AMD_CALLBACK,
        payload=dict(payload),
    )
    session.add(twilio_call_event)
    session.flush()

    # 3. Atualizar TwilioCall
    twilio_call.answered_by = answered_by
    session.add(twilio_call)

    # 3. Atualizar Call via FSM
    call = twilio_call.parent_call
    machine = CallMachine(call)

    if answered_by == TwilioAnsweredBy.HUMAN:
        machine.dial_connect()
    elif answered_by in (
        TwilioAnsweredBy.MACHINE_START,
        TwilioAnsweredBy.MACHINE_START_BEEP,
        TwilioAnsweredBy.MACHINE_END,
        TwilioAnsweredBy.MACHINE_END_BEEP,
        TwilioAnsweredBy.FAX,
    ):
        machine.dial_voicemail()
    else:
        machine.fail()

    session.add(call)
    session.commit()

    return {
        "call_id": call.id,
        "twilio_call_sid": twilio_call_sid,
        "twilio_call_answered_by": answered_by,
    }


@router.get("/status/{call_id}")
async def status(call_id: str, session: SessionDep):
    call = session.exec(select(Call).where(Call.id == call_id)).first()

    status = None
    if call.state in (CallState.INITIATED, CallState.RINGING, CallState.ANSWERED):
        status = "initiated"
    elif call.state in (CallState.FAILED,):
        status = "canceled"
    elif call.state in (CallState.CONNECTED,):
        status = "in-progress"
    elif call.state in (
        CallState.REDIRECTING,
        CallState.DESTINATION_INITIATED,
        CallState.DESTINATION_RINGING,
        CallState.DESTINATION_ANSWERED,
    ):
        status = "ringing"
    elif call.state in (CallState.NO_ANSWERED,):
        status = "no-answer"
    elif call.state in (CallState.COMPLETED,):
        status = "completed"

    return {"call_id": call.id, "status": status}
