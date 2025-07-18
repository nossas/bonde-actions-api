from pydantic import BaseModel

class PhonePressureActivist(BaseModel):
    name: str
    email: str
    phone: str

class PhoneTarget(BaseModel):
    name: str
    phone: str

class PhonePressureCustomFields(BaseModel):
    status: str
    target: PhoneTarget

class PhonePressureInput(BaseModel):
    custom_fields: PhonePressureCustomFields

class PhonePressureAction(BaseModel):
    widget_id: int
    activist: PhonePressureActivist
    input: PhonePressureInput

class PhoneCall(BaseModel):
    activist_number: str
    target_number: str
    widget_id: int
