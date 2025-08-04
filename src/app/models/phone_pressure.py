from typing import Optional

from pydantic import BaseModel

class PhonePressureActivist(BaseModel):
    name: str
    email: str
    phone: str

class PhoneTarget(BaseModel):
    name: str
    phone: str

class PhonePressureCustomFields(BaseModel):
    target: PhoneTarget
    call: Optional[str] = ''
    status: Optional[str] = 'queued'

class PhonePressureInput(BaseModel):
    custom_fields: PhonePressureCustomFields

class PhonePressureAction(BaseModel):
    widget_id: int
    activist: PhonePressureActivist
    input: PhonePressureInput

class PhoneCallResponse(BaseModel):
    call: str
    status: str
