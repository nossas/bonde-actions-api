from typing import Optional, Literal
from pydantic import BaseModel


TwilioCallStatus = Literal[
    "initiated",
    "queued",
    "ringing",
    "in-progress",
    "canceled",
    "completed",
    "busy",
    "no-answer",
    "failed",
]


class TwilioEventStatusCallback(BaseModel):
    ParentCallSid: str
    Direction: str
    Timestamp: str
    SequenceNumber: str
    CallSid: str
    To: str
    ToCity: str
    ToState: str
    CallStatus: TwilioCallStatus
    AccountSid: str
    From: str
    FromCity: str
    FromState: str
    AnsweredBy: Optional[str] = None


class TwilioGather(BaseModel):
    To: str
    ToCity: str
    ToState: str
    CallSid: str
    CallStatus: TwilioCallStatus
    AccountSid: str
    SpeechResult: Optional[str] = None
    MachineDetectionDuration: Optional[int] = None
    Confidence: Optional[float] = None
    AnsweredBy: Optional[str] = None


class CreateCallPayload(BaseModel):
    from_phone_number: str
    to_phone_number: str