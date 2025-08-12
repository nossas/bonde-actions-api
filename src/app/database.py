from datetime import datetime, timezone
from functools import cache
from typing import Optional, Tuple

from sqlmodel import Field, Session, SQLModel, create_engine, select
from twilio.rest.api.v2010.account.call import CallInstance
from app.models.twilio_callback import TwilioVoiceEvent
from sqlalchemy import event

from app.models.phone_pressure import PhonePressureAction
from app.models.twilio_callback import TwilioVoiceEvent
from app.settings import get_settings

def create_timestamp():
    return datetime.now(timezone.utc)


class Call(SQLModel, table=True):
    __tablename__: str = "phone_call"
    id: int | None = Field(default=None, primary_key=True)
    widget_id: int
    action_id: Optional[int] = None
    activist_number: str
    target_number: str
    created_at: datetime = Field(default_factory=create_timestamp)

class TwilioCall(SQLModel, table=True):
    __tablename__: str = "phone_twilio_call"
    call_id: int = Field(foreign_key="phone_call.id", index=True)
    sid: str = Field(primary_key=True)
    phone_to: str
    phone_from: str
    parent_call_sid: str | None
    status: str
    created_at: datetime = Field(default_factory=create_timestamp)
    updated_at: datetime = Field(default_factory=create_timestamp)
    
# Evento para atualizar automaticamente
@event.listens_for(TwilioCall, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    target.updated_at = create_timestamp()


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
    """_summary_

    Args:
        action (PhonePressureAction): _description_
        call (CallInstance): _description_
    """   
    with get_session() as session:
        try:
            db_call = Call(
                widget_id=action.widget_id,
                # action_id=
                activist_number=action.activist.phone,
                target_number=action.input.custom_fields.target.phone
            )
            session.add(db_call)
            session.flush()
            
            db_twilio_call = TwilioCall(
                call_id=db_call.id,
                sid=call.sid,
                phone_to=call.to,
                phone_from=call._from,
                parent_call_sid=call.parent_call_sid,
                status=call.status
            )
            session.add(db_twilio_call)
            session.commit()
        except:
            session.rollback()
            raise

def update_twilio_call_event(event: TwilioVoiceEvent) -> TwilioCall:
    """_summary_

    Args:
        event (TwilioVoiceEvent): _description_

    Raises:
        Exception: _description_
        Exception: _description_

    Returns:
        _type_: _description_
    """
    
    with get_session() as session:
        if event.Direction == "outbound-dial":
            # Update Target Call Event
            activist_call: TwilioCall | None = session.exec(
                select(TwilioCall).where(TwilioCall.sid == event.ParentCallSid)
            ).first()
            
            if not activist_call:
                raise Exception("ActivistCall not found, outbound-dial required register a parent call.")
            
            target_call: TwilioCall | None = session.exec(
                select(TwilioCall).where(TwilioCall.sid == event.CallSid)
            ).first()
            
            if not target_call:
                target_call = TwilioCall(
                    call_id=activist_call.call_id,
                    sid=event.CallSid,
                    phone_to=event.To,
                    phone_from=event.From,
                    parent_call_sid=event.ParentCallSid,
                    status=event.CallStatus
                )
            else:
                target_call.status = event.CallStatus
                
            session.add(target_call)
            session.commit()
            
            return target_call
        
        # Update Activist Call Event
        activist_call: TwilioCall | None = session.exec(
            select(TwilioCall).where(TwilioCall.sid == event.CallSid)
        ).first()
        
        if not activist_call:
            raise Exception("ActivistCall not found, outbound-api required register a call before.")
        
        activist_call.status = event.CallStatus
        
        session.add(activist_call)
        session.commit()
        
        return activist_call


def select_twilio_call(sid: str) -> TwilioCall | None:
    with get_session() as session:
        statement = select(TwilioCall) \
            .where(TwilioCall.sid == sid)
        event = session.exec(statement).first()
    
    return event


def select_twilio_calls(sid: str) -> Tuple[TwilioCall | None, TwilioCall | None]:
    with get_session() as session:
        statement = select(TwilioCall) \
            .where(TwilioCall.sid == sid)
        call = session.exec(statement).first()
        
        statement = select(TwilioCall) \
            .where(TwilioCall.parent_call_sid == sid)
        dial = session.exec(statement).first()
        
        return (call, dial)
    
    return (None, None)


def update_twilio_call(twilio_call: TwilioCall) -> TwilioCall:
    with get_session() as session:
        session.add(twilio_call)
        session.commit()
        session.refresh(twilio_call)
