import enum
from typing import List, Optional
from datetime import datetime, timezone

# from sqlalchemy import event
from sqlalchemy import Column, DateTime, func, Enum
from sqlmodel import SQLModel, Field, Relationship


class CallStatus(str, enum.Enum):
    # Ligação iniciada
    INITIATED = "initiated"
    QUEUED = "queued"
    # Gather respondido, ligando para o alvo
    RINGING = "ringing"
    # Chamada conectada com o alvo
    IN_PROGRESS = "in-progress"
    # Alvo ocupado
    BUSY = "busy"
    # Ligação pro Ativista falhou ou foi atendido por caixa postal
    FAILED = "failed"
    # Alvo não atendeu
    NO_ANSWER = "no-answer"
    # Ligação completada com sucesso
    COMPLETED = "completed"
    
    def __str__(self):
        return self.value

class CallReason(str, enum.Enum):
    ANSWERED_VOICEMAIL = "answered-voicemail"
    
    def __str__(self):
        return self.value

class CallKind(str, enum.Enum):
    API = "api"
    DIAL = "dial"
    
    def __str__(self):
        return self.value


def create_timestamp():
    return datetime.now(timezone.utc)


class Call(SQLModel, table=True):
    __tablename__ = "phone_calls"
    id: int | None = Field(default=None, primary_key=True)
    from_phone_number: str
    from_call_sid: Optional[str] = Field(default=None, index=True)
    to_phone_number: str
    to_call_sid: Optional[str] = Field(default=None, index=True)
    status: CallStatus = Field(sa_column=Column(Enum(CallStatus, values_callable=lambda x: [e.value for e in x]), default=CallStatus.INITIATED))
    reason: Optional[CallReason] = Field(sa_column=Column(Enum(CallReason, values_callable=lambda x: [e.value for e in x]), default=None))
    created_at: datetime = Field(default_factory=create_timestamp)
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )

    twilio_calls: List["TwilioCall"] = Relationship(back_populates="call")


class TwilioCall(SQLModel, table=True):
    __tablename__ = "phone_twilio_calls"
    sid: str = Field(primary_key=True)
    call_id: int = Field(foreign_key="phone_calls.id", index=True)
    status: CallStatus = Field(sa_column=Column(Enum(CallStatus, values_callable=lambda x: [e.value for e in x])))
    answered_by: Optional[str] = Field(default=None)
    kind: CallKind = Field(sa_column=Column(Enum(CallKind, values_callable=lambda x: [e.value for e in x])))
    created_at: datetime = Field(default_factory=create_timestamp)
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )

    call: Optional[Call] = Relationship(back_populates="twilio_calls")
