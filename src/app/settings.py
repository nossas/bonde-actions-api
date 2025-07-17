from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    model_config = SettingsConfigDict(case_sensitive=False)
