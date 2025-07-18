import logging
from starlette.requests import Request

def get_logger(name: str = "bonde"):
    logger = logging.getLogger(name)
    return logger

def get_server_url(request: Request):
    url = request.url
    return f"{url.scheme}://{url.netloc}"
