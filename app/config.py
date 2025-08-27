import logging
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "FastAPI + UV"
    base_url: str
    database_url: str
    debug: bool = True
    log_level: str = "INFO"
    # 
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    #
    graphql_api_url: str

    class Config:
        env_file = ".env"
    
    @property
    def get_log_level(self) -> int:
        """Converte a string LOG_LEVEL para a constante do logging.

        Returns:
            int: _description_
        """
        return getattr(logging, self.log_level.upper(), logging.INFO)

settings = Settings()