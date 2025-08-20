from typing import Annotated
from fastapi import APIRouter, Response, Request, Form
from sqlmodel import select
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial

from app.config import settings
from app.logger import get_logger
from app.db import SessionDep
from app.models import Call, TwilioCall, CallReason, CallStatus, CallKind
from app.api.typing import TwilioEventStatusCallback, TwilioGather


logger = get_logger(__name__)

router = APIRouter(prefix="/phone", tags=["Phone"])
base_url = settings.base_url + "/v1/phone"

client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


@router.post("/call")
async def make_call(from_phone_number: str, to_phone_number: str, session: SessionDep):
    logger.info(f"## Start Call to {from_phone_number}")

    try:
        # Inserir no banco de dados uma ligação
        call = Call(
            from_phone_number=from_phone_number, to_phone_number=to_phone_number
        )
        session.add(call)
        session.flush()

        # Prepara uma verificação de voz, para evitar o redirecionamento quando ligação cai na caixa postal
        resp = VoiceResponse()
        resp.say(
            "Olá! Para confirmar o redirecionamento informe seu nome.",
            voice="Polly.Camila",
            language="pt-BR",
        )
        resp.gather(
            input="speech",
            timeout=3,
            action=f"{base_url}/gather/{call.id}",
            method="POST",
        )

        # Realizar a chamada no Twilio
        twilio_call_response = client.calls.create(
            to=from_phone_number,
            from_=settings.twilio_phone_number,
            status_callback=f"{base_url}/call-status-callback/{call.id}",
            status_callback_method="POST",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            machine_detection="Enable",
            async_amd=True,
            async_amd_status_callback=f"{base_url}/amd-status-callback/{call.id}",
            async_amd_status_callback_method="POST",
            twiml=resp,
        )

        # Atualizar a referência da Chamada do Twilio na nossa Chamada
        call.from_call_sid = twilio_call_response.sid
        session.add(call)
        session.flush()

        # Inserir a Chamada do Twilio no banco de dados com o relacionamento
        twilio_call = TwilioCall(
            sid=twilio_call_response.sid,
            status=twilio_call_response.status,
            call_id=call.id,
            kind=CallKind.API,
        )
        session.add(twilio_call)
        session.commit()

        return {
            "call_sid": twilio_call_response.sid,
            "call_id": call.id,
            "call_status": twilio_call.status,
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error in make_call: {e}")


@router.post("/dial-status-callback/{call_id}")
async def dial_status_callback(
    call_id: int,
    request: Request,
    session: SessionDep,
    # event: Annotated[TwilioEventStatusCallback, Form()]
):
    form = await request.form()
    logger.info("## Dial Status Callback")
    logger.info(form)

    # create_or_update_twilio_call
    twilio_call = session.exec(
        select(TwilioCall).where(TwilioCall.sid == form.get("CallSid"))
    ).first()
    if twilio_call:
        twilio_call.status = form.get("CallStatus")

        answered_by = form.get("AnsweredBy", None)
        if answered_by:
            twilio_call.answered_by = answered_by

        session.add(twilio_call)
        session.commit()
    else:
        twilio_call = TwilioCall(
            call_id=call_id,
            sid=form.get("CallSid"),
            status=form.get("CallStatus"),
            kind=CallKind.DIAL,
        )

        answered_by = form.get("AnsweredBy", None)
        if answered_by:
            twilio_call.answered_by = answered_by

        session.add(twilio_call)
        session.commit()

    if twilio_call.status == CallStatus.COMPLETED:
        call = session.exec(
            select(Call).where(Call.id == call_id, Call.status == CallStatus.IN_PROGRESS),
        ).first()
        
        if call:
            logger.info("Tratar no caso de encerrar a ligação sem mapeamento")

    return {
        "call_id": call_id,
        "call_sid": twilio_call.sid,
        "call_status": twilio_call.status,
        "call_answered_by": twilio_call.answered_by,
    }


@router.post("/call-status-callback/{call_id}")
async def call_status_callback(
    call_id: int,
    request: Request,
    session: SessionDep,
    # event: Annotated[TwilioEventStatusCallback, Form()]
):
    form = await request.form()
    logger.info("## Call Status Callback")
    logger.info(form)

    twilio_call = session.exec(
        select(TwilioCall).where(TwilioCall.sid == form.get("CallSid"))
    ).first()
    if twilio_call:
        twilio_call.status = form.get("CallStatus")

        answered_by = form.get("AnsweredBy", None)
        if answered_by:
            twilio_call.answered_by = answered_by

        session.add(twilio_call)
        session.commit()
    else:
        twilio_call = TwilioCall(
            call_id=call_id,
            sid=form.get("CallSid"),
            status=form.get("CallStatus"),
            kind=CallKind.API,
        )

        answered_by = form.get("AnsweredBy", None)
        if answered_by:
            twilio_call.answered_by = answered_by

        session.add(twilio_call)
        session.commit()

    if twilio_call.status == CallStatus.COMPLETED:
        call = session.exec(
            select(Call).where(Call.id == call_id, Call.status.in_([CallStatus.RINGING, CallStatus.INITIATED])),
        ).first()
        
        twilio_call_dial = session.exec(
            select(TwilioCall).where(TwilioCall.call_id == call.id, TwilioCall.kind == CallKind.DIAL)
        ).first()
        
        # Nesse caso precisamos entender se o telefone foi atendido por humano
        # e se o problema foi na segunda ligação.
        if call and twilio_call_dial and twilio_call_dial.answered_by != "human":
            logger.info("Ligação foi atendida pelo Ativista, mas não foi atendida pelo alvo")
            call.status = CallStatus.NO_ANSWER
            session.add(call)
            session.commit()
        elif call and twilio_call_dial and twilio_call_dial.answered_by == "human":
            logger.info("Ligação foi atendida pelo Ativista, e pelo alvo")
            call.status = CallStatus.COMPLETED
            session.add(call)
            session.commit()
        else:
            logger.info("Tratar o caso de encerrar a ligação sem mapeamento")

    return {
        "call_id": call_id,
        "call_sid": twilio_call.sid,
        "call_status": twilio_call.status,
        "call_answered_by": twilio_call.answered_by,
    }


@router.post("/gather/{call_id}")
async def gather(
    call_id: int, session: SessionDep, gather: Annotated[TwilioGather, Form()]
):
    call = session.exec(select(Call).where(Call.id == call_id)).first()
    twilio_call = session.exec(
        select(TwilioCall).where(
            TwilioCall.call_id == call.id, TwilioCall.kind == CallKind.API
        )
    ).first()

    if (gather.AnsweredBy in ("machine_start", "machine_end")) or (
        twilio_call and twilio_call.answered_by in ("machine_start", "machine_end")
    ):
        # Testa duas hipóteses:
        # 1 - O próprio gather já responde com AnsweredBy
        # 2 - o AMD Status Callback já respondeu com AnsweredBy antes de executar o Gather
        logger.info(f"## Gather Complete, caixa postal")

        resp = VoiceResponse()
        resp.hangup()

        # Ligação para o ativista cai na caixa postal e redirecionamento não acontece
        call.status = CallStatus.FAILED
        call.reason = CallReason.ANSWERED_VOICEMAIL
        session.add(call)
        session.commit()

        return Response(content=str(resp), media_type="application/xml")

    # Realiza o redirecionamento
    logger.info(f"## Gather Complete, redirect to {call.to_phone_number}")
    logger.info(gather)

    resp = VoiceResponse()
    resp.say(
        "Obrigado! Vamos te conectar ao alvo, aguarde na linha",
        voice="Polly.Camila",
        language="pt-BR",
    )

    dial = Dial(caller_id=call.from_phone_number)
    dial.number(
        call.to_phone_number,
        status_callback=f"{base_url}/dial-status-callback/{call.id}",
        status_callback_event="ringing answered completed",
        status_callback_method="POST",
        machine_detection="Enable",
        amd_status_callback=f"{base_url}/amd-status-callback/{call.id}",
        amd_status_callback_method="POST",
    )
    resp.append(dial)

    # Confirma a instrução de redirecionamento e inicia o processo de ligação para o alvo
    call.status = CallStatus.RINGING
    session.add(call)
    session.commit()

    return Response(content=str(resp), media_type="application/xml")


@router.post("/amd-status-callback/{call_id}")
async def amd_status_callback(call_id: int, request: Request, session: SessionDep):
    form = await request.form()
    logger.info("## AMD Status Callback")
    logger.info(form)

    # call = session.exec(select(Call).where(Call.id == call_id)).first()
    twilio_call = session.exec(
        select(TwilioCall).where(TwilioCall.sid == form.get("CallSid"))
    ).first()
    twilio_call.answered_by = form.get("AnsweredBy")
    session.add(twilio_call)
    session.commit()

    return {
        "call_id": call_id,
        "call_sid": twilio_call.sid,
        "call_answered_by": twilio_call.answered_by,
    }
