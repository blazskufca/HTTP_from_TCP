import logging
from logging import Logger
from typing import Optional

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H-%M-%S",
)


logger = logging.getLogger(__name__)

def get_logger(name:Optional[str]=None) -> Logger:
    if name:
        return logging.getLogger(f"tcp_to_http.{name}")
    return logger
