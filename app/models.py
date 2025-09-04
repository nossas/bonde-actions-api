import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, func, JSON

from sqlmodel import SQLModel, Field, Relationship

from app.enum import CallState, TwilioCallStatus, TwilioAnsweredBy, EventType


def create_timestamp():
    return datetime.now(timezone.utc)

class Call(SQLModel, table=True):
    __tablename__ = "phone_calls"

    id: str | None = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    state: CallState = Field(sa_column=CallState.Column(), default=CallState.INITIATED)
    from_number: str
    to_number: str

    twilio_calls: List["TwilioCall"] = Relationship(back_populates="parent_call")
    
    created_at: Optional[datetime] = Field(default_factory=create_timestamp)
    updated_at: Optional[datetime] = Field(
        default_factory=create_timestamp,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )

    class Config:
        arbitrary_types_allowed = True


class TwilioCall(SQLModel, table=True):
    __tablename__ = "phone_twilio_calls"
    
    sid: str = Field(primary_key=True)
    status: TwilioCallStatus = Field(sa_column=TwilioCallStatus.Column())
    direction: str | None = Field(default=None)
    answered_by: TwilioAnsweredBy | None = Field(sa_column=TwilioAnsweredBy.Column(), default=None)
    
    parent_call_id: str = Field(foreign_key="phone_calls.id", index=True)
    parent_call: Call = Relationship(back_populates="twilio_calls")
    events: List["TwilioCallEvent"] = Relationship(back_populates="twilio_call")

    created_at: Optional[datetime] = Field(default_factory=create_timestamp)
    updated_at: Optional[datetime] = Field(
        default_factory=create_timestamp,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )
    
    class Config:
        arbitrary_types_allowed = True

class TwilioCallEvent(SQLModel, table=True):
    __tablename__ = "phone_twilio_call_events"
    
    id: int | None = Field(default=None, primary_key=True)
    event_type: EventType = Field(sa_column=EventType.Column())
    twilio_response: dict | None = Field(
        default=None,
        sa_column=Column(JSON)
    )
    
    twilio_call_sid: str = Field(foreign_key="phone_twilio_calls.sid", index=True)
    twilio_call: TwilioCall = Relationship(back_populates="events")
    
    created_at: Optional[datetime] = Field(default_factory=create_timestamp)
    updated_at: Optional[datetime] = Field(
        default_factory=create_timestamp,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )
    
    class Config:
        arbitrary_types_allowed = True


__all__ = [
    "Call",
    "TwilioCall",
    "TwilioCallEvent"
]