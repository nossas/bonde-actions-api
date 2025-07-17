from typing import Optional

from pydantic import BaseModel

class TwilioCallCallback(BaseModel):
    CallSid: str
    CallStatus: str
    From: str
    To: str
    Direction: Optional[str] = None
    Duration: Optional[str] = None
    AnsweredBy: Optional[str] = None
    Timestamp: Optional[str] = None
    ParentCallSid: Optional[str] = None
    RecordingUrl: Optional[str] = None
