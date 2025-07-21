from functools import cache
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine
from twilio.rest.api.v2010.account.call import CallInstance

from app.models.phone_pressure import PhoneCall
from app.models.twilio_callback import TwilioVoiceEvent

class TwilioCall(SQLModel, table=True):
    __tablename__: str = "twilio_call"
    call_sid: str = Field(primary_key=True)
    widget_id: int
    activist_number: str
    target_number: str

class TwilioCallEvent(SQLModel, table=True):
    __tablename__: str = "twilio_call_event"
    id: Optional[int] = Field(default=None, primary_key=True)
    call_sid: str = Field(foreign_key="twilio_call.call_sid")
    call_status: str

def create_database_and_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)

@cache
def get_engine():
    sqlite_url = "sqlite:////code/db.sqlite3"
    connect_args = {
        "check_same_thread": False,
    }
    engine = create_engine(sqlite_url, connect_args=connect_args)
    return engine

def get_session():
    engine = get_engine()
    return Session(engine)

def save_call(input: PhoneCall, call: CallInstance):
    db_call = TwilioCall(
        call_sid=call.sid,
        activist_number=input.activist_number,
        target_number=input.target_number,
        widget_id=input.widget_id,
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
