from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    callback_url: str
    graphql_api_url: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    model_config = SettingsConfigDict(case_sensitive=False)

@cache
def get_settings():
    return Settings()
