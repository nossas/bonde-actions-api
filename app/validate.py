import re
from pydantic_core import PydanticCustomError
from pydantic import GetCoreSchemaHandler
from pydantic import BaseModel
from pydantic.json_schema import JsonSchemaValue
from pydantic_core.core_schema import CoreSchema, no_info_plain_validator_function

# Regex para formato E.164 (ex: +5511912345678)
phone_regex = re.compile(r"^\+\d{1,3}\d{2}\d{8,9}$")


class PhoneNumberStr(str):
    """Custom type to validate phone number in format E.164"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        def validate(v: str) -> str:
            if not isinstance(v, str) or not phone_regex.match(v):
                raise PydanticCustomError(
                    "value_error",
                    "value is not a valid phone number: A phone number must have +5511912345678 format.",
                    dict(reason="A phone number must have +5511912345678 format.")
                )
            return v
    
        return no_info_plain_validator_function(validate)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetCoreSchemaHandler) -> JsonSchemaValue:
        schema = handler(core_schema)
        schema.update(type="string", example="+5511912345678")
        return schema
