from functools import cache
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, desc, select
from twilio.rest.api.v2010.account.call import CallInstance

from app.models.phone_pressure import PhoneCallResponse, PhonePressureAction
from app.models.twilio_callback import TwilioVoiceEvent
from app.settings import get_settings

class TwilioCall(SQLModel, table=True):
    __tablename__: str = "twilio_call"
    call_sid: str = Field(primary_key=True)
    widget_id: int
    activist_number: str
    target_number: str

class TwilioCallEvent(SQLModel, table=True):
    __tablename__: str = "twilio_call_event"
    id: Optional[int] = Field(default=None, primary_key=True)
    call_sid: str = Field(foreign_key="twilio_call.call_sid", index=True)
    call_status: str

def create_database_and_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)

@cache
def get_engine():
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        pool_reset_on_return=None,
    )
    return engine

def get_session():
    engine = get_engine()
    return Session(engine)

def save_call(action: PhonePressureAction, call: CallInstance):
    db_call = TwilioCall(
        call_sid=call.sid,
        activist_number=action.activist.phone,
        target_number=action.input.custom_fields.target,
        widget_id=action.widget_id,
    )
    db_event = TwilioCallEvent(
        call_sid=call.sid,
        call_status=call.status,
    )

    with get_session() as session:
        session.add(db_call)
        session.add(db_event)
        session.commit()

def save_call_event(event: TwilioVoiceEvent):
    db_event = TwilioCallEvent(
        call_sid=event.CallSid,
        call_status=event.CallStatus,
    )

    with get_session() as session:
        session.add(db_event)
        session.commit()

def select_latest_call_event(call_sid: str):
    with get_session() as session:
        statement = select(TwilioCallEvent) \
            .where(TwilioCallEvent.call_sid == call_sid) \
            .order_by(desc(TwilioCallEvent.id))
        event = session.exec(statement).first()

    if event is None:
        return None
    else:
        return PhoneCallResponse(call=event.call_sid, status=event.call_status)
