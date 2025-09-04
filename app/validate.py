import re
from typing import Annotated
from pydantic import AfterValidator
from pydantic_core import PydanticCustomError

phone_regex = re.compile(r"^\+\d{1,3}\d{2}\d{8,9}$")

def _validate_phone(v: str) -> str:
    if not isinstance(v, str) or not phone_regex.match(v):
        raise PydanticCustomError(
            "phone_number",
            "value is not a valid phone number, expected format +5511912345678",
        )
    return v


PhoneNumberStr = Annotated[str, AfterValidator(_validate_phone)]
